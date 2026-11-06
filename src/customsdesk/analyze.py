"""EDA and manager narrative derived only from executed SQL."""
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from .pipeline import kpis

def analyze(db,out="reports"):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); k=kpis(db)
    with db.connect() as conn:
        auth=pd.read_sql(text("SELECT * FROM vw_authority ORDER BY avg_response_hours DESC"),conn)
        months=pd.read_sql(text("SELECT * FROM vw_monthly ORDER BY month"),conn)
        quality=pd.read_sql(text("SELECT source,reason,COUNT(*) AS rows FROM rejected_records GROUP BY source,reason ORDER BY rows DESC"),conn)
        dist=pd.read_sql(text("SELECT response_hours,business_response_hours,backlog_hours FROM fact_customs_query"),conn).describe()
    for name,frame in [("authority_eda",auth),("monthly_eda",months),("quality_eda",quality),("duration_summary",dist)]: frame.to_csv(out/f"{name}.csv",index=name=="duration_summary")
    slow="No completed responses" if auth.empty or pd.isna(auth.iloc[0].avg_response_hours) else f"{auth.iloc[0].authority_id} has the highest mean response time ({auth.iloc[0].avg_response_hours:.2f} hours)."
    narrative=f'''# Business insights — SYNTHETIC DATA

Executed against {db.dialect.name}. Current warehouse snapshot only; no production or Volvo records.

There are {k['total_shipments']:,} accepted shipments and {k['total_queries']:,} accepted queries.
The backlog contains {k['open_queries']:,} queries without a closure, including {k['high_priority_unresolved']:,} high-priority queries.
Responded-but-unclosed queries remain in backlog. Unanswered queries do not enter response averages.

Mean response time is {k['avg_response_hours']} hours; median is {k['median_response_hours']} hours.
Completed-response SLA compliance is {k['sla_compliance_pct']} percent.
The overdue count is {k['sla_breaches']:,}; it includes unanswered queries overdue at the fixed cutoff.
{slow}

Missing classifications affect {k['missing_classification_pct']} percent of accepted part-master rows;
invalid-format codes affect {k['invalid_classification_pct']} percent. Codes are only syntax-checked.

Actions: triage high-priority unresolved records first; review the 72h+ ageing bucket; investigate the
slowest authority with case samples before assigning a cause. Route missing/invalid codes to a human
classification reviewer. Reconcile source defects before relying on the dashboard.

Use monthly_eda.csv for opened versus closed counts and month-on-month throughput. Zero months are
retained. No causal conclusion or financial saving is supported by these synthetic observations.

Limitations: deterministic simulated distributions; one current snapshot; UTC Mon-Fri 09–17 business
hours without holidays; no genuine authority performance comparison. Power BI Desktop is unverified.
'''
    (out/"BUSINESS_INSIGHTS.md").write_text(narrative)
    return k
