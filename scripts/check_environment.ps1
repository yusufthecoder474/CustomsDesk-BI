param([switch]$DryRun)
try {
    . "$PSScriptRoot\windows_common.ps1"
    Invoke-CustomsDeskWorkflow -Action check -DryRun:$DryRun
    exit 0
} catch { Write-Host ('ERROR: ' + $_.Exception.Message); exit 1 }
