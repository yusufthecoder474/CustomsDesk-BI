> Historical verification retained. Current enhancement results: reports/enhancement/VERIFICATION.md (61 SupplySight tests; 96 CustomsDesk tests plus 2 PostgreSQL skips).

# CustomsDesk BI — final repair verification

Independent student project. **SYNTHETIC DATA only.** No Volvo affiliation, production use or financial savings claimed.

## Completed and independently executed

| Check | Actual result |
|---|---|
| Existing ZIP inspection | Retrieved CustomsDesk-BI(1).zip; original source/data/reports inspected |
| Original baseline tests before repair | 43 passed, 0 failed, 1 PostgreSQL check skipped |
| Repaired automated suite | **85 passed, 0 failed, 2 skipped**; 1.031 seconds |
| Full unchanged synthetic workload | **55,004 physical inputs; 54,992 accepted records** |
| Loaded facts and part master | 19,998 shipments; 29,994 queries; 5,000 current parts |
| Repaired SQLite ETL | SUCCESS; 3.571 seconds in this environment (single observation) |
| Source/data preservation | Aggregate source checksum unchanged from original release |
| KPI preservation | All 13 SQL KPI values match the original release exactly |
| Change-regression trials | Compatible adapter PASS; intentionally unsupported state FAIL detected as expected |
| Configuration/port/credential guards | Automated tests passed, including a real occupied local socket |
| Dry-run logic | Executed on Linux; no files, Docker or database changes |
| PowerShell source syntax | All seven scripts parsed without errors using tree-sitter-powershell |
| DAX-observation comparator | Tested; blank input template remains PENDING, incorrect percentage scale is flagged |

Evidence: reports/repair-tests.xml, reports/repair-execution/latest_run.json,
reports/repair-execution/regression.json, reports/POWERSHELL_STATIC_CHECK.md.
Original reports/tests.xml, reports/latest_run.json and reports/VERIFICATION.md remain historical
43-pass evidence and were not overwritten. The user's reported Windows ~8.65-second ETL is historical
user-provided evidence, not a new measurement made by this environment.

Environment: Python 3.12.14, Linux x86_64,
Pandas 2.2.3, SQLAlchemy 2.0.43, SQLite 3.53.1.

Executed commands from the repaired repository:

```sh
python -m pytest -q --junitxml=/tmp/customsdesk-before-repair.xml
python -m pytest -q --tb=short --junitxml=reports/repair-tests.xml
PYTHONPATH=src python -m customsdesk.windows finish --dry-run
PYTHONPATH=src python -m customsdesk.cli etl --database sqlite --database-url sqlite:////tmp/customsdesk-repaired.db --reports reports/repair-execution
PYTHONPATH=src python -m customsdesk.cli export --database sqlite --database-url sqlite:////tmp/customsdesk-repaired.db --exports reports/repair-execution/exports
PYTHONPATH=src python -m customsdesk.cli analyze --database sqlite --database-url sqlite:////tmp/customsdesk-repaired.db --reports reports/repair-execution
PYTHONPATH=src python -m customsdesk.cli regress --database sqlite --database-url sqlite:////tmp/customsdesk-repaired.db --reports reports/repair-execution
```

## Implemented but not executed in the target environment

- Configurable Compose port mapping, persistent existing named volume and health/readiness flow.
- Owned-container PostgreSQL role password rotation and per-install identity marker provisioning.
- CMD/PowerShell one-click dependency/setup/ETL/verification workflow.
- Newly created random guarded PostgreSQL test database and full-source PostgreSQL/SQLite reconciliation.
- Separate hosted unit and PostgreSQL GitHub Actions jobs; hosted Actions were not triggered.
- Power Query/DAX changes, latest-run DQ import, relationship specification and Power BI page materials.
- GitHub publication wrapper (preview by default); statically parsed, not executed with GitHub CLI.

## Blocked and remaining manual validation

This environment has no Docker CLI/engine, PostgreSQL server, Windows PowerShell runtime or Power BI
Desktop. Therefore **both PostgreSQL tests remain skipped**, not failed and not verified. The full
Windows automation has not been run against the user's PC, Docker containers or local .env. The new
Decimal conversion is independently unit-tested, not proof of PostgreSQL execution.

Power BI Desktop remains **PENDING**: no real PBIX, connector refresh, evaluated DAX outputs or report
screenshots were generated. The static PowerShell parser is not a substitute for Windows runtime testing.
No server latency/query-performance values are fabricated in the PostgreSQL pending reports.

## Exact next actions on Windows

1. Copy the updated project files into the existing
   `D:\Downloads\CustomsDesk-BI\CustomsDesk-BI` directory while preserving local `.env`, `.venv`
   and all Docker data. The same-named Compose project in another directory is refused before startup.
2. With Docker Desktop running, double-click `scripts\finish_windows.cmd`. It installs/validates
   dependencies, selects the port, rotates the old local password safely, verifies only this dedicated
   database, runs all tests and saves a unique `reports\windows-runs\...` folder. Existing volumes,
   databases and other projects are not removed. No password needs to be typed into a terminal URL.
3. To preview or diagnose from CMD:

```bat
scripts\finish_windows.cmd -DryRun
scripts\finish_windows.cmd -Troubleshoot
```

4. Review the newest run's verification.json, POSTGRES_VERIFICATION.md, POSTGRES_TEST_RESULTS.txt,
   DATABASE_RECONCILIATION.csv and QUERY_TIMINGS.json. Claim PostgreSQL success only after those
   actual local results pass. The workflow treats any enabled skipped tests as incomplete.
5. Open Power BI Desktop and follow docs/POWER_BI_WINDOWS_CHECKLIST.md and docs/POWER_BI_SETUP.md.
   Use the actual selected port/CSV folder from that run's POWER_BI_CONNECTION.json. Refresh both
   data-source modes as applicable, evaluate all 22 measures, build the three pages, save/reopen the PBIX.
6. After entering actual raw DAX observations in the provided template, run from CMD:

```bat
.venv\Scripts\python.exe -m customsdesk.powerbi_check --actual powerbi\DAX_ACTUAL_VALUES_TEMPLATE.csv --out reports\POWER_BI_RECONCILIATION.csv
```

Numeric comparisons alone do not verify a PBIX or report layout. Complete reports/POWER_BI_VALIDATION.md
with actual Desktop results. If local authentication cannot be rotated through the owned container,
follow docs/POSTGRES_TROUBLESHOOTING.md; do not reset/delete a volume.

## Publication and scope

No GitHub repository was published or modified. No license was selected. Owner approval and visibility
choice remain prerequisites to publication. Existing ETL, source records, SQL KPIs and historical results
were preserved. This repair release is not represented as fully PostgreSQL/Power BI runtime-verified.

## Fresh extraction and installed-package check

The final ZIP was CRC-checked and extracted into a separate directory. Its test suite returned
**85 passed, 0 failed, 2 PostgreSQL checks skipped**. A regular Python 1.1.0 wheel was built and
installed outside the source tree, then its ETL processed the complete extracted input set. The
source checksum and all 13 KPI values matched the preserved baseline exactly. Packaged SQL resources
were present. This verifies package portability on Linux, not Windows/PostgreSQL/Power BI execution.
