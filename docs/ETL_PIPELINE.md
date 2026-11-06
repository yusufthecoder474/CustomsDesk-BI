# ETL pipeline

1. Generate three sources using NumPy seed 474. Save manifest and injected_defects.json.
2. Create a run ID; hash source bytes plus manifest; persist RUNNING and the UTC as-of cutoff.
3. Preserve every physical input record in raw_records, independently of the warehouse transaction.
4. Validate required schema; trim and normalize countries/statuses; require timezone-aware events;
   reject unknown keys, invalid timelines and unsupported enum values with explicit reasons.
5. Resolve exact duplicates once. Accept a higher valid part version; retain superseded input in quarantine.
   Same/older conflicting versions are rejected. Shipment/query conflicting updates require intervention.
6. Calculate response intervals and working-time overlaps using a documented fixed calendar.
7. In one transaction, write row reconciliation and quarantine; replace analytical snapshot in FK-safe
   order; create dimensions/facts; calculate SQL KPIs; save KPI snapshot and mark SUCCESS.
8. On error roll back analytical changes and mark FAILED separately; preserve previous good snapshot
   and raw lineage. Write a failure JSON. Every successful run writes run-ID JSON and latest_run.json.
9. Export facts, dimensions, audit records and analytical views to CSV; run SQL-driven EDA.

Full-snapshot replacement is intentional: repeated identical runs cannot duplicate facts. Audit runs
remain separate and accumulate by design. This is not incremental CDC or an SCD Type 2 warehouse.
A pipeline rejection differs from an invalid HS field retained as a reviewable business exception.

Reconciliation per source:
`source_rows = accepted + rejected + duplicates + superseded`.
DQ pass rate uses physical rows in the denominator, so duplicates and superseded versions lower it.

Operational assumptions: one ETL writer at a time; refresh Power BI after successful runs; do not run
concurrent imports. SIGKILL/power loss rolls back the open transaction but may leave RUNNING audit
status. After confirming the worker is stopped, mark that run FAILED with an interruption note and
rerun the same source snapshot. There is no automated stale-worker recovery service.

Source schema changes fail the run rather than silently loading an empty table. Individual bad rows
are quarantined. Unknown authorities/statuses require an explicit mapping change; no guessed mappings.
Raw CSV file bytes remain in data/sample; raw_records preserve parsed records, not CSV whitespace.
