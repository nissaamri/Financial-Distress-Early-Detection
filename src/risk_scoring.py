"""
risk_scoring.py
----------------
Turns the model's raw probability (0.0 to 1.0) into a simple 0-100 score
that's easier for a non-technical person to read, plus a risk category.

We call this an "Internal Financial Distress Risk Score" — NOT an official
credit rating. It is only based on the numbers in our small dataset and our
own model, not a licensed rating agency methodology.
"""

import warnings

import joblib
import pandas as pd

warnings.filterwarnings("ignore")

from train import FEATURE_COLS  # noqa: E402

BEST_MODEL_PATH = "models/xgboost.pkl"
DECISION_THRESHOLD = 0.40  # see reports/threshold_analysis.csv for why


def probability_to_score(prob: float) -> int:
    """Simple linear mapping: probability 0.0-1.0 -> score 0-100."""
    return int(round(prob * 100))


def score_to_category(score: int) -> str:
    if score <= 20:
        return "Very Low Risk"
    elif score <= 40:
        return "Low Risk"
    elif score <= 60:
        return "Moderate Risk"
    elif score <= 80:
        return "High Risk"
    else:
        return "Critical Risk"


def build_early_warning_alerts(row: pd.Series) -> list:
    """Simple, configurable rule-based alerts. These are NOT laws of accounting —
    just common-sense warning thresholds used for illustration."""
    alerts = []
    if pd.notna(row.get("Current Ratio")) and row["Current Ratio"] < 1:
        alerts.append("Liquidity warning: Current Ratio is below 1 (short-term bills may exceed short-term assets)")
    if pd.notna(row.get("Debt-to-Equity Change")) and row["Debt-to-Equity Change"] > 0.2:
        alerts.append("Leverage warning: Debt-to-Equity is rising quickly year over year")
    if pd.notna(row.get("Interest Coverage")) and row["Interest Coverage"] < 1.5:
        alerts.append("Interest warning: Interest Coverage is below 1.5x (thin cushion to pay interest)")
    if pd.notna(row.get("Operating Cash Flow")) and row["Operating Cash Flow"] < 0:
        alerts.append("Cash-flow warning: Operating Cash Flow is negative")
    if pd.notna(row.get("ROA")) and row["ROA"] < 0:
        alerts.append("Profitability warning: ROA is negative (losing money relative to assets)")
    return alerts


def main():
    model = joblib.load(BEST_MODEL_PATH)
    df = pd.read_csv("data/processed/modeling_dataset.csv")

    X_all = df[FEATURE_COLS]
    probabilities = model.predict_proba(X_all)[:, 1]

    df["Distress Probability (Next Year)"] = probabilities.round(4)
    df["Risk Score (0-100)"] = [probability_to_score(p) for p in probabilities]
    df["Risk Category"] = [score_to_category(s) for s in df["Risk Score (0-100)"]]
    df["Flagged High Risk (>= 0.40 threshold)"] = probabilities >= DECISION_THRESHOLD

    df["Early Warning Alerts"] = df.apply(build_early_warning_alerts, axis=1)
    df["Number of Alerts"] = df["Early Warning Alerts"].apply(len)

    # Note which rows had a trustworthy answer key to check against
    df["Has Trustworthy Next-Year Answer"] = (df["Year"] == 2023) & df["Target: Distress Next Year"].notna()

    out_cols = [
        "Company Name", "Ticker", "Industry", "Year",
        "Distress Probability (Next Year)", "Risk Score (0-100)", "Risk Category",
        "Flagged High Risk (>= 0.40 threshold)", "Number of Alerts", "Has Trustworthy Next-Year Answer",
    ]
    df.to_csv("data/processed/company_risk_scores.csv", index=False)
    print("Saved data/processed/company_risk_scores.csv")
    print(df[out_cols].sort_values("Risk Score (0-100)", ascending=False).head(15).to_string(index=False))


if __name__ == "__main__":
    main()
