"""
explainability.py
------------------
Uses SHAP to explain WHY the model thinks a company is risky.

SHAP gives each financial ratio a "contribution score" for one specific
company: how much did THIS ratio push the risk prediction up or down,
compared to an average company. Positive = pushed risk UP. Negative =
pushed risk DOWN (made the company look safer).
"""

import warnings

import joblib
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")

from train import FEATURE_COLS  # noqa: E402

BEST_MODEL_PATH = "models/xgboost.pkl"


def load_model_and_data():
    model = joblib.load(BEST_MODEL_PATH)
    df = pd.read_csv("data/processed/modeling_dataset.csv")
    return model, df


def get_shap_explainer(model, X_background):
    # our model is a Pipeline: [impute -> classifier]. SHAP's TreeExplainer needs
    # the raw classifier and already-imputed numbers.
    imputer = model.named_steps["impute"]
    clf = model.named_steps["clf"]
    X_imputed = pd.DataFrame(imputer.transform(X_background), columns=X_background.columns)
    explainer = shap.TreeExplainer(clf)
    return explainer, X_imputed


def compute_global_importance(explainer, X_imputed):
    shap_values = explainer.shap_values(X_imputed)
    # for binary classifiers, shap_values can be a list [class0, class1] or a 3D array
    if isinstance(shap_values, list):
        sv = shap_values[1]
    elif shap_values.ndim == 3:
        sv = shap_values[:, :, 1]
    else:
        sv = shap_values
    mean_abs = np.abs(sv).mean(axis=0)
    importance = pd.Series(mean_abs, index=X_imputed.columns).sort_values(ascending=False)
    return importance, sv


def explain_one_company(explainer, X_imputed, row_idx, feature_names, top_n=5):
    shap_values = explainer.shap_values(X_imputed.iloc[[row_idx]])
    if isinstance(shap_values, list):
        sv = shap_values[1][0]
    elif shap_values.ndim == 3:
        sv = shap_values[0, :, 1]
    else:
        sv = shap_values[0]

    contrib = pd.Series(sv, index=feature_names).sort_values(key=abs, ascending=False)
    top = contrib.head(top_n)
    explanation = []
    for feat, val in top.items():
        direction = "increases risk" if val > 0 else "decreases risk"
        explanation.append({"feature": feat, "shap_value": round(float(val), 4), "effect": direction})
    return explanation


def main():
    model, df = load_model_and_data()
    X_all = df[FEATURE_COLS]

    explainer, X_imputed = get_shap_explainer(model, X_all)

    importance, sv = compute_global_importance(explainer, X_imputed)
    importance.to_csv("reports/shap_global_importance.csv", header=["mean_abs_shap_value"])
    print("=== Top 10 Global Risk Drivers (SHAP) ===")
    print(importance.head(10))

    # save a plot
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 6))
    top15 = importance.head(15)[::-1]
    ax.barh(top15.index, top15.values, color="#2E86AB")
    ax.set_xlabel("Average impact on risk prediction (SHAP value)")
    ax.set_title("What drives the model's distress predictions? (Global)")
    fig.tight_layout()
    fig.savefig("reports/figures/11_shap_global_importance.png", dpi=130)
    plt.close(fig)
    print("Saved reports/figures/11_shap_global_importance.png")

    # save per-company local explanations for ALL rows (for dashboard use)
    all_explanations = []
    for idx in range(len(df)):
        exp = explain_one_company(explainer, X_imputed, idx, FEATURE_COLS, top_n=5)
        all_explanations.append({
            "Ticker": df.iloc[idx]["Ticker"],
            "Company Name": df.iloc[idx]["Company Name"],
            "Year": df.iloc[idx]["Year"],
            "top_risk_drivers": exp,
        })

    import json
    with open("reports/shap_local_explanations.json", "w") as f:
        json.dump(all_explanations, f, indent=2, default=str)
    print(f"Saved {len(all_explanations)} local SHAP explanations to reports/shap_local_explanations.json")


if __name__ == "__main__":
    main()
