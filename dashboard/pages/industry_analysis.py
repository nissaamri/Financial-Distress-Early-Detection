import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_data

st.title("🏭 Industry Risk")
st.caption("Which industries look riskier overall, based on the companies in our dataset?")

df = load_data()

years_available = sorted(df["Year"].unique())
year = st.select_slider("Year", options=years_available, value=years_available[-1])
view = df[df["Year"] == year].copy()

st.divider()

industry_summary = (
    view.groupby("Industry")
    .agg(
        Companies=("Ticker", "nunique"),
        Avg_Risk_Score=("Risk Score (0-100)", "mean"),
        Distress_Rate=("Distress Status", "mean"),
        Avg_ROA=("ROA", "mean"),
        Avg_Debt_to_Equity=("Debt-to-Equity", "mean"),
        Avg_Current_Ratio=("Current Ratio", "mean"),
    )
    .reset_index()
    .sort_values("Avg_Risk_Score", ascending=False)
)
industry_summary["Distress_Rate"] = (industry_summary["Distress_Rate"] * 100).round(1)
industry_summary["Avg_Risk_Score"] = industry_summary["Avg_Risk_Score"].round(1)
industry_summary["Avg_ROA"] = (industry_summary["Avg_ROA"] * 100).round(2)
industry_summary["Avg_Debt_to_Equity"] = industry_summary["Avg_Debt_to_Equity"].round(2)
industry_summary["Avg_Current_Ratio"] = industry_summary["Avg_Current_Ratio"].round(2)

st.caption(
    "Note: most industries in this dataset only have 1-3 companies, so treat these "
    "averages as illustrative, not statistically robust."
)

fig = px.bar(
    industry_summary.head(15), x="Avg_Risk_Score", y="Industry", orientation="h",
    color="Avg_Risk_Score", color_continuous_scale="Reds",
    title=f"Average Risk Score by Industry ({year})",
)
fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Full industry breakdown")
st.dataframe(
    industry_summary.rename(columns={
        "Avg_Risk_Score": "Avg Risk Score",
        "Distress_Rate": "Distress Rate (%)",
        "Avg_ROA": "Avg ROA (%)",
        "Avg_Debt_to_Equity": "Avg Debt-to-Equity",
        "Avg_Current_Ratio": "Avg Current Ratio",
    }),
    use_container_width=True, hide_index=True,
)
