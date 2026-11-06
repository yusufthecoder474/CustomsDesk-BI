"""Strict row validation with explicit quarantine and version resolution."""
import json
import re
from datetime import datetime, time, timedelta
import pandas as pd
from pydantic import BaseModel, ConfigDict

COLUMNS={
"parts":"part_id part_description part_category hs_code classification_status classification_version review_date review_required".split(),
"shipments":"shipment_id supplier_id part_id origin_country destination_country dispatch_date expected_arrival_date actual_arrival_date shipment_status declared_value quantity".split(),
"queries":"query_id shipment_id authority_id opened_at assigned_at responded_at closed_at query_priority query_type query_status sla_hours assigned_team response_outcome".split()}
KEYS={"parts":"part_id","shipments":"shipment_id","queries":"query_id"}
class SourceCounts(BaseModel):
    model_config=ConfigDict(strict=True)
    source:str
    source_rows:int
    accepted:int
    rejected:int
    duplicates:int
    superseded:int

def null(v):
    return v is None or str(v).strip() in ("", "nan", "NaT", "None")

def ts(v,required=False):
    if null(v):
        if required: raise ValueError("missing_timestamp")
        return None
    value=pd.Timestamp(v)
    if value.tzinfo is None: raise ValueError("timezone_required")
    return value.tz_convert("UTC")

def business_hours(start,end):
    """Overlap with Mon-Fri 09:00-17:00 UTC; no holiday calendar."""
    if end<start: raise ValueError("negative_duration")
    day=start.normalize(); total=0.0
    while day<=end.normalize():
        if day.weekday()<5:
            lo=max(start,day+pd.Timedelta(hours=9)); hi=min(end,day+pd.Timedelta(hours=17))
            total+=max(0,(hi-lo).total_seconds()/3600)
        day+=pd.Timedelta(days=1)
    return total

def country(v):
    v=str(v).strip().upper()
    v={"INDIA":"IN","SWEDEN":"SE","GERMANY":"DE","USA":"US","CHINA":"CN"}.get(v,v)
    if v not in {"IN","SE","DE","US","CN"}: raise ValueError("unknown_country")
    return v

def clean(source, records, as_of, parts=None, shipments=None):
    accepted=[]; rejects=[]; seen={}; positions={}; duplicates=0; superseded=0
    for index,raw in enumerate(records):
        row=dict(raw); reasons=[]
        try:
            missing=set(COLUMNS[source])-row.keys()
            if missing: raise ValueError("missing_columns:"+",".join(sorted(missing)))
            key=row[KEYS[source]]
            if null(key): raise ValueError("missing_primary_key")
            if key in seen:
                if row==seen[key]:
                    duplicates+=1; raise ValueError("exact_duplicate")
                if source=="parts":
                    version=int(row["classification_version"]); old=int(seen[key]["classification_version"])
                    if version<=old: raise ValueError("conflicting_or_stale_version")
                    # A higher version is validated before replacing the old row.
                else: raise ValueError("conflicting_source_update")
            if source=="parts":
                code=str(row["hs_code"]).strip() if not null(row["hs_code"]) else ""
                code=code.replace(".", "").replace(" ", "")
                valid=bool(re.fullmatch(r"\d{6}(\d{2})?(\d{2})?",code))
                row["hs_code"]=code or None
                row["code_state"]="MISSING" if not code else ("VALID" if valid else "INVALID")
                row["classification_status"]=str(row["classification_status"]).strip().upper()
                if row["classification_status"] not in {"PENDING","CLASSIFIED","REVIEW"}: raise ValueError("invalid_classification_status")
                row["classification_version"]=int(row["classification_version"])
                if row["classification_version"]<1: raise ValueError("invalid_version")
                if null(row["review_date"]): raise ValueError("missing_review_date")
                review=pd.Timestamp(row["review_date"])
                row["review_date"]=review.date().isoformat()
                val=str(row["review_required"]).lower()
                if val not in {"true","false","1","0"}: raise ValueError("invalid_boolean")
                row["review_required"]=val in {"true","1"} or row["code_state"]!="VALID"
            elif source=="shipments":
                if row["part_id"] not in parts: raise ValueError("unknown_part_reference")
                for field in ["origin_country","destination_country"]: row[field]=country(row[field])
                dispatch=ts(row["dispatch_date"],True); expected=ts(row["expected_arrival_date"],True); arrival=ts(row["actual_arrival_date"])
                if expected<dispatch or (arrival is not None and arrival<dispatch): raise ValueError("invalid_date_order")
                if dispatch>as_of or (arrival is not None and arrival>as_of): raise ValueError("future_event")
                row["shipment_status"]=str(row["shipment_status"]).strip().upper()
                if row["shipment_status"] not in {"DISPATCHED","IN_TRANSIT","ARRIVED"}: raise ValueError("invalid_shipment_status")
                if (row["shipment_status"]=="ARRIVED") != (arrival is not None): raise ValueError("arrival_status_mismatch")
                row["declared_value"]=float(row["declared_value"]); row["quantity"]=int(row["quantity"])
                if not (0<=row["declared_value"]<1e12) or row["quantity"]<=0: raise ValueError("invalid_amount")
                row["dispatch_date"]=dispatch.date().isoformat()
                row["expected_arrival_date"]=expected.date().isoformat(); row["actual_arrival_date"]=arrival.date().isoformat() if arrival is not None else None
            else:
                if row["shipment_id"] not in shipments: raise ValueError("unknown_shipment_reference")
                row["query_status"]=str(row["query_status"]).strip().upper()
                row["query_priority"]=str(row["query_priority"]).strip().upper()
                if row["query_status"] not in {"OPEN","ASSIGNED","RESPONDED","CLOSED"}: raise ValueError("invalid_query_status")
                if row["query_priority"] not in {"HIGH","NORMAL","LOW"}: raise ValueError("invalid_priority")
                if row["query_type"] not in {"CLASSIFICATION","VALUATION","DOCUMENTS"}: raise ValueError("invalid_query_type")
                if row["authority_id"] not in {"A1","A2","A3","A4","A5"}: raise ValueError("unknown_authority")
                opened=ts(row["opened_at"],True); assigned=ts(row["assigned_at"]); response=ts(row["responded_at"]); closed=ts(row["closed_at"])
                events=[v for v in [opened,assigned,response,closed] if v is not None]
                if events!=sorted(events): raise ValueError("invalid_timestamp_order")
                if events[-1]>as_of: raise ValueError("future_event")
                status=row["query_status"]
                if (status in {"RESPONDED","CLOSED"}) != (response is not None): raise ValueError("response_status_mismatch")
                if (status=="CLOSED") != (closed is not None): raise ValueError("closed_status_mismatch")
                if status!="OPEN" and assigned is None: raise ValueError("missing_assignment")
                row["sla_hours"]=float(row["sla_hours"])
                if not (0<row["sla_hours"]<=8760): raise ValueError("invalid_sla")
                row["response_hours"]=(response-opened).total_seconds()/3600 if response is not None else None
                row["business_response_hours"]=business_hours(opened,response) if response is not None else None
                row["backlog_hours"]=(as_of-opened).total_seconds()/3600 if closed is None else None
                row["sla_breach"]=int(((response if response is not None else as_of)-opened).total_seconds()/3600>row["sla_hours"])
                row["opened_date"]=opened.date().isoformat(); row["opened_month"]=opened.strftime("%Y-%m")
                row["closed_date"]=closed.date().isoformat() if closed is not None else None
                row["part_id"]=shipments[row["shipment_id"]]["part_id"]
                row["closed_month"]=closed.strftime("%Y-%m") if closed is not None else None
                row["country_code"]=shipments[row["shipment_id"]]["origin_country"]
                row["age_bucket"]=None if closed is not None else ("0-24h" if row["backlog_hours"]<=24 else ("24-72h" if row["backlog_hours"]<=72 else "72h+"))
                for field,value in zip(["opened_at","assigned_at","responded_at","closed_at"],[opened,assigned,response,closed]):
                    row[field]=value.isoformat() if value is not None else None
                if null(row["response_outcome"]): row["response_outcome"]=None
            if key in seen:
                oldrow=next(r for r in accepted if r[KEYS[source]]==key)
                accepted.remove(oldrow); superseded+=1
                rejects.append(dict(source=source,row_number=positions[key],reason="superseded_version",payload=json.dumps(seen[key],default=str)))
            seen[key]=dict(raw); positions[key]=index+1
            accepted.append(row)
        except (ValueError,TypeError,OverflowError) as exc:
            rejects.append(dict(source=source,row_number=index+1,reason=str(exc),payload=json.dumps(raw,default=str)))
    # Superseded versions are excluded from defect rejection count but retained in quarantine.
    counts=SourceCounts(source=source,source_rows=len(records),accepted=len(accepted),rejected=len(rejects)-duplicates-superseded,duplicates=duplicates,superseded=superseded)
    return accepted,rejects,counts.model_dump()
