# Danfoss project upgrade — current verification

Executed locally on 26 October 2026. Existing SupplySight Analytics and CustomsDesk BI were extended rather than rebuilt. The original source ZIPs, raw data, established forecasting algorithms, SQL warehouse schemas, 22 DAX definitions and Excel workflow were retained. No resume DOCX was opened or modified, and nothing was published to GitHub.

## Verified results

| Check | SupplySight Analytics | CustomsDesk BI |
|---|---|---|
| Tests | 101 passed, no skips/failures | 97 passed, 2 PostgreSQL checks skipped, no failures |
| Installation | Local source package installation passed with --no-deps --no-build-isolation into an isolated target directory | Same |
| Build | Python wheel built; packaged runtime code checked against final source | Same |
| New-module lint | PASS with Ruff | PASS with Ruff |
| Full-project lint | FAIL: 24 findings retained in lint_full_final.log | FAIL: 107 findings retained in lint_full_final.log |
| Data counts | 26,058 raw; 24,258 accepted; 1,800 rejected | 55,004 synthetic inputs; 54,992 accepted |
| KPI preservation | Eight Gold datasets; 14 SQL/arithmetic controls; 350,997 units | Thirteen existing SQL KPI targets reproduced |
| New functionality | Configurable capacity-constrained production plan and arrival-aware stock balance | Independent raw-table SQL references for all 22 DAX measure targets |
| Native/external checks | Databricks and Excel Desktop PENDING | Power BI Desktop/PBIX and PostgreSQL runtime PENDING |

Full-project lint findings include existing import ordering, unused imports and style issues; notebook imports depend on runtime workspace paths. The new modules and tests pass their focused lint checks. Full lint was not described as passed. No broad automatic rewrite of unrelated source was made. All initial failed lint runs and subsequent focused corrections are retained in reports/current_upgrade/initial_checks and pre_final_checks. The undefined implicit spark reference in notebook 05's logging expression was replaced with globals().get("spark").

Installation and wheel builds prove package installability in the recorded host environment, not successful resolution of the exact Windows dependency lock. The host's CustomsDesk NumPy, Pydantic, dotenv and pytest versions differ from its preserved lock. Exact versions are in reports/current_upgrade/environment.json. No original dependency pins were silently changed.

## SupplySight: record counts and preserved analytics

Both the clean CLI output directory /tmp/danfoss-current-clean and the clean notebook output directory /tmp/danfoss-current-notebooks reproduce 26,058 raw, 24,258 accepted and 1,800 rejected. Notebook 05 checks expected counts and all 14 KPI reconciliations. The old 52,116 count was retained in historical evidence; the prior diagnosis of legacy duplicate Spark part files is consistent with the arithmetic but that old host defect was not reproduced here. Counts are not corrected by dropping source rows.

Reproduce from PowerShell after installing the project and setting PYTHONPATH=src:
```powershell
New-Item -ItemType Directory -Force .verification/run01/data/raw | Out-Null
Copy-Item data/raw/retail_subset.csv .verification/run01/data/raw/retail_subset.csv
python -m supplysight.cli --root .verification/run01
New-Item -ItemType Directory -Force .verification/notebooks01/data/raw,.verification/notebooks01/data/synthetic,.verification/notebooks01/reports,.verification/notebooks01/docs/screenshots | Out-Null
Copy-Item data/raw/retail_subset.csv .verification/notebooks01/data/raw/retail_subset.csv
python scripts/verify_notebooks.py .verification/notebooks01
```
Use a NEW output folder for each independent clean run. Logs, exact executed host commands, row counts and KPI CSVs are in reports/current_upgrade. The five updated notebooks ran locally; this is not Databricks execution.

The four-model study remains unchanged: naive WAPE 92.53%, seasonal naive 99.06%, Ridge 76.64%, Croston SBA 82.92%. Ridge bias is −31.55%. These are errors, not accuracy percentages. All 20 products and 840 equal product/date targets per method are included. No new training/tuning or holdout-based selection was performed in this upgrade. The historical evaluation periods were evaluated previously and are not a new untouched holdout.

The enhanced Excel workbook is byte-for-byte unchanged from the previous supplied release: nine sheets, 5,545 formulas, including all 5,222 original formulas. This task preserved rather than reauthored it. Previous artifact-engine validation remains in reports/enhancement/workbook_validation.json; Excel Desktop opening, recalculation and PivotTables remain pending.

## New capacity-constrained planning

The default is the existing synthetic inventory/capacity scenario and prespecified seasonal-naive daily forecasts. A separate scenario CSV can configure stock, lead time, capacity, standard deviation and optional absolute safety-stock and reorder-point overrides. A separate forecast CSV can replace demand with exact product-key coverage. A policy JSON configures horizon, review period and safety_z. Derived Gold reorder points are recomputed for a changed policy; only explicit scenario CSV fields act as overrides.

The plan caps requested production by horizon capacity and reports deferred quantities, whether production arrives after the horizon, modeled unserved demand and projected ending stock. Stock/flow balance and production capacity are tested. Capacities are independent per product; this is not shared-machine scheduling or a real factory optimizer. Demand is uniform within a bucket; modeled missed demand is treated as lost sales. Batch sizes, yields, inbound orders, holidays and observed factory utilization are absent.

| Default synthetic seven-day plan | Result |
|---|---:|
| Products | 20 |
| Requested production | 11,757.1561 units |
| Capacity-limited planned production | 4,638 units |
| Deferred production | 7,119.1561 units |
| Capacity-limited recommendations | 8 products |
| Modeled unserved demand | 349 units across 2 products |

These numbers are synthetic model outputs, not real stock-outs or savings. The earlier module's 5 demand/capacity shortfall flags and 6 full-lead-time stock risks are preserved and answer different questions.

```powershell
$env:PYTHONPATH = "src"
python -m supplysight.constrained_planning --policy data/synthetic/planning_policy.json
python -m supplysight.constrained_planning --inputs data/synthetic/configurable_planning_example.csv --forecasts data/synthetic/configurable_forecast_example.csv --policy data/synthetic/planning_policy.json --output reports/my_demo
python -m pytest -q
```
The included one-product hand-calculated CLI trial requests 102 units, plans 35, defers 67, models 20 unserved units and ends with 5 stock units. It was executed, not just documented. See docs/CAPACITY_CONSTRAINED_PLANNING.md for formulas. Outputs are separate from Gold and the Excel data.

## CustomsDesk: independent SQL and Power BI

The 22 DAX definitions are byte-for-byte preserved. A new measure_sql.py implements 22 independent queries over fact/dimension/quality tables, without using the warehouse reporting views. All 22 values match the existing SQL targets within 1e-8. The SQL statements and reconciliation CSV are in reports/enhancement/independent_measure_queries.sql and independent_measure_sql.csv. This validates SQL references; actual DAX results remain PENDING.

The reporting kit retains three exact pages: Executive Overview, Backlog and SLA Analysis, Data Quality and Classification. It includes the response-time band transformation, theme, field mapping, 11 relationship checks and 38 SQL filter-context targets. Closure-date throughput, opened-date cohorts and fixed-snapshot backlog are explicitly distinguished. Part-master and latest-run DQ visuals do not inherit misleading query date/authority filters. These contracts are prepared and structurally checked, not native-engine certified.

Fresh SQLite evidence is in reports/current_upgrade, including nine reporting/star tables in the exports. Reproduce in a fresh extracted folder with the existing requirements-dev.txt setup:
```powershell
$env:PYTHONPATH = "src"
New-Item -ItemType Directory -Force reports/current_upgrade | Out-Null
python -m customsdesk.cli etl --database-url sqlite:///reports/current_upgrade/warehouse.sqlite --data data/sample --reports reports/current_upgrade
python -m customsdesk.cli export --database-url sqlite:///reports/current_upgrade/warehouse.sqlite --exports reports/current_upgrade/exports
python -m customsdesk.dashboard --database-url sqlite:///reports/current_upgrade/warehouse.sqlite
python -m customsdesk.measure_sql --database-url sqlite:///reports/current_upgrade/warehouse.sqlite
python -m pytest -q
```
Unfiltered SQL results include 19,998 shipments, 29,994 queries, 13,375 backlog, 2,673 high-priority unresolved, 52-hour median response, 61.0613% SLA compliance and 99.9782% DQ pass rate. Rates in DAX targets are fractions; warehouse percentage KPIs use a 0–100 scale.

No editable PBIX was present in the supplied ZIPs, and none was fabricated. There is no native Power BI screenshot. To finish: follow docs/MANUAL_VERIFICATION.md, load current exports or your retained PostgreSQL connection, use model_relationships.json and REPORT_LAYOUT.md, add all 22 definitions, run powerbi/verify_measures_query.dax in DAX Query View, and fill the actual-result CSV from real execution. Compare all 38 contexts using customsdesk.powerbi_check, save the actual PBIX and capture its three pages.

## Blocked runtime actions

- Databricks: no exposed Databricks connector or authorized workspace runtime. Follow SupplySight docs/DATABRICKS_SETUP.md. Upload source into workspace files and raw data into a dedicated Unity Catalog Volume run directory, set both widgets, run notebooks 01→05, and save runtime JSONL/KPI outputs. Notebook 04 now runs the actual constrained planner and notebook 05 checks its balances. Local success does not certify managed runtime compatibility.
- Power BI and Excel Desktop: executables unavailable on this Linux host. Genuine application screenshots and native validation are pending. Rendered previews from the earlier workbook are labeled as previews.
- PostgreSQL/Docker: executables/server unavailable. Preserve your existing .env and Docker volume; use the guarded Windows scripts for the two integration tests. No credentials or volumes were changed.
- Windows PowerShell: unavailable here; exact Windows commands and native checklists supplied.
- GitHub publication, deployment and collaboration: not performed or claimed.

Availability checks are recorded in reports/current_upgrade/native_availability.json. Blocked applications were not represented as successfully executed commands.

## Evidence and resume wording

Exact commands, exit codes and successful/failed outputs are in reports/current_upgrade/commands.json and its log files. Native pending actions are separate from executed commands. Prior reports are preserved; this document and docs/EVIDENCE.md are the current authority. Proposed bullets are in docs/PROPOSED_DANFOSS_RESUME_BULLETS.md and the separate Proposed-Danfoss-Resume-Bullets.md. No resume DOCX was changed.
