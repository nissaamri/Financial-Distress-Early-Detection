import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from data_loader import load_data, RISK_COLORS

st.title("🚨 Early-Warning Monitor")
st.caption("Companies ranked from highest to lowest risk, for the year you pick.")

df = load_data()

years_available = sorted(df["Year"].unique())
year = st.select_slider("Year", options=years_available, value=years_available[-1])

view = df[df["Year"] == year].copy()
view = view.sort_values("Risk Score (0-100)", ascending=False).reset_index(drop=True)
view.insert(0, "Rank", view.index + 1)
view["Probability (%)"] = (view["Distress Probability (Next Year)"] * 100).round(0)

st.divider()

category_filter = st.multiselect(
    "Filter by risk category",
    options=["Very Low Risk", "Low Risk", "Moderate Risk", "High Risk", "Critical Risk"],
    default=["High Risk", "Critical Risk"],
)
if category_filter:
    view_filtered = view[view["Risk Category"].isin(category_filter)]
else:
    view_filtered = view

st.dataframe(
    view_filtered[[
        "Rank", "Company Name", "Ticker", "Industry",
        "Risk Score (0-100)", "Probability (%)", "Risk Category", "Number of Alerts",
    ]],
    use_container_width=True, hide_index=True,
    column_config={
        "Probability (%)": st.column_config.ProgressColumn("Probability", min_value=0, max_value=100, format="%.0f%%"),
        "Risk Score (0-100)": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100),
    },
)

st.caption(
    f"Showing {len(view_filtered)} of {len(view)} companies for {year}. "
    "Risk Score and Probability both reflect our model's estimate of distress risk in the FOLLOWING year."
)
