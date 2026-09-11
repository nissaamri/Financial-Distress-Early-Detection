"""
Sanity checks on the financial ratio calculations.
"""

import pandas as pd
import numpy as np


def test_ratios_file_has_no_infinite_values():
    df = pd.read_csv("data/processed/financial_ratios.csv")
    numeric = df.select_dtypes(include=[np.number])
    assert not np.isinf(numeric.to_numpy()).any(), "Found infinite values — a division-by-zero wasn't handled."


def test_current_ratio_is_positive_when_present():
    df = pd.read_csv("data/processed/financial_ratios.csv")
    valid = df["Current Ratio"].dropna()
    assert (valid >= 0).all(), "Current Ratio should never be negative."


def test_free_cash_flow_equals_ocf_minus_capex():
    df = pd.read_csv("data/processed/financial_ratios.csv")
    calc = df["Operating Cash Flow"] - df["Capital Expenditure"]
    diff = (calc - df["Free Cash Flow"]).abs()
    assert (diff.dropna() < 1).all()
