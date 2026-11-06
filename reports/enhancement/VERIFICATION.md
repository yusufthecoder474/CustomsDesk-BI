> Previous enhancement record retained. Current results and proposed wording: docs/EVIDENCE.md and docs/PROPOSED_DANFOSS_RESUME_BULLETS.md.

# Danfoss project upgrade verification

Verified locally on 26 October 2026. Both attached projects were extended in place. Original datasets, baseline forecasting code, SQL schema and 22 CustomsDesk DAX definitions were preserved. No Git history was supplied and no project was uploaded to GitHub.

## Completed checks

| Area | Executed evidence | Status |
|---|---|---|
| SupplySight full ETL | Fresh local Spark CLI and five-notebook runs: 26,058 raw, 24,258 accepted, 1,800 rejected | PASS |
| SupplySight Gold/KPIs | 350,997 units, 20 products, 365 days, 8 Gold datasets, 14 arithmetic/SQL controls | PASS |
| SupplySight tests | 61 passed, 0 failures, 0 skips | PASS |
| Forecast study | Four methods, same 840 product/date targets per method; 3×14-day rolling origins | PASS |
| Demand diagnostics | Initial-training volume tertiles, zero-day shares, ADI/CV² patterns; product/segment/pattern/fold scores | PASS |
| Planning | Existing deterministic synthetic scenario; weekly capacity, cover, lead-time/reorder checks and 10 exception products | PASS |
| Excel preservation | All 5,222 original formulas and all original nonformula cell values unchanged | PASS |
| Enhanced Excel | 9 sheets, 5,545 formulas, 3 charts; original sheets retained; scenario edits update new flags; no formula errors found | PASS in artifact engine |
| CustomsDesk ETL | Fresh SQLite: 55,004 synthetic source rows, 54,992 accepted; historical 13 KPI targets reproduced | PASS |
| CustomsDesk tests | 96 passed, 0 failures, 2 PostgreSQL-specific skips | PASS locally |
| CustomsDesk reporting contract | 22 preserved measures, column references checked; 11 relationship specs checked for unique keys/orphans | PASS static/SQL only |
| DAX reconciliation preparation | 38 SQL measure/context targets, real-observation template and executable Desktop DAX query supplied | PREPARED |
| Three Power BI pages | Exact field layout, theme, M response distribution, relationship/filter instructions | PREPARED |
| Configuration | No private .env or Docker volume changed; setup now retains existing passwords by default | PASS tests |

## Forecast results and limits

| Model | Pooled WAPE | MAE, units | Bias | Products better / worse than seasonal naive |
|---|---:|---:|---:|---:|
| Naive | 92.53% | 67.06 | −11.88% | 9 / 11 |
| Seasonal naive | 99.06% | 71.80 | −9.47% | reference |
| Ridge | 76.64% | 55.55 | −31.55% | 18 / 2 |
| Croston SBA, alpha 0.1 | 82.92% | 60.09 | −18.29% | 15 / 5 |

The added Croston SBA does not beat Ridge overall. No new improvement over the existing Ridge result is claimed. Ridge's reproduced relative WAPE reduction versus seasonal naive is 22.63%, but its −31.55% bias signals substantial underforecasting. All 20 products are included. There are 137 zero-demand evaluation days out of 840 targets; MAE/WAPE include them, and separate zero-day forecast quantities are reported. Three expanding origins use only preceding actuals for training; Ridge forecasts recursively. Segments use only the first 323 training days. No hyperparameter search, winner selection or final-data tuning was performed. These historical evaluation periods were already inspected in the original project; they are not a newly untouched holdout. Prospective evaluation is pending.

Public retail sales are a demand proxy and absent transactions are assumed zero. They are not manufacturing production records. Seasonal naive remains the prespecified planning forecast. The reused seed-52316 capacity/stock scenario flags 5 modeled capacity shortfalls, 6 lead-time stock risks, 8 reorder needs and 10 unique exception products. Total expected weekly demand is 11,238 units against 14,110 modeled capacity units; product constraints still matter. No real utilization, stock-out, customer or savings outcome is claimed.

## Stale notebook discrepancy

The original notebook log reports 52,116 raw /24,258 accepted /27,858 rejected, despite its earlier Bronze message showing 26,058. Prior documentation attributes this to retained legacy part files. That diagnosis is consistent with exactly doubled raw rows but was not reproduced as a host defect here. The original log, prior failures and final original reports remain in the archive and at their original paths. Current clean CLI and notebook evidence both reproduce 26,058 /24,258 /1,800. The final notebook also asserts these expected dataset-specific counts, preventing a doubled but internally balanced partition from passing. See SupplySight docs/STALE_NOTEBOOK_RESOLUTION.md.

## Blocked and pending runtime checks

| Check | Why pending | Exact next action |
|---|---|---|
| Databricks Free Edition | No authorized workspace runtime available | Use SupplySight docs/DATABRICKS_SETUP.md; set code and Volume roots; execute 01→05; save real runtime logs and screenshots |
| Power BI Desktop/PBIX | Windows desktop application unavailable in Linux | Load actual exports, apply M/theme, build relationships/pages, execute verify_measures_query.dax and compare all 38 contexts |
| PostgreSQL | No PostgreSQL server/Docker executable available here | Retain local .env/volume and use guarded Windows verification scripts; run the two integration checks |
| Excel Desktop | Application unavailable | Open supplied workbook, fully recalculate, verify flags/charts/filters and save genuine screenshots |
| PivotTables/Excel Power Query | Native features were not created or verified | Follow optional Desktop steps; do not claim implemented until tested |
| Windows PowerShell setup | Commands prepared, Windows unavailable | Execute supplied checklist and retain logs |
| GitHub Actions | Remote workflow not executed | User-authorized future publication/CI run |

No Databricks outputs, PBIX, Desktop screenshots or native PivotTable results were fabricated. The included workbook images are rendered workbook previews; forecast PNGs are plots of executed predictions. Source-format notebooks and a Volume-aware writer are prepared for serverless compatibility; that is not Databricks runtime certification. All DAX actual-value cells remain empty and the comparison correctly returns 38 PENDING rows (exit 1). SQL/schema checks do not establish DAX filter-context behavior.

## Engineering evidence

Each project's reports/enhancement includes COMMANDS.md, environment.json, tests.log, tests.xml and result CSVs/JSON. SupplySight also has clean_pipeline_evaluation.json, clean_notebook_evaluation.json, notebook_runtime.jsonl, notebook logs and workbook_validation.json. CustomsDesk has dashboard_contract.json, relationship_checks.csv, DAX_SQL_TARGETS.csv and empty DAX_ACTUAL_VALUES.csv. The new dashboard module confirms the original 22 SQL targets, then adds 16 contexts (LOW priority, authority A1, empty query cohort, September opened cohort). The Power BI layout explicitly distinguishes opened cohorts, closure dates, current backlog and global classification/DQ measures.

Environment: Python 3.12.14, Java 17, Spark 3.5.3, pandas 2.2.3, NumPy 2.3.5, scikit-learn 1.8.0, DuckDB 2.0.0, PyArrow 26.0.0, SQLAlchemy 2.0.43, psycopg 3.2.10. CustomsDesk's original locked NumPy/Pydantic/dotenv/pytest differ from the host; the exact locked Windows environment remains pending. The lock was preserved.

Resolved execution issues include an unavailable optional tabulate dependency (removed from report generation), an exact floating-point equality test (replaced with tight tolerance) and one pre-notebook host startup error (original short log retained; subsequent sequential run passed). See COMMANDS.md.

## Deliverables

- SupplySight-Analytics-Enhanced.zip — source, tests, original data and archived evidence, new study/planning reports, enhanced Excel workbook, diagrams/banner and setup instructions.
- CustomsDesk-BI-Enhanced.zip — source, tests, original data and archived evidence, SQL exports, reporting kit, diagrams/banner and verification instructions.
- Manual-Verification-Checklist.md — explicit Windows, Databricks, Excel and Power BI actions.
- Verified-Resume-Bullets.md — three supported bullets for each project.
- Danfoss-Resume-Project-Section.md — concise section suitable for your one-page resume.

The two ZIPs exclude private configuration, credentials, virtual environments, Python/build caches, generated local SQLite database files and a stray incomplete hidden CSV export. Original input ZIPs are untouched. Original historical text is retained; current execution evidence always lives under reports/enhancement. See PACKAGE_MANIFEST.sha256 for included file checksums.
