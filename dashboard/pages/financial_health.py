import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data_loader import load_data

st.title("📈 Financial Health")
st.caption("See how a company's key numbers have moved over time.")

df = load_data()

companies = df[["Ticker", "Company Name"]].drop_duplicates().sort_values("Company Name")
company_labels = companies["Ticker"] + " — " + companies["Company Name"]
choice = st.selectbox("Choose a company", options=companies["Ticker"], format_func=lambda t: company_labels[companies["Ticker"] == t].values[0])

hist = df[df["Ticker"] == choice].sort_values("Year")

st.divider()

metric_groups = {
    "Revenue & Profit ($ Billions)": ["Revenue", "Net Income", "Operating Profit / EBIT"],
    "Debt & Cash ($ Billions)": ["Total Debt", "Cash & Cash Equivalents"],
    "Cash Flow ($ Billions)": ["Operating Cash Flow", "Free Cash Flow"],
}

for title, cols in metric_groups.items():
    fig = go.Figure()
    for c in cols:
        fig.add_trace(go.Scatter(
            x=hist["Year"], y=hist[c] / 1e9, mode="lines+markers", name=c,
        ))
    fig.update_layout(title=title, yaxis_title="$ Billions", xaxis=dict(dtick=1), height=350,
                       margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Ratio trends")
ratio_groups = {
    "Profitability": ["ROA", "ROE"],
    "Leverage & Liquidity": ["Debt-to-Equity", "Current Ratio"],
    "Interest Coverage": ["Interest Coverage"],
}
cols = st.columns(3)
for i, (title, metrics) in enumerate(ratio_groups.items()):
    fig = go.Figure()
    for m in metrics:
        fig.add_trace(go.Scatter(x=hist["Year"], y=hist[m], mode="lines+markers", name=m))
    fig.update_layout(title=title, height=300, margin=dict(t=40, b=20), xaxis=dict(dtick=1))
    cols[i].plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Raw numbers")
show_cols = ["Year", "Revenue", "Net Income", "Operating Profit / EBIT", "Total Debt",
             "Cash & Cash Equivalents", "Operating Cash Flow", "Free Cash Flow",
             "ROA", "Debt-to-Equity", "Current Ratio", "Interest Coverage"]
st.dataframe(hist[show_cols].set_index("Year"), use_container_width=True)
