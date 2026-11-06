# Five-minute recruiter demonstration

0:00–0:40: “This is an independent synthetic-data customs reporting project. It integrates shipment,
query and part-master systems. TariffLens focuses on evidence retrieval; this project focuses on
operational reporting and trustworthy data.”

0:40–1:30: Run `customsdesk demo` or show the saved execution output. Open manifest.json and the
injected defect ledger. Explain fixed seed, source checksums and three distinct schemas.

1:30–2:20: Show latest_run.json and quarantine exports. Explain exact duplicates, a higher part
version, unknown shipment references and normalized country aliases. Show why invalid HS codes
remain as review exceptions rather than disappearing from classification reporting.

2:20–3:10: Show SQL views and KPI dictionary. Explain opened→responded elapsed SLA, separate
closure backlog, unanswered exclusion from averages and single-grain counting.

3:10–4:10: If you built and verified PBIX, refresh and walk the three pages. Otherwise show the
M/DAX sources and visual mapping and state clearly that Desktop verification is pending.

4:10–5:00: Open regression.json. Explain adapter PASS and detected breaking-state FAIL. Show
pytest evidence and the skipped PostgreSQL check. End with the next work: PostgreSQL environment
verification, Windows Power BI refresh and a real approved holiday calendar.
