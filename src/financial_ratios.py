"""
financial_ratios.py
--------------------
Turns raw financial statement numbers into simple ratios that describe
a company's health. Ratios are easier to compare across companies of
very different sizes than raw dollar amounts.

Rule: if we can't safely divide (denominator is 0 or missing), the ratio
becomes "missing" (NaN) instead of a fake huge or infinite number.
"""

import numpy as np
import pandas as pd


def _safe_divide(numerator, denominator):
    """Divide two columns, but return NaN instead of infinity when the denominator is 0 or missing."""
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def add_liquidity_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Current Ratio"] = _safe_divide(df["Current Assets"], df["Current Liabilities"])
    df["Quick Ratio"] = _safe_divide(df["Current Assets"] - df["Inventory"], df["Current Liabilities"])
    df["Cash Ratio"] = _safe_divide(df["Cash & Cash Equivalents"], df["Current Liabilities"])
    return df


def add_profitability_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Net Profit Margin"] = _safe_divide(df["Net Income"], df["Revenue"])
    df["EBIT Margin"] = _safe_divide(df["Operating Profit / EBIT"], df["Revenue"])
    df["ROA"] = _safe_divide(df["Net Income"], df["Total Assets"])
    # ROE with negative or zero equity is misleading (a loss / negative equity gives a
    # deceptively "positive" ROE). We still calculate it but flag those rows.
    df["ROE"] = _safe_divide(df["Net Income"], df["Total Equity"])
    df["ROE_negative_equity_flag"] = df["Total Equity"] < 0
    return df


def add_leverage_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Debt-to-Equity"] = _safe_divide(df["Total Debt"], df["Total Equity"])
    df["Debt-to-Equity_negative_equity_flag"] = df["Total Equity"] < 0
    df["Debt Ratio"] = _safe_divide(df["Total Debt"], df["Total Assets"])
    df["Liabilities-to-Assets"] = _safe_divide(df["Total Liabilities"], df["Total Assets"])
    # Interest coverage: if a company has (almost) no interest expense, coverage is undefined,
    # not "infinitely safe" — we leave it missing rather than a huge fake number.
    df["Interest Coverage"] = _safe_divide(df["Operating Profit / EBIT"], df["Interest Expense"])
    return df


def add_efficiency_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Turnover ratios use an average of this year's and last year's balance where available.
    If last year isn't available (first year on record), we fall back to this year's ending balance."""
    df = df.copy()
    df = df.sort_values(["Ticker", "Year"])

    for col, avg_col in [("Inventory", "avg_inventory"), ("Accounts Receivable", "avg_receivables")]:
        prev = df.groupby("Ticker")[col].shift(1)
        df[avg_col] = np.where(prev.notna(), (df[col] + prev) / 2, df[col])

    df["Asset Turnover"] = _safe_divide(df["Revenue"], df["Total Assets"])
    df["Inventory Turnover"] = _safe_divide(df["Cost of Sales / COGS"], df["avg_inventory"])
    df["Receivables Turnover"] = _safe_divide(df["Revenue"], df["avg_receivables"])

    df = df.drop(columns=["avg_inventory", "avg_receivables"])
    return df


def add_cashflow_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Operating Cash Flow Ratio"] = _safe_divide(df["Operating Cash Flow"], df["Current Liabilities"])
    df["CFO to Debt"] = _safe_divide(df["Operating Cash Flow"], df["Total Debt"])
    df["Free Cash Flow"] = df["Operating Cash Flow"] - df["Capital Expenditure"]
    df["CFO to Net Income"] = _safe_divide(df["Operating Cash Flow"], df["Net Income"])
    return df


def build_all_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = add_liquidity_ratios(df)
    df = add_profitability_ratios(df)
    df = add_leverage_ratios(df)
    df = add_efficiency_ratios(df)
    df = add_cashflow_ratios(df)
    return df


if __name__ == "__main__":
    merged = pd.read_csv("data/processed/merged_financial_distress.csv")
    with_ratios = build_all_ratios(merged)
    with_ratios.to_csv("data/processed/financial_ratios.csv", index=False)
    print("Saved data/processed/financial_ratios.csv:", with_ratios.shape)
    ratio_cols = [
        "Current Ratio", "Quick Ratio", "Cash Ratio", "Net Profit Margin", "EBIT Margin",
        "ROA", "ROE", "Debt-to-Equity", "Debt Ratio", "Interest Coverage",
        "Asset Turnover", "Operating Cash Flow Ratio", "CFO to Debt", "Free Cash Flow",
    ]
    print(with_ratios[ratio_cols].describe().T[["count", "mean", "min", "max"]])
