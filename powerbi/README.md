# Power BI dashboard

The tables in `data/` are made by `python src/models.py` and `python src/dashboard.py`.

| File | What it holds |
|---|---|
| `fraud_by_hour.csv` | Transactions, frauds and fraud rate for each hour (0-23) |
| `fraud_by_amount_band.csv` | The same, by amount band |
| `model_results.csv` | Every model's ROC-AUC, PR-AUC, precision, recall, F1 and tuned cutoff |
| `threshold_curve.csv` | Precision, recall and F1 of the best model at cutoffs 0.01-0.99 |
| `test_predictions.csv` | Test-set rows with the best model's score and flag |

## Build it

1. Power BI Desktop → Get data → Text/CSV, and load all five files.
2. **Cards:** total transactions, total frauds and fraud rate (from `fraud_by_hour`), plus the best `pr_auc` from `model_results`.
3. **Clustered column:** `fraud_by_hour`, hour on the axis, `fraud_rate_pct` as the value.
4. **Clustered column:** `fraud_by_amount_band`, band on the axis, `fraud_rate_pct` as the value.
5. **Clustered bar:** `model_results`, model on the axis, `pr_auc` and `f1` as values.
6. **Line chart:** `threshold_curve`, threshold on the axis, precision, recall and F1 as values.
7. **Table:** `model_results` with precision, recall, F1, frauds caught, frauds missed and false alarms.
8. Save as `powerbi/fraud_dashboard.pbix`, export a screenshot to `images/powerbi_dashboard.png`, and swap it into the main README.

`images/dashboard_preview.png` shows the same layout drawn in Python.
