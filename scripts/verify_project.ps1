param([switch]$DryRun,[switch]$Troubleshoot)
try {
    . "$PSScriptRoot\windows_common.ps1"
    Invoke-CustomsDeskWorkflow -Action verify -DryRun:$DryRun -Troubleshoot:$Troubleshoot
    exit 0
} catch { Write-Host ('ERROR: ' + $_.Exception.Message); exit 1 }
