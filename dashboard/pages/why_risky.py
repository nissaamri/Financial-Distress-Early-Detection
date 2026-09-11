import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_data, load_shap_global, load_shap_local

st.title("🧠 Why Is This Company Risky?")
st.caption(
    "We use a technique called SHAP to explain, in plain terms, which financial ratios "
    "pushed a company's risk prediction up or down."
)

df = load_data()
shap_global = load_shap_global()
shap_local = load_shap_local()

companies = df[["Ticker", "Company Name"]].drop_duplicates().sort_values("Company Name")
company_labels = companies["Ticker"] + " — " + companies["Company Name"]
choice = st.selectbox("Choose a company", options=companies["Ticker"], format_func=lambda t: company_labels[companies["Ticker"] == t].values[0])

years_available = sorted(df[df["Ticker"] == choice]["Year"].unique())
year = st.select_slider("Year", options=years_available, value=years_available[-1])

row = df[(df["Ticker"] == choice) & (df["Year"] == year)].iloc[0]

st.divider()

c1, c2 = st.columns([1, 2])
with c1:
    st.metric("Risk Probability", f"{row['Distress Probability (Next Year)']*100:.0f}%")
    st.metric("Risk Category", row["Risk Category"])

with c2:
    st.subheader("Main risk drivers for this company")
    drivers = shap_local.get((choice, int(year)), [])
    if drivers:
        for d in drivers:
            emoji = "🔴" if d["effect"] == "increases risk" else "🟢"
            label = "increases" if d["effect"] == "increases risk" else "decreases"
            st.markdown(f"{emoji} **{d['feature']}** — {label} this company's predicted risk")
    else:
        st.info("No SHAP explanation available for this company-year.")

st.divider()

st.subheader("Global view: what usually drives risk predictions across ALL companies?")
st.caption("This is not specific to one company — it shows which ratios matter most to the model in general.")

top15 = shap_global.sort_values("mean_abs_shap_value", ascending=True).tail(15)
fig = go.Figure(go.Bar(
    x=top15["mean_abs_shap_value"], y=top15.index, orientation="h",
    marker_color="#2E86AB",
))
fig.update_layout(
    xaxis_title="Average impact on risk prediction (higher = matters more)",
    height=500, margin=dict(l=10, t=10),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Note: SHAP shows correlation-based importance learned by the model on our small dataset — "
    "it is not proof of cause and effect."
)
