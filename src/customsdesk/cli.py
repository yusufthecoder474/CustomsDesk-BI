import argparse
import json
import os
from pathlib import Path
from .generate import generate
from .settings import resolve,checked_engine,ConfigurationError
from .warehouse import engine,initialize
from .pipeline import run,export,kpis
from .regression import regress
from .analyze import analyze

def main():
    p=argparse.ArgumentParser(description="CustomsDesk BI — SYNTHETIC DATA")
    p.add_argument("command",choices=["generate","init","etl","kpis","export","analyze","regress","demo"])
    p.add_argument("--database-url",default=None)
    p.add_argument("--database",choices=["sqlite","postgresql"],help="Explicit dialect; SQLite never replaces a failed PostgreSQL connection")
    p.add_argument("--env-root",default=".",help="Folder containing local .env")
    p.add_argument("--data",default="data/sample"); p.add_argument("--reports",default="reports")
    p.add_argument("--config",help="Optional generator settings JSON")
    p.add_argument("--exports",default="data/exports"); p.add_argument("--seed",type=int,default=474)
    p.add_argument("--shipments",type=int,default=20000); p.add_argument("--queries",type=int,default=30000); p.add_argument("--parts",type=int,default=5000)
    a=p.parse_args()
    if a.command in {"generate","demo"}:
        result=generate(a.data,a.seed,a.shipments,a.queries,a.parts,config=json.loads(Path(a.config).read_text()) if a.config else None)
        if a.command=="generate": print(json.dumps(result,indent=2)); return
    try:
        settings=resolve(a.env_root,a.database_url,a.database)
        db=checked_engine(settings)
    except ConfigurationError as exc:
        p.exit(2,str(exc)+"\n")
    try:
        if a.command=="init": initialize(db); result={"initialized":True,"database":db.dialect.name}
        elif a.command in {"etl","demo"}: result=run(db,a.data,a.reports)
        elif a.command=="kpis": result=kpis(db)
        elif a.command=="export": export(db,a.exports); result={"exported":a.exports}
        elif a.command=="analyze": result=analyze(db,a.reports)
        elif a.command=="regress": result=regress(db,a.data,a.reports)
        if a.command=="demo": export(db,a.exports); analyze(db,a.reports); regress(db,a.data,a.reports)
        print(json.dumps({"connection":settings.public_summary(),"result":result},indent=2))
    finally: db.dispose()
if __name__=="__main__": main()
