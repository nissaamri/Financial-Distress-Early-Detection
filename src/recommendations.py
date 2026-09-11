"""
recommendations.py
-------------------
Turns a company's actual weak spots into plain-English management
recommendations. Every recommendation is tied to an actual number for that
company — no generic advice with nothing behind it.
"""

import pandas as pd


def get_recommendations(row: pd.Series) -> list:
    recs = []

    # --- Leverage ---
    if pd.notna(row.get("Debt-to-Equity")) and row["Debt-to-Equity"] > 2:
        recs.append(
            f"High leverage (Debt-to-Equity = {row['Debt-to-Equity']:.2f}): "
            "review debt restructuring, refinancing options, and whether capital "
            "spending can be reduced to pay down debt faster."
        )
    if pd.notna(row.get("Interest Coverage")) and row["Interest Coverage"] < 1.5:
        recs.append(
            f"Thin interest cushion (Interest Coverage = {row['Interest Coverage']:.2f}x): "
            "review the debt repayment schedule and consider renegotiating loan terms "
            "before interest costs become harder to cover."
        )

    # --- Liquidity ---
    if pd.notna(row.get("Current Ratio")) and row["Current Ratio"] < 1:
        recs.append(
            f"Weak liquidity (Current Ratio = {row['Current Ratio']:.2f}): "
            "review working capital, speed up receivables collection, and build up cash reserves "
            "to cover short-term obligations."
        )
    if pd.notna(row.get("Cash Ratio")) and row["Cash Ratio"] < 0.2:
        recs.append(
            f"Low cash cushion (Cash Ratio = {row['Cash Ratio']:.2f}): "
            "review immediate cash reserves against upcoming short-term bills."
        )

    # --- Cash flow ---
    if pd.notna(row.get("Operating Cash Flow")) and row["Operating Cash Flow"] < 0:
        recs.append(
            "Negative Operating Cash Flow: review day-to-day operating expenses, "
            "collection speed from customers, and payment terms with suppliers."
        )
    if pd.notna(row.get("Free Cash Flow")) and row["Free Cash Flow"] < 0:
        recs.append(
            "Negative Free Cash Flow: review capital expenditure plans — the company is "
            "spending more on operations and investment than it's bringing in."
        )

    # --- Profitability ---
    if pd.notna(row.get("ROA")) and row["ROA"] < 0:
        recs.append(
            f"Negative ROA ({row['ROA']:.2%}): review operating costs, pricing, and "
            "which business segments are dragging down overall profit."
        )
    if pd.notna(row.get("Net Profit Margin")) and row["Net Profit Margin"] < 0:
        recs.append(
            f"Negative Net Profit Margin ({row['Net Profit Margin']:.2%}): "
            "review pricing strategy and cost structure — the company is losing money on sales overall."
        )

    if not recs:
        recs.append("No major red flags found in the core ratios we track. Continue routine monitoring.")

    return recs


def main():
    df = pd.read_csv("data/processed/company_risk_scores.csv")
    df["Management Recommendations"] = df.apply(get_recommendations, axis=1)
    df.to_csv("data/processed/company_risk_scores.csv", index=False)
    print("Added 'Management Recommendations' column to data/processed/company_risk_scores.csv")

    # print an example for a high risk company
    example = df.sort_values("Risk Score (0-100)", ascending=False).iloc[0]
    print(f"\nExample — {example['Company Name']} ({example['Ticker']}, {example['Year']}):")
    for r in example["Management Recommendations"]:
        print(" -", r)


if __name__ == "__main__":
    main()
