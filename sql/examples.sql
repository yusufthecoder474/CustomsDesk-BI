-- Run after init and ETL. All results describe SYNTHETIC DATA.
-- 1. Snapshot KPIs: each fact counted at its own grain.
SELECT * FROM vw_kpis;
-- 2. Slow authorities: responded queries only in the AVG.
SELECT * FROM vw_authority ORDER BY avg_response_hours DESC;
-- 3. Origin-country breakdown. This is not authority geography.
SELECT * FROM vw_country ORDER BY queries DESC;
-- 4. Ageing by priority, without closed queries.
SELECT * FROM vw_backlog ORDER BY query_priority,age_bucket;
-- 5. Zero-filled months, separate opened/closed dates and calendar-month LAG.
SELECT * FROM vw_monthly ORDER BY month;
-- 6. High-priority unclosed exceptions at the fixed cutoff.
SELECT query_id, authority_id, query_status, backlog_hours, sla_breach
FROM fact_customs_query
WHERE query_priority='HIGH' AND closed_at IS NULL ORDER BY backlog_hours DESC;
-- 7. Part business exceptions retained rather than hidden.
SELECT part_id,hs_code,classification_version,code_state,review_required
FROM dim_part WHERE code_state<>'VALID' OR review_required=true;
-- 8. Physical-row reconciliation for every source and run. Must return zero rows.
SELECT * FROM data_quality_results
WHERE source_rows<>accepted+rejected+duplicates+superseded;
-- 9. Join shipments to a pre-aggregated query count; preserve shipment value once.
WITH queries_per_shipment AS (
 SELECT shipment_id,COUNT(*) AS query_count FROM fact_customs_query GROUP BY shipment_id
)
SELECT s.shipment_id,s.declared_value,COALESCE(q.query_count,0) AS query_count
FROM fact_shipment s LEFT JOIN queries_per_shipment q ON s.shipment_id=q.shipment_id;
-- 10. Audit physical rows by rejection reason (choose a run_id when reconciling one run).
SELECT run_id,source,reason,COUNT(*) AS records
FROM rejected_records GROUP BY run_id,source,reason ORDER BY records DESC;
