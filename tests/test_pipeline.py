import json
import os
import hashlib
import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from customsdesk.generate import generate,AS_OF
from customsdesk.clean import clean,business_hours,country
from customsdesk.pipeline import run,kpis,export,load_sources
from customsdesk.regression import compare,regress
from customsdesk.warehouse import engine,initialize


def test_generator_deterministic(tmp_path):
    for folder in ['a','b']: generate(tmp_path/folder,seed=12,shipments=30,queries=40,parts=15)
    for name in ['parts.csv','shipments.csv','queries.json','injected_defects.json','manifest.json']:
        assert (tmp_path/'a'/name).read_bytes()==(tmp_path/'b'/name).read_bytes()

def test_generator_seed_changes(tmp_path):
    for i in [1,2]: generate(tmp_path/str(i),seed=i,shipments=30,queries=40,parts=15)
    assert (tmp_path/'1/shipments.csv').read_bytes()!=(tmp_path/'2/shipments.csv').read_bytes()

def test_size_and_ledger(source):
    m=json.loads((source/'manifest.json').read_text())
    assert m['rows']==dict(shipments=51,queries=81,parts=22)
    ledger=json.loads((source/'injected_defects.json').read_text())
    assert len(ledger)>=13
    assert sum(x['defect']!='missing_hs_assumption' for x in ledger)==13
    assert {x['defect'] for x in ledger}>={'missing_hs','conflicting_update','unknown_reference'}

@pytest.mark.parametrize('value,expected',[(' india ','IN'),('se','SE'),('USA','US'),('Germany','DE')])
def test_country_alias(value,expected): assert country(value)==expected

def test_unknown_country():
    with pytest.raises(ValueError,match='unknown_country'): country('XX')

@pytest.mark.parametrize('start,end,hours',[
    ('2026-01-02T16:00Z','2026-01-05T10:00Z',2),
    ('2026-01-03T10:00Z','2026-01-04T18:00Z',0),
    ('2026-01-05T08:00Z','2026-01-05T18:00Z',8),
    ('2026-01-05T10:00Z','2026-01-05T10:00Z',0)])
def test_business_hours(start,end,hours): assert business_hours(pd.Timestamp(start),pd.Timestamp(end))==hours

def test_clean_parts(source):
    parts=load_sources(source)['parts']; accepted,rejected,c=clean('parts',parts,pd.Timestamp(AS_OF))
    byid={r['part_id']:r for r in accepted}
    assert byid['P00000']['code_state']=='INVALID'
    assert byid['P00001']['code_state']=='MISSING'
    assert byid['P00002']['hs_code']=='731815'
    assert byid['P00006']['classification_version']==2
    assert c['duplicates']==1 and c['superseded']==1
    assert c['source_rows']==sum(c[x] for x in ['accepted','rejected','duplicates','superseded'])

def test_missing_columns():
    a,r,c=clean('parts',[{'part_id':'X'}],pd.Timestamp(AS_OF))
    assert not a and 'missing_columns' in r[0]['reason']

@pytest.mark.parametrize('change,reason',[
    ({'opened_at':None},'missing_timestamp'),
    ({'opened_at':'2026-01-01T00:00:00'},'timezone_required'),
    ({'query_status':'ESCALATED'},'invalid_query_status'),
    ({'shipment_id':'missing'},'unknown_shipment_reference'),
    ({'sla_hours':0},'invalid_sla'),
    ({'authority_id':'A99'},'unknown_authority'),
    ({'responded_at':'2025-01-01T00:00Z','query_status':'RESPONDED'},'invalid_timestamp_order')])
def test_query_rejections(source,change,reason):
    raw=load_sources(source)['queries'][8]; raw.update(change)
    a,r,c=clean('queries',[raw],pd.Timestamp(AS_OF),shipments={raw['shipment_id']:{'origin_country':'IN'}} if raw['shipment_id']!='missing' else {})
    assert not a and reason in r[0]['reason']

def test_etl_reconciliation_and_idempotency(db,source,tmp_path):
    first=run(db,source,tmp_path/'reports'); second=run(db,source,tmp_path/'reports')
    assert first['kpis']==second['kpis']
    assert first['checksum']==second['checksum'] and first['run_id']!=second['run_id']
    for x in first['sources']: assert x['source_rows']==sum(x[n] for n in ['accepted','rejected','duplicates','superseded'])
    with db.connect() as c:
        assert c.scalar(text('SELECT COUNT(*) FROM raw_records'))==2*(51+81+22)
        assert c.scalar(text("SELECT COUNT(*) FROM rejected_records WHERE reason='unknown_shipment_reference'"))>0
        assert c.scalar(text('SELECT COUNT(*) FROM etl_run_log'))==2

def test_rollback_retains_previous_snapshot(db,source,tmp_path):
    run(db,source,tmp_path); before=kpis(db)
    with pytest.raises(RuntimeError,match='intentional'): run(db,source,tmp_path,fail_after='delete')
    assert kpis(db)==before
    with db.connect() as c: assert c.scalar(text("SELECT COUNT(*) FROM etl_run_log WHERE status='FAILED'"))==1
    assert len(list(tmp_path.glob('failure-*.json')))==1

def test_constraints(db,source,tmp_path):
    run(db,source,tmp_path)
    with pytest.raises(IntegrityError):
        with db.begin() as c: c.execute(text("UPDATE fact_shipment SET quantity=-1"))
    with pytest.raises(IntegrityError):
        with db.begin() as c: c.execute(text("UPDATE fact_shipment SET part_id='NOPE'"))
    with pytest.raises(IntegrityError):
        with db.begin() as c: c.execute(text("INSERT INTO dim_country VALUES ('IN','Duplicate')"))

def test_exports(db,source,tmp_path):
    run(db,source,tmp_path/'reports'); export(db,tmp_path/'exports')
    assert len(list((tmp_path/'exports').glob('*.csv')))==16
    assert len(pd.read_csv(tmp_path/'exports/fact_shipment.csv'))==kpis(db)['total_shipments']

def test_regression_trials(db,source,tmp_path):
    run(db,source,tmp_path); before=kpis(db); r=regress(db,source,tmp_path)
    assert r['all_expected'] and [x['status'] for x in r['trials']]==['PASS','FAIL']
    assert kpis(db)==before
    with db.connect() as c: assert c.scalar(text('SELECT COUNT(*) FROM change_request_log'))==2

def test_compare():
    assert compare({'a':1.,'b':None},{'a':1.+1e-10,'b':None})=={}
    assert 'b' in compare({'b':None},{'b':0})

@pytest.mark.parametrize('responded',[False,True])
def test_hand_calculated_kpis(db,tmp_path,responded):
    path=tmp_path/'fixture';generate(path,shipments=10,queries=10,parts=10,defects=False)
    sources=load_sources(path)
    parts=sources['parts'][:2]
    parts[0]['hs_code']='';parts[1]['hs_code']='BAD'
    shipments=sources['shipments'][:2]
    for i,s in enumerate(shipments):
        s.update(part_id=parts[i]['part_id'],dispatch_date='2026-01-01T00:00Z',expected_arrival_date='2026-01-08T00:00Z',actual_arrival_date='2026-01-02T00:00Z')
    queries=[]
    # Fri 16 -> Mon 10 = 66 wall hours, 2 working hours; another at 2 wall/working hours.
    for i,(opening,response) in enumerate([('2026-01-02T16:00Z','2026-01-05T10:00Z'),('2026-01-05T10:00Z','2026-01-05T12:00Z'),('2026-01-05T10:00Z',None)]):
        q=dict(sources['queries'][i]); end=response if responded else None
        q.update(query_id=f'Q{i}',shipment_id=shipments[0]['shipment_id'],opened_at=opening,assigned_at=opening,responded_at=end,closed_at=end,query_status='CLOSED' if end else 'ASSIGNED',query_priority='HIGH',sla_hours=24)
        queries.append(q)
    pd.DataFrame(parts).to_csv(path/'parts.csv',index=False);pd.DataFrame(shipments).to_csv(path/'shipments.csv',index=False)
    (path/'queries.json').write_text(json.dumps(queries))
    r=run(db,path,tmp_path,as_of='2026-01-06T10:00Z'); k=r['kpis']
    assert k['total_shipments']==2 and k['total_queries']==3
    assert k['missing_classification_pct']==50 and k['invalid_classification_pct']==50
    if responded:
        assert k['avg_response_hours']==34 and k['median_response_hours']==34
        assert k['avg_business_response_days']==.25
        assert k['sla_compliance_pct']==50 and k['sla_breaches']==1
        assert k['open_queries']==1 and k['high_priority_unresolved']==1 and k['avg_backlog_hours']==24
    else:
        assert k['avg_response_hours'] is None and k['median_response_hours'] is None and k['sla_compliance_pct'] is None
        assert k['open_queries']==3 and k['sla_breaches']==1

def test_postgresql_contract(source,tmp_path):
    url=os.getenv('TEST_POSTGRES_URL')
    if not url: pytest.skip('PostgreSQL unavailable; set TEST_POSTGRES_URL to an EMPTY disposable test database')
    from customsdesk.verification import assert_disposable_test
    assert_disposable_test(url,os.getenv('CUSTOMSDESK_TEST_TOKEN'))
    pg=engine(url)
    try:
        r=run(pg,source,tmp_path/'pg'); second=run(pg,source,tmp_path/'pg')
        assert r['kpis']==second['kpis']
        local=engine('sqlite:///:memory:'); comparison=run(local,source,tmp_path/'sqlite')
        assert compare(r['kpis'],comparison['kpis'])=={}
        before=kpis(pg)
        with pytest.raises(RuntimeError): run(pg,source,tmp_path/'pg',fail_after='delete')
        assert before==kpis(pg)
        for statement in ["UPDATE fact_shipment SET quantity=-1", "UPDATE fact_shipment SET part_id='UNKNOWN'", "INSERT INTO dim_country VALUES ('IN','Duplicate')"]:
            with pytest.raises(IntegrityError):
                with pg.begin() as c: c.execute(text(statement))
        assert before==kpis(pg)
    finally: pg.dispose()


def test_schema_change_fails_with_audit(db,source,tmp_path):
    run(db,source,tmp_path); before=kpis(db)
    records=json.loads((source/'queries.json').read_text())
    for row in records: row['status_v2']=row.pop('query_status')
    (source/'queries.json').write_text(json.dumps(records))
    with pytest.raises(ValueError,match='source_schema_changed'): run(db,source,tmp_path)
    assert before==kpis(db)
    with db.connect() as c: assert c.scalar(text("SELECT COUNT(*) FROM etl_run_log WHERE status='FAILED'"))==1


def test_timezone_equivalence(source):
    raw=load_sources(source)['queries'][8]
    raw.update(opened_at='2026-01-05T15:30:00+05:30',assigned_at='2026-01-05T10:00Z',responded_at='2026-01-05T12:00Z',closed_at=None,query_status='RESPONDED')
    a,_,_=clean('queries',[raw],pd.Timestamp(AS_OF),shipments={raw['shipment_id']:{'origin_country':'IN','part_id':'P0'}})
    assert a[0]['response_hours']==2
    assert a[0]['opened_at']=='2026-01-05T10:00:00+00:00'


def test_responded_unclosed_is_backlog(source):
    raw=load_sources(source)['queries'][8]
    raw.update(opened_at='2026-01-05T10:00Z',assigned_at='2026-01-05T10:00Z',responded_at='2026-01-05T12:00Z',closed_at=None,query_status='RESPONDED')
    a,_,_=clean('queries',[raw],pd.Timestamp('2026-01-06T10:00Z'),shipments={raw['shipment_id']:{'origin_country':'IN','part_id':'P0'}})
    assert a[0]['backlog_hours']==24 and a[0]['response_hours']==2


def test_empty_warehouse_kpis(db):
    initialize(db); k=kpis(db)
    assert k['total_queries']==0 and k['total_shipments']==0
    assert k['sla_compliance_pct'] is None and k['median_response_hours'] is None


def test_calendar_zero_months(db,source,tmp_path):
    run(db,source,tmp_path)
    with db.connect() as c:
        rows=c.execute(text('SELECT * FROM vw_monthly ORDER BY month')).mappings().all()
    assert len(rows)==10 and rows[-1]['month']=='2026-10' and rows[-1]['closed']==0
    assert rows[0]['mom_throughput_pct'] is None


def test_odd_median(db,source,tmp_path):
    run(db,source,tmp_path)
    with db.begin() as c:
        ids=list(c.execute(text('SELECT query_id FROM fact_customs_query LIMIT 3')).scalars())
        c.execute(text('UPDATE fact_customs_query SET response_hours=NULL'))
        for ident,v in zip(ids,[1,4,100]): c.execute(text('UPDATE fact_customs_query SET response_hours=:v WHERE query_id=:id'),{'v':v,'id':ident})
    assert kpis(db)['median_response_hours']==4


def test_same_version_conflict_quarantined(source):
    raw=load_sources(source)['parts'][8]; other=dict(raw,hs_code='123456')
    accepted,rejected,c=clean('parts',[raw,other],pd.Timestamp(AS_OF))
    assert len(accepted)==1 and c['rejected']==1 and rejected[0]['reason']=='conflicting_or_stale_version'


def test_negative_business_duration():
    with pytest.raises(ValueError,match='negative_duration'): business_hours(pd.Timestamp('2026-01-06T10:00Z'),pd.Timestamp('2026-01-05T10:00Z'))


def test_packaged_sql_matches_repository():
    from pathlib import Path
    from customsdesk import warehouse
    assert Path(warehouse.__file__).with_name('views.sql').read_bytes()==Path('sql/views.sql').read_bytes()


def test_corrupt_json_marks_failed(db,source,tmp_path):
    (source/'queries.json').write_text('{broken')
    with pytest.raises(json.JSONDecodeError): run(db,source,tmp_path)
    with db.connect() as c: assert c.scalar(text("SELECT COUNT(*) FROM etl_run_log WHERE status='FAILED'"))==1


def test_hs_leading_zero_preserved(source):
    part=load_sources(source)['parts'][8];part['hs_code']='010121'
    rows,_,_=clean('parts',[part],pd.Timestamp(AS_OF))
    assert rows[0]['hs_code']=='010121' and rows[0]['code_state']=='VALID'


def test_generator_configuration_validates():
    from customsdesk.config import GeneratorConfig
    with pytest.raises(ValueError): GeneratorConfig(status_probabilities=[.5,.5])
    with pytest.raises(ValueError): GeneratorConfig(missing_classification_rate=1.1)


def test_configurable_missing_classifications(tmp_path):
    generate(tmp_path,shipments=10,queries=10,parts=10,defects=False,config={'missing_classification_rate':1.})
    parts=load_sources(tmp_path)['parts']
    assert all(r['hs_code']=='' for r in parts)


def test_missing_source_file_logged(db,source,tmp_path):
    (source/'parts.csv').unlink()
    with pytest.raises(FileNotFoundError): run(db,source,tmp_path)
    with db.connect() as c: assert c.scalar(text("SELECT COUNT(*) FROM etl_run_log WHERE status='FAILED'"))==1
    failure=json.loads(next(tmp_path.glob('failure-*.json')).read_text())
    assert failure['execution_seconds']>=0 and failure['error']
