# Manual Windows, Databricks and Power BI verification

Status: all tasks in this checklist require your Windows installation or authorized cloud workspace unless identified as locally executed. Current evidence is in each project's reports/enhancement; historical evidence is under reports/archive/original.

## 1. SupplySight on Windows PowerShell
Extract into a new folder. Install Python 3.12 and Java 17; set JAVA_HOME to your Java installation. From SupplySight-Analytics:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m supplysight.cli
python -m supplysight.study
python -m supplysight.capacity
python scripts/prepare_workbook_enhancement.py
python -m pytest -q
```
Expected: 26,058/24,258/1,800 rows; 14 KPI checks; four-model study WAPE approximately 76.64% Ridge, 82.92% Croston SBA, 92.53% naive, 99.06% seasonal naive. The original CLI regenerates Gold and old reporting; the extension regenerates the enhancement study. Run these in order. Do not run simultaneous writers.

## 2. SupplySight Excel Desktop — PENDING
Open excel/SupplySight_Operations_Analysis.xlsx. Confirm nine sheets, three charts, tables/filters and conditional flags. Set Calculation Options → Automatic, then Ctrl+Alt+F9. Compare Executive Summary B6:B10 against 350997,20,8,4,34.856763075... (last value approximately 34.9). B23:B25 must be 5,6,10. Forecast Study displays all four WAPE and bias results. Check that Inventory Risk E:H remain editable. In a disposable copy set Inventory Risk G6=1: Capacity Planning E6 must become 1. Restore G6, set E6=0: Capacity Planning L6 must become 1. Restore and close without saving test inputs. Check all original tabs, lookups, filters and charts after recalculation. Artifact-rendered workbook previews are included; these are not Excel Desktop screenshots.

Workbook regeneration requires Node and @oai/artifact-tool, the original supplied authoring dependency. It is not required to OPEN the supplied workbook. The builder is scripts/enhance_workbook.mjs and uses reports/archive/original/SupplySight_Operations_Analysis.xlsx as the preserved base and reports/enhancement/workbook_enhancement.json as executed study input. With artifact-tool available on Node's package path: `node scripts/enhance_workbook.mjs .`. Baseline original data are unchanged; if the source dataset changes, regenerate the base with scripts/build_workbook.mjs, inspect it, archive that refreshed base deliberately, then apply the enhancement builder.

PivotTables and Excel Power Query are NOT created or engine-verified. Optional PivotTable: click a Demand History table cell → Insert → PivotTable → New Worksheet; product_id to Rows, date grouped by Months to Columns, units summed to Values. Optional Power Query: Data → Get Data → From Text/CSV → select reports/enhancement/capacity_planning.csv, set product_id to Text and quantities to Decimal Number → Load To Table on a new worksheet. These optional additions alter sheet counts and require updating release checks. Capture genuine Desktop images only after execution.

## 3. Databricks Free Edition — PENDING
Follow SupplySight docs/DATABRICKS_SETUP.md exactly: upload code to workspace files, raw CSV to a NEW dedicated Unity Catalog Volume run directory, install non-Spark dependencies using requirements-databricks.txt, set BOTH widgets on each notebook, create output folders, then run 01→05. Download JSONL runtime logs, quality and reconciliation files. Verify the exact row counts above. Save real workspace/version and notebook-output screenshots. Locally executed Spark does not satisfy this check.

## 4. CustomsDesk local baseline on Windows PowerShell
Do not overwrite an existing .env or delete Docker volumes. Keep the original Compose project directory for an existing PostgreSQL instance. Copy only source/reporting changes into it, retaining private configuration and installed environment. The ordinary CLI uses your retained database settings. Avoid `docker compose down -v`. No password rotation is required.

For a completely separate SQLite verification in a fresh extracted folder:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
New-Item -ItemType Directory -Force reports/enhancement | Out-Null
python -m customsdesk.cli etl --database-url sqlite:///reports/enhancement/warehouse.sqlite --data data/sample --reports reports/enhancement
python -m customsdesk.cli export --database-url sqlite:///reports/enhancement/warehouse.sqlite --exports reports/enhancement/exports
python -m customsdesk.dashboard --database-url sqlite:///reports/enhancement/warehouse.sqlite
python -m pytest -q
```
Expected 96 passing tests and 2 skips without PostgreSQL. For a retained PostgreSQL connection run ordinary `customsdesk.cli kpis`, `etl`, `export` through your configured .env, and use scripts/verify_project.ps1 for guarded integration verification. The dedicated one-click setup stops and preserves a nonempty DATABASE_URL rather than replacing it; use the ordinary CLI for that configuration. Existing passwords are retained unless explicitly rotated. New installations generate a password locally. Record actual PostgreSQL result counts, versions and nine imported reporting tables; no PostgreSQL execution was possible in this task.

## 5. Power BI Desktop — PENDING
1. Get Data → Blank Query → Advanced Editor. Create text parameters as powerbi/parameters.md specifies. SourceMode=CSV and ExportFolder=<absolute project>\reports\enhancement\exports is the locally reproduced source; PostgreSQL mode uses your actual retained server/database. Credentials go in Data source settings.
2. Create fxLoad from powerbi/fxLoad.m (function), LatestSuccessfulRun from its .m (connection-only), then dim_date, dim_country, dim_part, dim_authority, dim_query_type, fact_shipment, fact_customs_query, etl_run_log and data_quality_results from matching .m files. These are the nine star/reporting tables. The optional rejected_records table supports reason drill-down; it is not needed for the existing 22 measures. Use exact query names.
3. Check dates are Date, response/backlog/SLA hours Decimal, flags Whole Number or Logical as M specifies, identifiers and HS codes Text. Confirm response_bucket exists on fact_customs_query, with zero/24h in first band, >24–48h in second, >48–72h in third, >72h in fourth, and unresponded separate. M execution is still unverified.
4. Add all 11 relationships from model_relationships.json. Closed-date and destination-country relationships are inactive; other listed relationships active, single direction. Do not add active fact-to-fact links. Mark dim_date[date_key] as the date table.
5. Modeling → New measure; paste each of the 22 individual definitions from measures.dax. Format rates as percentage fractions, counts as whole numbers and hours as decimal. Do not paste all definitions into one measure. SQL/schema checks are not a DAX engine parse check.
6. View → Themes → Browse for themes → select powerbi/theme.json. Build Executive Overview, Backlog and SLA Analysis, Data Quality and Classification using powerbi/REPORT_LAYOUT.md. Verify each slicer's intended visual interactions.
7. Use Power BI Desktop DAX Query View to run powerbi/verify_measures_query.dax and obtain all 38 explicit contexts. Export the real output, retaining the three column labels; replace blank numeric cells with literal BLANK before comparing. Alternatively use cards with the listed filters. Compare the 22 original targets plus 16 filter-context targets from reports/enhancement/DAX_SQL_TARGETS.csv against real Desktop card/table values. September throughput uses closure dates, while ordinary queries use opened dates. LOW priority must force High Priority Unresolved=0. Empty cohorts yield 0 counts and BLANK response/compliance. Authority A1 is query-only. DQ stays on the latest successful run. Page 3 part-master totals remain independent of query date/authority filters.
8. Fill reports/enhancement/DAX_ACTUAL_VALUES.csv only with executed numbers; use literal BLANK for DAX blank values. Keep measure/filter_context labels. Then run:
```powershell
python -m customsdesk.powerbi_check --expected reports/enhancement/DAX_SQL_TARGETS.csv --actual reports/enhancement/DAX_ACTUAL_VALUES.csv --out reports/enhancement/POWER_BI_RECONCILIATION.csv
```
Exit 0 requires every comparison PASS. Empty observations intentionally stay PENDING. Confirm 19,998 shipments, 29,994 queries, 13,375 backlog, 2,673 high-priority unresolved, 52h median, 61.0613% SLA compliance and 99.9782% DQ pass rate unfiltered. Backlog is a fixed-snapshot cohort measure, not reconstructed historical backlog.
9. Save a genuine CustomsDesk-BI.pbix, refresh from your selected source, export three real page screenshots, and retain the successful reconciliation CSV. Only then describe the dashboard as completed. Power BI Desktop cannot run in this Linux environment.
