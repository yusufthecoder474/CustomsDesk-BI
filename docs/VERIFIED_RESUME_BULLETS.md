> Previous enhancement record retained. Current results and proposed wording: docs/EVIDENCE.md and docs/PROPOSED_DANFOSS_RESUME_BULLETS.md.

# Verified resume bullets

## SupplySight Analytics
- Built a PySpark Bronze–Silver–Gold pipeline for 26,058 public retail records, accepting 24,258 and quarantining 1,800, with eight Gold datasets and 14 reconciled KPI checks.
- Evaluated four forecasting methods across 20 products using three chronological 14-day rolling origins; reproduced Ridge WAPE of 76.64% versus seasonal naive's 99.06%, while reporting product-level errors and −31.55% pooled Ridge bias.
- Added synthetic capacity and lead-time stock-risk planning with hand-calculated regression fixtures and a nine-sheet Excel report; preserved 5,222 existing formulas and passed 61 automated tests.

## CustomsDesk BI
- Implemented auditable Python ETL and a relational SQL warehouse for 55,004 synthetic operational records, accepting 54,992 and reproducing 13 operational KPI targets in SQLite.
- Passed 96 automated tests with two PostgreSQL-specific checks skipped, covering data quality, SLA rules, change regression, relationship integrity and credential preservation.
- Prepared a three-page Power BI reporting kit with 22 authored DAX measures, typed Power Query imports, 11 relationship checks and 38 SQL measure/context targets; Power BI Desktop execution remains pending.

Do not describe synthetic inputs as observed factory results. Do not claim Databricks execution, PostgreSQL verification in this task, a completed Power BI dashboard, native Excel PivotTables or manufacturing savings. Four-model study periods were evaluated historically; no new untouched holdout is claimed. Ridge's 22.63% relative WAPE reduction against seasonal naive is reproduced historical performance, not a new improvement from the added model.
