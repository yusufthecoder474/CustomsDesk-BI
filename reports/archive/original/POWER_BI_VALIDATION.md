# Power BI validation — PENDING

Power BI Desktop and an M/DAX engine are unavailable here. No PBIX or Power BI screenshots were
fabricated. All 22 measures and existing report materials were retained; response-count zero handling,
boolean parsing and latest-successful-run DQ loading were repaired by source inspection.

Use docs/POWER_BI_WINDOWS_CHECKLIST.md and docs/POWER_BI_SETUP.md. Fill these fields after real execution:

- Desktop version:
- Actual server/port/database or CSV folder:
- Source mode and successful refresh time (check both modes where applicable):
- Star relationships/date roles checked:
- Number of measures actually evaluated and compared (target 22):
- DAX-observation reconciliation output:
- Three-page visual/interaction checks:
- Saved PBIX location and reopen outcome:
- Remaining errors or limitations:

powerbi/MEASURE_EXPECTATIONS.csv contains real SQL targets. DAX_ACTUAL_VALUES_TEMPLATE.csv is deliberately
empty, not execution evidence. The comparator has unit tests; a numeric pass does not prove Desktop execution.
