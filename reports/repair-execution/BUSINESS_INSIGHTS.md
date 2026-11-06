# Business insights — SYNTHETIC DATA

Executed against sqlite. Current warehouse snapshot only; no production or Volvo records.

There are 19,998 accepted shipments and 29,994 accepted queries.
The backlog contains 13,375 queries without a closure, including 2,673 high-priority queries.
Responded-but-unclosed queries remain in backlog. Unanswered queries do not enter response averages.

Mean response time is 52.03376519655693 hours; median is 52.0 hours.
Completed-response SLA compliance is 61.0613186618156 percent.
The overdue count is 16,232; it includes unanswered queries overdue at the fixed cutoff.
A1 has the highest mean response time (52.35 hours).

Missing classifications affect 5.44 percent of accepted part-master rows;
invalid-format codes affect 0.02 percent. Codes are only syntax-checked.

Actions: triage high-priority unresolved records first; review the 72h+ ageing bucket; investigate the
slowest authority with case samples before assigning a cause. Route missing/invalid codes to a human
classification reviewer. Reconcile source defects before relying on the dashboard.

Use monthly_eda.csv for opened versus closed counts and month-on-month throughput. Zero months are
retained. No causal conclusion or financial saving is supported by these synthetic observations.

Limitations: deterministic simulated distributions; one current snapshot; UTC Mon-Fri 09–17 business
hours without holidays; no genuine authority performance comparison. Power BI Desktop is unverified.
