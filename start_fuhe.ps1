param(
    [string]$InstallRoot = "D:\fuhe_deploy",
    [int]$NginxPort = 80,
    [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"
$NginxRoot = Join-Path $InstallRoot "nginx"
$ScriptsRoot = Join-Path $InstallRoot "scripts"
$NginxExe = Join-Path $NginxRoot "nginx.exe"
$BackendRunner = Join-Path $ScriptsRoot "run_backend.cmd"
$StopScript = Join-Path $PSScriptRoot "stop_fuhe.ps1"

if (Test-Path -Path $StopScript) {
    & $StopScript -InstallRoot $InstallRoot
}

if (-not (Test-Path -Path $BackendRunner)) {
    throw "Backend runner script not found: $BackendRunner"
}

if (-not (Test-Path -Path $NginxExe)) {
    throw "Nginx executable not found: $NginxExe"
}

Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$BackendRunner`"" -WindowStyle Hidden
Start-Sleep -Seconds 2

Push-Location $NginxRoot
& .\nginx.exe
Pop-Location

Write-Host "Fuhe services started."
Write-Host "Frontend: http://127.0.0.1:$NginxPort"
Write-Host "Backend health: http://127.0.0.1:$BackendPort/zyfh/api/v1/health"
