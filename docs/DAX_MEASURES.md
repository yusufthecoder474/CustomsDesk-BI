# DAX measures — SYNTHETIC DATA

Not yet verified in Power BI Desktop. Create measures in listed order. Expected unfiltered outputs come from reports/latest_run.json and data/exports/vw_kpis.csv. No hard-coded card values. SQL parameter placeholders represent a manual selected month. DAX percentages are fractions; SQL percentages are on a 0–100 scale.

## Total Shipments

```dax
Total Shipments = COALESCE(COUNTROWS(fact_shipment),0)
```

Meaning: Shipment count.
Validation: `SELECT total_shipments FROM vw_kpis`.
Expected output / edge cases: Integer; empty table returns 0.

## Total Queries

```dax
Total Queries = COALESCE(COUNTROWS(fact_customs_query),0)
```

Meaning: Query count.
Validation: `SELECT total_queries FROM vw_kpis`.
Expected output / edge cases: Integer; empty table returns 0.

## Open Backlog

```dax
Open Backlog = CALCULATE([Total Queries], KEEPFILTERS(ISBLANK(fact_customs_query[closed_at])))
```

Meaning: Queries without closure, including responded.
Validation: `SELECT open_queries FROM vw_kpis`.
Expected output / edge cases: Blank closures count as unresolved.

## Average Response Hours

```dax
Average Response Hours = AVERAGE(fact_customs_query[response_hours])
```

Meaning: Mean of completed responses.
Validation: `SELECT avg_response_hours FROM vw_kpis`.
Expected output / edge cases: Unanswered rows excluded; no response gives BLANK.

## Median Response Hours

```dax
Median Response Hours = MEDIAN(fact_customs_query[response_hours])
```

Meaning: Median of completed responses.
Validation: `SELECT median_response_hours FROM vw_kpis`.
Expected output / edge cases: No response gives BLANK.

## Business Response Days

```dax
Business Response Days = DIVIDE(AVERAGE(fact_customs_query[business_response_hours]),8)
```

Meaning: Mean working hours / eight.
Validation: `SELECT avg_business_response_days FROM vw_kpis`.
Expected output / edge cases: No holidays; UTC workday.

## Responded Queries

```dax
Responded Queries = COALESCE(COUNT(fact_customs_query[response_hours]),0)
```

Meaning: Completed responses.
Validation: `SELECT COUNT(response_hours) FROM fact_customs_query`.
Expected output / edge cases: Zero if none.

## SLA Met Responses

```dax
SLA Met Responses = COALESCE(COUNTROWS(FILTER(fact_customs_query, NOT ISBLANK(fact_customs_query[response_hours]) && fact_customs_query[sla_breach] = 0)),0)
```

Meaning: Responses within or exactly at SLA.
Validation: `SELECT COUNT(*) FROM fact_customs_query WHERE response_hours IS NOT NULL AND sla_breach=0`.
Expected output / edge cases: Unanswered rows excluded.

## SLA Compliance %

```dax
SLA Compliance % = DIVIDE([SLA Met Responses],[Responded Queries])
```

Meaning: Met responses / responded queries.
Validation: `SELECT sla_compliance_pct FROM vw_kpis`.
Expected output / edge cases: Format percentage. SQL value divided by 100; blank denominator → BLANK.

## SLA Breaches

```dax
SLA Breaches = COALESCE(SUM(fact_customs_query[sla_breach]),0)
```

Meaning: Overdue completed and unanswered queries.
Validation: `SELECT sla_breaches FROM vw_kpis`.
Expected output / edge cases: Strictly greater than SLA; exact threshold compliant.

## Average Backlog Hours

```dax
Average Backlog Hours = AVERAGE(fact_customs_query[backlog_hours])
```

Meaning: Age since opening for unclosed queries.
Validation: `SELECT avg_backlog_hours FROM vw_kpis`.
Expected output / edge cases: No unresolved rows → BLANK.

## High Priority Unresolved

```dax
High Priority Unresolved = CALCULATE([Open Backlog], KEEPFILTERS(fact_customs_query[query_priority] = "HIGH"))
```

Meaning: High-priority queries without closure.
Validation: `SELECT high_priority_unresolved FROM vw_kpis`.
Expected output / edge cases: Responded but unclosed count.

## Total Parts

```dax
Total Parts = COALESCE(COUNTROWS(dim_part),0)
```

Meaning: Accepted current part-master rows.
Validation: `SELECT COUNT(*) FROM dim_part`.
Expected output / edge cases: Part grain, not shipment grain.

## Missing Parts

```dax
Missing Parts = CALCULATE([Total Parts], KEEPFILTERS(dim_part[code_state] = "MISSING"))
```

Meaning: Parts with absent codes.
Validation: `SELECT COUNT(*) FROM dim_part WHERE code_state='MISSING'`.
Expected output / edge cases: Syntax only; no classification recommendation.

## Invalid Parts

```dax
Invalid Parts = CALCULATE([Total Parts], KEEPFILTERS(dim_part[code_state] = "INVALID"))
```

Meaning: Parts with invalid code syntax.
Validation: `SELECT COUNT(*) FROM dim_part WHERE code_state='INVALID'`.
Expected output / edge cases: Invalid-code rows retained for review.

## Missing Classification %

```dax
Missing Classification % = DIVIDE([Missing Parts],[Total Parts])
```

Meaning: Missing / all accepted parts.
Validation: `SELECT missing_classification_pct FROM vw_kpis`.
Expected output / edge cases: SQL percentage divided by 100; empty → BLANK.

## Invalid Classification %

```dax
Invalid Classification % = DIVIDE([Invalid Parts],[Total Parts])
```

Meaning: Invalid / all accepted parts.
Validation: `SELECT invalid_classification_pct FROM vw_kpis`.
Expected output / edge cases: SQL percentage divided by 100; empty → BLANK.

## Parts Requiring Review

```dax
Parts Requiring Review = CALCULATE([Total Parts], KEEPFILTERS(dim_part[review_required] = TRUE()))
```

Meaning: Flagged or missing/invalid parts.
Validation: `SELECT COUNT(*) FROM dim_part WHERE review_required = true`.
Expected output / edge cases: Boolean field, not text.

## Closed Throughput

```dax
Closed Throughput = CALCULATE([Total Queries], USERELATIONSHIP(dim_date[date_key],fact_customs_query[closed_date]), KEEPFILTERS(NOT ISBLANK(fact_customs_query[closed_at])))
```

Meaning: Closures under the closure date relationship.
Validation: `SELECT closed FROM vw_monthly WHERE month = :month`.
Expected output / edge cases: Use dim_date on axis; no responses counted as closures.

## Previous Month Throughput

```dax
Previous Month Throughput = CALCULATE([Closed Throughput], DATEADD(dim_date[date_key], -1, MONTH))
```

Meaning: Previous calendar month closures.
Validation: `SELECT prior_closed FROM vw_monthly WHERE month = :month`.
Expected output / edge cases: Contiguous date table; first month may be blank.

## MoM Throughput %

```dax
MoM Throughput % = DIVIDE([Closed Throughput] - [Previous Month Throughput],[Previous Month Throughput])
```

Meaning: Change divided by prior closures.
Validation: `SELECT mom_throughput_pct/100.0 FROM vw_monthly WHERE month = :month`.
Expected output / edge cases: Zero prior month → BLANK. Only use in monthly context.

## DQ Pass Rate %

```dax
DQ Pass Rate % = VAR LatestRun = MAXX(TOPN(1, FILTER(ALL(etl_run_log), etl_run_log[status] = "SUCCESS"), etl_run_log[finished_at], DESC, etl_run_log[run_id], DESC), etl_run_log[run_id])
RETURN DIVIDE(CALCULATE(SUM(data_quality_results[accepted]), data_quality_results[run_id] = LatestRun), CALCULATE(SUM(data_quality_results[source_rows]), data_quality_results[run_id] = LatestRun))
```

Meaning: Accepted / physical input rows for latest successful run.
Validation: `SELECT dq_pass_rate_pct FROM vw_kpis`.
Expected output / edge cases: Global snapshot metric, not a country/period metric; SQL divided by 100.

Exact SQL-derived targets for all 22 measures: powerbi/MEASURE_EXPECTATIONS.csv. Monthly targets use September 2026. These targets are validation inputs for Windows, not evidence of DAX execution.
