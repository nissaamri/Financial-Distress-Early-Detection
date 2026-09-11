"""
feature_engineering.py
-----------------------
Two jobs:

1. Build "year-over-year change" features (trend features), like
   "did Revenue grow or shrink compared to last year?"
   These only ever look BACKWARD in time (this year vs last year),
   never forward — so we don't leak future information.

2. Build the EARLY-WARNING TARGET.
   Instead of predicting "is this company distressed THIS year"
   (which is really just re-stating a label we already have), we shift
   the label forward by one year:

       Financial data at Year T   -->   predict Distress Status at Year T+1

   If Year T+1 doesn't exist for a company (for example, there's no
   2026 data), we simply cannot build that row, and we drop it. We do
   NOT invent a future label.
"""

import numpy as np
import pandas as pd


TREND_BASE_COLS = {
    "Revenue": "Revenue Growth",
    "Net Income": "Net Income Growth",
    "Operating Profit / EBIT": "EBIT Growth",
    "Total Debt": "Total Debt Growth",
    "Total Assets": "Asset Growth",
    "ROA": "ROA Change",
    "ROE": "ROE Change",
    "Current Ratio": "Current Ratio Change",
    "Debt-to-Equity": "Debt-to-Equity Change",
    "Interest Coverage": "Interest Coverage Change",
    "Operating Cash Flow": "Operating Cash Flow Change",
    "Free Cash Flow": "Free Cash Flow Change",
}


def _pct_change(current, previous):
    """Percent change that returns NaN (instead of inf) when last year's value was 0."""
    previous_safe = previous.replace(0, np.nan)
    return (current - previous_safe) / previous_safe.abs()


def add_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["Ticker", "Year"]).copy()

    for base_col, new_col in TREND_BASE_COLS.items():
        prev = df.groupby("Ticker")[base_col].shift(1)
        if base_col in ("ROA", "ROE", "Current Ratio", "Debt-to-Equity", "Interest Coverage"):
            # These are already ratios, so we use a simple difference ("+0.02" = 2 percentage points),
            # not a percent-of-percent change, which is confusing.
            df[new_col] = df[base_col] - prev
        else:
            # These are dollar amounts, so a percent change is more meaningful.
            df[new_col] = _pct_change(df[base_col], prev)

    return df


def add_deterioration_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Simple yes/no flags that say 'this specific thing got worse this year'."""
    df = df.copy()
    df["Flag: ROA Declining"] = df["ROA Change"] < 0
    df["Flag: Revenue Declining"] = df["Revenue Growth"] < 0
    df["Flag: Debt Increasing"] = df["Total Debt Growth"] > 0
    df["Flag: Interest Coverage Declining"] = df["Interest Coverage Change"] < 0
    df["Flag: Operating Cash Flow Negative"] = df["Operating Cash Flow"] < 0
    df["Flag: Free Cash Flow Negative"] = df["Free Cash Flow"] < 0
    df["Flag: Current Ratio Declining"] = df["Current Ratio Change"] < 0
    df["Flag: Debt-to-Equity Increasing"] = df["Debt-to-Equity Change"] > 0

    flag_cols = [c for c in df.columns if c.startswith("Flag:")]
    df["Deterioration Score (0-8)"] = df[flag_cols].sum(axis=1)
    return df


def build_next_year_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    For every company-year row (Year = T), look up that SAME company's
    Distress Status at Year = T+1, and store it as 'Target: Distress Next Year'.
    If Year T+1 isn't in our data, the target is left as missing (NaN),
    and that row cannot be used for training an early-warning model
    (it can still be used to display current financial health).
    """
    df = df.copy()
    lookup = df.set_index(["Ticker", "Year"])["Distress Status"]

    def get_next_year_label(row):
        key = (row["Ticker"], row["Year"] + 1)
        if key in lookup.index:
            val = lookup.loc[key]
            # in case of any accidental duplicate keys, take the first value
            if isinstance(val, pd.Series):
                val = val.iloc[0]
            return val
        return np.nan

    df["Target: Distress Next Year"] = df.apply(get_next_year_label, axis=1)
    return df


def build_modeling_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = add_trend_features(df)
    df = add_deterioration_flags(df)
    df = build_next_year_target(df)
    return df


if __name__ == "__main__":
    ratios = pd.read_csv("data/processed/financial_ratios.csv")
    full = build_modeling_dataset(ratios)
    full.to_csv("data/processed/modeling_dataset.csv", index=False)
    print("Saved data/processed/modeling_dataset.csv:", full.shape)

    print("\nHow many rows have a usable next-year target?")
    print(full["Target: Distress Next Year"].value_counts(dropna=False))

    usable = full.dropna(subset=["Target: Distress Next Year"])
    print(f"\nRows usable for early-warning training (have a next-year label): {len(usable)}")
    print(f"Of those, distressed next year = 1: {(usable['Target: Distress Next Year']==1).sum()}")
    print(f"Of those, healthy next year = 0: {(usable['Target: Distress Next Year']==0).sum()}")
