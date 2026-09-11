"""
data_cleaning.py
-----------------
Light-touch cleaning of the raw financial data.

RULES WE FOLLOW (see reports/data_quality_report.md for details):
- We do NOT invent numbers.
- We do NOT delete companies or rows just because a value looks unusual.
- We only fix things that are clearly just text/formatting problems
  (like extra spaces or a stray punctuation mark in a name).
- Missing numeric values stay missing (NaN). We do not guess-fill them.
"""

import pandas as pd


def clean_company_names(df: pd.DataFrame) -> pd.DataFrame:
    """Fix small text problems in company names (extra spaces, stray trailing punctuation).
    We do NOT change the actual company identity — Ticker is our real key, not the name."""
    df = df.copy()
    df["Company Name"] = (
        df["Company Name"]
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"\s*-\s*$", "", regex=True)  # trailing " -" like "Warner Bros. Discovery, Inc. -"
    )
    return df


def clean_tickers(df: pd.DataFrame) -> pd.DataFrame:
    """Make sure tickers are upper-case with no stray spaces."""
    df = df.copy()
    df["Ticker"] = df["Ticker"].str.strip().str.upper()
    return df


def clean_financial_data(fin: pd.DataFrame) -> pd.DataFrame:
    """Main cleaning function for the 50-companies-financial.csv file."""
    df = fin.copy()
    df = clean_company_names(df)
    df = clean_tickers(df)
    df["Industry"] = df["Industry"].str.strip()

    # Make sure Year is a whole number
    df["Year"] = df["Year"].astype(int)

    # Numeric columns should really be numbers, not text. Force conversion,
    # turning anything that can't be read as a number into a missing value (NaN)
    # instead of crashing or silently guessing.
    numeric_cols = [c for c in df.columns if c not in ("Company Name", "Ticker", "Industry", "Year")]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["Ticker", "Year"]).reset_index(drop=True)
    return df


def clean_label_data(lab: pd.DataFrame) -> pd.DataFrame:
    """Main cleaning function for the distress_labels.csv file."""
    df = lab.copy()
    df = clean_company_names(df)
    df = clean_tickers(df)
    df["Year"] = df["Year"].astype(int)
    df["Distress Status"] = pd.to_numeric(df["Distress Status"], errors="coerce").astype("Int64")
    df["Distress Event Year"] = pd.to_numeric(df["Distress Event Year"], errors="coerce")
    df = df.sort_values(["Ticker", "Year"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    fin = pd.read_csv("data/raw/50-companies-financial.csv")
    lab = pd.read_csv("data/raw/distress_labels.csv")

    fin_clean = clean_financial_data(fin)
    lab_clean = clean_label_data(lab)

    fin_clean.to_csv("data/processed/cleaned_financial_data.csv", index=False)
    lab_clean.to_csv("data/processed/cleaned_labels.csv", index=False)

    print("Saved data/processed/cleaned_financial_data.csv:", fin_clean.shape)
    print("Saved data/processed/cleaned_labels.csv:", lab_clean.shape)
