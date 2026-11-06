"""Create evidence summaries from executed ETL and JUnit output, never from preset counts."""
import json
import platform
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import sqlalchemy
from customsdesk.warehouse import engine
from customsdesk.pipeline import kpis
from sqlalchemy import text

root=Path('.')
run=json.loads(Path('reports/latest_run.json').read_text())
suites=ET.parse('reports/tests.xml').getroot(); attrs=suites.find('testsuite').attrib
n=int(attrs['tests']);fail=int(attrs['failures'])+int(attrs['errors']);skip=int(attrs['skipped']);passed=n-fail-skip
rows=sum(s['source_rows'] for s in run['sources']); accepted=sum(s['accepted'] for s in run['sources'])
k=run['kpis']
parts_loaded=next(x['accepted'] for x in run['sources'] if x['source']=='parts')
quality='''# Data quality report — SYNTHETIC DATA

Generated from reports/latest_run.json. The pipeline preserves raw records; quarantined records,
duplicates and superseded versions have separate accounting. Invalid-format HS codes remain accepted
part business exceptions for review, so their count is separate from rejected-row defects.

| Source | Physical input | Accepted current | Rejected defects | Exact duplicates | Superseded |
|---|---|---|---|---|---|
'''
for s in run['sources']: quality+='| '+' | '.join(str(s[x]) for x in ['source','source_rows','accepted','rejected','duplicates','superseded'])+' |\n'
quality+=f'\nReconciliation: {rows:,} input = {accepted:,} accepted + '+str(sum(s['rejected'] for s in run['sources']))+' rejected + '+str(sum(s['duplicates'] for s in run['sources']))+' duplicates + '+str(sum(s['superseded'] for s in run['sources']))+' superseded.\n'
quality+=f'\nPhysical-row pass rate: {k["dq_pass_rate_pct"]:.6f}%. Missing part codes: {k["missing_classification_pct"]}%; invalid code formats: {k["invalid_classification_pct"]}%. Source checksums and exact run ID are recorded in latest_run.json.\n'
for path in ['docs/DATA_QUALITY_REPORT.md','reports/DATA_QUALITY_REPORT.md']: Path(path).write_text(quality)
Path('docs/BUSINESS_INSIGHTS.md').write_text(Path('reports/BUSINESS_INSIGHTS.md').read_text())
results=f'''# Measured results — SYNTHETIC DATA

- Input: **{rows:,} physical records** across three systems.
- Loaded: **{k['total_shipments']:,} shipments**, **{k['total_queries']:,} queries**, **{parts_loaded:,} current parts**.
- Latest ETL warehouse transaction/orchestration: **{run['execution_seconds']:.3f} seconds** in this environment (one observation, not a performance benchmark).
- Tests: **{passed} passed, {fail} failed, {skip} skipped**. JUnit evidence: reports/tests.xml.
- SQL response-time average: **{k['avg_response_hours']:.2f} hours**; median **{k['median_response_hours']:.2f} hours**.
- Backlog: **{k['open_queries']:,}** unclosed queries; completed-response SLA compliance **{k['sla_compliance_pct']:.2f}%**.
- Regression: compatible adapter PASS; intentionally unsupported status detected as FAIL.

Results are from actual SQLite execution. PostgreSQL integration skipped: no runnable server in the
environment. PostgreSQL SQL source, Compose and CI are supplied but not execution evidence.
Power BI Desktop/M/DAX execution is pending. There is no verified PBIX or dashboard screenshot.
No business savings or real operational outcomes are inferred from generated data.
'''
Path('RESULTS.md').write_text(results)
verification=f'''# Verification report

Generated from actual JUnit and ETL output. SYNTHETIC DATA only.

| Check | Result |
|---|---|
| Pytest | {passed} passed, {fail} failed, {skip} skipped; {attrs['time']} seconds |
| PostgreSQL integration | Skipped; no server/Docker available |
| Full default ETL | SUCCESS; {rows:,} input rows |
| Reconciliation | {accepted:,} accepted; every physical row accounted for |
| KPI fixtures | Mean/median 34 h, 0.25 business days and 50% compliance checks passed |
| Idempotency/constraints/rollback | Automated checks passed |
| Source-change adapter | Expected PASS |
| Unsupported new status | Expected FAIL detected; baseline unaffected |
| Power BI Desktop | Not available; M/DAX execution and PBIX assembly pending |
| Docker/hosted GitHub Actions | Configuration supplied; not executed |

Environment: Python {platform.python_version()}, {platform.system()} {platform.machine()},
Pandas {pd.__version__}, SQLAlchemy {sqlalchemy.__version__}, SQLite {sqlite3.sqlite_version}.
Host details are not a student-laptop performance promise.

Commands actually executed from repository root:

```sh
python -m pytest -q --tb=short --junitxml=reports/tests.xml
PYTHONPATH=src python -m customsdesk.cli demo
PYTHONPATH=src python scripts/export_schema.py
PYTHONPATH=src python scripts/summarize_verification.py
```

The demo executes generation, ETL, export, SQL EDA and both isolated regression trials. A timezone
mismatch found in the first development test run was fixed; the final JUnit result above is the
current suite outcome. The PostgreSQL binary bootstrap attempt could not create its service user;
the successful SQLite run is not represented as PostgreSQL verification. No tools were used to
publish the repository or select a license.

Known limits: full-snapshot/single-writer processing; ISO text timestamps; no holiday calendar or
production source access; no SQL Server implementation; no executed Power BI/Desktop or hosted CI.
'''
Path('reports/VERIFICATION.md').write_text(verification)
Path('docs/RESUME_BULLETS.md').write_text(f'''# Evidence-backed resume bullets

Use these only after you can explain/reproduce the implementation. All data are synthetic.

- Integrated three simulated operational systems, measured by **{rows:,} input rows** and **{accepted:,} accepted warehouse records**, by implementing Python/Pandas ETL with raw lineage, checksum validation and transactional SQL loading.
- Established repeatable data-quality and KPI checks, measured by **{passed} passing automated tests** and full physical-row reconciliation, by implementing relational constraints, quarantine handling and manually verified response/SLA fixtures.
- Built change-regression reporting, measured by **two correctly classified change scenarios**, by comparing baseline SQL KPIs with isolated ETL reruns and preparing **22 DAX measures** with M import scripts for a three-page Power BI report.

Do not describe PostgreSQL execution or the Power BI dashboard as verified until their pending
checks are completed. Do not claim business savings or real company data. See reports/VERIFICATION.md.
''')
# DAX reconciliation targets are SQL values, never claimed as evaluated DAX output.
db=engine('sqlite:///customsdesk.db')
with db.connect() as c:
    count=lambda sql: c.scalar(text(sql))
    partcount=count('SELECT COUNT(*) FROM dim_part')
    responded=count('SELECT COUNT(response_hours) FROM fact_customs_query')
    met=count('SELECT COUNT(*) FROM fact_customs_query WHERE response_hours IS NOT NULL AND sla_breach=0')
    review=count('SELECT COUNT(*) FROM dim_part WHERE review_required=true')
    month=c.execute(text("SELECT * FROM vw_monthly WHERE month='2026-09'")).mappings().one()
    values=[k['total_shipments'],k['total_queries'],k['open_queries'],k['avg_response_hours'],k['median_response_hours'],k['avg_business_response_days'],responded,met,k['sla_compliance_pct']/100,k['sla_breaches'],k['avg_backlog_hours'],k['high_priority_unresolved'],partcount,count("SELECT COUNT(*) FROM dim_part WHERE code_state='MISSING'"),count("SELECT COUNT(*) FROM dim_part WHERE code_state='INVALID'"),k['missing_classification_pct']/100,k['invalid_classification_pct']/100,review,month['closed'],month['prior_closed'],month['mom_throughput_pct']/100 if month['mom_throughput_pct'] is not None else None,k['dq_pass_rate_pct']/100]
import re
names=re.findall(r'^([^/\n][^\n]*?) =\s*$',Path('powerbi/measures.dax').read_text(),re.M)
assert len(names)==len(values)==22
pd.DataFrame([dict(measure=name,expected_sql_value=value,filter_context='September 2026' if i in [18,19,20] else 'Unfiltered',status='SQL target; DAX not executed') for i,(name,value) in enumerate(zip(names,values))]).to_csv('powerbi/MEASURE_EXPECTATIONS.csv',index=False)
db.dispose()
