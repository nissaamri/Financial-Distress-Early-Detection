"""
merge_data.py
-------------
Joins the cleaned financial data with the cleaned distress labels.

We match on Ticker + Year (not company name), because names can be written
slightly differently ("AMC Entertainment Holdings, Inc." vs "...Inc"),
while tickers are a cleaner, more reliable ID. We use Company Name only
to double check the match makes sense.

We use a LEFT JOIN starting from the financial data, because financial
numbers are the input to our model. A company-year with no label just
means "we don't know the answer" for that row — we keep it, but we mark
it clearly instead of guessing.
"""

import pandas as pd


def merge_financial_and_labels(fin: pd.DataFrame, lab: pd.DataFrame) -> pd.DataFrame:
    lab_small = lab[["Ticker", "Year", "Distress Status", "Distress Event", "Distress Event Year"]]

    merged = fin.merge(lab_small, on=["Ticker", "Year"], how="left", indicator=True)

    matched = (merged["_merge"] == "both").sum()
    unmatched_financial = (merged["_merge"] == "left_only").sum()

    print(f"Financial rows: {len(fin)}")
    print(f"Label rows: {len(lab)}")
    print(f"Matched rows (financial + label found): {matched}")
    print(f"Financial rows with NO label found: {unmatched_financial}")

    if unmatched_financial > 0:
        missing = merged.loc[merged["_merge"] == "left_only", ["Company Name", "Ticker", "Year"]]
        print("Company-years with financial data but NO distress label (kept, marked as missing label):")
        print(missing.to_string(index=False))

    # Any label rows that never found a matching financial row (e.g. SATS)
    lab_tickers_years = set(zip(lab["Ticker"], lab["Year"]))
    fin_tickers_years = set(zip(fin["Ticker"], fin["Year"]))
    orphan_labels = lab_tickers_years - fin_tickers_years
    if orphan_labels:
        print(f"\nLabel rows with NO matching financial data (dropped, can't be used): {sorted(orphan_labels)}")

    merged = merged.drop(columns=["_merge"])
    return merged


if __name__ == "__main__":
    fin = pd.read_csv("data/processed/cleaned_financial_data.csv")
    lab = pd.read_csv("data/processed/cleaned_labels.csv")

    merged = merge_financial_and_labels(fin, lab)
    merged.to_csv("data/processed/merged_financial_distress.csv", index=False)
    print(f"\nSaved data/processed/merged_financial_distress.csv: {merged.shape}")
