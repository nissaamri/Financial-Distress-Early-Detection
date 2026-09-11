"""
app.py
------
Main entry point for the Streamlit dashboard.
Run with:  streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Financial Distress Early-Warning System",
    page_icon="⚠️",
    layout="wide",
)

overview_page = st.Page("pages/overview.py", title="Executive Overview", icon="🏠")
company_page = st.Page("pages/company_risk.py", title="Company Risk Monitor", icon="🔎")
health_page = st.Page("pages/financial_health.py", title="Financial Health", icon="📈")
why_page = st.Page("pages/why_risky.py", title="Why Is This Company Risky?", icon="🧠")
warning_page = st.Page("pages/early_warning.py", title="Early-Warning Monitor", icon="🚨")
industry_page = st.Page("pages/industry_analysis.py", title="Industry Risk", icon="🏭")

nav = st.navigation([overview_page, company_page, health_page, why_page, warning_page, industry_page])
nav.run()
