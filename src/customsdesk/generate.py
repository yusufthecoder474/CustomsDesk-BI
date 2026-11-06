"""Three simulated systems; fixed-seed assumptions, never genuine business data."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

AS_OF = "2026-10-01T00:00:00Z"
from .config import GeneratorConfig

COUNTRIES = ["IN", "SE", "DE", "US", "CN"]

def generate(path, seed=474, shipments=20000, queries=30000, parts=5000, defects=True, config=None):
    if min(shipments, queries, parts) < 10:
        raise ValueError("Each system requires at least 10 rows")
    settings=GeneratorConfig.model_validate(config or {})
    out = Path(path); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    def stamp(value):
        return pd.Timestamp(value).isoformat().replace("+00:00", "Z")
    p = []
    categories = ["Fasteners", "Seals", "Bearings", "Sensors", "Housings"]
    for i in range(parts):
        missing = rng.random() < settings.missing_classification_rate
        p.append(dict(part_id=f"P{i:05}", part_description=f"Synthetic {categories[i%5]} {i}",
            part_category=categories[i%5], hs_code="" if missing else f"{[731815,401693,848210,903180,848390][i%5]}",
            classification_status="PENDING" if missing else "CLASSIFIED", classification_version=1,
            review_date="2026-01-01", review_required=bool(missing or rng.random()<settings.review_rate)))
    s=[]
    for i in range(shipments):
        dispatch=pd.Timestamp("2026-01-01",tz="UTC")+pd.Timedelta(days=int(rng.integers(0,260)))
        expected=dispatch+pd.Timedelta(days=7)
        arrival=expected+pd.Timedelta(days=int(rng.integers(-2,6)))
        s.append(dict(shipment_id=f"S{i:06}", supplier_id=f"SUP{int(rng.integers(1,101)):03}",
            part_id=f"P{int(rng.integers(parts)):05}", origin_country=str(rng.choice(COUNTRIES)),
            destination_country="IN", dispatch_date=stamp(dispatch), expected_arrival_date=stamp(expected),
            actual_arrival_date=stamp(arrival), shipment_status="ARRIVED",
            declared_value=round(float(rng.uniform(100,50000)),2), quantity=int(rng.integers(1,200))))
    q=[]
    for i in range(queries):
        ship=s[int(rng.integers(shipments))]
        opened=pd.Timestamp(ship["dispatch_date"])+pd.Timedelta(hours=int(rng.integers(0,48)))
        assigned=opened+pd.Timedelta(hours=int(rng.integers(0,8)))
        responded=assigned+pd.Timedelta(hours=int(rng.integers(1,settings.max_response_hours+1)))
        closed=responded+pd.Timedelta(hours=int(rng.integers(0,24)))
        status=str(rng.choice(["OPEN","ASSIGNED","RESPONDED","CLOSED"],p=settings.status_probabilities))
        priority=str(rng.choice(["HIGH","NORMAL","LOW"],p=settings.priority_probabilities))
        q.append(dict(query_id=f"Q{i:06}",shipment_id=ship["shipment_id"],authority_id=f"A{int(rng.integers(1,6))}",
            opened_at=stamp(opened),assigned_at=stamp(assigned) if status!="OPEN" else None,
            responded_at=stamp(responded) if status in ["RESPONDED","CLOSED"] else None,
            closed_at=stamp(closed) if status=="CLOSED" else None,
            query_priority=priority,query_type=str(rng.choice(["CLASSIFICATION","VALUATION","DOCUMENTS"])),
            query_status=status,sla_hours=24 if priority=="HIGH" else 72,
            assigned_team="Trade Operations",response_outcome="INFORMATION_PROVIDED" if status in ["RESPONDED","CLOSED"] else None))
    ledger=[dict(source="parts",row_number=i+1,field="hs_code",before=str([731815,401693,848210,903180,848390][i%5]),after="",defect="missing_hs_assumption") for i,record in enumerate(p) if not record["hs_code"]]
    def change(source, records, row, field, value, issue):
        before=records[row][field]; records[row][field]=value
        ledger.append(dict(source=source,row_number=row+1,field=field,before=before,after=value,defect=issue))
    if defects:
        change("parts",p,0,"hs_code","AB123!","invalid_hs")
        change("parts",p,1,"hs_code","","missing_hs")
        change("parts",p,2,"hs_code","7318.15","formatted_hs")
        change("shipments",s,0,"dispatch_date","not-a-date","invalid_date")
        change("shipments",s,1,"shipment_status","TELEPORTED","invalid_status")
        change("shipments",s,2,"origin_country"," india ","country_alias")
        change("queries",q,0,"shipment_id","UNKNOWN","unknown_reference")
        change("queries",q,1,"opened_at",None,"missing_timestamp")
        change("queries",q,2,"query_status","BANANA","invalid_status")
        for source,records,key in [("parts",p,"part_id"),("shipments",s,"shipment_id"),("queries",q,"query_id")]:
            records.append(dict(records[5]))
            ledger.append(dict(source=source,row_number=len(records),field=key,defect="exact_duplicate",before=None,after=records[5][key]))
        conflict=dict(p[6]); conflict["classification_version"]=2; conflict["hs_code"]="848210"; p.append(conflict)
        ledger.append(dict(source="parts",row_number=len(p),field="part_id",defect="conflicting_update",before=p[6],after=conflict))
    pd.DataFrame(s).to_csv(out/"shipments.csv",index=False)
    pd.DataFrame(p).to_csv(out/"parts.csv",index=False)
    (out/"queries.json").write_text(json.dumps(q,indent=2),encoding="utf-8")
    (out/"injected_defects.json").write_text(json.dumps(ledger,indent=2),encoding="utf-8")
    manifest=dict(label="SYNTHETIC DATA",seed=seed,as_of=AS_OF,rows=dict(shipments=len(s),queries=len(q),parts=len(p)),
        config=settings.model_dump(),assumptions="Uniform values, five countries/authorities; independent query types; configurable artificial status mix. No observed trade distributions.")
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest
