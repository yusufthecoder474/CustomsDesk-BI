"""Local configuration with explicit precedence and credential-free diagnostics."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping
import ipaddress
import os
import re
from dotenv import dotenv_values
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

class ConfigurationError(ValueError):
    pass

@dataclass(frozen=True)
class Settings:
    url: URL
    instance_id: str = ''
    connect_timeout: int = 5
    selection: str = ''

    @property
    def dialect(self): return self.url.get_backend_name()

    def public_summary(self):
        if self.dialect=='sqlite': return {'dialect':'sqlite','selection':self.selection}
        return {'dialect':'postgresql','host':self.url.host,'port':self.url.port,'database':self.url.database,'selection':self.selection}


def values(root=Path('.'), environ=None):
    # dotenv_values does not mutate os.environ. Interpolation is deliberately disabled:
    # dollar signs, hashes and URL metacharacters in passwords stay literal.
    local={k:v for k,v in dotenv_values(Path(root)/'.env',interpolate=False).items() if v is not None}
    return {**local,**dict(os.environ if environ is None else environ)}


def identifier(value,label):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',value or ''):
        raise ConfigurationError(f'{label} must be a simple PostgreSQL identifier (max 63 characters).')
    return value


def resolve(root=Path('.'),explicit_url=None,database=None,environ=None):
    env=values(root,environ)
    mode=database or (None if explicit_url else env.get('CUSTOMSDESK_DATABASE'))
    raw=explicit_url or (env.get('DATABASE_URL') if database!='sqlite' else None)
    try:
        timeout=int(env.get('CUSTOMSDESK_CONNECT_TIMEOUT','5'))
        if not 1<=timeout<=30: raise ValueError()
    except ValueError: raise ConfigurationError('CUSTOMSDESK_CONNECT_TIMEOUT must be 1–30 seconds.') from None
    parsed=None
    if raw:
        try:
            parsed=make_url(raw)
            _=parsed.port
        except (ValueError,ArgumentError,TypeError):
            raise ConfigurationError('Malformed DATABASE_URL; use component variables or an encoded SQLAlchemy URL.') from None
        inferred=parsed.get_backend_name()
        if mode and mode!=inferred:
            raise ConfigurationError('Database selector and DATABASE_URL disagree; remove the stale override.')
        mode=inferred
    mode=mode or 'sqlite'
    if mode not in {'sqlite','postgresql'}: raise ConfigurationError('Only sqlite and postgresql are supported.')
    if mode=='sqlite':
        if parsed and (parsed.username or parsed.host or parsed.query): raise ConfigurationError('Unsupported SQLite URL options.')
        return Settings(parsed or make_url('sqlite:///customsdesk.db'),connect_timeout=timeout,selection='explicit SQLite' if database else 'documented local SQLite default/config')
    host=env.get('CUSTOMSDESK_HOST','127.0.0.1')
    try:
        port=int(env.get('CUSTOMSDESK_HOST_PORT','5434'))
        if not 1024<=port<=65535: raise ValueError()
    except ValueError: raise ConfigurationError('CUSTOMSDESK_HOST_PORT must be between 1024 and 65535.') from None
    if host not in {'localhost','127.0.0.1','::1','db'}:
        if env.get('CUSTOMSDESK_ALLOW_REMOTE')!='1':
            raise ConfigurationError('Remote PostgreSQL requires explicit CUSTOMSDESK_ALLOW_REMOTE=1 and matching configured host.')
    user=identifier(env.get('POSTGRES_USER','customsdesk'),'POSTGRES_USER')
    dbname=identifier(env.get('POSTGRES_DB','customsdesk'),'POSTGRES_DB')
    if parsed:
        if parsed.drivername not in {'postgresql','postgresql+psycopg'}: raise ConfigurationError('Use the psycopg PostgreSQL driver.')
        samehost=parsed.host==host or {parsed.host,host}<={'localhost','127.0.0.1','::1'}
        if not samehost or (parsed.port or 5432)!=port or parsed.database!=dbname or parsed.username!=user:
            raise ConfigurationError('DATABASE_URL target differs from configured host/port/user/database. Refusing a potentially unrelated PostgreSQL instance.')
        if parsed.query: raise ConfigurationError('Put connection timeouts in CUSTOMSDESK_CONNECT_TIMEOUT; URL query overrides are not accepted.')
        password=parsed.password
    else: password=env.get('POSTGRES_PASSWORD')
    if not password or password.startswith('GENERATE_') or password=='YOUR_PASSWORD':
        raise ConfigurationError('No usable POSTGRES_PASSWORD. Run scripts/finish_windows.cmd to configure it without printing credentials.')
    # URL.create preserves special characters without unsafe concatenation.
    url=URL.create('postgresql+psycopg',username=user,password=password,host=host,port=port,database=dbname)
    return Settings(url,env.get('CUSTOMSDESK_INSTANCE_ID',''),timeout,'explicit URL' if explicit_url else '.env/shell PostgreSQL settings')


def checked_engine(settings):
    """No writes until an instance marker and database identity match."""
    from .warehouse import engine
    from sqlalchemy import text
    db=engine(settings.url,timeout=settings.connect_timeout)
    if settings.dialect=='sqlite': return db
    try:
        with db.connect() as conn:
            actual=conn.execute(text('SELECT current_database(), current_user')).one()
            if actual[0]!=settings.url.database or actual[1]!=settings.url.username:
                raise ConfigurationError('Database identity mismatch. No warehouse changes were made.')
            exists=conn.scalar(text("SELECT to_regclass('public.customsdesk_instance')"))
            if not settings.instance_id or not exists:
                raise ConfigurationError('CustomsDesk ownership marker is missing. Use the one-click setup to provision only the owned Compose service.')
            rows=conn.execute(text('SELECT instance_id FROM public.customsdesk_instance')).scalars().all()
            if rows != [settings.instance_id]:
                raise ConfigurationError('CustomsDesk ownership marker does not match .env. No warehouse changes were made.')
    except ConfigurationError:
        db.dispose(); raise
    except Exception:
        db.dispose()
        raise ConfigurationError('PostgreSQL connection failed: check the chosen port, service health and local password rotation. No SQLite fallback was attempted. Run finish_windows.cmd -Troubleshoot.') from None
    return db
