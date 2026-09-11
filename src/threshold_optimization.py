"""
threshold_optimization.py
--------------------------
By default, a model says "distressed" only if its predicted probability is
above 50%. But in this project, MISSING a distressed company (a false
negative) is worse than raising a false alarm on a healthy one (a false
positive) — an investor or manager would rather double-check a company that
turns out fine, than be blindsided by one that fails.

So we test several thresholds and show the trade-off, instead of blindly
using 0.50.
"""

import copy
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

from train import FEATURE_COLS, TARGET_COL, get_models  # noqa: E402

THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70]


def get_oof_probabilities(model, X, y, n_splits=5):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof_proba = np.zeros(len(y))
    for train_idx, test_idx in skf.split(X, y):
        m = copy.deepcopy(model)
        m.fit(X.iloc[train_idx], y.iloc[train_idx])
        oof_proba[test_idx] = m.predict_proba(X.iloc[test_idx])[:, 1]
    return oof_proba


def main():
    df = pd.read_csv("data/processed/modeling_dataset.csv")
    train_data = df[(df["Year"] == 2023) & (df[TARGET_COL].notna())].copy()
    X = train_data[FEATURE_COLS]
    y = train_data[TARGET_COL].astype(int)

    models = get_models()
    best_model_name = "XGBoost"  # chosen for highest ROC-AUC + recall; see model_evaluation_report.md
    model = models[best_model_name]

    proba = get_oof_probabilities(model, X, y)

    rows = []
    for t in THRESHOLDS:
        pred = (proba >= t).astype(int)
        rows.append({
            "Threshold": t,
            "Precision": round(precision_score(y, pred, zero_division=0), 3),
            "Recall": round(recall_score(y, pred, zero_division=0), 3),
            "F1": round(f1_score(y, pred, zero_division=0), 3),
            "Flagged as High Risk": int(pred.sum()),
            "Actually Distressed Next Year": int(y.sum()),
        })

    table = pd.DataFrame(rows)
    table.to_csv("reports/threshold_analysis.csv", index=False)
    print(f"Threshold analysis for {best_model_name} (out-of-fold predictions):")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
