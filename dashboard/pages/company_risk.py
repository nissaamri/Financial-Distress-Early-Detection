import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from data_loader import load_data, RISK_COLORS

def pd_notna(x):
    return pd.notna(x)


st.title("🔎 Company Risk Monitor")
st.caption("Pick a company to see its full risk picture.")

df = load_data()

companies = df[["Ticker", "Company Name"]].drop_duplicates().sort_values("Company Name")
company_labels = companies["Ticker"] + " — " + companies["Company Name"]
choice = st.selectbox("Choose a company", options=companies["Ticker"], format_func=lambda t: company_labels[companies["Ticker"] == t].values[0])

years_available = sorted(df[df["Ticker"] == choice]["Year"].unique())
year = st.select_slider("Year", options=years_available, value=years_available[-1])

row = df[(df["Ticker"] == choice) & (df["Year"] == year)].iloc[0]

st.divider()

# --- Header info ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Company", row["Ticker"])
c2.metric("Industry", row["Industry"])
c3.metric("Risk Score", f"{row['Risk Score (0-100)']} / 100")
c4.metric("Probability of Distress (next year)", f"{row['Distress Probability (Next Year)']*100:.1f}%")

color = RISK_COLORS.get(row["Risk Category"], "#888888")
st.markdown(
    f"<div style='padding:14px;border-radius:8px;background-color:{color}22;border:1px solid {color};'>"
    f"<span style='font-size:18px;font-weight:600;color:{color};'>Risk Category: {row['Risk Category']}</span>"
    f"</div>",
    unsafe_allow_html=True,
)

if not row["Has Trustworthy Next-Year Answer"]:
    st.caption(
        "ℹ️ This company-year wasn't part of our trustworthy training/testing set "
        "(see Data notes) — this is a live prediction, not a graded one."
    )

st.divider()

st.subheader("Financial health snapshot")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Liquidity", "Profitability", "Leverage", "Cash Flow", "Efficiency"])

with tab1:
    cols = st.columns(3)
    cols[0].metric("Current Ratio", f"{row['Current Ratio']:.2f}" if pd_notna(row['Current Ratio']) else "N/A")
    cols[1].metric("Quick Ratio", f"{row['Quick Ratio']:.2f}" if pd_notna(row['Quick Ratio']) else "N/A")
    cols[2].metric("Cash Ratio", f"{row['Cash Ratio']:.2f}" if pd_notna(row['Cash Ratio']) else "N/A")
    st.caption("Rule of thumb: Current Ratio below 1.0 means short-term bills may exceed short-term assets.")

with tab2:
    cols = st.columns(4)
    cols[0].metric("Net Profit Margin", f"{row['Net Profit Margin']*100:.1f}%" if pd_notna(row['Net Profit Margin']) else "N/A")
    cols[1].metric("EBIT Margin", f"{row['EBIT Margin']*100:.1f}%" if pd_notna(row['EBIT Margin']) else "N/A")
    cols[2].metric("ROA", f"{row['ROA']*100:.1f}%" if pd_notna(row['ROA']) else "N/A")
    cols[3].metric("ROE", f"{row['ROE']*100:.1f}%" if pd_notna(row['ROE']) else "N/A")
    if row.get("ROE_negative_equity_flag"):
        st.caption("⚠️ This company has negative Total Equity, so ROE can look misleadingly high or strange. Read it with caution.")

with tab3:
    cols = st.columns(3)
    cols[0].metric("Debt-to-Equity", f"{row['Debt-to-Equity']:.2f}" if pd_notna(row['Debt-to-Equity']) else "N/A")
    cols[1].metric("Debt Ratio", f"{row['Debt Ratio']:.2f}" if pd_notna(row['Debt Ratio']) else "N/A")
    cols[2].metric("Interest Coverage", f"{row['Interest Coverage']:.2f}x" if pd_notna(row['Interest Coverage']) else "N/A")
    if row.get("Debt-to-Equity_negative_equity_flag"):
        st.caption("⚠️ Negative Total Equity makes Debt-to-Equity look unusual (can even appear negative). Read it with caution.")

with tab4:
    cols = st.columns(3)
    cols[0].metric("Operating Cash Flow Ratio", f"{row['Operating Cash Flow Ratio']:.2f}" if pd_notna(row['Operating Cash Flow Ratio']) else "N/A")
    cols[1].metric("CFO to Debt", f"{row['CFO to Debt']:.2f}" if pd_notna(row['CFO to Debt']) else "N/A")
    cols[2].metric("Free Cash Flow", f"${row['Free Cash Flow']/1e9:.2f}B" if pd_notna(row['Free Cash Flow']) else "N/A")

with tab5:
    cols = st.columns(3)
    cols[0].metric("Asset Turnover", f"{row['Asset Turnover']:.2f}" if pd_notna(row['Asset Turnover']) else "N/A")
    cols[1].metric("Inventory Turnover", f"{row['Inventory Turnover']:.2f}" if pd_notna(row['Inventory Turnover']) else "N/A")
    cols[2].metric("Receivables Turnover", f"{row['Receivables Turnover']:.2f}" if pd_notna(row['Receivables Turnover']) else "N/A")

st.divider()

st.subheader("⚠️ Early-warning alerts")
alerts = row["Early Warning Alerts"]
if alerts:
    for a in alerts:
        st.error(a)
else:
    st.success("No alerts triggered for this company-year.")

st.subheader("✅ Management recommendations")
recs = row["Management Recommendations"]
for r in recs:
    st.markdown(f"- {r}")
