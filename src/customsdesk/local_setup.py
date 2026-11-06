"""Safe local setup helpers. Only operate on the Compose service in the given root."""
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import time
from datetime import datetime,timezone
from pathlib import Path
from dotenv import dotenv_values
from psycopg import sql
from .settings import ConfigurationError,identifier,resolve

class SetupError(RuntimeError): pass

def command(args,*,input=None,timeout=60,env=None):
    try:
        result=subprocess.run(args,input=input,text=True,capture_output=True,timeout=timeout,env=env)
    except (OSError,subprocess.TimeoutExpired):
        raise SetupError(f'{Path(str(args[0])).name} unavailable or timed out; check installation/service readiness.') from None
    if result.returncode:
        # Never relay external stderr: psql errors can contain SQL including a password literal.
        raise SetupError(f'{Path(str(args[0])).name} operation failed (exit {result.returncode}). No credentials or raw stderr were logged.')
    return result.stdout.strip()


def port_available(port):
    try:
        with socket.socket() as sock:
            if hasattr(socket,'SO_EXCLUSIVEADDRUSE'): sock.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            sock.bind(('127.0.0.1',port))
        return True
    except OSError: return False


def choose_port(preferred=5434,owned_running_port=None):
    if not 1024<=preferred<=65535: raise SetupError('Configured host port must be 1024–65535.')
    if preferred==owned_running_port or port_available(preferred): return preferred
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); candidate=sock.getsockname()[1]
    if candidate<1024: raise SetupError('No permitted free local port found.')
    return candidate


def write_env(path,updates):
    """Atomic targeted edit; retain comments and unrelated settings; never print values."""
    path=Path(path); before=path.read_text(encoding='utf-8-sig') if path.exists() else ''
    lines=before.splitlines(); found=set(); output=[]
    for line in lines:
        match=re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=',line)
        if match and match[1] in updates:
            key=match[1]
            if key not in found: output.append(key+'='+json.dumps(str(updates[key])))
            found.add(key)
        else: output.append(line)
    for key,value in updates.items():
        if key not in found: output.append(key+'='+json.dumps(str(value)))
    content='\n'.join(output)+'\n'
    if content==before: return None
    backup=None
    if path.exists():
        backup=path.with_name('.env.backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+secrets.token_hex(3))
        shutil.copy2(path,backup)
        try: backup.chmod(0o600)
        except OSError: pass
    temp=path.with_name('.env.pending-'+secrets.token_hex(5))
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream: stream.write(content)
    os.replace(temp,path)
    try: path.chmod(0o600)
    except OSError: pass
    return backup


def prepare_env(root,owned_running_port=None,rotate=False):
    root=Path(root); path=root/'.env'
    existing={k:v for k,v in dotenv_values(path,interpolate=False).items() if v is not None}
    if existing.get('CUSTOMSDESK_HOST','127.0.0.1') not in {'localhost','127.0.0.1'}:
        raise SetupError('One-click setup manages a local dedicated container only; remote host configuration was preserved.')
    user=identifier(existing.get('POSTGRES_USER','customsdesk'),'POSTGRES_USER')
    db=identifier(existing.get('POSTGRES_DB','customsdesk'),'POSTGRES_DB')
    if db in {'postgres','template0','template1'}: raise SetupError('Choose an application database, not a PostgreSQL system database.')
    try: preferred=int(existing.get('CUSTOMSDESK_HOST_PORT','5434'))
    except ValueError: raise SetupError('CUSTOMSDESK_HOST_PORT is not numeric; original .env preserved.') from None
    port=choose_port(preferred,owned_running_port)
    if existing.get('DATABASE_URL'):
        raise SetupError('Existing DATABASE_URL preserved. Use the standalone CLI for this configured connection; dedicated-container setup will not replace it.')
    old=existing.get('POSTGRES_PASSWORD','')
    rotate=rotate or not old or old.startswith('GENERATE_')
    password=secrets.token_urlsafe(36) if rotate else old
    updates=dict(CUSTOMSDESK_DATABASE='postgresql',CUSTOMSDESK_HOST='127.0.0.1',CUSTOMSDESK_HOST_PORT=port,
        POSTGRES_USER=user,POSTGRES_DB=db,POSTGRES_PASSWORD=password,
        CUSTOMSDESK_INSTANCE_ID=existing.get('CUSTOMSDESK_INSTANCE_ID') or secrets.token_hex(24),
        CUSTOMSDESK_CONNECT_TIMEOUT=existing.get('CUSTOMSDESK_CONNECT_TIMEOUT','5'),
        CUSTOMSDESK_PASSWORD_ROTATED='0' if rotate else '1',DATABASE_URL='')
    backup=write_env(path,updates)
    return resolve(root,environ={}),rotate,backup

class Compose:
    def __init__(self,root,runner=command):
        self.root=Path(root).resolve(); self.runner=runner
        self.prefix=['docker','compose','--project-directory',str(self.root),'--env-file',str(self.root/'.env'),'-f',str(self.root/'compose.yaml')]
    def invoke(self,*args,**kwargs):
        # Dedicated automation uses this project's .env, not stale shell database overrides.
        managed={'DATABASE_URL','POSTGRES_USER','POSTGRES_DB','POSTGRES_PASSWORD','CUSTOMSDESK_HOST_PORT','COMPOSE_PROJECT_NAME'}
        child={k:v for k,v in os.environ.items() if k not in managed}
        return self.runner([*self.prefix,*args],env=child,**kwargs)
    def container(self):
        ids=self.runner(['docker','ps','-a','-q','--filter','label=com.docker.compose.service=db','--filter','label=com.docker.compose.project.working_dir='+str(self.root)]).splitlines()
        if len(ids)>1: raise SetupError('More than one db service container; manual ownership review required.')
        if not ids: return None
        cid=ids[0]; self.assert_owned(cid); return cid
    def assert_owned(self,cid):
        labels=json.loads(self.runner(['docker','inspect','--format','{{json .Config.Labels}}',cid])) or {}
        working=labels.get('com.docker.compose.project.working_dir','')
        if labels.get('com.docker.compose.service')!='db' or os.path.normcase(str(Path(working).resolve()))!=os.path.normcase(str(self.root)):
            raise SetupError('Container ownership does not match this project directory; no container was changed.')
        image=self.runner(['docker','inspect','--format','{{.Config.Image}}',cid])
        if image!='postgres:17.6': raise SetupError('Owned service is not the expected postgres:17.6 image; refusing automatic role changes.')
    def running_port(self):
        cid=self.container()
        if not cid: return None
        running=self.runner(['docker','inspect','--format','{{.State.Running}}',cid])=='true'
        if not running: return None
        bindings=json.loads(self.runner(['docker','inspect','--format','{{json .NetworkSettings.Ports}}',cid])) or {}
        ports=bindings.get('5432/tcp') or []
        return int(ports[0]['HostPort']) if len(ports)==1 and ports[0]['HostIp']=='127.0.0.1' else None
    def start(self):
        # The same Compose project name in another directory must never be adopted/recreated.
        # Config JSON can contain secrets: inspect in memory only, never print/store it.
        project=json.loads(self.invoke('config','--format','json')).get('name')
        if not project: raise SetupError('Compose did not resolve a project name.')
        ids=self.runner(['docker','ps','-a','-q','--filter','label=com.docker.compose.project='+project,'--filter','label=com.docker.compose.service=db']).splitlines()
        for existing in ids: self.assert_owned(existing)
        self.invoke('up','-d','--no-deps','db',timeout=180)
        cid=self.container()
        if not cid: raise SetupError('Database container was not created.')
        for _ in range(60):
            status=self.runner(['docker','inspect','--format','{{if .State.Health}}{{.State.Health.Status}}{{end}}',cid])
            if status=='healthy': return cid
            if status=='unhealthy': raise SetupError('Owned database is unhealthy. Existing volume was preserved; see password/role recovery guide.')
            time.sleep(1)
        raise SetupError('Database did not become healthy within 60 seconds; volume preserved.')
    def psql(self,cid,user,dbname,statement):
        self.assert_owned(cid)
        return self.runner(['docker','exec','-i',cid,'psql','-w','-X','-A','-t','-v','ON_ERROR_STOP=1','-U',user,'-d',dbname],input=statement,timeout=30)
    def provision(self,cid,settings,rotate):
        user=settings.url.username; db=settings.url.database
        marker_exists=self.psql(cid,user,db,"SELECT to_regclass('public.customsdesk_instance') IS NOT NULL;")
        if marker_exists=='t':
            marker=self.psql(cid,user,db,'SELECT instance_id FROM public.customsdesk_instance;')
            if marker!=settings.instance_id: raise SetupError('Existing instance marker differs; refusing password rotation or reassignment. Restore matching local configuration.')
        else:
            # Refuse to adopt an unrelated database even inside an owned service.
            from .warehouse import metadata
            tables=set(filter(None,self.psql(cid,user,db,"SELECT tablename FROM pg_tables WHERE schemaname='public';").splitlines()))
            if tables-set(metadata.tables): raise SetupError('Unrecognized tables in unmarked database; no role or data changes made.')
        statements=['BEGIN;','CREATE TABLE IF NOT EXISTS public.customsdesk_instance (singleton integer PRIMARY KEY CHECK(singleton=1), instance_id text NOT NULL);']
        statements.append(sql.SQL('INSERT INTO public.customsdesk_instance VALUES (1,{}) ON CONFLICT (singleton) DO NOTHING;').format(sql.Literal(settings.instance_id)).as_string())
        if rotate:
            statements.append(sql.SQL('ALTER ROLE {} WITH PASSWORD {};').format(sql.Identifier(user),sql.Literal(settings.url.password)).as_string())
        statements.append('COMMIT;')
        self.psql(cid,user,db,'\n'.join(statements))
        if rotate: write_env(self.root/'.env',{'CUSTOMSDESK_PASSWORD_ROTATED':'1'})
