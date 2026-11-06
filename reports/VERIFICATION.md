> Historical verification retained. Current enhancement results: reports/enhancement/VERIFICATION.md (61 SupplySight tests; 96 CustomsDesk tests plus 2 PostgreSQL skips).

# Verification report

Generated from actual JUnit and ETL output. SYNTHETIC DATA only.

| Check | Result |
|---|---|
| Pytest | 43 passed, 0 failed, 1 skipped; 1.122 seconds |
| PostgreSQL integration | Skipped; no server/Docker available |
| Full default ETL | SUCCESS; 55,004 input rows |
| Reconciliation | 54,992 accepted; every physical row accounted for |
| KPI fixtures | Mean/median 34 h, 0.25 business days and 50% compliance checks passed |
| Idempotency/constraints/rollback | Automated checks passed |
| Source-change adapter | Expected PASS |
| Unsupported new status | Expected FAIL detected; baseline unaffected |
| Power BI Desktop | Not available; M/DAX execution and PBIX assembly pending |
| Docker/hosted GitHub Actions | Configuration supplied; not executed |

Environment: Python 3.12.14, Linux x86_64,
Pandas 2.2.3, SQLAlchemy 2.0.43, SQLite 3.53.1.
Host details are not a student-laptop performance promise.

Commands actually executed from repository root:

```sh
python -m pytest -q --tb=short --junitxml=reports/tests.xml
PYTHONPATH=src python -m customsdesk.cli demo
PYTHONPATH=src python scripts/export_schema.py
PYTHONPATH=src python scripts/summarize_verification.py
```

The demo executes generation, ETL, export, SQL EDA and both isolated regression trials. A timezone
mismatch found in the first development test run was fixed; the final JUnit result above is the
current suite outcome. The PostgreSQL binary bootstrap attempt could not create its service user;
the successful SQLite run is not represented as PostgreSQL verification. No tools were used to
publish the repository or select a license.

Known limits: full-snapshot/single-writer processing; ISO text timestamps; no holiday calendar or
production source access; no SQL Server implementation; no executed Power BI/Desktop or hosted CI.
