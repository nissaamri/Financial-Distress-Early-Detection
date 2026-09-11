# Data Quality Report (Plain English)

This report explains what we found when we checked the two data files, **before** building any model.

---

## 1. The two files

**File 1: `50-companies-financial.csv`**
- 149 rows (not 150). We expected 50 companies × 3 years = 150 rows.
- 50 companies, 3 years (2023, 2024, 2025), 38 industries.
- **FUBO (fuboTV)** only has 2 years of data (2023, 2024). No 2025 row. This is why we have 149 rows instead of 150. We did **not** invent a 2025 row for FUBO — we just note it's missing.

**File 2: `distress_labels.csv`**
- 150 rows. It has a label for almost every company-year (not just the distressed ones).
- 111 rows say "not distressed" (0), 39 rows say "distressed" (1).
- 25 different companies were marked distressed at least once, out of 50 companies total.

---

## 2. Do the two files match up?

We compared the company ticker symbols in both files:

- **SATS** (EchoStar Corporation / DISH) appears in the labels file but **not** in the financial data file. So we have no financial numbers for this company. It will be dropped — we can't predict anything without financial data.
- **GME** (GameStop) appears in the financial data file but has **no label at all** in the labels file. So we don't know if GameStop was distressed or not. We will keep its financial numbers but mark it as "no label available" — we will **not** guess whether it was distressed.
- No duplicate rows and no duplicate company-year pairs in either file. That's good — nothing is double counted.

---

## 3. Do the numbers inside the file make sense?

We checked some basic accounting rules that should always be true.

**Total Debt = Short-Term Debt + Long-Term Debt**
- ✅ This is true for every row. No problem here.

**Gross Profit = Revenue − Cost of Sales**
- Almost all rows match. Only **2 rows (Peloton, 2023 and 2024)** are off, and only by about $100,000 — which is tiny compared to Peloton's ~$900 million to $1.2 billion Gross Profit. This is just normal rounding, not a real error. We keep the numbers as given.

**Total Assets = Total Liabilities + Total Equity** (this must always be true in accounting)
- 11 rows are off by more than 2%. This is expected in real-world data because companies sometimes report a few extra balance-sheet lines we don't have (like "non-controlling interests"). We are **not** changing these numbers — we flag them so a reader knows they exist, but we still use the numbers as reported.
- Companies involved: Coca-Cola (2025), NextEra Energy (2023–2025), Walmart (2023–2025), ExxonMobil (2023), Carvana (2023, 2025), Plug Power (2024).

**Negative Total Equity (19 rows)**
- This is not a data error. Negative equity is a real and important warning sign — it means a company owes more than it owns. Companies like American Airlines, AMC, McDonald's, Beyond Meat, Lucid, Peloton, and others show this in at least one year. We keep these numbers because they are meaningful for our risk model, not noise.

**Negative EBIT / Operating Profit (48 rows)**
- Also a real signal, not an error — many growth or struggling companies had negative operating profit in these years (e.g., Rivian, Lucid, Beyond Meat, Blink Charging, GoPro, Peloton).

**Zero Inventory (31 rows)**
- Normal. Many companies in this list (banks, software, airlines, some service companies) simply don't hold physical inventory. Not an error.

**Missing values**
- Several columns have small numbers of missing values (6–9 rows out of 149): Cost of Sales, Gross Profit, EBIT, EBITDA, Accounts Receivable, Current Assets, Current Liabilities, Total Liabilities, Capital Expenditure, and Interest Expense.
- We do **not** guess these numbers. When a ratio needs a missing number, that ratio will simply be blank (missing) for that company-year, instead of us making up a number.

---

## 4. What we did NOT do

- We did **not** delete any company or any row just because a number looked unusual.
- We did **not** fill in missing numbers with guesses.
- We did **not** change any reported financial figure.
- We did **not** invent a distress label for GME.
- We did **not** invent a 2025 row for FUBO.

---

## 5. Simple summary table

| Check | Result |
|---|---|
| Rows in financial file | 149 (FUBO missing 2025) |
| Rows in label file | 150 |
| Duplicate rows | 0 |
| Companies matched between both files | 49 of 50 |
| Unmatched: label has company, financial doesn't | SATS (dropped) |
| Unmatched: financial has company, label doesn't | GME (kept, no label) |
| Total Debt formula check | Passes 100% |
| Gross Profit formula check | Passes ~99% (2 tiny rounding cases) |
| Balance sheet identity check | Off by >2% in 11 rows (real-world reporting gaps, not fixed) |
| Missing values | Small amount in 10 columns, left as missing |
| Negative equity | 19 rows — real signal, kept |
| Negative EBIT | 48 rows — real signal, kept |
