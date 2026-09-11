# Model Evaluation Report (Plain English)

## What we're predicting

For each company, using its financial ratios in one year, we try to predict:
**"Will this company be marked distressed NEXT year?"**

## How we tested the models (and why not a normal train/test split)

We only trust one slice of the data for this: 2023 financial numbers predicting
2024 distress. That gives us **49 company-years**, with **13 of them actually
becoming distressed** the next year. (Full explanation in
`reports/target_and_sample_size_notes.md`.)

49 rows is too small to split into one training group and one separate testing
group and trust the result — a single split could get lucky or unlucky just by
chance. So instead we used **Stratified 5-Fold Cross-Validation**: we split the
49 rows into 5 groups, keeping about the same mix of distressed/healthy in
each group. We train on 4 groups and test on the 1 left out, five times in a
row (so every row gets tested exactly once), then average the results. This
gives a fairer picture than one lucky/unlucky split.

## The models we compared

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.836 | 0.733 | 0.700 | 0.708 | 0.786 |
| Decision Tree        | 0.793 | 0.650 | 0.733 | 0.651 | 0.815 |
| Random Forest        | 0.773 | 0.567 | 0.700 | 0.621 | 0.888 |
| **XGBoost**           | 0.773 | 0.567 | **0.767** | 0.640 | **0.911** |

## What do these numbers mean, in plain words?

- **Accuracy** = out of all predictions, how many were right. This is the
  least useful number here, because most companies are healthy — a model
  that always guesses "healthy" would already score ~73% accuracy without
  being useful at all.
- **Recall** (for the distressed class) = out of all companies that actually
  became distressed, how many did the model successfully catch. **This is
  the most important number for an early-warning system** — missing a company
  that's about to get into trouble is the costly mistake we most want to avoid.
- **Precision** = out of all the companies the model flagged as risky, how
  many were actually right. A false alarm here (flagging a healthy company)
  is a much smaller problem than missing a real one.
- **F1** = a balance between Precision and Recall.
- **ROC-AUC** = a general measure of how well the model tells risky and safe
  companies apart, across all possible thresholds. 0.5 = random guessing,
  1.0 = perfect.

## Why we picked XGBoost as the main model

We told ourselves in advance to prioritize, in this order: **Recall, F1,
ROC-AUC, Precision, Accuracy** (in that order), because catching a
distressed company matters more than perfect accuracy.

- **XGBoost has the best Recall (0.767)** — it catches about 3 out of 4
  companies that actually go on to become distressed.
- It also has the **best ROC-AUC (0.911)**, meaning it separates risky
  from safe companies quite well overall.
- Its F1 (0.640) is close to the others, and its lower Precision (more
  false alarms) is an acceptable trade-off given our stated priorities.

Logistic Regression had the best F1 and Precision, and is worth keeping
around as a simple, transparent "sanity check" model — but XGBoost is our
main model because it catches more real cases of distress.

## Threshold decision

By default, a model says "risky" only if its probability is above 50%. We
tested several thresholds instead:

| Threshold | Precision | Recall | F1 | Flagged High Risk | Actually Distressed |
|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.556 | 0.769 | 0.645 | 18 | 13 |
| 0.40 | 0.556 | 0.769 | 0.645 | 18 | 13 |
| 0.50 | 0.556 | 0.769 | 0.645 | 18 | 13 |
| 0.60 | 0.588 | 0.769 | 0.667 | 17 | 13 |
| 0.70 | 0.562 | 0.692 | 0.621 | 16 | 13 |

Recall stays the same (0.769) from 0.30 to 0.60, and only drops at 0.70. We
picked **0.40** as our working threshold — it keeps Recall high (catches the
most distressed companies) while being a bit more cautious than the default
0.50, in line with an early-warning system's job of raising a flag sooner
rather than later.

**Business trade-off, in plain words:** a lower threshold means we flag more
companies as "risky", so we catch more real problems (fewer false negatives)
but also raise more false alarms (more false positives) — meaning more
companies get investigated that turn out fine. A higher threshold does the
opposite. We chose to lean toward catching more real problems, because in
this context, missing a real distress case is more costly than double-checking
a company that's actually fine.

## Honest limitations

- 49 training rows and only 13 positive (distressed) cases is a **small**
  dataset for machine learning. Please treat these results as a demonstration
  of methodology, not a production-grade prediction system.
- Cross-validation folds are small (about 10 rows per fold, 2-3 of them
  distressed), so individual fold results can swing quite a bit — the average
  across folds is more reliable than any single fold.
- We did not have enough historical years (only 2023-2025) to test a true
  multi-year chronological split, as a bigger, real-world project would.
