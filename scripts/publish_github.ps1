param([ValidateSet('private','public')][string]$Visibility='private',[switch]$Publish)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $Root
try {
    Write-Host ('Planned destination: yusufthecoder474/CustomsDesk-BI ('+$Visibility+')')
    Write-Host 'No license is selected. Review the final report, staged files, visibility and pending checks first.'
    if (-not $Publish) { Write-Host 'PREVIEW ONLY. No Git or GitHub changes made. Use -Publish only after you approve publication.'; exit 0 }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI gh is required.' }
    & gh auth status
    if ($LASTEXITCODE -ne 0) { throw 'Authenticate with gh auth login before publishing.' }
    $Existing = & gh repo view yusufthecoder474/CustomsDesk-BI --json name 2>$null
    if ($LASTEXITCODE -eq 0) { throw 'Destination already exists. It was not modified; use a separately reviewed commit/PR workflow.' }
    # A failed view can also be a network/permissions failure; create below fails safely if it exists.
    if (-not (Test-Path .git)) { & git init; if ($LASTEXITCODE -ne 0) { throw 'git init failed' } }
    & git add --all
    if ($LASTEXITCODE -ne 0) { throw 'Could not stage repository' }
    $Staged = @(& git diff --cached --name-only)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect staged files' }
    foreach ($Name in $Staged) {
        if (($Name -match '(^|/)(\.env($|\.)|\.venv/|\.local/)') -and $Name -ne '.env.example') { throw 'Sensitive local file staged; publication stopped.' }
        if ($Name -match '\.(db|sqlite|pyc)$') { throw 'Database/cache staged; publication stopped.' }
    }
    if ($Staged.Count -gt 0) { & git commit -m 'Repair CustomsDesk BI configuration and verification workflow'; if ($LASTEXITCODE -ne 0) { throw 'Commit failed' } }
    $CreateArguments = @('repo','create','yusufthecoder474/CustomsDesk-BI','--source','.','--remote','origin','--push',('--'+$Visibility))
    & gh @CreateArguments
    if ($LASTEXITCODE -ne 0) { throw 'Creation/push failed; existing repositories were not overwritten.' }
} finally { Pop-Location }
