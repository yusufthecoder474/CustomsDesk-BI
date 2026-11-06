# IT-change regression validation

Run `customsdesk regress` after a successful ETL. The warehouse kpi_snapshot stores each baseline;
change_request_log records trial outcomes and reports/regression.json contains exact differences.
Trials use isolated temporary SQLite warehouses and leave the baseline untouched. These trials
are not claimed as PostgreSQL change tests. CI separately exercises the PostgreSQL ETL contract.

- Passing scenario: source renames query_status to status_v2; a deliberate explicit adapter restores
  the supported interface. ETL reruns, row-quality checks and all KPI values match baseline.
- Intentionally failing scenario: a new ESCALATED status is introduced without an approved mapping.
  Every affected record is quarantined, query KPIs change, and the comparison flags FAIL.
  The harness passes only when this breaking scenario is detected as intended.

`compare` checks union of KPI names, handles NULL distinctly from zero and uses absolute 1e-9
numeric tolerance. DQ pass rate is part of the comparison. Tests independently confirm rollback,
row reconciliation, idempotent facts and unchanged baseline after trials.

A detected FAIL is an expected demonstration outcome, not a hidden passing claim. The module does
not resolve business semantics for new states; an analyst must agree mappings and fixture expectations.
