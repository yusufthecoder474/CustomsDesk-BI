# CustomsDesk BI

**Customs Operations ETL, SQL Warehouse & Power BI Analytics**

**SYNTHETIC DATA · Independent student portfolio project · No Volvo affiliation**

Customs teams need a consistent view of shipments, authority queries and part classifications.
CustomsDesk BI integrates three simulated operational systems, preserves source lineage, quarantines
invalid records and calculates operational KPIs from a relational warehouse.

**Verification status:** Python/SQL execution was verified using SQLite. PostgreSQL is the primary
deployment target; its integration test is supplied but skipped here because a server was unavailable.
Power BI Desktop is unavailable: M, DAX, CSV exports and a three-page report guide are supplied,
**not yet verified in Power BI Desktop**. No PBIX has been fabricated. Nothing was published to GitHub.

## What is implemented

- Configurable fixed-seed generator: shipment CSV, query JSON and part CSV, with a defect ledger.
- Validated ETL, immutable per-run raw records, checksums, quarantine reasons and reconciliation.
- Star schema with relational constraints/indexes, atomic snapshot replacement and fact idempotency.
- SQL KPIs, median via window functions, calendar-month throughput and month-over-month LAG.
- UTC response/SLA rules, business-calendar overlap and explicit unresolved-query handling.
- Isolated source-change trials, KPI comparisons and an intentionally detected breaking change.
- SQL-driven EDA, business insights, 16 dashboard-ready CSV exports.
- Power Query loader and table queries, **22 DAX measures**, theme and exact three-page visual mapping.
- Automated tests, PostgreSQL CI configuration, Windows setup and interview materials.

```mermaid
flowchart TD
  A["Three synthetic systems"] --> B["Raw audit and validation"]
  B --> C["Quarantine and quality report"]
  B --> D["Atomic SQL warehouse"]
  D --> E["SQL KPIs and CSV exports"]
  E --> F["Power Query and DAX"]
  F --> G["Three Power BI pages"]
  D --> H["Change trials and regression report"]
```

## Quick start — Windows PowerShell

Extract the ZIP and open PowerShell **in the CustomsDesk-BI folder**. Python 3.12 is recommended.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -e .
python -m customsdesk.cli demo
python -m pytest -q
```

If script execution is restricted, activation is optional: run `.\.venv\Scripts\python.exe` instead
of `python` for each command. The quick start intentionally uses SQLite and recreates the synthetic
sources, warehouse, exports and reports. No local database is included in the ZIP.
On Linux/macOS use `python3 -m venv .venv` and `source .venv/bin/activate`.

## Primary PostgreSQL setup

Install/start Docker Desktop; copy `.env.example` to `.env`, choose a local password and keep `.env`
untracked. Compose loads it for the database; the Python CLI reads environment variables, not .env files.

```powershell
Copy-Item .env.example .env
# Edit .env to set POSTGRES_PASSWORD before continuing.
docker compose up -d db
docker compose ps
# Replace placeholders; URL-encode password characters in the URL.
$env:DATABASE_URL = 'postgresql+psycopg://customsdesk:YOUR_URL_ENCODED_PASSWORD@localhost:5432/customsdesk'
python -m customsdesk.cli init
python -m customsdesk.cli generate
python -m customsdesk.cli etl
python -m customsdesk.cli export
python -m customsdesk.cli analyze
python -m customsdesk.cli regress
```

`init` creates tables and views using SQLAlchemy. Generated PostgreSQL DDL is also provided in
sql/schema_postgresql.sql and sql/views_postgresql.sql. Use one initialization route on a new
empty database; there is no automatic migration of an older schema. SQL Server is not implemented.
Stop the local service with `docker compose stop db`.

For the PostgreSQL integration test, use a **separate disposable test database** because tests replace
warehouse contents. Set TEST_POSTGRES_URL to that database, then run pytest. Never point tests at an
operational warehouse. CI is configured to do this on PostgreSQL 17.6; hosted CI was not run here.

## Commands

```powershell
customsdesk generate --seed 474 --shipments 20000 --queries 30000 --parts 5000
customsdesk etl
customsdesk kpis
customsdesk export
customsdesk analyze
customsdesk regress
customsdesk demo
```

Generator distributions are configurable with `--config data/generator_config.json`; probabilities and rates are validated. Status order is OPEN, ASSIGNED, RESPONDED, CLOSED; priority order is HIGH, NORMAL, LOW.

All commands accept `--database-url`, `--data`, `--reports` and `--exports`. `demo` regenerates sources,
runs ETL, exports, EDA and isolated change trials. It replaces the analytical snapshot; raw audits
accumulate. Use a fresh database for one-run reconciliation. Run one ETL writer at a time.
`requirements-lock.txt` pins the dependency closure captured in the verification environment.

## Power BI

Start with [docs/POWER_BI_SETUP.md](docs/POWER_BI_SETUP.md), then [powerbi/REPORT_LAYOUT.md](powerbi/REPORT_LAYOUT.md).

1. Create parameters and fxLoad from powerbi/; choose PostgreSQL or CSV fallback.
2. Import named table queries, configure the documented star relationships and date roles.
3. Create measures from powerbi/measures.dax, import theme.json and assemble three pages.
4. Refresh and reconcile to data/exports/vw_kpis.csv and vw_monthly.csv.
5. Save CustomsDesk-BI.pbix locally. Complete reports/POWER_BI_VALIDATION.md after real execution.

Pages: Executive Operations Overview; Process Bottlenecks; Classification & Data Quality.
Power BI is the intended business dashboard. There is no substitute Streamlit dashboard.

## Data and definitions

Default inputs contain 20,000 shipments, 30,000 queries and 5,000 parts **before** duplicate/update
injections. The generator records all assumptions and defects. Values, authority identities, event
frequencies and country mix are simulated; none represent Volvo records or observed customs operations.
The cutoff is fixed at 2026-10-01 UTC for reproducibility. HS checking validates format only.
Read docs/KPI_DICTIONARY.md before interpreting any chart. Currency is synthetic USD.

## Measured results

See reports/VERIFICATION.md for executed commands and environment; reports/latest_run.json for
run ID/checksums/timing and actual counts; reports/tests.xml for test evidence. The generated
RESULTS.md summarizes the verified build. Business findings come from SQL in reports/BUSINESS_INSIGHTS.md.
No cost savings, production users, real operational improvement or unexecuted dashboard results are claimed.

## Repository map

| Folder | Contents |
|---|---|
| src/customsdesk | Generator, validation, warehouse, ETL, SQL-driven EDA, regression and CLI |
| sql | PostgreSQL schema, views and example analytical queries |
| tests | Unit, integration, hand-calculated KPI and rollback checks |
| data/sample | Full reproducible synthetic inputs and injected-defect ledger |
| data/exports | Power BI-ready UTF-8 CSV snapshots |
| powerbi | M queries, DAX source, theme and visual layout |
| reports | Actual run/quality/regression/EDA/test evidence |
| docs | Dictionaries, setup, architecture, interview and publishing instructions |

## Limits and next steps

PostgreSQL/Docker execution and Power BI Desktop refresh remain unverified in this build environment.
SQLite tests do not prove PostgreSQL execution. Dates/timestamps are persisted as normalized ISO text
in the portable warehouse; duration fields are numeric. The pipeline is a single-writer full snapshot,
not production CDC, scheduling or historical classification tracking. There is no holiday calendar,
legal tariff verification, currency conversion, authentication service or real source integration.
Dependencies/container tags and CI are supplied, not claimed as executed hosted services.
Next steps: verify PostgreSQL/Power BI on Windows, agree business calendars, add source contracts and
incremental/history handling, and validate with approved real data.

## License and publication

No open-source license selected. Repository visibility and publication remain the owner's decision.
See docs/GITHUB_PUBLISH.md for manual publishing to `yusufthecoder474/CustomsDesk-BI` after review.
