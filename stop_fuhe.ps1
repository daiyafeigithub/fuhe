param(
    [string]$InstallRoot = "D:\fuhe_deploy"
)

$ErrorActionPreference = "SilentlyContinue"
$NginxRoot = Join-Path $InstallRoot "nginx"
$NginxExe = Join-Path $NginxRoot "nginx.exe"

if (Test-Path -Path $NginxExe) {
    & $NginxExe -s quit | Out-Null
}

Start-Sleep -Seconds 1

Get-Process -Name "nginx" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

$pythonCandidates = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue
foreach ($proc in $pythonCandidates) {
    if ($proc.CommandLine -and $proc.CommandLine -match "uvicorn" -and $proc.CommandLine -match "backend\.app\.main:app") {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Fuhe services stopped."
