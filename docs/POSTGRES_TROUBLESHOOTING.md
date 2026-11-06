# PostgreSQL troubleshooting without data loss

## Port already allocated

The repaired mapping is `127.0.0.1:${CUSTOMSDESK_HOST_PORT:-5434}:5432`. Port 5432 inside PostgreSQL
stays unchanged. The one-click workflow binds a local socket to check availability, reuses the port
of this exact owned running service, or chooses/persists a free permitted port. Another project is
never stopped. A rare bind race stops startup safely; rerunning checks availability again.

## Authentication failed after editing .env

An initialized PostgreSQL volume keeps its existing role password. Editing POSTGRES_PASSWORD is not
a reset. Do not erase the volume. Run finish_windows.cmd: it validates the dedicated container and
uses local psql inside it to rotate the existing configured role, then verifies TCP authentication.
The new password is generated and stored locally without terminal display.

If local psql is not authorized or POSTGRES_USER differs from the original administrator, the workflow
stops instead of guessing other roles. Preserve the volume and .env backup. Confirm the original
administrator from your own installation records. An authorized local administrator can use an
interactive psql session and `\password customsdesk` to set a new password without putting it in
command history, then update local .env privately and rerun. Do not weaken host authentication or
change/delete another project's database. No administrator password can be recovered by this build.

## Instance marker mismatch

This prevents accidental connection to an unrelated or differently configured database. Restore the
matching .env from your local ignored backup or point the project at its original owned container.
Do not delete/reassign the marker to silence the error. No warehouse changes are made by the CLI
until the identity check passes.

## Old .env URL or shell settings still point at 5432

One-click automation scopes itself to the project configuration and safely migrates its local URL to
component settings after backup. Standalone CLI deliberately respects explicit shell overrides and
will reject a target mismatch. Run the CMD wrapper directly to avoid stale manually entered URLs.
Power BI should use the actual host/port from the latest POWER_BI_CONNECTION.json.

## Python, Docker or internet missing

The workflow stops with a short error. Start Docker Desktop or install Python 3.12 with the py launcher
as appropriate, then rerun the same CMD file. It never recreates an existing incompatible virtual
environment or prunes Docker resources. A dependency-install failure may require internet access.

## Integration test skipped/refused

The workflow supplies a newly created disposable test database and token automatically. Do not point
TEST_POSTGRES_URL at your application database. A manual pytest invocation without this guarded
environment legitimately skips PostgreSQL checks. See the latest run report before claiming a pass.
