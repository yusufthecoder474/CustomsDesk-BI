# Measured results — SYNTHETIC DATA

- Input: **55,004 physical records** across three systems.
- Loaded: **19,998 shipments**, **29,994 queries**, **5,000 current parts**.
- Latest ETL warehouse transaction/orchestration: **4.061 seconds** in this environment (one observation, not a performance benchmark).
- Tests: **43 passed, 0 failed, 1 skipped**. JUnit evidence: reports/tests.xml.
- SQL response-time average: **52.03 hours**; median **52.00 hours**.
- Backlog: **13,375** unclosed queries; completed-response SLA compliance **61.06%**.
- Regression: compatible adapter PASS; intentionally unsupported status detected as FAIL.

Results are from actual SQLite execution. PostgreSQL integration skipped: no runnable server in the
environment. PostgreSQL SQL source, Compose and CI are supplied but not execution evidence.
Power BI Desktop/M/DAX execution is pending. There is no verified PBIX or dashboard screenshot.
No business savings or real operational outcomes are inferred from generated data.
