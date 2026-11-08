# ADR 0001: Warehouse design for Meridian

Date: 2026-11-08
Status: accepted

## Context
31.8M transactions, 1.37M customers, 105k articles (H&M Kaggle). Local DuckDB first, Databricks later.

## Decisions
1. **Parquet, not CSV.** 3.49 GB to 470 MB (7.4x). Types preserved; article_id kept as text (leading zero).
2. **Staging as tables, not views.** Views stored a relative file path and broke when queried from another folder.
3. **No dedupe of transactions.** Identical rows are real repeat purchases. Surrogate key sale_line_id added instead.
4. **sales_channel 1 = store, 2 = online was an assumption, now SUPPORTED.** Channel 1 had zero sales in April 2020 when stores were closed. 70.4% of sales are channel 2.
5. **Weeks start Monday.** dim_date starts on the Monday before the first sale so every week_start joins.
6. **fct_weekly_customer is sparse** (only weeks with a purchase). A full grid would be 144M rows; built per model when needed.
7. **Reconciliation tests** prove gold = staging in rows and revenue.

## Consequences
- Every model reads gold tables only, never raw files.
- If H&M's channel mapping is ever confirmed differently, flip one CASE in stg_transactions.
