"""Compare models and tune the decision threshold.

Same setup as the original notebook: 60/20/20 stratified split, scaled features,
random undersampling of the training set. XGBoost is added, plus one XGBoost
trained on the full (not undersampled) training set with class weighting.

The threshold is picked on the validation set (real class balance) as the cutoff
with the best F1, then every number is reported on the untouched test set.

Run: python src/models.py   (expects data/creditcard.csv)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.under_sampling import RandomUnderSampler
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BI = ROOT / "powerbi" / "data"
OUT.mkdir(exist_ok=True)
BI.mkdir(parents=True, exist_ok=True)
SEED = 42

df = pd.read_csv(ROOT / "data" / "creditcard.csv")
X, y = df.drop(columns=["Class"]), df["Class"]
X_tv, X_test, y_tv, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
X_train, X_val, y_train, y_val = train_test_split(X_tv, y_tv, test_size=0.25, stratify=y_tv, random_state=SEED)

scaler = StandardScaler().fit(X_train)
X_train_s, X_val_s, X_test_s = (scaler.transform(a) for a in (X_train, X_val, X_test))
X_under, y_under = RandomUnderSampler(random_state=SEED).fit_resample(X_train_s, y_train)

spw = (y_train == 0).sum() / (y_train == 1).sum()
models = {
    "Dummy": (DummyClassifier(strategy="prior"), "under"),
    "Logistic Regression": (LogisticRegression(C=1.0, max_iter=10000), "under"),
    "Naive Bayes": (GaussianNB(), "under"),
    "Random Forest": (RandomForestClassifier(n_estimators=500, max_depth=10, min_samples_leaf=10,
                                             max_features="sqrt", n_jobs=-1, random_state=SEED), "under"),
    "XGBoost": (XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05, subsample=0.8,
                              colsample_bytree=0.8, eval_metric="aucpr", random_state=SEED), "under"),
    "XGBoost (full data, weighted)": (XGBClassifier(n_estimators=600, max_depth=5, learning_rate=0.05,
                                                    subsample=0.8, colsample_bytree=0.8,
                                                    scale_pos_weight=spw, eval_metric="aucpr",
                                                    random_state=SEED, n_jobs=-1), "full"),
}


def best_threshold(y_true, p):
    prec, rec, thr = precision_recall_curve(y_true, p)
    f1 = 2 * prec * rec / np.clip(prec + rec, 1e-12, None)
    i = int(np.nanargmax(f1[:-1])) if len(thr) else 0
    return float(thr[i]) if len(thr) else 0.5


def metrics(y_true, p, t):
    pred = (p >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return dict(precision=precision_score(y_true, pred, zero_division=0),
                recall=recall_score(y_true, pred, zero_division=0),
                f1=f1_score(y_true, pred, zero_division=0),
                tp=tp, fp=fp, fn=fn, tn=tn)


rows, probs = [], {}
for name, (model, data) in models.items():
    Xf, yf = (X_under, y_under) if data == "under" else (X_train_s, y_train)
    model.fit(Xf, yf)
    p_val = model.predict_proba(X_val_s)[:, 1]
    p_test = model.predict_proba(X_test_s)[:, 1]
    probs[name] = p_test
    t = best_threshold(y_val, p_val)
    base, tuned = metrics(y_test, p_test, 0.5), metrics(y_test, p_test, t)
    rows.append({
        "model": name, "train_data": "undersampled" if data == "under" else "full, class-weighted",
        "roc_auc": roc_auc_score(y_test, p_test), "pr_auc": average_precision_score(y_test, p_test),
        "precision@0.5": base["precision"], "recall@0.5": base["recall"], "f1@0.5": base["f1"],
        "false_alarms@0.5": base["fp"], "tuned_threshold": t,
        "precision": tuned["precision"], "recall": tuned["recall"], "f1": tuned["f1"],
        "frauds_caught": tuned["tp"], "frauds_missed": tuned["fn"], "false_alarms": tuned["fp"],
    })
    print(f"{name:32s} ROC-AUC {rows[-1]['roc_auc']:.4f}  PR-AUC {rows[-1]['pr_auc']:.4f}  "
          f"F1@0.5 {base['f1']:.3f}  F1@{t:.3f} {tuned['f1']:.3f}")

res = pd.DataFrame(rows)
res.round(4).to_csv(OUT / "model_comparison.csv", index=False)
res.round(4).to_csv(BI / "model_results.csv", index=False)

# Markdown table for the README
cols = ["model", "roc_auc", "pr_auc", "f1@0.5", "tuned_threshold", "precision", "recall", "f1",
        "frauds_caught", "frauds_missed", "false_alarms"]
md = res[cols].copy()
for c in ["roc_auc", "pr_auc", "f1@0.5", "precision", "recall", "f1"]:
    md[c] = md[c].map("{:.3f}".format)
md["tuned_threshold"] = md["tuned_threshold"].map("{:.4f}".format)
lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in md.itertuples(index=False)]
(OUT / "model_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

# PR curves on the test set
fig, ax = plt.subplots(figsize=(8, 6))
for name, p in probs.items():
    if name == "Dummy":
        continue
    prec, rec, _ = precision_recall_curve(y_test, p)
    ax.plot(rec, prec, label=f"{name} (PR-AUC {average_precision_score(y_test, p):.3f})")
ax.set(xlabel="Recall (share of fraud caught)", ylabel="Precision (share of alerts that are fraud)",
       title="Precision-recall on the test set")
ax.legend(loc="lower left", fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "pr_curves.png", dpi=120)

# Threshold trade-off for the best model
best = res.sort_values("pr_auc", ascending=False).iloc[0]
p = probs[best["model"]]
ts = np.linspace(0.01, 0.99, 99)
curve = pd.DataFrame([{"threshold": t, **metrics(y_test, p, t)} for t in ts])
curve.round(4).to_csv(BI / "threshold_curve.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 5))
for m in ["precision", "recall", "f1"]:
    ax.plot(curve["threshold"], curve[m], label=m.capitalize())
ax.axvline(best["tuned_threshold"], color="grey", ls="--", label=f"Chosen cutoff {best['tuned_threshold']:.2f}")
ax.set(xlabel="Decision threshold", ylabel="Score", title=f"Threshold trade-off: {best['model']}")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "threshold_tradeoff.png", dpi=120)

# Test-set predictions for Power BI
pred = X_test[["Time", "Amount"]].copy()
pred["hour"] = (pred["Time"] // 3600 % 24).astype(int)
pred["actual"] = y_test.values
pred["score"] = p.round(5)
pred["flagged"] = (p >= best["tuned_threshold"]).astype(int)
pred.to_csv(BI / "test_predictions.csv", index=False)
print("\nBest model:", best["model"], "| results in", OUT)
