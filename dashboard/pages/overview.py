import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_data, load_model_comparison, RISK_COLORS

st.title("🏠 Executive Overview")
st.caption("A quick summary of financial distress risk across all companies we track.")

df = load_data()
latest_year = df["Year"].max()
latest = df[df["Year"] == latest_year].copy()

st.info(
    f"Showing the most recent year available in the data: **{latest_year}**. "
    "Every company below has its own Risk Score based on its own financial numbers."
)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Companies Tracked", df["Ticker"].nunique())
col2.metric("Distressed (labeled, any year)", int((df["Distress Status"] == 1).sum()))
col3.metric(f"Avg Risk Score ({latest_year})", f"{latest['Risk Score (0-100)'].mean():.0f} / 100")
col4.metric("High Risk companies", int((latest["Risk Category"] == "High Risk").sum()))
col5.metric("Critical Risk companies", int((latest["Risk Category"] == "Critical Risk").sum()))

st.divider()

left, right = st.columns([1.2, 1])

with left:
    st.subheader("How many companies are in each risk category?")
    order = ["Very Low Risk", "Low Risk", "Moderate Risk", "High Risk", "Critical Risk"]
    counts = latest["Risk Category"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Risk Category", "Count"]
    fig = px.bar(
        counts, x="Risk Category", y="Count", color="Risk Category",
        color_discrete_map=RISK_COLORS, category_orders={"Risk Category": order}, text="Count",
    )
    fig.update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Model performance")
    st.caption("How well the early-warning model predicted distress one year ahead (5-fold cross-validation).")
    comp = load_model_comparison()
    st.dataframe(comp, use_container_width=True)
    st.caption(
        "We picked **XGBoost** as the main model — it had the best Recall (catches the most "
        "distressed companies) and the best ROC-AUC. See `reports/model_evaluation_report.md`."
    )

st.divider()

st.subheader("Companies to watch first (highest risk, most recent year)")
watch = latest.sort_values("Risk Score (0-100)", ascending=False).head(10)
st.dataframe(
    watch[["Company Name", "Ticker", "Industry", "Risk Score (0-100)", "Risk Category", "Number of Alerts"]],
    use_container_width=True, hide_index=True,
)

st.warning(
    "⚠️ **Please read before trusting these numbers too much:** this project is trained on a "
    "small dataset (about 49 usable examples). Treat this as an educational demo of how an "
    "early-warning system could work, not a certified financial rating. "
    "See `reports/target_and_sample_size_notes.md` for full details."
)
