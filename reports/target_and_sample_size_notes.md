# Early-Warning Target: What We Found, In Plain English

## How we built the target

For every company-year row at Year T, we look up that same company's
`Distress Status` at Year T+1, and use it as what we're trying to predict.

```
2023 financial numbers  ->  predict 2024 Distress Status
2024 financial numbers  ->  predict 2025 Distress Status
2025 financial numbers  ->  no 2026 data exists, so no target — not used for training
```

## Important problem we found — and did NOT hide

When we built this, we noticed something important:

**Every single company has `Distress Status = 0` in the year 2025.**
Even companies that were clearly struggling in 2023/2024 (American Airlines, AMC,
BlackBerry, Rivian, Carvana, etc.) show `0` for 2025.

This is almost certainly because the label file only recorded distress events
that were **known at the time the data was put together**, and 2025 is very
recent — so no new 2025 distress events had been confirmed/recorded yet. It does
**not** mean these companies definitely became financially healthy in 2025.

### What this means for us

The "2024 financial data → predict 2025 distress" pairing is **not trustworthy**.
Every single one of those 48 rows has target = 0, with zero exceptions. A model
trained on this would just learn "always predict safe", which teaches us nothing
and would make our "Recall" number for the distressed class meaningless.

### What we did about it

We only use the **"2023 financial data → predict 2024 distress"** pairing to
train and test the early-warning model. This gives us:

- **49 usable rows**
- **13 rows where the company became/was distressed the next year**
- **36 rows where the company stayed healthy the next year**

We still **generate risk scores for every company in every year** (including
2024 and 2025) using the trained model — we just don't pretend we can grade
those extra predictions as "correct" or "incorrect", because we don't have a
trustworthy answer key for them.

## Why we don't do a normal train/2024-validate/2025-test split

The project brief suggested a year-by-year split (train on 2023, validate on
2024, test on 2025). We can't do that here, because after removing the
untrustworthy 2025 target, we are left with usable target data from **only
one year (2023)**. There is nothing to chronologically split.

**What we did instead:** Stratified 5-fold cross-validation on the 49 usable
rows. This means we split the 49 rows into 5 random groups (keeping the ratio
of distressed/healthy roughly equal in each group), train on 4 groups, test
on the 1 left out, and repeat 5 times so every row gets tested exactly once.
This is a well-accepted, defensible way to evaluate a model when you don't
have enough data for a clean time-based split.

## Bottom line on sample size

- 49 rows is a **small** dataset for machine learning. Please read the results
  in this project as a **directional, educational demonstration**, not a
  production-grade credit model. A real bank or rating agency would use
  thousands of company-years of history.
- We use simple models with regularization, and we do not overclaim accuracy.
