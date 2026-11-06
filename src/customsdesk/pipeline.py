"""Full-snapshot ETL: audited extraction, atomic warehouse replacement, exact reconciliation."""
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from . import warehouse as w
from .clean import clean,COLUMNS

def now(): return datetime.now(timezone.utc).isoformat()
def load_sources(path):
    path=Path(path)
    return {"parts":pd.read_csv(path/"parts.csv",dtype=str,keep_default_na=False).to_dict("records"),
            "shipments":pd.read_csv(path/"shipments.csv",dtype=str,keep_default_na=False).to_dict("records"),
            "queries":json.loads((path/"queries.json").read_text())}

def insert(conn,table,rows):
    if rows:
        names={c.name for c in table.columns}
        for start in range(0,len(rows),1000):
            conn.execute(table.insert(),[{k:v for k,v in r.items() if k in names} for r in rows[start:start+1000]])

def normalize_kpis(row):
    from decimal import Decimal
    return {k:float(v) if isinstance(v,Decimal) else v for k,v in dict(row).items()}

def kpis(db):
    with db.connect() as conn: return normalize_kpis(conn.execute(text("SELECT * FROM vw_kpis")).mappings().one())

def run(db,path,report_dir="reports",as_of=None,fail_after=None):
    w.initialize(db); rid=str(uuid.uuid4()); started=now(); timer=time.perf_counter(); path=Path(path)
    cutoff=None; checksum=None
    with db.begin() as conn:
        conn.execute(w.etl_run_log.insert().values(run_id=rid,status="RUNNING",started_at=started))
    try:
        manifest=json.loads((path/"manifest.json").read_text())
        cutoff=pd.Timestamp(as_of or manifest["as_of"])
        if cutoff.tzinfo is None: raise ValueError("as_of requires timezone")
        cutoff=cutoff.tz_convert("UTC")
        checksum=hashlib.sha256(b"".join((path/f).read_bytes() for f in ["parts.csv","shipments.csv","queries.json","manifest.json"])).hexdigest()
        with db.begin() as conn:
            conn.execute(w.etl_run_log.update().where(w.etl_run_log.c.run_id==rid).values(checksum=checksum,as_of=cutoff.isoformat()))
        sources=load_sources(path)
        # Preserve input independently of the warehouse transaction, including rejected rows.
        with db.begin() as conn:
            for source,rows in sources.items():
                insert(conn,w.raw_records,[dict(run_id=rid,source=source,row_number=i+1,payload=json.dumps(r,default=str)) for i,r in enumerate(rows)])
        cleaned={}; all_rejects=[]; counts=[]
        for source in ["parts","shipments","queries"]:
            # Empty sources still require an intact source schema.
            if not sources[source]: raise ValueError("empty_source:"+source)
            missing=set(COLUMNS[source])-set(sources[source][0])
            if missing: raise ValueError("source_schema_changed:"+source+":"+",".join(sorted(missing)))
            accepted,rejected,metrics=clean(source,sources[source],cutoff,
                parts={r["part_id"] for r in cleaned.get("parts",[])},
                shipments={r["shipment_id"]:r for r in cleaned.get("shipments",[])})
            metrics["source_checksum"]=hashlib.sha256((path/{"parts":"parts.csv","shipments":"shipments.csv","queries":"queries.json"}[source]).read_bytes()).hexdigest()
            cleaned[source]=accepted; all_rejects.extend(rejected); counts.append(metrics)
        with db.begin() as conn:
            insert(conn,w.rejected_records,[dict(run_id=rid,**r) for r in all_rejects])
            insert(conn,w.data_quality_results,[dict(run_id=rid,**r) for r in counts])
            for tbl in [w.fact_customs_query,w.fact_shipment,w.dim_part,w.dim_date,w.dim_country,w.dim_authority,w.dim_query_type]: conn.execute(tbl.delete())
            if fail_after=="delete": raise RuntimeError("intentional_transaction_failure")
            dates=pd.date_range("2026-01-01",cutoff.date(),freq="D")
            # Date range follows source event dates too, rather than assuming generator dates.
            source_dates=[r["dispatch_date"] for r in cleaned["shipments"]]+[r["opened_date"] for r in cleaned["queries"]]
            if source_dates: dates=pd.date_range(min("2026-01-01",min(source_dates)),cutoff.date(),freq="D")
            insert(conn,w.dim_date,[dict(date_key=d.date().isoformat(),year=d.year,month=d.month,is_weekday=d.weekday()<5) for d in dates])
            insert(conn,w.dim_country,[dict(country_code=k,country_name=v) for k,v in {"IN":"India","SE":"Sweden","DE":"Germany","US":"United States","CN":"China"}.items()])
            insert(conn,w.dim_authority,[dict(authority_id=f"A{i}",authority_name=f"Synthetic Authority {i}") for i in range(1,6)])
            insert(conn,w.dim_query_type,[dict(query_type=v) for v in ["CLASSIFICATION","VALUATION","DOCUMENTS"]])
            for source,tbl in [("parts",w.dim_part),("shipments",w.fact_shipment),("queries",w.fact_customs_query)]: insert(conn,tbl,cleaned[source])
            elapsed=time.perf_counter()-timer
            conn.execute(w.etl_run_log.update().where(w.etl_run_log.c.run_id==rid).values(status="SUCCESS",finished_at=now(),execution_seconds=elapsed))
            snapshot=normalize_kpis(conn.execute(text("SELECT * FROM vw_kpis")).mappings().one())
            conn.execute(w.kpi_snapshot.insert().values(snapshot_id=str(uuid.uuid4()),run_id=rid,label="ETL",payload=json.dumps(snapshot)))
    except Exception as exc:
        elapsed=time.perf_counter()-timer
        with db.begin() as conn:
            conn.execute(w.etl_run_log.update().where(w.etl_run_log.c.run_id==rid).values(status="FAILED",finished_at=now(),execution_seconds=elapsed,error=str(exc)))
        out=Path(report_dir); out.mkdir(parents=True,exist_ok=True)
        (out/f"failure-{rid}.json").write_text(json.dumps(dict(run_id=rid,status="FAILED",error=str(exc),checksum=checksum,execution_seconds=elapsed,as_of=cutoff.isoformat() if cutoff is not None else None,processing_timestamp=started,sources=locals().get("counts",[])),indent=2))
        raise
    report=dict(label="SYNTHETIC DATA",database=db.dialect.name,run_id=rid,status="SUCCESS",checksum=checksum,as_of=cutoff.isoformat(),processing_timestamp=started,execution_seconds=elapsed,sources=counts,kpis=snapshot)
    out=Path(report_dir); out.mkdir(parents=True,exist_ok=True)
    (out/f"run-{rid}.json").write_text(json.dumps(report,indent=2))
    (out/"latest_run.json").write_text(json.dumps(report,indent=2))
    return report

def export(db,path="data/exports"):
    out=Path(path); out.mkdir(parents=True,exist_ok=True)
    names=["dim_date","dim_country","dim_part","dim_authority","dim_query_type","fact_shipment","fact_customs_query","data_quality_results","etl_run_log","rejected_records","vw_kpis","vw_monthly","vw_authority","vw_country","vw_backlog","vw_query_detail"]
    with db.connect() as conn:
        for name in names: pd.read_sql(text(f"SELECT * FROM {name}"),conn).to_csv(out/f"{name}.csv",index=False)
