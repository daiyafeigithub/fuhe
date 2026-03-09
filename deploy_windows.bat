@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy_windows.ps1" %*
exit /b %ERRORLEVEL%
