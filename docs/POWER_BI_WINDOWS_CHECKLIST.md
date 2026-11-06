# Power BI Desktop — manual validation still required

1. Finish the Windows workflow. Open its POWER_BI_CONNECTION.json to get the real Server, Database
   and ExportFolder. Choose PostgreSQL or CSV in the existing parameter definitions.
2. Create fxLoad and parameters, then the connection-only scalar query LatestSuccessfulRun. Create
   the table queries including data_quality_results (automatically latest successful run).
3. Follow POWER_BI_SETUP.md and model_relationships.json. Keep all HS codes/identifiers as text,
   date keys as Date, flags as Boolean and time/duration fields typed. No fact-to-fact active link.
4. Add the 22 existing measures. Response denominators exclude unanswered queries. All-breached
   responded cohorts must show 0%, not BLANK. Zero responded queries must show undefined/BLANK.
5. Build the three pages using REPORT_LAYOUT.md and theme.json. Put SYNTHETIC DATA and the cutoff
   on every page. Use origin country for country breakdowns and closure date for throughput.
6. Use MEASURE_EXPECTATIONS.csv as the SQL reference. Fill DAX_ACTUAL_VALUES_TEMPLATE.csv only with
   values actually evaluated in Desktop, keeping filter_context unchanged. September 2026 is used
   for the three monthly targets; other targets are unfiltered. Enter raw percentage fractions
   (for example 0.5, not 50 or 50%) and unrounded decimal values. Use BLANK for an evaluated blank;
   leave an untested value empty. The comparator requires numerical agreement within 1e-8.
7. Run this command using the project virtual-environment Python after saving your observed CSV:

```bat
.venv\Scripts\python.exe -m customsdesk.powerbi_check --actual powerbi\DAX_ACTUAL_VALUES_TEMPLATE.csv --out reports\POWER_BI_RECONCILIATION.csv
```

An empty template returns PENDING/failure, never a fabricated pass. A successful numeric comparison
only proves the supplied observations match targets; it does not by itself verify page layout,
connector refresh or PBIX reopening. Record version, actual data source, refresh time, filters,
measure checks, screenshots if desired, and the saved/reopened PBIX in POWER_BI_VALIDATION.md.
8. Test both CSV and PostgreSQL refresh separately, leading-zero codes, NULL responses, date slicing,
   latest-run DQ and country/authority interactions. Save a genuine CustomsDesk-BI.pbix and reopen it.

Do not describe this as an executed Power BI dashboard until those Desktop checks are completed.
