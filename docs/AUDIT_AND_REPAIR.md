# Existing-project audit and repair

Input inspected: CustomsDesk-BI(1).zip, matching the previously delivered 104-file release.
The only new attachment was the repair specification containing Windows error descriptions; no
separate Windows log files, local .env or live Windows session were available. No claim is made
that this environment inspected D:\Downloads or the user's running Docker containers.

## Preserved working implementation

- Three fixed-seed source systems and all 55,004 physical source records.
- Original cleaning, quarantine, fact/dimension schema, SQL views, business-calendar rules and EDA.
- Raw lineage, checksums, version handling, transaction rollback and idempotent facts.
- All 43 originally passing tests and historical JUnit/run/evaluation reports.
- All 22 DAX measures, M table sources, theme, three-page layout and SQL KPI targets.
- License remains undecided; nothing was published to GitHub.

## Findings and repairs

| Finding | Consequence | Repair |
|---|---|---|
| Compose bound 5432 unconditionally | Port allocation failed; CLI could reach an unrelated server | Configurable loopback port default 5434; occupied-port detection and owned-service reuse |
| CLI ignored .env | Shell, Compose and Python could use different credentials/ports | python-dotenv with interpolation disabled; explicit precedence and URL.create |
| No target/instance identity check | Wrong local PostgreSQL could receive warehouse writes | Host/port/user/db agreement and per-install database marker checked before CLI writes |
| Raw URL/no timeout configuration | Fragile password handling and long failures | Component URL construction, 1–30 second timeout, sanitized connection errors |
| PostgreSQL percentage results can be Decimal | JSON KPI snapshots could fail | Explicit Decimal normalization tested independently of PostgreSQL |
| Integration test trusted arbitrary TEST_POSTGRES_URL | Existing warehouse could be replaced by tests | Random newly created test database, name guard and matching token required before replacement |
| No end-to-end Windows workflow | Manual command/terminal inconsistencies | CMD entry point plus PowerShell wrappers around testable Python orchestration |
| Existing PostgreSQL volumes retain initial password | Editing POSTGRES_PASSWORD alone does not rotate it | Owned-container local administrative connection performs an explicit role password rotation |
| DAX SLA numerator could be BLANK when no response met SLA | Report might show blank rather than 0% for an all-breached responded cohort | COALESCE response/met-response counts; Desktop execution still pending |
| M boolean conversion silently treated unknown text as false | Bad flags could be hidden | Fail invalid boolean strings; keep NULL semantics |
| DQ query loaded multiple historical runs | Matrix could double-count repeated imports | LatestSuccessfulRun scalar and latest-run DQ query |
| Windows, Power BI, Docker and hosted CI unavailable here | No legitimate runtime proof for those components | Separate pending reports, exact local workflow, real SQL targets and manual checklist |

All seven PowerShell scripts were parsed with a PowerShell tree-sitter grammar on Linux. This is
syntax evidence only. Real Windows PowerShell, Docker Compose and Power BI execution remain pending.
The Python port/configuration/ownership/credential/test-guard logic was exercised by automated tests.
