"""
eda.py
------
Makes simple charts comparing healthy companies vs distressed companies.
"Distressed" here means Distress Status = 1 for that company-year
(the CURRENT year label, which is what we have full data for).
Charts are saved as PNG images in reports/figures/.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
FIG_DIR = "reports/figures"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/{name}.png", dpi=130)
    plt.close(fig)
    print(f"Saved {FIG_DIR}/{name}.png")


def plot_class_distribution(df):
    fig, ax = plt.subplots(figsize=(5, 4))
    counts = df["Distress Status"].value_counts().sort_index()
    labels = ["Healthy (0)", "Distressed (1)"]
    ax.bar(labels, counts.values, color=["#4C956C", "#D7263D"])
    ax.set_title("How many companies are healthy vs distressed?")
    ax.set_ylabel("Number of company-years")
    for i, v in enumerate(counts.values):
        ax.text(i, v + 1, str(v), ha="center")
    save(fig, "01_class_distribution")


def plot_ratio_comparison(df, col, title, name):
    fig, ax = plt.subplots(figsize=(6, 4))
    plot_df = df[[col, "Distress Status"]].dropna()
    plot_df["Group"] = plot_df["Distress Status"].map({0: "Healthy", 1: "Distressed"})
    sns.boxplot(data=plot_df, x="Group", y=col, ax=ax, palette={"Healthy": "#4C956C", "Distressed": "#D7263D"},
                showfliers=False)
    ax.set_title(title)
    save(fig, name)


def plot_ocf_comparison(df):
    fig, ax = plt.subplots(figsize=(6, 4))
    plot_df = df[["Operating Cash Flow", "Distress Status"]].dropna()
    plot_df["Group"] = plot_df["Distress Status"].map({0: "Healthy", 1: "Distressed"})
    plot_df["OCF ($ Billion)"] = plot_df["Operating Cash Flow"] / 1e9
    sns.boxplot(data=plot_df, x="Group", y="OCF ($ Billion)", ax=ax,
                palette={"Healthy": "#4C956C", "Distressed": "#D7263D"}, showfliers=False)
    ax.set_title("Operating Cash Flow: Healthy vs Distressed")
    save(fig, "06_ocf_comparison")


def plot_revenue_growth_comparison(df):
    fig, ax = plt.subplots(figsize=(6, 4))
    plot_df = df[["Revenue Growth", "Distress Status"]].dropna()
    plot_df["Group"] = plot_df["Distress Status"].map({0: "Healthy", 1: "Distressed"})
    sns.boxplot(data=plot_df, x="Group", y="Revenue Growth", ax=ax,
                palette={"Healthy": "#4C956C", "Distressed": "#D7263D"}, showfliers=False)
    ax.set_title("Revenue Growth: Healthy vs Distressed")
    save(fig, "07_revenue_growth_comparison")


def plot_debt_trend(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    grp = df.groupby(["Year", "Distress Status"])["Debt Ratio"].mean().reset_index()
    grp["Group"] = grp["Distress Status"].map({0: "Healthy", 1: "Distressed"})
    sns.lineplot(data=grp, x="Year", y="Debt Ratio", hue="Group", marker="o", ax=ax,
                 palette={"Healthy": "#4C956C", "Distressed": "#D7263D"})
    ax.set_title("Average Debt Ratio Over Time")
    save(fig, "08_debt_trend")


def plot_profitability_trend(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    grp = df.groupby(["Year", "Distress Status"])["ROA"].mean().reset_index()
    grp["Group"] = grp["Distress Status"].map({0: "Healthy", 1: "Distressed"})
    sns.lineplot(data=grp, x="Year", y="ROA", hue="Group", marker="o", ax=ax,
                 palette={"Healthy": "#4C956C", "Distressed": "#D7263D"})
    ax.set_title("Average ROA (Profitability) Over Time")
    save(fig, "09_profitability_trend")


def plot_industry_distress_rate(df):
    grp = df.groupby("Industry")["Distress Status"].mean().sort_values(ascending=False)
    grp = grp[grp > 0].head(15)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(grp.index[::-1], (grp.values[::-1] * 100), color="#D7263D")
    ax.set_xlabel("Distress rate (%)")
    ax.set_title("Top 15 Industries by Distress Rate")
    save(fig, "10_industry_distress_rate")


def run_eda(df):
    plot_class_distribution(df)
    plot_ratio_comparison(df, "ROA", "ROA: Healthy vs Distressed Companies", "02_roa_comparison")
    plot_ratio_comparison(df, "Debt-to-Equity", "Debt-to-Equity: Healthy vs Distressed", "03_debt_to_equity_comparison")
    plot_ratio_comparison(df, "Current Ratio", "Current Ratio: Healthy vs Distressed", "04_current_ratio_comparison")
    plot_ratio_comparison(df, "Interest Coverage", "Interest Coverage: Healthy vs Distressed", "05_interest_coverage_comparison")
    plot_ocf_comparison(df)
    plot_revenue_growth_comparison(df)
    plot_debt_trend(df)
    plot_profitability_trend(df)
    plot_industry_distress_rate(df)


if __name__ == "__main__":
    df = pd.read_csv("data/processed/modeling_dataset.csv")
    run_eda(df)
