# PowerShell source validation

All 7 PowerShell files parsed without syntax errors using tree-sitter-powershell 0.26.4 / tree-sitter 0.26.0.

A parsing issue in the GitHub publication command was corrected by passing an argument array. This is static Linux grammar validation, not actual execution in Windows PowerShell 5.1, PowerShell 7, Docker Desktop or GitHub CLI.

- scripts/windows_common.ps1: syntax parsed
- scripts/finish_windows.ps1: syntax parsed
- scripts/check_environment.ps1: syntax parsed
- scripts/run_demo.ps1: syntax parsed
- scripts/verify_project.ps1: syntax parsed
- scripts/verify_postgres.ps1: syntax parsed
- scripts/publish_github.ps1: syntax parsed
