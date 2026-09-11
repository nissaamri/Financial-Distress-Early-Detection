# Financial Distress Early-Warning System

A simple, easy-to-follow project that looks at company financial numbers and
tries to warn — **one year ahead** — if a company might get into serious
financial trouble.

> **Note on scope:** This project was intentionally kept simple and honest
> rather than maximally fancy. It's built for learning, and every claim in
> here is backed by a number you can check in the `reports/` folder.

---

## 1. What this project does (in plain words)

1. Take company financial statements (revenue, debt, cash, etc.)
2. Turn them into simple ratios (like Current Ratio, Debt-to-Equity, ROA)
3. Look at whether those ratios are getting better or worse
4. Use a machine learning model to guess: "will this company be in distress
   **next year**?"
5. Turn that guess into an easy 0–100 Risk Score
6. Explain **why** the model thinks a company is risky
7. Give simple, evidence-based suggestions for what management could look at
8. Show everything on an interactive dashboard

---

## 2. Business problem

Investors, lenders, and managers want to know a company is in trouble
**before** it's obvious — not after. This project builds a small early-warning
system: using this year's numbers to flag risk for next year, instead of
just confirming trouble that's already happened.

---

## 3. The data

Two files were provided:

- **`50-companies-financial.csv`** — 50 companies, 2023–2025, with income
  statement, balance sheet, and cash flow numbers.
- **`distress_labels.csv`** — whether each company was marked "distressed"
  in each year, and what event caused it.

We checked both files carefully before doing anything else. Full findings are
in [`reports/data_quality_report.md`](reports/data_quality_report.md). Short
version:
- FUBO is missing 2025 data. We left it missing — we did not invent a number.
- GameStop (GME) has financial data but no distress label at all — kept, but
  marked "unknown", never guessed.
- One company (SATS / EchoStar) has a label but no financial data — dropped,
  since we can't predict without financial numbers.
- Some rows have negative equity or negative profit — these are **real
  financial signals**, not data errors, and we kept them.

### Data dictionary (short version)

| Group | Examples |
|---|---|
| Company info | Company Name, Ticker, Industry, Year |
| Income statement | Revenue, COGS, Gross Profit, EBIT, EBITDA, Interest Expense, Net Income |
| Balance sheet | Cash, Receivables, Inventory, Current/Total Assets, Current/Total Liabilities, Debt, Equity |
| Cash flow | Operating/Investing/Financing Cash Flow, Capital Expenditure |
| Label | Distress Status (0/1), Distress Event, Distress Event Year |

---

## 4. Important limitation — please read this first

When we tried to build "this year's numbers → next year's distress label",
we found that **every single company shows "not distressed" in 2025**, even
companies that were clearly struggling. This looks like the label file simply
hadn't recorded any new 2025 events yet when it was built — not that every
company suddenly became healthy.

**What we did about it:** we only trust the "2023 data → 2024 label" pairing
for training and testing the model. That gives us **49 usable rows, 13 of
them actually distressed the following year**. This is a small sample, and
we say so clearly throughout this project instead of overselling the results.

Full details: [`reports/target_and_sample_size_notes.md`](reports/target_and_sample_size_notes.md)

We also discovered that year-over-year "trend" features (like Revenue
Growth) can't be calculated for 2023, since there's no 2022 data to compare
against — and 2023 is our only trustworthy training year. So the model uses
**snapshot ratios only** (this year's Current Ratio, ROA, Debt-to-Equity,
etc.), not trend changes. Trend features are still calculated and shown on
the dashboard for 2024/2025, just not used to train the model.

---

## 5. Methodology, step by step

| Step | What we did | Where |
|---|---|---|
| Data audit | Checked missing values, duplicates, formula consistency, negative values | `src/data_validation.py` |
| Cleaning | Fixed text formatting only (names, tickers); never guessed missing numbers | `src/data_cleaning.py` |
| Merging | Joined financial data + labels on Ticker + Year | `src/merge_data.py` |
| Ratios | Built liquidity, profitability, leverage, efficiency, cash-flow ratios | `src/financial_ratios.py` |
| Trend features | Year-over-year changes (for display, not for training — see limitation above) | `src/feature_engineering.py` |
| Target | Shifted label forward one year (T → T+1) | `src/feature_engineering.py` |
| EDA | 10 charts comparing healthy vs distressed companies | `src/eda.py`, `reports/figures/` |
| Modeling | Logistic Regression, Decision Tree, Random Forest, XGBoost, 5-fold cross-validation | `src/train.py` |
| Threshold tuning | Tested 0.30–0.70, picked 0.40 | `src/threshold_optimization.py` |
| Explainability | SHAP global + local (per-company) explanations | `src/explainability.py` |
| Risk scoring | Probability → 0–100 score → risk category | `src/risk_scoring.py` |
| Recommendations | Rule-based, tied to each company's real numbers | `src/recommendations.py` |
| Dashboard | 6-page Streamlit app | `dashboard/` |

---

## 6. Financial ratios used (with plain-English meaning)

**Liquidity — can the company pay short-term bills?**
- Current Ratio = Current Assets / Current Liabilities
- Quick Ratio = (Current Assets − Inventory) / Current Liabilities
- Cash Ratio = Cash / Current Liabilities

**Profitability — is the company making money?**
- Net Profit Margin = Net Income / Revenue
- EBIT Margin = EBIT / Revenue
- ROA = Net Income / Total Assets
- ROE = Net Income / Total Equity (unreliable when Equity is negative — we flag this)

**Leverage — how much debt does the company carry?**
- Debt-to-Equity = Total Debt / Total Equity
- Debt Ratio = Total Debt / Total Assets
- Interest Coverage = EBIT / Interest Expense

**Efficiency — how well does the company use its assets?**
- Asset Turnover = Revenue / Total Assets
- Inventory Turnover = COGS / Average Inventory
- Receivables Turnover = Revenue / Average Receivables

**Cash flow risk — is cash actually coming in?**
- Operating Cash Flow Ratio = Operating Cash Flow / Current Liabilities
- CFO to Debt = Operating Cash Flow / Total Debt
- Free Cash Flow = Operating Cash Flow − Capital Expenditure

All ratios return "missing" instead of a fake huge number when we can't
safely divide (for example, dividing by zero).

---

## 7. Machine learning results

We compared 4 models using 5-fold cross-validation on the 49 usable rows.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.836 | 0.733 | 0.700 | 0.708 | 0.786 |
| Decision Tree | 0.793 | 0.650 | 0.733 | 0.651 | 0.815 |
| Random Forest | 0.773 | 0.567 | 0.700 | 0.621 | 0.888 |
| **XGBoost (chosen)** | 0.773 | 0.567 | **0.767** | 0.640 | **0.911** |

**Why XGBoost?** In an early-warning system, missing a company that's about
to get into trouble (a false negative) is worse than a false alarm. So we
prioritize **Recall** first — and XGBoost catches the most real cases
(76.7%), along with the best overall separation between risky and safe
companies (ROC-AUC 0.911).

Full write-up: [`reports/model_evaluation_report.md`](reports/model_evaluation_report.md)

**Decision threshold: 0.40** (instead of the default 0.50) — chosen to keep
recall high, since flagging a company that turns out fine is a smaller
mistake than missing one that fails.

---

## 8. Explainable AI (SHAP)

For every company-year, we can show which financial ratios pushed the risk
prediction up or down. Top overall risk drivers found by the model:

1. CFO to Net Income (cash flow quality)
2. Net Profit Margin
3. ROA
4. Interest Coverage
5. EBIT Margin

See the dashboard's "Why Is This Company Risky?" page for company-specific
explanations.

---

## 9. Risk score

We turn the model's probability into a simple 0–100 **Internal Financial
Distress Risk Score** — this is our own internal score, **not** an official
credit rating from any agency.

| Score | Category |
|---|---|
| 0–20 | Very Low Risk |
| 21–40 | Low Risk |
| 41–60 | Moderate Risk |
| 61–80 | High Risk |
| 81–100 | Critical Risk |

---

## 10. The dashboard

Run it with:

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

Pages:
1. **Executive Overview** — company counts, average risk, top watch-list, model performance
2. **Company Risk Monitor** — pick any company, see its full ratio breakdown, alerts, and recommendations
3. **Financial Health** — trends over time for revenue, debt, cash flow, ratios
4. **Why Is This Company Risky?** — SHAP explanations, per company and overall
5. **Early-Warning Monitor** — all companies ranked by risk, filterable
6. **Industry Risk** — average risk and distress rate by industry

### No-install version

Don't want to set up Python or Streamlit just to look around? Open
[`dashboard/dashboard_static.html`](dashboard/dashboard_static.html) directly in
any web browser — double-click the file, no installation, no server, no
internet connection needed. It has the same 5 views (Overview, Company Risk
Monitor, Why Is This Company Risky?, Early-Warning Monitor, Industry Risk),
with real search, filtering, and company/year selection built in using plain
JavaScript. All the data and charting code (Chart.js) is embedded directly in
the file, so it keeps working even offline. The only thing it can't do that
the live Streamlit app can is recompute anything from new data — it's a
snapshot of the dataset at the time it was generated.

### Written report

The full write-up in Sections 1–17 of this README is also available as a
formatted document:
- [`reports/Project_Report_Full.docx`](reports/Project_Report_Full.docx) — Word version (Times New Roman, 1.5 line spacing, justified), for printing or editing.
- [`reports/Project_Report.html`](reports/Project_Report.html) — HTML version with the same content, a clickable sidebar table of contents, and all charts/screenshots embedded in one file — open it directly in a browser, no installation needed.

---

## 11. Key findings

- The dataset is small (149 usable company-years, 49 with a trustworthy
  next-year answer) — results should be read as a demonstration, not a
  production credit model.
- Companies flagged highest-risk in the most recent data include names like
  Rivian, Plug Power, Beyond Meat, Peloton, BlackBerry, and ChargePoint —
  all companies with negative operating cash flow, weak interest coverage,
  and/or negative profitability.
- Cash flow quality (CFO relative to Net Income) and core profitability
  (Net Profit Margin, ROA) were the strongest risk drivers the model found —
  more so than raw debt levels alone.
- Most industries in this dataset only have 1–3 companies, so industry-level
  averages should be read as illustrative, not statistically robust.

---

## 12. Limitations (please read)

1. **Small sample size.** Only 49 rows with a trustworthy next-year answer,
   13 of them positive. A real system would use thousands of company-years.
2. **2025 labels are not usable for training/testing** — every company shows
   "not distressed" in 2025, most likely because the label file hadn't
   caught up with 2025 events yet.
3. **No trend features in the model** — because our only trustworthy
   training year (2023) has no prior year to compare against.
4. **This is not a credit rating.** Our Risk Score is an internal, simplified
   estimate — do not use it for real investment or lending decisions.
5. A few rows don't perfectly satisfy the accounting identity
   (Assets = Liabilities + Equity), likely due to balance sheet lines we
   don't have (like non-controlling interests). We didn't "fix" these —
   we flagged them and moved on.

---

## 13. Future improvements

- Add more years of history so trend features and a real chronological
  train/validate/test split become possible.
- Add more companies per industry for meaningful industry comparisons.
- Track distress labels going forward so the 2025+ "predict next year"
  pairing becomes trustworthy.
- Add TNB (or any newly available company) as a real-world featured case
  study once its financial data is available in the same format.

---

## 14. How to run the whole project

```bash
# 1. Install everything
pip install -r requirements.txt

# 2. Run the data pipeline, in order
python src/data_cleaning.py
python src/merge_data.py
python src/financial_ratios.py
python src/feature_engineering.py
python src/eda.py

# 3. Train models and generate explanations / risk scores
python src/train.py
PYTHONPATH=src python src/threshold_optimization.py
PYTHONPATH=src python src/explainability.py
PYTHONPATH=src python src/risk_scoring.py
python src/recommendations.py

# 4. Run the tests (optional but recommended)
pytest tests/

# 5. Launch the dashboard
streamlit run dashboard/app.py
```

---

## 15. Project folder structure

```
financial-distress-early-warning/
├── data/
│   ├── raw/                      # original CSVs, untouched
│   ├── processed/                # cleaned, merged, ratio, and modeling datasets
│   └── validation/                # label audit table
├── src/                          # all the Python pipeline code
├── models/                       # saved trained models (.pkl) + feature list
├── dashboard/                    # Streamlit app (6 pages)
├── reports/                      # data quality report, model evaluation, SHAP outputs, charts
├── tests/                        # sanity-check tests (pytest)
├── requirements.txt
└── README.md   <-- you are here
```

**Note on scope:** the original brief also listed a `notebooks/` folder with
8 separate notebooks. To keep this project easy to follow (as requested), we
built the pipeline as clean, well-commented `.py` scripts in `src/` instead
of duplicating the same logic across many notebooks. Every script can be run
on its own and prints out what it's doing.
