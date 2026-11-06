# Windows one-click verification

Use the updated project files in the original existing project folder. A same-named Compose project belonging to another directory is refused before startup. Keep your existing .env locally: the package does not
contain one. Copying the repaired code over the existing project is supported; never copy .env.example
over an existing .env. The workflow preserves its unrelated settings and creates an ignored local
backup before targeted changes. It does not delete/recreate the virtual environment.

**Double-click `scripts\finish_windows.cmd`.** Keep Docker Desktop running first. Python 3.12 must
be installed; an existing Python-3.12 .venv is reused. Missing environments/dependencies are created
or installed automatically. You do not need to activate a virtual environment or type database URLs.

The workflow detects a free loopback port (5434 by default), rotates the previous local password on
first migration, starts only this directory's db service, waits for health and checks container and
database ownership. It then runs ETL, export, all tests against a new guarded PostgreSQL test database,
full-data SQLite/PostgreSQL reconciliation, regression and business analysis.

It leaves the database running for Power BI. Every run has a unique evidence folder under
`reports\windows-runs\<timestamp-id>`. Prior successful reports and exports are not overwritten.
Test databases are newly named `customsdesk_test_<random>` and are retained for inspection; no existing
database is reused or dropped. They may be reviewed later by the owner for retention management.

## Preview and diagnostics

From CMD in the project folder (these are CMD commands):

```bat
scripts\finish_windows.cmd -DryRun
scripts\finish_windows.cmd -Troubleshoot
scripts\finish_windows.cmd -RotatePassword
```

DryRun prints a plan with no file, environment, Docker or database changes. Troubleshoot checks the
existing dedicated service/configuration/identity without rotating credentials or starting services;
it writes a new diagnostic summary. RotatePassword explicitly rotates only the owned database role.

For PowerShell users, separate wrappers are available:

```powershell
.\scripts\check_environment.ps1
.\scripts\verify_postgres.ps1
.\scripts\verify_project.ps1
```

The CMD wrapper invokes Windows PowerShell with execution bypass scoped to that process. It does not
change the user's execution policy. The shared wrapper avoids Python command quoting that breaks in
Windows PowerShell 5.1. This source has been statically parsed, not executed on a Windows host here.

## Expected summary

A successful full invocation reports:

- Python/dependencies and Docker engine ready.
- Local configuration preserved, selected host port printed (password never printed).
- Owned container healthy; network authentication and instance marker verified.
- Actual postgresql ETL, test counts with zero skips, KPI reconciliation and regression completed.
- Evidence folder with verification.json, tests.xml, POSTGRES_TEST_RESULTS.txt,
  POSTGRES_VERIFICATION.md, DATABASE_RECONCILIATION.csv, QUERY_TIMINGS.json, CSV exports and
  POWER_BI_CONNECTION.json (host/port/database/export path only; no credentials).

Power BI Desktop verification is separate. A PASS here does not assert that a PBIX was created.
Stop safely with `docker compose stop db` from this project root when you finish using its database.
This stops only the current Compose project's db service; it does not remove data.

## If it stops

Read the short error and newest timestamped report. Other project resources and all PostgreSQL
volumes remain untouched. Do not run pruning or volume-deletion commands to solve authentication.
See POSTGRES_TROUBLESHOOTING.md for a non-destructive recovery path.
