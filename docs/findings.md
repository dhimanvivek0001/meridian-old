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
