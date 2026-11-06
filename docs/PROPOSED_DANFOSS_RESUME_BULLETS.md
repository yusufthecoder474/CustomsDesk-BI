# Proposed Danfoss resume bullets — review before DOCX edits

No resume DOCX was opened, edited or replaced in this task. These bullets describe executed local work and prepared reporting assets accurately.

## SupplySight Analytics
- Built a PySpark Bronze–Silver–Gold pipeline for 26,058 public retail records, accepting 24,258 and quarantining 1,800; reconciled eight Gold datasets and 14 SQL/arithmetic KPIs.
- Compared four forecasting methods over 20 products using three 14-day chronological rolling origins; reproduced Ridge WAPE of 76.64% versus seasonal naive's 99.06%, with product-level errors and forecast-bias analysis.
- Implemented configurable, capacity-constrained inventory planning with safety-stock, reorder and lead-time checks; passed 101 tests while preserving a nine-sheet Excel workbook and all 5,222 original formulas.

## CustomsDesk BI
- Integrated 55,004 synthetic operational records through auditable Python ETL, accepting 54,992 into a relational warehouse and reproducing 13 SQL KPI targets in SQLite.
- Reconciled references for 22 authored DAX measures against independent raw-table SQL and checked 11 relationship specifications; passed 97 tests with two PostgreSQL checks skipped.
- Prepared a three-page Power BI reporting kit with typed Power Query imports, SLA/backlog/response and data-quality views, plus 38 SQL filter-context targets; Power BI Desktop execution remains pending.

## Accuracy notes
The capacity data and operational CustomsDesk inputs are synthetic. Do not call modeled exposure an observed stock-out. Databricks execution and Power BI dashboard completion cannot yet be claimed. Ridge remains the best tested model but has −31.55% pooled bias, so the error figure must not be called 76.64% accuracy. The final evaluation periods were used historically; no new untouched holdout is claimed. PostgreSQL is the existing deployment target, not a newly executed backend in this task. Native Excel PivotTables, collaboration, deployments and savings were not verified.
