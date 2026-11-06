"""Disposable PostgreSQL test provisioning and cross-database evidence."""
import csv
import json
import os
import re
import secrets
import time
import uuid
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from psycopg import sql
from .warehouse import engine
from .pipeline import run,kpis
from .regression import compare
from .settings import ConfigurationError

TEST_PATTERN=r'customsdesk_test_[a-f0-9]{12}'

def create_test_database(settings):
    """CREATE only a new random database; never reuse/drop any existing database."""
    name='customsdesk_test_'+uuid.uuid4().hex[:12]; token=secrets.token_hex(24)
    admin=engine(settings.url.set(database='postgres'),timeout=settings.connect_timeout)
    try:
        with admin.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
            c.exec_driver_sql(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)).as_string())
    finally: admin.dispose()
    url=settings.url.set(database=name)
    db=engine(url,timeout=settings.connect_timeout)
    try:
        with db.begin() as c:
            c.execute(text('CREATE TABLE public.customsdesk_test_guard (token text NOT NULL)'))
            c.execute(text('INSERT INTO public.customsdesk_test_guard VALUES (:token)'),{'token':token})
    finally: db.dispose()
    return url,token


def assert_disposable_test(url,token):
    from sqlalchemy.engine import make_url
    target=make_url(url)
    if target.get_backend_name()!='postgresql' or not re.fullmatch(TEST_PATTERN,target.database or '') or not token:
        raise ConfigurationError('Integration tests require a newly provisioned customsdesk_test_<random> database and matching guard token.')
    db=engine(target)
    try:
        with db.connect() as c:
            actual=c.scalar(text('SELECT current_database()'))
            if actual!=target.database: raise ConfigurationError('Disposable database identity mismatch.')
            guard=c.execute(text('SELECT token FROM public.customsdesk_test_guard')).scalars().all()
            if guard!=[token]: raise ConfigurationError('Disposable database guard token mismatch.')
    except ConfigurationError: raise
    except Exception: raise ConfigurationError('Disposable test guard could not be verified. No test data was replaced.') from None
    finally: db.dispose()


def reconcile(pg,source,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    local=engine('sqlite:///'+str((out/'reconciliation.sqlite.db').resolve()))
    try:
        sqlite_run=run(local,source,out/'sqlite-reference')
        before=kpis(pg); differences=compare(before,sqlite_run['kpis'],tolerance=1e-8)
        with (out/'DATABASE_RECONCILIATION.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['kpi','postgresql','sqlite','absolute_tolerance','status']);writer.writeheader()
            for key,value in before.items(): writer.writerow(dict(kpi=key,postgresql=value,sqlite=sqlite_run['kpis'][key],absolute_tolerance=1e-8,status='FAIL' if key in differences else 'PASS'))
        if differences: raise RuntimeError('PostgreSQL/SQLite KPI reconciliation failed; see comparison CSV.')
        measurements=[]
        for name,query in [('kpis','SELECT * FROM vw_kpis'),('monthly','SELECT * FROM vw_monthly'),('authority','SELECT * FROM vw_authority')]:
            with pg.connect() as c:
                start=time.perf_counter(); rows=c.execute(text(query)).all(); elapsed=time.perf_counter()-start
            measurements.append(dict(query=name,rows=len(rows),seconds=elapsed))
        (out/'QUERY_TIMINGS.json').write_text(json.dumps(measurements,indent=2))
        return dict(status='PASS',kpis_compared=len(before),tolerance=1e-8,timings=measurements)
    finally: local.dispose()


def ci_main():
    """CI uses an ephemeral service; its connection URL is environment-only, never printed."""
    from .settings import Settings
    from sqlalchemy.engine import make_url
    from .local_setup import command
    url=os.environ.get('CUSTOMSDESK_CI_ADMIN_URL')
    if not url: raise SystemExit('CUSTOMSDESK_CI_ADMIN_URL is required.')
    target=make_url(url)
    if target.database!='postgres' or target.host not in {'localhost','127.0.0.1'}:
        raise SystemExit('CI provisioning requires the explicitly configured local ephemeral postgres admin database.')
    dburl,token=create_test_database(Settings(target))
    child=dict(os.environ,TEST_POSTGRES_URL=dburl.render_as_string(hide_password=False),CUSTOMSDESK_TEST_TOKEN=token)
    import subprocess,sys
    result=subprocess.run([sys.executable,'-m','pytest','-q','--junitxml=reports/ci-postgres-tests.xml'],env=child)
    raise SystemExit(result.returncode)
if __name__=='__main__': ci_main()
