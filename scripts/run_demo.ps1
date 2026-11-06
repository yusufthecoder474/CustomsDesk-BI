$ErrorActionPreference = 'Stop'
# Run from repository root after installing requirements and activating .venv.
python -m customsdesk.cli demo
if ($LASTEXITCODE -ne 0) { throw 'Demo failed' }
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
