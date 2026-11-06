# Executed commands and environment

All commands ran on Linux with Python 3.12.14 and Java 17. Full package versions are recorded in environment.json. These are local checks, not Windows/native or cloud certification.

| Command (from project directory; PYTHONPATH=src) | Outcome |
|---|---|
| SupplySight python -m pytest -q --junitxml=reports/enhancement/tests.xml | Final: 61 passed |
| SupplySight python -m supplysight.cli --root /tmp/supplysight-clean | PASS; fresh CLI outputs |
| SupplySight python scripts/verify_notebooks.py /tmp/supplysight-notebooks | PASS initial fresh run; PASS final rerun with runtime-duration logs |
| SupplySight python -m supplysight.study | PASS after removing optional tabulate dependency |
| SupplySight python -m supplysight.capacity | PASS |
| Artifact-tool node enhance.mjs <project-root> | PASS; saved XLSX, renders and scenario mutation checks |
| CustomsDesk python -m pytest -q --junitxml=reports/enhancement/tests.xml | Final: 96 passed, 2 PostgreSQL skipped |
| CustomsDesk python -m customsdesk.cli etl --database-url sqlite:///reports/enhancement/warehouse.sqlite --data data/sample --reports reports/enhancement | PASS |
| CustomsDesk python -m customsdesk.cli export --database-url sqlite:///reports/enhancement/warehouse.sqlite --exports reports/enhancement/exports | PASS |
| CustomsDesk python -m customsdesk.dashboard --database-url sqlite:///reports/enhancement/warehouse.sqlite | PASS; preserved original 22 SQL targets, produced 38 contexts |
| Saved XLSX inspection using read-only openpyxl | Original 5,222 formulas unchanged; 5,545 total, 9 sheets, 3 charts |

## Failures and corrections
The study initially attempted pandas.to_markdown without tabulate, and failed after generating its CSVs/charts. Removed that optional dependency and reran successfully. One added capacity test used exact floating-point equality after CSV serialization; changed it to a tight numerical tolerance after confirming the independently computed ratio. A notebook retry failed before notebook execution with 'fatal library error, lookup self'; its short log remains notebooks_repeat.log. A subsequent sequential notebook run succeeded. No definitive cause for that host startup failure was established. A few editing helper invocations used a wrong relative working path; corrected to absolute paths without altering source data.

Dependency installation: installed PySpark 3.5.3, DuckDB 2.0.0, SQLAlchemy 2.0.43 and psycopg 3.2.10 into the execution host. Preinstalled CustomsDesk pandas/SQLAlchemy/psycopg matched pins; numpy 2.3.5, Pydantic 2.14.1, python-dotenv 1.2.4 and pytest 9.1.1 differ from its original lock. Tests passed in the recorded environment; the exact Windows locked environment is pending. No dependency lock was falsely regenerated.

The workbook was authored/imported/exported with the bundled @oai/artifact-tool; openpyxl was used only for read-only inspection and existing tests. No native PivotTable or Power Query workbook feature is claimed. Screenshots of native Excel, Power BI and Databricks were not possible. Rendered XLSX previews are explicitly labeled.
