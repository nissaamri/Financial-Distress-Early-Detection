"""
Sanity checks on the trained model and risk scores.
"""

import pandas as pd


def test_risk_scores_are_in_range():
    df = pd.read_csv("data/processed/company_risk_scores.csv")
    assert df["Risk Score (0-100)"].between(0, 100).all()


def test_probabilities_are_in_range():
    df = pd.read_csv("data/processed/company_risk_scores.csv")
    assert df["Distress Probability (Next Year)"].between(0, 1).all()


def test_every_company_has_a_risk_category():
    df = pd.read_csv("data/processed/company_risk_scores.csv")
    valid_categories = {"Very Low Risk", "Low Risk", "Moderate Risk", "High Risk", "Critical Risk"}
    assert set(df["Risk Category"].unique()).issubset(valid_categories)


def test_model_comparison_file_has_all_models():
    df = pd.read_csv("reports/model_comparison.csv", index_col=0)
    expected = {"Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"}
    assert expected.issubset(set(df.index))
