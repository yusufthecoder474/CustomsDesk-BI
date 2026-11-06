# Data dictionary — SYNTHETIC DATA

Full columns and SQL types: sql/schema_postgresql.sql. Required source columns: clean.COLUMNS.
Raw CSV/JSON sources preserve all input fields and values before normalization.

| Source/table | Key and grain | Main fields and units |
|---|---|---|
| Shipments / fact_shipment | shipment_id, one shipment | supplier_id, part_id, origin_country, destination_country, dispatch/expected/actual dates; declared_value in synthetic USD; quantity in units; shipment_status |
| Queries / fact_customs_query | query_id, one customs query | shipment_id, authority_id; UTC opened/assigned/responded/closed timestamps; priority, type, status, SLA in elapsed hours, team and response outcome |
| Parts / dim_part | part_id, latest valid version | description, category, HS text, status, version, review date, review_required and code_state |
| dim_country | country_code | IN, SE, DE, US, CN; closed simulated reference set |
| dim_authority | authority_id | A1–A5 are fictional operational authorities |
| dim_query_type | query_type | CLASSIFICATION, VALUATION, DOCUMENTS |
| dim_date | date_key | Continuous ISO dates, year, month, weekday flag; starts at earliest dispatch/open or 2026-01-01 through cutoff |
| etl_run_log | run_id | RUNNING/SUCCESS/FAILED, checksum, cutoff, processing timestamps, elapsed seconds, error |
| raw_records | generated id; run/source/row lineage | Unmodified record JSON; includes duplicates and quarantined records |
| rejected_records | generated id; run/source/physical row | JSON payload and explicit reason, including exact duplicates and superseded part versions |
| data_quality_results | run_id and source | Physical source rows, accepted current rows, rejected defects, duplicate rows, superseded versions |
| kpi_snapshot | snapshot_id | Run-linked JSON values and label for baseline comparisons |
| change_request_log | change_id | Trial scenario, expected comparison outcome and exact differences |

Derived query fields: response_hours (nullable), business_response_hours (nullable), backlog_hours
(nullable for closed), sla_breach (0/1), opened_date/month, closed_date/month, age_bucket,
country_code (shipment origin), part_id (shipment part). Part code_state is MISSING, INVALID or VALID.
Invalid and absent HS codes remain in the part master for reporting; they are flagged for review,
not treated as shipment quarantine failures. HS-format validity is not legal classification validity.

Every generated artifact is labeled SYNTHETIC DATA in source manifest or accompanying report documentation.
No personally identifiable information is generated. A fixed seed and size parameters reproduce inputs.
