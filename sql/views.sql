CREATE VIEW IF NOT EXISTS vw_query_detail AS
SELECT q.*, a.authority_name, c.country_name,
       CASE WHEN responded_at IS NOT NULL AND sla_breach=0 THEN 1 ELSE 0 END AS response_within_sla,
       CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END AS is_backlog
FROM fact_customs_query q
JOIN dim_authority a ON q.authority_id=a.authority_id
JOIN dim_country c ON q.country_code=c.country_code;
CREATE VIEW IF NOT EXISTS vw_kpis AS
WITH ranked AS (
 SELECT response_hours,ROW_NUMBER() OVER(ORDER BY response_hours) AS rn,
 COUNT(*) OVER() AS n FROM fact_customs_query WHERE response_hours IS NOT NULL
), median AS (
 SELECT AVG(response_hours) AS value FROM ranked WHERE rn >= n/2.0 AND rn <= n/2.0+1
), dq AS (
 SELECT SUM(accepted)*100.0/NULLIF(SUM(source_rows),0) AS pass_rate
 FROM data_quality_results WHERE run_id=(SELECT run_id FROM etl_run_log WHERE status='SUCCESS' ORDER BY finished_at DESC, run_id DESC LIMIT 1)
)
SELECT
 (SELECT COUNT(*) FROM fact_shipment) AS total_shipments,
 COUNT(*) AS total_queries,
 COALESCE(SUM(CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END),0) AS open_queries,
 AVG(response_hours) AS avg_response_hours,
 (SELECT value FROM median) AS median_response_hours,
 AVG(business_response_hours)/8.0 AS avg_business_response_days,
 SUM(CASE WHEN responded_at IS NOT NULL AND sla_breach=0 THEN 1.0 ELSE 0 END)*100.0/NULLIF(COUNT(response_hours),0) AS sla_compliance_pct,
 COALESCE(SUM(sla_breach),0) AS sla_breaches,
 AVG(backlog_hours) AS avg_backlog_hours,
 COALESCE(SUM(CASE WHEN query_priority='HIGH' AND closed_at IS NULL THEN 1 ELSE 0 END),0) AS high_priority_unresolved,
 (SELECT SUM(CASE WHEN code_state='MISSING' THEN 1.0 ELSE 0 END)*100.0/NULLIF(COUNT(*),0) FROM dim_part) AS missing_classification_pct,
 (SELECT SUM(CASE WHEN code_state='INVALID' THEN 1.0 ELSE 0 END)*100.0/NULLIF(COUNT(*),0) FROM dim_part) AS invalid_classification_pct,
 (SELECT pass_rate FROM dq) AS dq_pass_rate_pct
FROM fact_customs_query;
CREATE VIEW IF NOT EXISTS vw_authority AS
 SELECT authority_id,COUNT(*) AS queries,AVG(response_hours) AS avg_response_hours,SUM(sla_breach) AS breaches,
 SUM(CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END) AS backlog FROM fact_customs_query GROUP BY authority_id;
CREATE VIEW IF NOT EXISTS vw_country AS
 SELECT country_code,COUNT(*) AS queries FROM fact_customs_query GROUP BY country_code;
CREATE VIEW IF NOT EXISTS vw_backlog AS
 SELECT age_bucket,query_priority,COUNT(*) AS queries FROM fact_customs_query WHERE closed_at IS NULL GROUP BY age_bucket,query_priority;
CREATE VIEW IF NOT EXISTS vw_monthly AS
WITH monthly AS (
 SELECT SUBSTR(date_key,1,7) AS month FROM dim_date GROUP BY SUBSTR(date_key,1,7)
), counts AS (
 SELECT month,
 (SELECT COUNT(*) FROM fact_customs_query q WHERE q.opened_month=m.month) AS opened,
 (SELECT COUNT(*) FROM fact_customs_query q WHERE q.closed_month=m.month) AS closed
 FROM monthly m
), lagged AS (
 SELECT *,LAG(closed) OVER(ORDER BY month) AS prior_closed FROM counts
)
SELECT *, (closed-prior_closed)*100.0/NULLIF(prior_closed,0) AS mom_throughput_pct FROM lagged;
