@echo off
setlocal EnableDelayedExpansion
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "LOG_STAMP=%%I"
set "LOG_FILE=%~dp0deploy_!LOG_STAMP!.log"
echo Deployment log: !LOG_FILE!
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy_windows.ps1" -LogFile "!LOG_FILE!" %* >> "!LOG_FILE!" 2>&1
exit /b !ERRORLEVEL!
