# GitHub publishing — manual, after review

No repository has been published by this build. No open-source license has been selected.
Review code, outputs, license choice and visibility first. Do not publish local databases, .env,
virtual environments or credentials. Synthetic source/exports and reports may be committed.

From the extracted repository in PowerShell:

```powershell
git init
git add .
git status --short
git commit -m "Build CustomsDesk BI synthetic customs analytics pipeline"
# Choose ONE visibility option yourself after reviewing.
gh repo create yusufthecoder474/CustomsDesk-BI --private --source=. --remote=origin --push
# Use --public instead of --private only if you decide to make it public.
```

If a repo already exists, set origin to its actual URL rather than creating another one. Verify
GitHub Actions results; local test results do not prove hosted CI passed. Add a license only after
you decide the legal permissions you want to grant. README license status intentionally remains undecided.

## Reviewed publishing wrapper

`scripts/publish_github.ps1` defaults to preview with no local Git/GitHub mutation. It was statically
parsed; live GitHub CLI execution was not performed. After reviewing the complete project and choosing
visibility/license policy, the owner can explicitly run it with -Publish and -Visibility private/public.
It refuses an existing destination rather than overwriting it, screens staged local configuration/databases,
and does not add a license. No repository has been created by this work.

Suggested description: Synthetic customs operations ETL, SQL warehouse and Power BI build materials with guarded Windows verification and KPI regression checks.

Suggested topics: python, pandas, etl, postgresql, sql, powerbi, dax, power-query, data-quality, customs, business-intelligence, pytest.
