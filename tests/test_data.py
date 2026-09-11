"""
Simple sanity checks on the processed data.
Run with: pytest tests/
"""

import pandas as pd


def test_no_duplicate_company_years():
    df = pd.read_csv("data/processed/cleaned_financial_data.csv")
    assert df.duplicated(subset=["Ticker", "Year"]).sum() == 0


def test_merged_file_has_expected_rows():
    df = pd.read_csv("data/processed/merged_financial_distress.csv")
    # We expect the same number of rows as the cleaned financial file (left join)
    fin = pd.read_csv("data/processed/cleaned_financial_data.csv")
    assert len(df) == len(fin)


def test_no_negative_revenue():
    df = pd.read_csv("data/processed/cleaned_financial_data.csv")
    assert (df["Revenue"] < 0).sum() == 0


def test_total_debt_formula_holds():
    df = pd.read_csv("data/processed/cleaned_financial_data.csv")
    calc = df["Short-Term Debt"] + df["Long-Term Debt"]
    assert ((calc - df["Total Debt"]).abs() > 1).sum() == 0
