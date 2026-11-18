"""Export the tables the Power BI dashboard uses, and draw a preview of it.

Run after src/models.py:  python src/dashboard.py
Writes powerbi/data/*.csv and images/dashboard_preview.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BI = ROOT / "powerbi" / "data"
IMG = ROOT / "images"
BI.mkdir(parents=True, exist_ok=True)
IMG.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "data" / "creditcard.csv", usecols=["Time", "Amount", "Class"])
df["hour"] = (df["Time"] // 3600 % 24).astype(int)
bins = [-0.01, 0, 10, 50, 100, 500, 1000, float("inf")]
labels = ["Zero", "Under 10", "10-50", "50-100", "100-500", "500-1000", "1000+"]
df["amount_band"] = pd.cut(df["Amount"], bins=bins, labels=labels)


def rate(g):
    out = g["Class"].agg(transactions="count", frauds="sum").reset_index()
    out["fraud_rate_pct"] = (100 * out["frauds"] / out["transactions"]).round(3)
    return out


by_hour = rate(df.groupby("hour"))
by_band = rate(df.groupby("amount_band", observed=True))
by_hour.to_csv(BI / "fraud_by_hour.csv", index=False)
by_band.to_csv(BI / "fraud_by_amount_band.csv", index=False)

models = pd.read_csv(BI / "model_results.csv")
models = models[models["model"] != "Dummy"].sort_values("pr_auc")
curve = pd.read_csv(BI / "threshold_curve.csv")
best = models.iloc[-1]

INK, MUTED, BLUE, ORANGE, GRID = "#1f2937", "#6b7280", "#2563eb", "#ea580c", "#e5e7eb"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": INK,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlelocation": "left"})
fig = plt.figure(figsize=(14, 8.5), facecolor="white")
gs = fig.add_gridspec(3, 4, height_ratios=[0.5, 1.6, 1.6], hspace=0.55, wspace=0.35)
fig.suptitle("Credit card fraud: patterns and model results", x=0.06, ha="left",
             fontsize=15, fontweight="bold", color=INK)

kpis = [("Transactions", f"{len(df):,}"), ("Frauds", f"{int(df['Class'].sum()):,}"),
        ("Fraud rate", f"{100 * df['Class'].mean():.3f}%"),
        ("Best model PR-AUC", f"{best['pr_auc']:.3f}")]
for i, (label, value) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i])
    ax.axis("off")
    ax.text(0, 0.75, label, color=MUTED, fontsize=10, transform=ax.transAxes)
    ax.text(0, 0.05, value, color=INK, fontsize=20, fontweight="bold", transform=ax.transAxes)


def clean(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)


ax = fig.add_subplot(gs[1, :2])
ax.bar(by_hour["hour"], by_hour["fraud_rate_pct"], color=BLUE)
ax.set(title="Fraud rate by hour (hours since data start, mod 24)", xlabel="Hour", ylabel="Fraud rate %")
ax.set_xticks(range(0, 24, 2))
clean(ax)

ax = fig.add_subplot(gs[1, 2:])
ax.bar(by_band["amount_band"].astype(str), by_band["fraud_rate_pct"], color=BLUE)
ax.set(title="Fraud rate by amount band", xlabel="Amount", ylabel="Fraud rate %")
clean(ax)

ax = fig.add_subplot(gs[2, :2])
y = range(len(models))
ax.barh([v - 0.2 for v in y], models["pr_auc"], height=0.4, color=BLUE, label="PR-AUC")
ax.barh([v + 0.2 for v in y], models["f1"], height=0.4, color=ORANGE, label="F1 at tuned cutoff")
ax.set_yticks(list(y), models["model"])
ax.set(title="Model comparison (test set)", xlim=(0, 1))
ax.legend(loc="lower right", frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color=GRID)
ax.set_axisbelow(True)

ax = fig.add_subplot(gs[2, 2:])
ax.plot(curve["threshold"], curve["precision"], color=BLUE, label="Precision")
ax.plot(curve["threshold"], curve["recall"], color=ORANGE, label="Recall")
ax.plot(curve["threshold"], curve["f1"], color=INK, label="F1")
ax.axvline(best["tuned_threshold"], color=MUTED, ls="--", lw=1)
ax.text(best["tuned_threshold"] - 0.02, 0.05, f"cutoff {best['tuned_threshold']:.2f}", ha="right", color=MUTED)
ax.set(title=f"Threshold trade-off: {best['model']}", xlabel="Decision threshold", ylim=(0, 1.02))
ax.legend(loc="lower left", frameon=False, fontsize=9)
clean(ax)

fig.savefig(IMG / "dashboard_preview.png", dpi=110, bbox_inches="tight")
print("Saved", IMG / "dashboard_preview.png")
