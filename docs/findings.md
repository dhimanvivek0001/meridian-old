# Meridian findings

## Data (M0)
- 31,788,324 sales, 1,371,980 customers, 105,542 articles; 20 Sep 2018 to 22 Sep 2020
- 9,699 customers never bought; 995 articles never sold (cold-start)
- Channel 2 (assumed online) = 70.4% of sales
- Age missing for 1.16% of customers; median age 32

## M1 part 1: KPI tree + cohorts
- Revenue fell YoY in 10 of 11 months (Oct 2019 - Aug 2020); total -115.6 log %
- Decline split: customers 47%, frequency 26%, basket 26%
- Decline started BEFORE COVID: Oct 2019 - Feb 2020 already -40 log points
- COVID (Mar-Apr 2020): customers -14, frequency -8 to -10, basket +10 in April (fewer, bigger orders)
- June 2020: customers recovered (-0.1) but basket -14 -> markdown hypothesis, test in part 2
- Aug 2020 +8.1 is partly a base effect: Aug 2019 was the weakest month of 2019
- Month-1 retention: 17-20% (H1 2019 cohorts) vs 12-15% (later). Decline partly a LEFT-CENSORING artifact
- Summer cohorts (Jul/Aug) retain worst: 13.5-13.9% month-1

## M1 part 2: seasonality + events
- STL (period 52, 104 weeks) OVERFIT: seasonal strength 1.00, zero leftover. Rejected.
- Replaced with robust regression: cubic trend + 3 Fourier terms + event flags. Validated on synthetic planted shock.
- Underlying trend: -12.9% peak to low (excl. lockdown). Cubic edge effect makes first-vs-last unreliable.
- Seasonal swing: 42 pts. Peak = week of 20 May, low = week of 24 Dec.
- Black Friday: +88% vs a normal week. Lockdown (16 Mar - 4 May 2020): -17% on average
- Lockdown hides 2 phases: crash in March, then +70% online surge week of 6 Apr (Easter)
- Recurring unexplained spikes: late Sep (both years, +43% / +63%), summer sale mid/late June (+42 to +47%)
- Pre-Christmas rush week of 16 Dec 2019: +37%

## M1 part 3: basket split + channels
- BUG FOUND: DuckDB sum() of ints -> HUGEINT -> Polars Decimal(scale 0) -> integer division. Fix: ::bigint. Caught by identity check (parts must add to total).
- June 2020 basket -14.0 = -9.5 fewer items per order + -4.5 cheaper items. Markdown hypothesis only 1/3 right.
- Structural shift: items per order down YoY in 9 of 11 months; price per item up in 7 of 11. Started pre-COVID.
- April 2020: store channel = ZERO sales. Online orders +57% (Jan -> Apr), items/order +12%, basket +10%.
- May 2020 store reopening: 3.14 items/order vs 2.35 pre-lockdown (pent-up demand)
- Channel mapping 1 = store, 2 = online now SUPPORTED by data (channel 1 zero during lockdown)

## Phase 1: from-scratch builds
- Build 1 linear regression (log year-2 spend): R^2 0.506 vs 0 baseline; top driver = past spend. Matches sklearn.
- Build 2 logistic regression (buys again in year 2): AUC 0.834, log loss 0.478 vs 0.655 baseline, lift 2.1x in riskiest decile (76.9% vs 36.3% churn).
- Drivers differ by question: RETURN driven by frequency (odds x9.07/std) + recency (x0.58); AMOUNT driven by spend. -> hurdle model for CLV.
- Accuracy trap: 76.1% vs 63.7% for "everyone returns". Use AUC / lift, not accuracy.
- Collinearity: units weight unstable (-0.008 vs -0.019) with zero effect on AUC.
