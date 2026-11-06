Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Invoke-CustomsDeskWorkflow {
    param([string]$Action, [switch]$DryRun, [switch]$Troubleshoot, [switch]$RotatePassword)
    $Root = Split-Path -Parent $PSScriptRoot
    Push-Location -LiteralPath $Root
    try {
        if ($DryRun) {
            Write-Host 'DRY RUN: no files, environments, containers or databases will be changed.'
            Write-Host 'Plan: validate Python 3.12/dependencies/Docker; preserve .env; choose free port; rotate local password; start only db; verify identity; ETL/export; isolated PostgreSQL tests; reconcile SQL KPIs; timestamp evidence.'
            Write-Host 'Power BI Desktop build and refresh remain separate manual checks.'
            return
        }
        $Python = Join-Path $Root '.venv\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $Python)) {
            if ($Troubleshoot -or $Action -eq 'check') { throw 'Project .venv is missing. Run finish_windows.cmd first.' }
            $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
            if (-not $PyLauncher) { throw 'Python launcher not found. Install Python 3.12 with the Windows py launcher.' }
            $PyVersion = & py -3.12 -c 'import sys; print(sys.version_info[:2] == (3, 12))' 2>$null
            if ($LASTEXITCODE -ne 0 -or $PyVersion -ne 'True') { throw 'Python 3.12 is required. Install it before continuing.' }
            & py -3.12 -m venv .venv
            if ($LASTEXITCODE -ne 0) { throw 'Could not create .venv; existing project files were preserved.' }
        }
        $Version = & $Python -c 'import sys; print(sys.version_info[:2] == (3, 12))'
        if ($LASTEXITCODE -ne 0 -or $Version -ne 'True') { throw 'The existing .venv must use Python 3.12. It was not deleted or recreated.' }
        # Troubleshooting/check modes are read-only, including dependency installation.
        if (-not $Troubleshoot -and $Action -ne 'check') {
            Write-Host 'Checking/installing pinned project dependencies...'
            $InstallOutput = & $Python -m pip install --disable-pip-version-check -r requirements-dev.txt -e . 2>&1
            if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check internet access and Python 3.12. Raw installer logs were not printed to avoid leaking private index settings.' }
        }
        $ImportOutput = & $Python -c 'import pandas,numpy,sqlalchemy,psycopg,dotenv,pytest,customsdesk' 2>&1
        if ($LASTEXITCODE -ne 0) { throw 'Project dependencies are missing; run finish_windows.cmd with internet access.' }
        $Arguments = @('-m','customsdesk.windows',$Action,'--root',$Root)
        if ($Troubleshoot) { $Arguments += '--troubleshoot' }
        if ($RotatePassword) { $Arguments += '--rotate-password' }
        & $Python @Arguments
        if ($LASTEXITCODE -ne 0) { throw 'Verification stopped safely. Read the message and newest reports/windows-runs folder.' }
    } finally { Pop-Location }
}
