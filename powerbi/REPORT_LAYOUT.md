# Three-page Power BI build specification

Status: PREPARED; Power BI Desktop unavailable. Zero pages executed; no PBIX or screenshot created. Canvas 1280×800, supplied theme.json, margin 32px, dark navy headers and restrained red exceptions. Label all pages SYNTHETIC DATA, fixed snapshot 2026-10-01 UTC. Charts show the current snapshot's opened/closed cohorts; backlog trend is not a historical as-of reconstruction.

## Page 1 — Executive Overview
Six 192×96 cards at y=88: Total Shipments, Open Backlog, High Priority Unresolved, Median Response Hours, SLA Compliance %, Total Queries. Format response as hours and compliance as percentage (stored fraction). At y=240 place a 780×300 line/column chart with dim_date[date_key] by month, Total Queries and Closed Throughput. At x=850,y=240,w=390,h=300 show authority_name and Average Response Hours. At y=570 a query exception table uses query_id, query_priority, backlog_hours, authority_id, query_status filtered to HIGH and closed_at blank.

## Page 2 — Backlog and SLA Analysis
At x=32,y=150,w=580,h=250: stacked bar with fact_customs_query[age_bucket], Open Backlog, legend query_priority, excluding blank ages. At x=650,y=150: query_priority against Total Queries and SLA Breaches. At x=32,y=450: fact_customs_query[response_bucket] against Total Queries; the response bands are created by fact_customs_query.m and include a separate Not responded bucket. At x=650,y=450: dim_date[date_key] month against SLA Breaches and Closed Throughput. Query-detail drillthrough table uses query_id, sla_hours, response_hours, backlog_hours, closed_at and priority.

## Page 3 — Data Quality and Classification
At y=90 four cards: Missing Parts, Invalid Parts, Parts Requiring Review, DQ Pass Rate %. At x=32,y=230,w=570,h=220: classification_status against Total Parts. At x=640,y=230: data_quality_results[source] with source_rows, accepted, rejected, duplicates, superseded; M already filters the latest successful ETL run. At x=32,y=500: dim_part detail filtered code_state <> VALID or review_required true. At x=640,y=500: query_status against Total Queries and a month variance table with Closed Throughput, Previous Month Throughput and MoM Throughput %.

## Relationships, filters and interpretation
Use model_relationships.json exactly: single-direction dimension-to-fact filters, date→opened active, date→closed inactive, origin→country active and destination inactive. No active fact-to-fact relationship. Mark dim_date as a date table on date_key; turn off auto date/time. Month labels must be sorted chronologically; source date_key covers the calendar.

Pages 1–2 use country_name, authority_name and date_key range slicers at y=38. The date slicer means opened cohorts for query measures, dispatch dates for shipments, and closed dates for Closed Throughput (USERELATIONSHIP). Shipment counts do not filter by authority. Current backlog is the still-open subset of selected opened cohorts, not backlog as of the selected past date. Median includes responded queries only. SLA compliance denominator is responded queries; SLA Breaches includes overdue unresponded queries per warehouse rules.

Page 3 part-master and latest-run DQ visuals must not receive query date/authority/country slicers: no classification history or shipment exposure bridge exists. Scope date slicers to the throughput and query-resolution visuals only through Edit interactions. Current classification gaps cannot be inferred from historical query filters.

Do not load aggregate vw_* queries into the star model or relate them to facts. Keep them connection-only for reconciliation. Power Query type conversion preserves HS codes as text and UTC timestamps as UTC-naive datetime. The only new transformation is response_bucket for the requested response distribution; all existing measures remain unchanged.
