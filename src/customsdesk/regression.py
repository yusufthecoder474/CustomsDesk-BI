"""Isolated IT-change trials; baseline warehouse is never overwritten."""
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from sqlalchemy import text
from .pipeline import run,kpis
from .warehouse import engine,change_request_log

def compare(before,after,tolerance=1e-9):
    differences={}
    for key in before.keys()|after.keys():
        a,b=before.get(key),after.get(key)
        same=a==b if a is None or b is None else abs(a-b)<=tolerance
        if not same: differences[key]={"before":a,"after":b}
    return differences

def regress(db,source,out="reports"):
    baseline=kpis(db); trials=[]
    for scenario in ["renamed_column_with_adapter","unknown_status_breaking"]:
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); data=root/"source"; shutil.copytree(source,data)
            records=json.loads((data/"queries.json").read_text())
            if scenario=="renamed_column_with_adapter":
                for r in records: r["status_v2"]=r.pop("query_status")
                # Explicit, versioned adapter; do not silently guess changed fields.
                for r in records: r["query_status"]=r.pop("status_v2")
            else:
                for r in records: r["query_status"]="ESCALATED"
            (data/"queries.json").write_text(json.dumps(records))
            trial=engine("sqlite:///"+str(root/"trial.db"))
            result=run(trial,data,root/"reports")
            differences=compare(baseline,result["kpis"])
            rejected=sum(x["rejected"] for x in result["sources"])
            status="PASS" if not differences else "FAIL"
            item=dict(scenario=scenario,status=status,differences=differences,rejected_rows=rejected,trial_database="sqlite",expected=status==("PASS" if scenario=="renamed_column_with_adapter" else "FAIL"))
            trials.append(item)
            with db.begin() as conn: conn.execute(change_request_log.insert().values(change_id=str(uuid.uuid4()),scenario=scenario,status=status,details=json.dumps(item)))
            trial.dispose()
    report=dict(label="SYNTHETIC DATA",baseline=baseline,trials=trials,all_expected=all(t["expected"] for t in trials))
    Path(out).mkdir(parents=True,exist_ok=True); (Path(out)/"regression.json").write_text(json.dumps(report,indent=2))
    return report
