from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import pytest
from sqlalchemy.engine import make_url
from sqlalchemy import text
from customsdesk.settings import resolve,ConfigurationError,Settings,checked_engine
from customsdesk.local_setup import (choose_port,port_available,prepare_env,write_env,Compose,SetupError,command)
from customsdesk.pipeline import normalize_kpis
from customsdesk.verification import assert_disposable_test
from customsdesk.windows import execute

@pytest.fixture
def pg_env():
    return dict(CUSTOMSDESK_DATABASE='postgresql',CUSTOMSDESK_HOST_PORT='5434',POSTGRES_USER='customsdesk',POSTGRES_DB='customsdesk',POSTGRES_PASSWORD='unit-test-only-characters-@:/#%$!')

def test_dotenv_load_and_password_metacharacters(tmp_path,pg_env):
    write_env(tmp_path/'.env',pg_env)
    settings=resolve(tmp_path,environ={})
    assert settings.url.password==pg_env['POSTGRES_PASSWORD'] and settings.url.port==5434
    assert pg_env['POSTGRES_PASSWORD'] not in json.dumps(settings.public_summary())

def test_shell_precedence(tmp_path,pg_env):
    write_env(tmp_path/'.env',pg_env)
    s=resolve(tmp_path,environ={'CUSTOMSDESK_HOST_PORT':'5448','POSTGRES_PASSWORD':'different-test-secret'})
    assert s.url.port==5448 and s.url.password=='different-test-secret'

def test_explicit_url_precedence(tmp_path,pg_env):
    write_env(tmp_path/'.env',pg_env)
    url=resolve(tmp_path,environ={}).url.set(password='explicit-pw').render_as_string(hide_password=False)
    s=resolve(tmp_path,explicit_url=url,environ={'DATABASE_URL':'invalid'})
    assert s.url.password=='explicit-pw'

@pytest.mark.parametrize('url',['not-a-url','postgresql+psycopg://u:p@localhost:bad/db','mysql://u:p@localhost/db'])
def test_malformed_or_unsupported_urls(tmp_path,url):
    with pytest.raises(ConfigurationError): resolve(tmp_path,explicit_url=url,environ={})

@pytest.mark.parametrize('field,value',[('CUSTOMSDESK_HOST_PORT','5432'),('POSTGRES_DB','other'),('POSTGRES_USER','other'),('CUSTOMSDESK_HOST','remote.invalid')])
def test_url_target_guard(tmp_path,pg_env,field,value):
    raw=resolve(tmp_path,environ=pg_env).url.render_as_string(hide_password=False)
    env={**pg_env,field:value}
    with pytest.raises(ConfigurationError): resolve(tmp_path,explicit_url=raw,environ=env)

def test_no_password_echo_on_url_error(tmp_path,pg_env):
    raw='postgresql+psycopg://customsdesk:EXAMPLE_PRIVATE_TEXT@127.0.0.1:5432/customsdesk'
    with pytest.raises(ConfigurationError) as e: resolve(tmp_path,explicit_url=raw,environ=pg_env)
    assert 'EXAMPLE_PRIVATE_TEXT' not in str(e.value)

@pytest.mark.parametrize('timeout',['0','31','abc'])
def test_timeout_validation(tmp_path,pg_env,timeout):
    with pytest.raises(ConfigurationError,match='TIMEOUT'): resolve(tmp_path,environ={**pg_env,'CUSTOMSDESK_CONNECT_TIMEOUT':timeout})

@pytest.mark.parametrize('port',['0','1023','65536','bad'])
def test_port_validation(tmp_path,pg_env,port):
    with pytest.raises(ConfigurationError,match='HOST_PORT'): resolve(tmp_path,environ={**pg_env,'CUSTOMSDESK_HOST_PORT':port})

def test_explicit_sqlite_bypasses_pg_selection(tmp_path,pg_env):
    write_env(tmp_path/'.env',{**pg_env,'DATABASE_URL':'invalid'})
    s=resolve(tmp_path,database='sqlite',environ={})
    assert s.dialect=='sqlite'
    db=checked_engine(s);db.dispose()

def test_database_selector_mismatch(tmp_path,pg_env):
    with pytest.raises(ConfigurationError,match='disagree'): resolve(tmp_path,explicit_url='sqlite:///:memory:',database='postgresql',environ=pg_env)

def test_component_placeholder_rejected(tmp_path,pg_env):
    with pytest.raises(ConfigurationError,match='PASSWORD'): resolve(tmp_path,environ={**pg_env,'POSTGRES_PASSWORD':'GENERATE_LOCALLY'})

def test_connection_timeout_forwarded(monkeypatch,tmp_path,pg_env):
    import customsdesk.warehouse as w
    captured={}
    real=w.create_engine
    def fake(url,**kw): captured.update(kw); return real('sqlite:///:memory:')
    monkeypatch.setattr(w,'create_engine',fake)
    db=w.engine(resolve(tmp_path,environ=pg_env).url,timeout=7)
    assert captured['connect_args']=={'connect_timeout':7} and captured['hide_parameters'] is True
    db.dispose()

def test_decimal_kpis_json_safe():
    value=normalize_kpis({'pct':Decimal('50.25'),'empty':None,'count':4})
    assert value=={'pct':50.25,'empty':None,'count':4}
    assert json.loads(json.dumps(value))==value

def test_port_collision_chooses_free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1];sock.listen()
        assert not port_available(port)
        chosen=choose_port(port)
        assert chosen!=port and port_available(chosen)

def test_own_running_port_reused(): assert choose_port(5434,owned_running_port=5434)==5434

def test_env_preservation_rotation_and_idempotency(tmp_path,monkeypatch):
    monkeypatch.setattr('customsdesk.local_setup.choose_port',lambda *a:5434)
    path=tmp_path/'.env';path.write_text('# keep comment\nOTHER_SETTING=kept\nPOSTGRES_PASSWORD=old-exposed-example\n')
    s,rotated,backup=prepare_env(tmp_path,rotate=True)
    assert rotated and s.url.password!='old-exposed-example' and len(s.url.password)>=32
    assert backup.read_text().startswith('# keep comment') and 'OTHER_SETTING=kept' in path.read_text()
    marker=s.instance_id
    write_env(path,{'CUSTOMSDESK_PASSWORD_ROTATED':'1'})
    second,rotated,_=prepare_env(tmp_path)
    assert not rotated and second.url.password==s.url.password and second.instance_id==marker

def test_env_write_preserves_literal_password(tmp_path):
    value='test@:/#$% characters\\with"quotes'
    write_env(tmp_path/'.env',{'POSTGRES_PASSWORD':value})
    from dotenv import dotenv_values
    assert dotenv_values(tmp_path/'.env',interpolate=False)['POSTGRES_PASSWORD']==value

def test_dry_run_has_no_side_effects(tmp_path,capsys):
    result=execute(tmp_path,dry_run=True)
    assert result['status']=='DRY_RUN' and list(tmp_path.iterdir())==[]
    assert 'no configuration' in capsys.readouterr().out

def test_foreign_container_refused(tmp_path):
    def runner(args,**kw):
        if 'Labels' in ' '.join(args):return json.dumps({'com.docker.compose.service':'db','com.docker.compose.project.working_dir':str(tmp_path/'other')})
        return 'cid'
    with pytest.raises(SetupError,match='ownership'): Compose(tmp_path,runner).assert_owned('cid')

def test_compose_target_and_stale_shell_isolation(tmp_path,monkeypatch):
    captured=[]
    def runner(args,**kw): captured.append((args,kw));return ''
    monkeypatch.setenv('CUSTOMSDESK_HOST_PORT','5432');monkeypatch.setenv('POSTGRES_PASSWORD','not-for-this-project')
    compose=Compose(tmp_path,runner);compose.invoke('up','-d','--no-deps','db')
    args,kw=captured[0]
    assert args[-4:]==['up','-d','--no-deps','db'] and '--env-file' in args
    assert 'POSTGRES_PASSWORD' not in kw['env'] and 'CUSTOMSDESK_HOST_PORT' not in kw['env']

def test_password_sent_to_psql_only_via_stdin(tmp_path,pg_env,monkeypatch):
    settings=resolve(tmp_path,environ=pg_env);settings=Settings(settings.url,'unit-instance')
    captured=[]
    compose=Compose(tmp_path,lambda *a,**k:'')
    responses=iter(['t','unit-instance',''])
    def psql(cid,user,dbname,statement): captured.append(statement);return next(responses)
    monkeypatch.setattr(compose,'psql',psql)
    compose.provision('cid',settings,True)
    assert settings.url.password in captured[-1] and 'ALTER ROLE' in captured[-1]
    # command runner never receives SQL as a command-line argument.
    calls=[]
    monkeypatch.setattr(compose,'assert_owned',lambda cid:None)
    compose.runner=lambda args,**kw:calls.append((args,kw)) or ''
    Compose.psql(compose,'cid','customsdesk','customsdesk',captured[-1])
    assert settings.url.password not in ' '.join(calls[0][0])
    assert settings.url.password in calls[0][1]['input']

def test_instance_mismatch_stops_rotation(tmp_path,pg_env,monkeypatch):
    compose=Compose(tmp_path); calls=[]
    def fake(*args): calls.append(args[-1]);return 't' if len(calls)==1 else 'foreign-instance'
    monkeypatch.setattr(compose,'psql',fake)
    with pytest.raises(SetupError,match='marker differs'): compose.provision('cid',Settings(resolve(tmp_path,environ=pg_env).url,'ours'),True)
    assert not any('ALTER ROLE' in x for x in calls)

def test_subprocess_failure_does_not_leak(monkeypatch):
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:subprocess.CompletedProcess(a,1,'','PASSWORD=private-example'))
    with pytest.raises(SetupError) as exc: command(['docker','exec'],input='private-example')
    assert 'private-example' not in str(exc.value)

@pytest.mark.parametrize('url,token',[('sqlite:///:memory:','x'),('postgresql+psycopg://u:p@localhost/customsdesk','x'),('postgresql+psycopg://u:p@localhost/customsdesk_test_123456abcdef',None)])
def test_disposable_guard_before_any_connection(url,token):
    with pytest.raises(ConfigurationError,match='newly provisioned'): assert_disposable_test(url,token)


def test_postgresql_full_source(tmp_path):
    url=os.getenv('TEST_POSTGRES_URL')
    if not url: pytest.skip('PostgreSQL unavailable; full synthetic-source contract pending')
    assert_disposable_test(url,os.getenv('CUSTOMSDESK_TEST_TOKEN'))
    from customsdesk.pipeline import run
    from customsdesk.warehouse import engine
    from customsdesk.verification import reconcile
    pg=engine(url)
    try:
        source=Path('data/sample')
        result=run(pg,source,tmp_path/'pg-full')
        assert sum(x['source_rows'] for x in result['sources'])==55004
        assert sum(x['accepted'] for x in result['sources'])==54992
        compared=reconcile(pg,source,tmp_path/'reconciliation')
        assert compared['status']=='PASS' and compared['kpis_compared']==13
    finally: pg.dispose()


def test_explicit_url_overrides_dotenv_dialect(tmp_path,pg_env):
    write_env(tmp_path/'.env',pg_env)
    s=resolve(tmp_path,explicit_url='sqlite:///:memory:',environ={})
    assert s.dialect=='sqlite'


def test_powerbi_template_never_claims_pass(tmp_path):
    from customsdesk.powerbi_check import compare_files
    passed,rows=compare_files('powerbi/MEASURE_EXPECTATIONS.csv','powerbi/DAX_ACTUAL_VALUES_TEMPLATE.csv',tmp_path/'compared.csv')
    assert not passed and len(rows)==22 and all(r['status']=='PENDING' for r in rows)


def test_powerbi_actual_comparison_scales_and_blanks(tmp_path):
    from customsdesk.powerbi_check import compare_files
    (tmp_path/'expected.csv').write_text('measure,filter_context,expected_sql_value\nSLA,all,0.5\nMedian,all,\n')
    (tmp_path/'actual.csv').write_text('measure,filter_context,actual_dax_value\nSLA,all,50\nMedian,all,BLANK\n')
    passed,rows=compare_files(tmp_path/'expected.csv',tmp_path/'actual.csv',tmp_path/'result.csv')
    assert not passed and [r['status'] for r in rows]==['FAIL','PASS']


def test_windows_failure_creates_evidence_and_stops(tmp_path,monkeypatch):
    def unavailable(): raise SetupError('Docker engine unavailable')
    monkeypatch.setattr('customsdesk.windows.check_environment',unavailable)
    with pytest.raises(SetupError): execute(tmp_path)
    assert not (tmp_path/'.env').exists()
    evidence=list((tmp_path/'reports/windows-runs').glob('*/verification.json'))
    assert len(evidence)==1 and json.loads(evidence[0].read_text())['status']=='FAIL'


def test_model_spec_columns_exist():
    from customsdesk.warehouse import metadata
    spec=json.loads(Path('powerbi/model_relationships.json').read_text())
    for rel in spec['relationships']:
        for end in ['one','many']:
            table,column=rel[end].split('.')
            assert column in metadata.tables[table].c
        assert rel['direction']=='single'
    assert not any(r['one'].startswith('fact_') for r in spec['relationships'])


def test_same_compose_project_in_foreign_directory_not_recreated(tmp_path):
    calls=[]
    def runner(args,**kw):
        calls.append(args)
        if 'config' in args:return json.dumps({'name':'customsdesk-bi','services':{'db':{'environment':{'POSTGRES_PASSWORD':'fake-sensitive-config'}}}})
        if args[:2]==['docker','ps']:return 'foreign-cid'
        if 'Labels' in ' '.join(args):return json.dumps({'com.docker.compose.service':'db','com.docker.compose.project.working_dir':str(tmp_path/'other')})
        return ''
    with pytest.raises(SetupError,match='ownership'): Compose(tmp_path,runner).start()
    assert not any('up' in args for args in calls)
