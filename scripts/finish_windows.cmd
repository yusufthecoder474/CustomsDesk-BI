@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0finish_windows.ps1" %*
set "CUSTOMSDESK_EXIT=%ERRORLEVEL%"
echo.
if not "%CUSTOMSDESK_EXIT%"=="0" echo Verification stopped safely. Review the message above.
if /I not "%CUSTOMSDESK_NO_PAUSE%"=="1" pause
exit /b %CUSTOMSDESK_EXIT%
