"""
data_loader.py
---------------
Shared helper to load the final dataset once and share it across all
dashboard pages. Keeping this in one place means every page shows the
exact same numbers.
"""

import ast
import json
import os

import pandas as pd
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "company_risk_scores.csv")
SHAP_GLOBAL_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "shap_global_importance.csv")
SHAP_LOCAL_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "shap_local_explanations.json")
MODEL_COMPARISON_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "model_comparison.csv")


def _parse_list_column(val):
    """Some columns were saved as Python-list-looking strings (e.g. "['a', 'b']").
    This safely turns them back into real lists."""
    if isinstance(val, list):
        return val
    if pd.isna(val):
        return []
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return []


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    for col in ["Early Warning Alerts", "Management Recommendations"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_list_column)
    return df


@st.cache_data
def load_shap_global() -> pd.DataFrame:
    return pd.read_csv(SHAP_GLOBAL_PATH, index_col=0)


@st.cache_data
def load_shap_local() -> dict:
    with open(SHAP_LOCAL_PATH) as f:
        records = json.load(f)
    # index by (ticker, year) for quick lookup
    lookup = {}
    for r in records:
        lookup[(r["Ticker"], int(r["Year"]))] = r["top_risk_drivers"]
    return lookup


@st.cache_data
def load_model_comparison() -> pd.DataFrame:
    return pd.read_csv(MODEL_COMPARISON_PATH, index_col=0)


RISK_COLORS = {
    "Very Low Risk": "#4C956C",
    "Low Risk": "#8FC93A",
    "Moderate Risk": "#F4A300",
    "High Risk": "#F26419",
    "Critical Risk": "#D7263D",
}
