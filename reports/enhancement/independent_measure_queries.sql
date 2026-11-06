-- Total Shipments
SELECT COUNT(*) FROM fact_shipment;

-- Total Queries
SELECT COUNT(*) FROM fact_customs_query;

-- Open Backlog
SELECT COUNT(*) FROM fact_customs_query WHERE closed_at IS NULL;

-- Average Response Hours
SELECT AVG(response_hours) FROM fact_customs_query;

-- Median Response Hours
WITH ordered AS (
        SELECT response_hours, ROW_NUMBER() OVER (ORDER BY response_hours) AS position,
        COUNT(*) OVER () AS population FROM fact_customs_query WHERE response_hours IS NOT NULL)
        SELECT AVG(response_hours) FROM ordered
        WHERE position IN (CAST((population+1)/2 AS INTEGER), CAST((population+2)/2 AS INTEGER));

-- Business Response Days
SELECT AVG(business_response_hours)/8.0 FROM fact_customs_query;

-- Responded Queries
SELECT COUNT(response_hours) FROM fact_customs_query;

-- SLA Met Responses
SELECT COUNT(*) FROM fact_customs_query WHERE response_hours IS NOT NULL AND sla_breach=0;

-- SLA Compliance %
SELECT COUNT(CASE WHEN response_hours IS NOT NULL AND sla_breach=0 THEN 1 END)*1.0/NULLIF(COUNT(response_hours),0) FROM fact_customs_query;

-- SLA Breaches
SELECT COALESCE(SUM(sla_breach),0) FROM fact_customs_query;

-- Average Backlog Hours
SELECT AVG(backlog_hours) FROM fact_customs_query;

-- High Priority Unresolved
SELECT COUNT(*) FROM fact_customs_query WHERE closed_at IS NULL AND query_priority='HIGH';

-- Total Parts
SELECT COUNT(*) FROM dim_part;

-- Missing Parts
SELECT COUNT(*) FROM dim_part WHERE code_state='MISSING';

-- Invalid Parts
SELECT COUNT(*) FROM dim_part WHERE code_state='INVALID';

-- Missing Classification %
SELECT COUNT(CASE WHEN code_state='MISSING' THEN 1 END)*1.0/NULLIF(COUNT(*),0) FROM dim_part;

-- Invalid Classification %
SELECT COUNT(CASE WHEN code_state='INVALID' THEN 1 END)*1.0/NULLIF(COUNT(*),0) FROM dim_part;

-- Parts Requiring Review
SELECT COUNT(*) FROM dim_part WHERE review_required=TRUE;

-- Closed Throughput
SELECT COUNT(*) FROM fact_customs_query WHERE closed_at IS NOT NULL AND closed_date>='2026-09-01' AND closed_date<'2026-10-01';

-- Previous Month Throughput
SELECT COUNT(*) FROM fact_customs_query WHERE closed_at IS NOT NULL AND closed_date>='2026-08-01' AND closed_date<'2026-09-01';

-- MoM Throughput %
SELECT (SUM(CASE WHEN closed_date>='2026-09-01' AND closed_date<'2026-10-01' THEN 1.0 ELSE 0 END)-
        SUM(CASE WHEN closed_date>='2026-08-01' AND closed_date<'2026-09-01' THEN 1.0 ELSE 0 END))/
        NULLIF(SUM(CASE WHEN closed_date>='2026-08-01' AND closed_date<'2026-09-01' THEN 1.0 ELSE 0 END),0)
        FROM fact_customs_query WHERE closed_at IS NOT NULL;

-- DQ Pass Rate %
SELECT SUM(accepted)*1.0/NULLIF(SUM(source_rows),0) FROM data_quality_results
        WHERE run_id=(SELECT run_id FROM etl_run_log WHERE status='SUCCESS'
        ORDER BY finished_at DESC,run_id DESC LIMIT 1);