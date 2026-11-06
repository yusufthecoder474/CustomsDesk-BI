# Configuration and security

## Standalone CLI precedence

1. Explicit --database-url (target must agree with PostgreSQL component settings).
2. Explicit --database chooses the dialect; --database sqlite ignores inherited DATABASE_URL.
3. Shell environment variables override matching .env values.
4. .env in --env-root (default current folder).
5. Documented local SQLite default when no database configuration is present.

An explicit URL determines dialect unless a conflicting explicit --database was also supplied.
For PostgreSQL, defaults are host 127.0.0.1, host port 5434, user/database customsdesk. Connection
components must match any supplied URL; stale URLs pointing at 5432 are rejected before connecting.
Build URLs using SQLAlchemy URL.create; standalone encoded URLs are supported, not printed.
The app never retries a failed PostgreSQL connection with SQLite.

.env uses python-dotenv with interpolation disabled. Dollar signs/hashes in quoted passwords remain
literal. No process-global os.environ mutation is needed. Connect timeout defaults to five seconds
and must be 1–30. Non-loopback hosts require an explicit remote opt-in and matching target settings.
The internal Docker hostname db can be used with port 5432 from a container; configure its host/port
explicitly. The supplied Compose launches PostgreSQL only, not the Python application container.

## One-click workflow isolation

Dedicated-container automation intentionally uses this project's .env rather than inherited database
shell overrides. It clears managed overrides only in child Compose/test processes, never globally.
It preserves other environment variables needed for Docker Desktop/context. Standalone CLI retains
normal shell precedence. A stale local DATABASE_URL is backed up and replaced with an empty value;
component settings become canonical and special characters need no manual URL encoding.

## Ownership and password rotation

The workflow locates containers by this exact Compose working directory and service=db, checks the
labels and postgres:17.6 image, and sends administrative SQL only to that owned container. Before
adopting an unmarked database, it refuses unknown public tables. Existing marker mismatches stop
without rotating the role or reassigning the database. CLI network connections require the matching
CUSTOMSDESK_INSTANCE_ID marker before warehouse initialization/ETL.

The first migration generates a new strong password rather than reusing potentially exposed prior
credentials. Later invocations reuse it; -RotatePassword requests another rotation. SQL passwords
are sent to psql via stdin, never process arguments or terminal output. Changing Compose environment
values alone does not reset an existing PostgreSQL role: an explicit ALTER ROLE is required and is
performed only through the owned-container administrative channel.

.env edits are atomic and retain unrelated settings/comments. Backups are local sensitive files:
.env and .env.* are ignored, with .env.example explicitly allowed. POSIX permissions are restricted
where supported; Windows ACL hardening is not claimed. Protect your project folder/backups locally.
No .env, backup, real password/token, venv, local database or raw Docker/psql stderr belongs in releases. A .dockerignore also excludes these local files from Docker build contexts.

## Disposable integration tests

A new random test database is created without reusing or deleting existing databases. A random guard
token is inserted before tests. Both database name and token are checked before tests may replace
facts. Test URLs/tokens live only in the subprocess environment. Windows JUnit is scrubbed for the
known connection password/URL before retention. The intentionally ephemeral CI password is only for
a fresh service container and is not a real credential. No repository secrets are required for it.

This is a local student analytics project, not a production access-control or secrets-management
service. Real deployments need governed source access, retention, least privilege and managed secrets.
