# KPI dictionary

All records are synthetic. Default cutoff **2026-10-01 00:00:00 UTC** comes from manifest.json.
Timestamps must have offsets and are converted to UTC; naive timestamps are rejected. Durations
are fractional hours. SLA starts at opened_at and ends at responded_at or at cutoff if unanswered.
Exactly at the SLA threshold is compliant; strictly greater is a breach. Closure is a separate event.
Working time: Monday–Friday 09:00–17:00 UTC, no holidays or local calendars; one working day = 8 hours.
This is a configurable code assumption, not an authority service commitment.

| KPI | Formula / numerator | Denominator | Grain / date basis | Exclusions |
|---|---|---|---|---|
| Total shipments | COUNT fact_shipment | none | Shipment; dispatch date | Quarantined and duplicate shipments |
| Total customs queries | COUNT fact_customs_query | none | Query; opened date | Quarantined and duplicate queries |
| Open customs queries | COUNT where closed_at NULL | none | Query; opened cohort, cutoff backlog | Closed queries; responded-unclosed retained |
| Average response lead time | SUM(response_hours) | Responded query count | Query; opened cohort | Unanswered queries |
| Median response lead time | Middle response_hours, mean of two for even N | Responded query set | Query; opened cohort | Unanswered; SQL window ranks |
| Business-day response time | AVG(business_response_hours)/8 | Responded query count inside average | Query; opened cohort | Unanswered; weekends/off-hours removed |
| SLA compliance % | Responded and response_hours <= sla_hours × 100 | Responded queries | Query; opened cohort | Unanswered excluded from denominator |
| SLA breach count | SUM sla_breach | none | Query; opened cohort, unanswered age at cutoff | Unanswered not yet overdue |
| Backlog ageing | cutoff - opened_at; average or buckets <=24h, >24–72h, >72h | Unclosed count for average | Query; snapshot cutoff | Closed queries |
| High-priority unresolved | HIGH and closed_at NULL count | none | Query; snapshot cutoff | Non-high or closed |
| Queries by authority | GROUP BY authority_id COUNT | none | Query; opened cohort | Quarantined records |
| Queries by country | GROUP BY shipment-origin country COUNT | none | Query; opened cohort | Country does not mean authority geography |
| Missing classification % | code_state=MISSING parts ×100 | All accepted current parts | Current part master; no query date slicing | Duplicate/superseded/rejected parts |
| Invalid classification % | code_state=INVALID parts ×100 | All accepted current parts | Current part master | Missing codes separated; syntax only |
| Monthly throughput | COUNT closed queries by closed_month | none | Query; closure calendar month | Unclosed queries |
| Month-over-month change | (current closed - prior closed) ×100 | Prior calendar-month closures | Query; closure month with zero-filled calendar | First or zero prior month returns NULL |
| DQ pass rate | Accepted current rows ×100 | Physical rows across three sources for latest successful run | Run/source, processing basis | No country/date slicing; duplicate/superseded rows lower rate |

SQL percentages use 0–100. DAX percentages are fractions formatted as percent. SQL SUM/AVG can return
NULL on empty sets; do not replace undefined average/compliance values with zero. Cards should show
“No responses” or blank where appropriate. Currency is synthetic USD with no FX conversion.

Power BI dim_date active relation to query opened_date defines an opened cohort. Closed Throughput
uses inactive closed_date via USERELATIONSHIP; it answers closure-period questions. SQL monthly
view uses both opened and closed counts with separate date bases. Do not label opened-cohort SLA
breaches as “breaches occurring in month”; breach occurrence dates are not modeled.

Tests include a manually verifiable Fri 16:00 → Mon 10:00 response: 66 elapsed hours, 2 working
hours, and a 2-hour response. Their mean and median = 34 hours, business-day mean = 0.25, completed
response compliance = 50% for a 24-hour SLA. Unanswered-at-exact-SLA does not breach.
