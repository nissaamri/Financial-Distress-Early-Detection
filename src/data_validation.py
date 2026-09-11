"""
data_validation.py
-------------------
Simple checks on the raw data. These functions only LOOK at the data
and REPORT problems. They never change or delete anything.
Think of this file as a "health checkup" for the data.
"""

import pandas as pd


def check_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Count how many blanks (missing values) are in each column."""
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    return missing.rename("missing_count").to_frame()


def check_duplicates(df: pd.DataFrame, keys=None) -> dict:
    """Check for fully duplicated rows, and duplicated key combinations (e.g. Ticker+Year)."""
    result = {"duplicate_rows": int(df.duplicated().sum())}
    if keys:
        result["duplicate_key_rows"] = int(df.duplicated(subset=keys).sum())
    return result


def check_total_debt_formula(df: pd.DataFrame) -> pd.DataFrame:
    """Total Debt should equal Short-Term Debt + Long-Term Debt. Flags rows that don't match."""
    calc = df["Short-Term Debt"] + df["Long-Term Debt"]
    mismatch = (calc - df["Total Debt"]).abs() > 1  # allow $1 rounding
    return df.loc[mismatch, ["Company Name", "Ticker", "Year", "Short-Term Debt", "Long-Term Debt", "Total Debt"]]


def check_gross_profit_formula(df: pd.DataFrame) -> pd.DataFrame:
    """Gross Profit should equal Revenue - Cost of Sales. Flags rows that are noticeably off (>0.5% of revenue)."""
    calc = df["Revenue"] - df["Cost of Sales / COGS"]
    diff = (calc - df["Gross Profit"]).abs()
    threshold = 0.005 * df["Revenue"].abs()
    mismatch = diff > threshold
    return df.loc[mismatch, ["Company Name", "Ticker", "Year", "Revenue", "Cost of Sales / COGS", "Gross Profit"]]


def check_balance_sheet_identity(df: pd.DataFrame, tolerance_pct=0.02) -> pd.DataFrame:
    """Total Assets should equal Total Liabilities + Total Equity (accounting identity).
    Flags rows off by more than `tolerance_pct` of total assets. This is informational only —
    real company filings often have extra lines (e.g. non-controlling interests) we don't have."""
    calc = df["Total Liabilities"] + df["Total Equity"]
    diff = (calc - df["Total Assets"]).abs()
    mismatch = diff > (tolerance_pct * df["Total Assets"].abs())
    return df.loc[mismatch, ["Company Name", "Ticker", "Year", "Total Assets", "Total Liabilities", "Total Equity"]]


def check_negative_values(df: pd.DataFrame, columns) -> pd.DataFrame:
    """For columns that should normally never be negative (like Revenue or Total Assets),
    list any rows where they are negative."""
    out = {}
    for col in columns:
        if col in df.columns:
            neg_rows = df[df[col] < 0]
            if len(neg_rows) > 0:
                out[col] = neg_rows[["Company Name", "Ticker", "Year", col]]
    return out


def check_ticker_overlap(fin_df: pd.DataFrame, label_df: pd.DataFrame) -> dict:
    """Compare which companies appear in the financial data vs the label data."""
    fin_tickers = set(fin_df["Ticker"].unique())
    lab_tickers = set(label_df["Ticker"].unique())
    return {
        "only_in_labels": sorted(lab_tickers - fin_tickers),
        "only_in_financials": sorted(fin_tickers - lab_tickers),
        "in_both": len(fin_tickers & lab_tickers),
    }


def check_years_per_company(df: pd.DataFrame, expected_years=3) -> pd.DataFrame:
    """Flag companies that don't have the expected number of yearly rows."""
    counts = df.groupby("Ticker")["Year"].count()
    return counts[counts != expected_years].rename("num_years").to_frame()


def run_full_audit(fin_df: pd.DataFrame, label_df: pd.DataFrame) -> dict:
    """Run every check above and return one dictionary with everything, so we can
    print it or save it as a report."""
    report = {}
    report["missing_values"] = check_missing_values(fin_df)
    report["duplicates"] = check_duplicates(fin_df, keys=["Ticker", "Year"])
    report["total_debt_mismatches"] = check_total_debt_formula(fin_df)
    report["gross_profit_mismatches"] = check_gross_profit_formula(fin_df)
    report["balance_sheet_mismatches"] = check_balance_sheet_identity(fin_df)
    report["negative_value_flags"] = check_negative_values(
        fin_df, ["Revenue", "Total Assets", "Cash & Cash Equivalents", "Total Equity", "Operating Profit / EBIT"]
    )
    report["ticker_overlap"] = check_ticker_overlap(fin_df, label_df)
    report["years_per_company"] = check_years_per_company(fin_df)
    return report


if __name__ == "__main__":
    fin = pd.read_csv("data/raw/50-companies-financial.csv")
    lab = pd.read_csv("data/raw/distress_labels.csv")
    report = run_full_audit(fin, lab)
    for key, value in report.items():
        print(f"\n=== {key} ===")
        print(value)
