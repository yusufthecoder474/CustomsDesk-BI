# Interview preparation

Independent student portfolio project. All source records are synthetic. Describe what you can
personally explain and reproduce; mention development assistance honestly if asked.

## 60-second explanation

“CustomsDesk BI brings shipment, customs-query and part-master records into one reporting workflow.
I built three simulated source systems so I could test data problems safely. The Python pipeline
preserves raw records, cleans supported values and quarantines records it cannot trust. It loads a
star-schema warehouse and uses SQL to calculate response times, SLA compliance, backlog and missing
classifications. I kept shipments and queries at separate grains so totals are not inflated.
I also built a regression workflow that detects when a source-system change breaks the reporting.
The package contains Power Query, DAX and instructions for a three-page Power BI report. I verified
the Python and SQL workflow on SQLite here; PostgreSQL and Power BI Desktop still need their separate
execution checks. The project demonstrates the reporting process, not real customs performance.”

## STAR explanation

**Situation:** The project brief describes operational records spread across shipment, query and
part systems. Missing classifications and inconsistent status/timestamp values can make reports unreliable.

**Task:** Build a reproducible integration and reporting workflow with clear KPI meanings and tests.

**Action:** Generate fixed-seed synthetic records, preserve the raw inputs, validate keys and dates,
resolve duplicates explicitly, and load dimensions and facts in a transaction. Define response time
separately from closure backlog. Test a renamed column with an explicit adapter and an unsupported
new query status. Prepare M/DAX and exact report fields for local Power BI assembly.

**Result:** Use the measured input/accepted counts and test outcomes in RESUME_BULLETS.md. Both change
scenarios behaved as expected: compatible adapter preserved KPIs; unsupported state changed KPIs
and was flagged. No business savings or production use were measured.

## Why this stack

Python/Pandas make CSV and JSON inspection and transformation straightforward. NumPy provides a
reproducible generator. SQLAlchemy defines one relational model and transaction boundary. PostgreSQL
is the primary target for relational constraints and analytical SQL. SQLite provides an explicit
local fallback and isolated regression sandboxes; it does not prove PostgreSQL compatibility.
Power BI is the intended stakeholder report, with Power Query handling refresh and DAX handling
interactive measures. Pytest makes expected rules repeatable. Compose and CI describe reproducible
execution on environments that support their services.

## Technical challenges and fixes

- Fact-to-fact joins multiply shipments. Count facts separately and share dimensions in Power BI.
- A responded query can still be unclosed. Use responded_at for response metrics and closed_at for backlog.
- Unanswered queries cannot have a completed response duration. Keep NULL; use cutoff only for ageing/SLA risk.
- Higher part versions are legitimate updates. Validate them before replacing the prior accepted version;
  retain the old source record with its physical-row lineage.
- Source fields/states change. Fail unknown schema changes, quarantine unsupported states, compare snapshots.
- A timezone mismatch was found while generating the date dimension during testing. Generate a consistent
  calendar date range, require aware source timestamps and add equivalent-offset/boundary tests.

## Ten role-focused questions and answers

1. **What business problem does the project address?** It consolidates separate operational records so a
   manager can see response delays, closure backlog and classification exceptions with consistent definitions.
2. **How do you trust the source data?** Preserve raw inputs and checksums, reconcile every physical row,
   validate identifiers/timestamps and keep rejected records with reasons. Validation does not make synthetic
   data representative of real operations.
3. **What is the difference between response time and resolution time?** This project measures opening to
   first recorded response. Closure is separate. It does not model multiple exchanges or final resolution quality.
4. **How do you calculate SLA compliance?** Completed responses within their elapsed-hour SLA divided by
   completed responses. I report unanswered-overdue queries in the breach count, not in the completed-response denominator.
5. **Why use a star schema?** It keeps stable analytical dimensions around facts with a clear grain. It
   supports filters without joining a shipment once for every query and inflating shipment counts or values.
6. **What happens if ETL fails halfway through?** The warehouse transaction rolls back; the previous good
   snapshot remains. The failed-run audit and raw inputs remain for diagnosis. Abrupt interruption can leave a RUNNING log to reconcile.
7. **How would you handle an IT change request?** Agree the business meaning, add an explicit adapter/mapping,
   rerun a baseline fixture and compare both quality and KPI values before accepting the change.
8. **What do Power Query and DAX each do?** M imports and shapes the refreshed data. DAX calculates measures
   in the report's filter context. I supply both, but do not claim engine verification until Desktop refresh succeeds.
9. **What action would you recommend from the report?** Triage high-priority unclosed cases and missing codes;
   inspect case samples behind long authority response times before deciding the cause or allocating resources.
10. **What would you improve for real deployment?** Verify PostgreSQL and Power BI execution, agree a local
    holiday/calendar policy, add incremental updates/history, define source contracts and set governed access
    and retention. Real source integration needs approved access and business validation.
