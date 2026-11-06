"""SQL dashboard targets and model-contract validation; never executes DAX."""
import argparse
import json
import re
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from .warehouse import engine,metadata
from .pipeline import kpis


def response_bucket(hours):
    if hours is None or pd.isna(hours):return "Not responded"
    if hours<0:raise ValueError("Nonnegative response time required")
    if hours<=24:return "01: 0–24h"
    if hours<=48:return "02: >24–48h"
    if hours<=72:return "03: >48–72h"
    return "04: >72h"


def validate_model(root, db):
    root=Path(root)
    definitions=(root/"powerbi/measures.dax").read_text()
    names=re.findall(r"^([^/\n][^\n]*?) =\s*$",definitions,re.M)
    if len(names)!=22 or len(set(names))!=22:raise ValueError("Expected preserved 22 measures")
    for table,column in re.findall(r"(\w+)\[([^]]+)\]",definitions):
        if table not in metadata.tables or column not in metadata.tables[table].c:
            raise ValueError(f"Unknown DAX column {table}[{column}]")
    results=[]
    model=json.loads((root/"powerbi/model_relationships.json").read_text())
    with db.connect() as conn:
        for rel in model["relationships"]:
            one,oc=rel["one"].split(".");many,mc=rel["many"].split(".")
            assert oc in metadata.tables[one].c and mc in metadata.tables[many].c
            assert rel["direction"]=="single"
            duplicate=conn.scalar(text(f"SELECT count(*) FROM (SELECT {oc} FROM {one} GROUP BY {oc} HAVING count(*)>1) x"))
            orphan=conn.scalar(text(f"SELECT count(*) FROM {many} m LEFT JOIN {one} d ON m.{mc}=d.{oc} WHERE m.{mc} IS NOT NULL AND d.{oc} IS NULL"))
            results.append(dict(one=rel["one"],many=rel["many"],active=rel["active"],duplicate_keys=duplicate,orphan_keys=orphan,status="PASS" if duplicate==orphan==0 else "FAIL"))
    assert all(x["status"]=="PASS" for x in results)
    return names,results


def run(root,url):
    root=Path(root);out=root/"reports/enhancement";out.mkdir(parents=True,exist_ok=True)
    db=engine(url)
    try:
        names,relations=validate_model(root,db)
        pd.DataFrame(relations).to_csv(out/"relationship_checks.csv",index=False)
        k=kpis(db)
        with db.connect() as conn:
            scalar=lambda query:conn.scalar(text(query))
            total=scalar("SELECT count(*) FROM dim_part")
            responded=scalar("SELECT count(response_hours) FROM fact_customs_query")
            met=scalar("SELECT count(*) FROM fact_customs_query WHERE response_hours IS NOT NULL AND sla_breach=0")
            missing=scalar("SELECT count(*) FROM dim_part WHERE code_state='MISSING'")
            invalid=scalar("SELECT count(*) FROM dim_part WHERE code_state='INVALID'")
            reviewed=scalar("SELECT count(*) FROM dim_part WHERE review_required=true")
            month=conn.execute(text("SELECT * FROM vw_monthly WHERE month='2026-09'")).mappings().one()
            values=[k["total_shipments"],k["total_queries"],k["open_queries"],k["avg_response_hours"],k["median_response_hours"],k["avg_business_response_days"],responded,met,k["sla_compliance_pct"]/100,k["sla_breaches"],k["avg_backlog_hours"],k["high_priority_unresolved"],total,missing,invalid,missing/total,invalid/total,reviewed,month["closed"],month["prior_closed"],month["mom_throughput_pct"]/100,k["dq_pass_rate_pct"]/100]
            targets=[dict(measure=n,expected_sql_value=v,filter_context="September 2026" if i in [18,19,20] else "Unfiltered",status="SQL target; DAX PENDING") for i,(n,v) in enumerate(zip(names,values))]
            # Additional contexts test KEEPFILTERS, empty cohorts and query-only dimensions.
            for context,predicate in [("Priority LOW","query_priority='LOW'"),("Authority A1","authority_id='A1'"),("Empty query cohort","opened_date='1900-01-01'"),("September opened cohort","opened_month='2026-09'")]:
                for measure,expr in [("Total Queries","count(*)"),("Open Backlog","coalesce(sum(CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END),0)"),("High Priority Unresolved","coalesce(sum(CASE WHEN closed_at IS NULL AND query_priority='HIGH' THEN 1 ELSE 0 END),0)"),("SLA Compliance %","sum(CASE WHEN response_hours IS NOT NULL AND sla_breach=0 THEN 1.0 ELSE 0 END)/nullif(count(response_hours),0)")]:
                    value=scalar(f"SELECT {expr} FROM fact_customs_query WHERE {predicate}")
                    # COALESCE inside Total Queries preserves a zero in empty backlog contexts.
                    targets.append(dict(measure=measure,expected_sql_value=value,filter_context=context,status="SQL target; DAX PENDING"))
            pd.DataFrame(targets).to_csv(out/"DAX_SQL_TARGETS.csv",index=False)
            actual=pd.DataFrame(targets)[["measure","filter_context"]];actual["actual_dax_value"]=""
            actual.to_csv(out/"DAX_ACTUAL_VALUES.csv",index=False)
            original=pd.read_csv(root/"powerbi/MEASURE_EXPECTATIONS.csv")
            for r in targets[:22]:
                old=original[original.measure==r["measure"]].expected_sql_value.iloc[0]
                assert abs(old-r["expected_sql_value"])<1e-8
            for name,query in {
                "executive":"SELECT * FROM vw_kpis",
                "monthly":"SELECT * FROM vw_monthly",
                "backlog":"SELECT * FROM vw_backlog",
                "priority":"SELECT query_priority,count(*) AS queries,sum(sla_breach) AS breaches FROM fact_customs_query GROUP BY query_priority",
                "resolution":"SELECT query_status,count(*) AS queries FROM fact_customs_query GROUP BY query_status",
                "quality":"SELECT * FROM data_quality_results WHERE run_id=(SELECT run_id FROM etl_run_log WHERE status='SUCCESS' ORDER BY finished_at DESC,run_id DESC LIMIT 1)",
            }.items():pd.read_sql(text(query),conn).to_csv(out/(name+".csv"),index=False)
            q=pd.read_sql(text("SELECT query_id,response_hours FROM fact_customs_query"),conn)
            q["response_bucket"]=q.response_hours.map(response_bucket)
            q.groupby("response_bucket").size().rename("queries").to_csv(out/"response_distribution.csv")
        (out/"dashboard_contract.json").write_text(json.dumps(dict(measures_preserved=22,dax_column_references="PASS",relationships_checked=len(relations),sql_kpis_reproduced=len(k),sql_target_contexts=len(targets),power_bi_runtime="PENDING",pbix_created=False),indent=2))
        return targets
    finally:db.dispose()

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--database-url",required=True)
    a=p.parse_args();run(a.root,a.database_url)
