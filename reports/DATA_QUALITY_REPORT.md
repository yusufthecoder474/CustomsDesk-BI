# Data quality report — SYNTHETIC DATA

Generated from reports/latest_run.json. The pipeline preserves raw records; quarantined records,
duplicates and superseded versions have separate accounting. Invalid-format HS codes remain accepted
part business exceptions for review, so their count is separate from rejected-row defects.

| Source | Physical input | Accepted current | Rejected defects | Exact duplicates | Superseded |
|---|---|---|---|---|---|
| parts | 5002 | 5000 | 0 | 1 | 1 |
| shipments | 20001 | 19998 | 2 | 1 | 0 |
| queries | 30001 | 29994 | 6 | 1 | 0 |

Reconciliation: 55,004 input = 54,992 accepted + 8 rejected + 3 duplicates + 1 superseded.

Physical-row pass rate: 99.978183%. Missing part codes: 5.44%; invalid code formats: 0.02%. Source checksums and exact run ID are recorded in latest_run.json.
