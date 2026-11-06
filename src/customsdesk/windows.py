"""Windows orchestration; shell wrappers handle Python/venv bootstrap, logic is testable on Linux."""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
from .local_setup import Compose,SetupError,command,prepare_env
from .settings import resolve,checked_engine,ConfigurationError
from .pipeline import run,kpis,export
from .warehouse import initialize
from .regression import regress
from .analyze import analyze
from .verification import create_test_database,reconcile

PLAN=[
 'Check Python 3.12, dependencies, Docker CLI/engine and Compose v2.',
 'Inspect ownership of this project service; preserve .env and existing volumes.',
 'Choose a free loopback host port (prefer 5434); preserve the password; generate only for a new configuration.',
 'Start only the db service, wait for health, validate/adopt its dedicated instance marker.',
 'Verify network authentication/identity, initialize, ETL, KPIs and exports.',
 'Create a new random guarded test database; run all tests and SQLite/PostgreSQL reconciliation.',
 'Run regression and business analysis; write timestamped evidence and Power BI parameters.',
 'Leave the database running for Power BI; do not delete containers, volumes or databases.']

def check_environment():
    if sys.version_info[:2]!=(3,12): raise SetupError('Python 3.12 is required for this verification workflow.')
    import pandas,numpy,sqlalchemy,psycopg,dotenv,pytest
    command(['docker','version','--format','{{.Server.Version}}'],timeout=20)
    command(['docker','compose','version','--short'],timeout=20)
    return {'python':platform.python_version(),'platform':platform.platform(),'docker_engine':'reachable','compose':'available'}


def pytest_evidence(root,out,testurl,token):
    child=dict(os.environ,TEST_POSTGRES_URL=testurl.render_as_string(hide_password=False),CUSTOMSDESK_TEST_TOKEN=token)
    junit=out/'tests.xml'
    # No URL/password on the command line. Inherited DATABASE_URL cannot select a test database.
    result=subprocess.run([sys.executable,'-m','pytest','-q','--tb=no','--junitxml='+str(junit)],cwd=root,env=child,text=True,capture_output=True,timeout=600)
    if junit.exists():
        from urllib.parse import quote
        content=junit.read_text(encoding='utf-8')
        for secret in [testurl.render_as_string(hide_password=False),testurl.password,quote(testurl.password or '',safe='')]:
            if secret: content=content.replace(secret,'[REDACTED]')
        junit.write_text(content,encoding='utf-8')
    if not junit.exists(): raise SetupError('Pytest did not produce JUnit evidence. Dependencies/test collection need review.')
    suites=ET.parse(junit).getroot(); all_suites=suites.findall('testsuite') if suites.tag!='testsuite' else [suites]
    total=sum(int(s.attrib.get('tests',0)) for s in all_suites); failed=sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in all_suites);skipped=sum(int(s.attrib.get('skipped',0)) for s in all_suites)
    summary={'passed':total-failed-skipped,'failed':failed,'skipped':skipped,'exit_code':result.returncode}
    # Raw tracebacks can contain a connection URL supplied by a third-party driver. Store a summary only.
    (out/'POSTGRES_TEST_RESULTS.txt').write_text(json.dumps(summary,indent=2))
    if result.returncode or skipped: raise SetupError('Tests failed or skipped with PostgreSQL enabled. Review the sanitized summary/JUnit evidence before claiming success.')
    return summary


def execute(root,action='finish',dry_run=False,troubleshoot=False,rotate_password=False):
    root=Path(root).resolve()
    if dry_run:
        print('DRY RUN — no configuration, Docker or database changes')
        for step in PLAN: print('- '+step)
        return {'status':'DRY_RUN','steps':PLAN}
    report={'status':'RUNNING','power_bi':'PENDING — Desktop must be verified separately','action':action,'steps':[]}
    out=root/'reports'/'windows-runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    db=None
    try:
        report['environment']=check_environment(); print('[OK] Python/dependencies and Docker engine ready')
        if action=='check': report['status']='PASS';return report
        compose=Compose(root)
        own_port=compose.running_port()
        if troubleshoot:
            # Read-only diagnostics: do not create/rotate .env or start anything.
            settings=resolve(root,environ={})
            report['connection']=settings.public_summary(); report['owned_running_port']=own_port
            db=checked_engine(settings)
            report['status']='PASS';print('[OK] Dedicated database identity and authentication verified');return report
        settings,rotated,backup=prepare_env(root,own_port,rotate_password)
        print('[OK] Local configuration preserved; selected host port '+str(settings.url.port))
        if backup: print('[OK] Previous .env preserved in an ignored local backup')
        if os.getenv('DATABASE_URL'): print('[INFO] Dedicated-container automation ignores inherited DATABASE_URL; standalone CLI keeps documented shell precedence')
        cid=compose.start();compose.provision(cid,settings,rotated)
        db=checked_engine(settings);report['connection']=settings.public_summary();report['password_rotated']=rotated
        print('[OK] Owned database healthy; network authentication and instance marker verified')
        if action=='postgres': report['status']='PASS';return report
        initialize(db)
        result=run(db,root/'data/sample',out/'etl');report['etl']=result
        # Each invocation keeps its own evidence/exports, never overwrites prior successful runs.
        export(db,out/'exports'); analyze(db,out)
        (out/'KPI_OUTPUT.json').write_text(json.dumps(kpis(db),indent=2))
        print('[OK] ETL completed using postgresql; '+str(sum(s['source_rows'] for s in result['sources']))+' source rows')
        testurl,token=create_test_database(settings)
        report['test_database']=testurl.database
        report['tests']=pytest_evidence(root,out,testurl,token)
        print('[OK] All enabled tests passed without skips')
        report['reconciliation']=reconcile(db,root/'data/sample',out)
        report['regression']=regress(db,root/'data/sample',out)
        if not report['regression']['all_expected']: raise SetupError('Regression outcomes did not match their expectations.')
        (out/'POWER_BI_CONNECTION.json').write_text(json.dumps({'Server':str(settings.url.host)+':'+str(settings.url.port),'Database':settings.url.database,'ExportFolder':str(out/'exports'),'SourceMode':'PostgreSQL','label':'SYNTHETIC DATA','cutoff':result['as_of']},indent=2))
        (out/'POSTGRES_VERIFICATION.md').write_text('# PostgreSQL verification\n\nPASS: dedicated instance, ETL, all enabled tests, full-source SQLite reconciliation and regression completed.\nSee verification.json, tests.xml, DATABASE_RECONCILIATION.csv and QUERY_TIMINGS.json.\nPower BI Desktop remains pending.\n')
        report['status']='PASS';print('[OK] PostgreSQL/SQLite KPIs and expected regression outcomes match')
        return report
    except (SetupError,ConfigurationError) as exc:
        report['status']='FAIL';report['error']=str(exc);print('[FAIL] '+str(exc));raise
    except Exception:
        report['status']='FAIL';report['error']='Verification stopped on an unexpected failure; prior evidence and Docker volumes were preserved.'
        print('[FAIL] '+report['error']);raise SetupError(report['error']) from None
    finally:
        if db is not None: db.dispose()
        (out/'verification.json').write_text(json.dumps(report,indent=2))
        (out/'FINAL_VERIFICATION_REPORT.md').write_text('# Windows verification\n\nStatus: '+report['status']+'\n\n'+(report.get('error') or 'See verification.json for executed checks.')+'\n\nPower BI Desktop: PENDING. No report refresh or PBIX verification is implied.\n')
        print('Evidence folder: '+str(out))
        if report['status']=='PASS': print('Verification successful for requested action. Power BI Desktop validation is separate.')


def main():
    p=argparse.ArgumentParser(description='Dedicated CustomsDesk local verification')
    p.add_argument('action',choices=['finish','check','postgres','verify'])
    p.add_argument('--root',default='.')
    p.add_argument('--dry-run',action='store_true');p.add_argument('--troubleshoot',action='store_true');p.add_argument('--rotate-password',action='store_true')
    a=p.parse_args()
    try: execute(a.root,a.action,a.dry_run,a.troubleshoot,a.rotate_password)
    except (SetupError,ConfigurationError): raise SystemExit(1)
if __name__=='__main__': main()
