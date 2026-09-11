"""
train.py
--------
Trains and compares 4 models for the EARLY-WARNING target
("financial data at Year T -> will the company be distressed at Year T+1?").

Because we only have 49 trustworthy rows (see reports/target_and_sample_size_notes.md),
we use Stratified 5-Fold Cross-Validation instead of a single train/test split.
This is the fair, honest way to evaluate a model on a small dataset.

We also fit each model one final time on ALL 49 usable rows, so we have one
saved model per algorithm that can generate a risk score for ANY company-year
(including 2024 and 2025 rows, where we don't have a trustworthy answer key,
but a prediction is still useful as an early warning).
"""

import copy
import json
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

TARGET_COL = "Target: Distress Next Year"

# Features: financial ratios only (level ratios, NOT year-over-year trend features).
#
# IMPORTANT LIMITATION (documented plainly): our only trustworthy training year is
# 2023 (see reports/target_and_sample_size_notes.md). But 2023 is the FIRST year in
# our data — there is no 2022 data to compare it against — so every single trend
# feature (Revenue Growth, ROA Change, Debt-to-Equity Change, Deterioration Score,
# etc.) is empty (NaN) for every 2023 row. We can still CALCULATE and DISPLAY trend
# features for 2024 and 2025 (shown on the dashboard and used in EDA), but we cannot
# train the model on them, because the one year we have real answers for has none of
# this information available. So the model below only uses "snapshot" ratios — what
# a company's liquidity/profit/debt/cash-flow ratios look like in a single year.
#
# We deliberately EXCLUDE raw dollar amounts (Revenue, Total Assets, etc.) as
# direct features, because company SIZE shouldn't be what predicts distress —
# ratios put companies on a level playing field. We also exclude anything
# derived from the label file itself (Distress Event, Distress Event Year,
# current-year Distress Status) since using those would leak the answer.
FEATURE_COLS = [
    "Current Ratio", "Quick Ratio", "Cash Ratio",
    "Net Profit Margin", "EBIT Margin", "ROA", "ROE",
    "Debt-to-Equity", "Debt Ratio", "Liabilities-to-Assets", "Interest Coverage",
    "Asset Turnover", "Inventory Turnover", "Receivables Turnover",
    "Operating Cash Flow Ratio", "CFO to Debt", "CFO to Net Income",
]

# These ARE calculated in the modeling dataset and shown on the dashboard / in EDA,
# but are excluded from FEATURE_COLS for the reason explained above.
TREND_FEATURE_COLS = [
    "Revenue Growth", "Net Income Growth", "EBIT Growth", "Total Debt Growth", "Asset Growth",
    "ROA Change", "ROE Change", "Current Ratio Change", "Debt-to-Equity Change",
    "Interest Coverage Change", "Operating Cash Flow Change", "Free Cash Flow Change",
    "Deterioration Score (0-8)",
]


def get_models():
    return {
        "Logistic Regression": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=0.5, random_state=42)),
        ]),
        "Decision Tree": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("clf", DecisionTreeClassifier(max_depth=3, min_samples_leaf=4, class_weight="balanced", random_state=42)),
        ]),
        "Random Forest": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=300, max_depth=4, min_samples_leaf=3,
                class_weight="balanced", random_state=42)),
        ]),
        "XGBoost": Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("clf", XGBClassifier(
                n_estimators=200, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                eval_metric="logloss", random_state=42,
                scale_pos_weight=(36 / 13),  # healthy / distressed ratio, to help with imbalance
            )),
        ]),
    }


def cross_validate_model(model, X, y, n_splits=5):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    metrics = {"accuracy": [], "precision": [], "recall": [], "f1": [], "roc_auc": []}
    oof_pred = np.zeros(len(y))
    oof_proba = np.zeros(len(y))

    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model_clone = copy.deepcopy(model)
        model_clone.fit(X_train, y_train)

        proba = model_clone.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)

        oof_pred[test_idx] = pred
        oof_proba[test_idx] = proba

        metrics["accuracy"].append(accuracy_score(y_test, pred))
        metrics["precision"].append(precision_score(y_test, pred, zero_division=0))
        metrics["recall"].append(recall_score(y_test, pred, zero_division=0))
        metrics["f1"].append(f1_score(y_test, pred, zero_division=0))
        try:
            metrics["roc_auc"].append(roc_auc_score(y_test, proba))
        except ValueError:
            pass  # happens if a fold has only one class present

    summary = {k: float(np.mean(v)) if len(v) else None for k, v in metrics.items()}
    return summary, oof_proba


def main():
    df = pd.read_csv("data/processed/modeling_dataset.csv")

    # Only 2023 rows have a trustworthy next-year target (see target_and_sample_size_notes.md)
    train_data = df[(df["Year"] == 2023) & (df[TARGET_COL].notna())].copy()
    print(f"Rows used for training/evaluation (2023 -> 2024 target only): {len(train_data)}")
    print(train_data[TARGET_COL].value_counts())

    X = train_data[FEATURE_COLS]
    y = train_data[TARGET_COL].astype(int)

    results = {}
    fitted_models = {}

    for name, model in get_models().items():
        print(f"\n--- {name} ---")
        summary, oof_proba = cross_validate_model(model, X, y)
        print(summary)
        results[name] = summary

        # fit final version on ALL usable rows, to use for scoring every company-year later
        model.fit(X, y)
        fitted_models[name] = model

    # Save comparison table
    comparison = pd.DataFrame(results).T
    comparison = comparison[["accuracy", "precision", "recall", "f1", "roc_auc"]]
    comparison.columns = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    comparison = comparison.round(3)
    comparison.to_csv("reports/model_comparison.csv")
    print("\n=== MODEL COMPARISON (5-fold cross-validation average) ===")
    print(comparison)

    # Save models
    for name, model in fitted_models.items():
        fname = name.lower().replace(" ", "_")
        joblib.dump(model, f"models/{fname}.pkl")
        print(f"Saved models/{fname}.pkl")

    # Save feature list + training row ids for reproducibility
    with open("models/feature_columns.json", "w") as f:
        json.dump(FEATURE_COLS, f, indent=2)

    return comparison


if __name__ == "__main__":
    main()
