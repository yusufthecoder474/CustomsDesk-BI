param([switch]$DryRun,[switch]$Troubleshoot,[switch]$RotatePassword)
try {
    . "$PSScriptRoot\windows_common.ps1"
    Invoke-CustomsDeskWorkflow -Action finish -DryRun:$DryRun -Troubleshoot:$Troubleshoot -RotatePassword:$RotatePassword
    exit 0
} catch { Write-Host ('ERROR: ' + $_.Exception.Message); exit 1 }
