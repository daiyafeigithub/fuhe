param(
    [string]$InstallRoot = "D:\fuhe_deploy",
    [string]$RepoUrl = "https://gitee.com/daiyafeigitee/fuhe.git",
    [int]$NginxPort = 80,
    [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Write-Step {
    param([string]$Message)
    Write-Host "`n==== $Message ====" -ForegroundColor Cyan
}

function Ensure-Admin {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host "Requesting administrator privileges..."
        $argList = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$PSCommandPath`"",
            "-InstallRoot", "`"$InstallRoot`"",
            "-RepoUrl", "`"$RepoUrl`"",
            "-NginxPort", "$NginxPort",
            "-BackendPort", "$BackendPort"
        )
        Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Verb RunAs
        exit 0
    }
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -Path $Path)) {
        New-Item -Path $Path -ItemType Directory -Force | Out-Null
    }
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Download-File {
    param(
        [string]$Url,
        [string]$OutFile
    )

    if ((Test-Path -Path $OutFile) -and ((Get-Item -Path $OutFile).Length -gt 0)) {
        Write-Host "Using cached package: $OutFile"
        return
    }

    Write-Host "Downloading: $Url"
    Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
}

function Command-Exists {
    param([string]$Name)
    return [bool](Get-Command -Name $Name -ErrorAction SilentlyContinue)
}

function Ensure-Git {
    param([string]$CacheDir)

    if (Command-Exists "git") {
        Write-Host "Git is already installed."
        return
    }

    $installer = Join-Path $CacheDir "Git-64-bit.exe"
    Download-File -Url "https://github.com/git-for-windows/git/releases/latest/download/Git-64-bit.exe" -OutFile $installer

    Write-Host "Installing Git..."
    Start-Process -FilePath $installer -ArgumentList "/VERYSILENT", "/NORESTART", "/SP-" -Wait
    Refresh-Path

    if (-not (Command-Exists "git")) {
        throw "Git installation failed."
    }
}

function Resolve-PythonExe {
    if (Command-Exists "py") {
        try {
            $resolved = (& py -3.11 -c "import sys; print(sys.executable)" 2>$null)
            if ($resolved) {
                return $resolved.Trim()
            }
        } catch {
        }
    }

    if (Command-Exists "python") {
        $pythonCmd = Get-Command -Name "python" -ErrorAction SilentlyContinue
        if ($pythonCmd) {
            return $pythonCmd.Source
        }
    }

    return $null
}

function Get-PythonVersion {
    param([string]$PythonExe)

    try {
        $ver = (& $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)
        if ($ver) {
            return $ver.Trim()
        }
    } catch {
    }

    return "0.0"
}

function Ensure-Python {
    param([string]$CacheDir)

    $pythonExe = Resolve-PythonExe
    if ($pythonExe) {
        $ver = Get-PythonVersion -PythonExe $pythonExe
        $parts = $ver.Split('.')
        if (($parts.Length -ge 2) -and (([int]$parts[0] -gt 3) -or (([int]$parts[0] -eq 3) -and ([int]$parts[1] -ge 11)))) {
            Write-Host "Python $ver is already installed."
            return $pythonExe
        }
    }

    $installer = Join-Path $CacheDir "python-3.11.9-amd64.exe"
    Download-File -Url "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $installer

    Write-Host "Installing Python 3.11..."
    Start-Process -FilePath $installer -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
    Refresh-Path

    $pythonExe = Resolve-PythonExe
    if (-not $pythonExe) {
        throw "Python installation failed."
    }

    return $pythonExe
}

function Ensure-Node {
    param([string]$CacheDir)

    if (Command-Exists "node") {
        try {
            $verRaw = (& node --version)
            if ($verRaw) {
                $major = [int]($verRaw.Trim().TrimStart('v').Split('.')[0])
                if ($major -ge 18) {
                    Write-Host "Node.js $verRaw is already installed."
                    return
                }
            }
        } catch {
        }
    }

    $installer = Join-Path $CacheDir "node-v20.19.0-x64.msi"
    Download-File -Url "https://nodejs.org/dist/v20.19.0/node-v20.19.0-x64.msi" -OutFile $installer

    Write-Host "Installing Node.js..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", "`"$installer`"", "/qn", "/norestart" -Wait
    Refresh-Path

    if (-not (Command-Exists "node")) {
        throw "Node.js installation failed."
    }
}

function Ensure-Nginx {
    param(
        [string]$CacheDir,
        [string]$NginxRoot,
        [string]$BaseDir
    )

    $nginxExe = Join-Path $NginxRoot "nginx.exe"
    if (Test-Path -Path $nginxExe) {
        Write-Host "Nginx is already installed at $NginxRoot"
        return
    }

    $zipFile = Join-Path $CacheDir "nginx-1.26.3.zip"
    Download-File -Url "https://nginx.org/download/nginx-1.26.3.zip" -OutFile $zipFile

    if (Test-Path -Path $NginxRoot) {
        Remove-Item -Path $NginxRoot -Recurse -Force
    }

    Write-Host "Installing Nginx..."
    Expand-Archive -Path $zipFile -DestinationPath $BaseDir -Force

    $expanded = Join-Path $BaseDir "nginx-1.26.3"
    if (-not (Test-Path -Path $expanded)) {
        throw "Nginx archive structure is not expected."
    }

    Rename-Item -Path $expanded -NewName (Split-Path -Path $NginxRoot -Leaf)
}

function Stop-FuheProcesses {
    param([string]$NginxRoot)

    $nginxExe = Join-Path $NginxRoot "nginx.exe"
    if (Test-Path -Path $nginxExe) {
        try {
            & $nginxExe -s quit | Out-Null
        } catch {
        }
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
}

function Test-PortInUse {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop
        return $conn.Count -gt 0
    } catch {
        return $false
    }
}

function Get-AvailablePort {
    param(
        [int]$PreferredPort,
        [int[]]$ExcludePorts = @(),
        [int]$MaxAttempts = 200
    )

    $candidate = $PreferredPort
    for ($i = 0; $i -lt $MaxAttempts; $i++) {
        if (($ExcludePorts -notcontains $candidate) -and -not (Test-PortInUse -Port $candidate)) {
            return $candidate
        }
        $candidate++
    }

    throw "No available port found near $PreferredPort after $MaxAttempts attempts."
}

function Ensure-FirewallPort {
    param(
        [string]$RuleName,
        [int]$Port
    )

    & netsh advfirewall firewall delete rule name="$RuleName" | Out-Null
    & netsh advfirewall firewall add rule name="$RuleName" dir=in action=allow protocol=TCP localport=$Port | Out-Null
}

function Get-LanIPList {
    $ips = @()

    try {
        $ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
            Where-Object {
                $_.IPAddress -ne "127.0.0.1" -and
                $_.IPAddress -notlike "169.254*"
            } |
            Select-Object -ExpandProperty IPAddress -Unique
    } catch {
    }

    if (-not $ips -or $ips.Count -eq 0) {
        $ips = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
            Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and $_.IPAddressToString -ne "127.0.0.1" } |
            ForEach-Object { $_.IPAddressToString } |
            Select-Object -Unique
    }

    return $ips
}

function Build-NginxConfig {
    param(
        [string]$OutputPath,
        [string]$FrontendRoot,
        [int]$ListenPort,
        [int]$ApiPort
    )

    $template = @'
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    server {
        listen       __NGINX_PORT__;
        server_name  _;

        charset utf-8;
        root __FRONTEND_ROOT__;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /zyfh/api/ {
            proxy_pass http://127.0.0.1:__BACKEND_PORT__;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /zyfh/qrcodes/ {
            proxy_pass http://127.0.0.1:__BACKEND_PORT__;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /zyfh/reports/ {
            proxy_pass http://127.0.0.1:__BACKEND_PORT__;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /docs {
            proxy_pass http://127.0.0.1:__BACKEND_PORT__;
            proxy_set_header Host $host;
        }

        location /openapi.json {
            proxy_pass http://127.0.0.1:__BACKEND_PORT__;
            proxy_set_header Host $host;
        }
    }
}
'@

    $config = $template.Replace("__NGINX_PORT__", "$ListenPort").Replace("__BACKEND_PORT__", "$ApiPort").Replace("__FRONTEND_ROOT__", "$FrontendRoot")
    Set-Content -Path $OutputPath -Value $config -Encoding ASCII
}

Ensure-Admin

if (($InstallRoot -like "D:*") -and (-not (Test-Path -Path "D:\"))) {
    Write-Warning "Drive D: is not available. Falling back to C:\fuhe_deploy"
    $InstallRoot = "C:\fuhe_deploy"
}

$DownloadCache = Join-Path $InstallRoot "downloads"
$ProjectRoot = Join-Path $InstallRoot "fuhe"
$NginxRoot = Join-Path $InstallRoot "nginx"
$ScriptsRoot = Join-Path $InstallRoot "scripts"
$DataRoot = Join-Path $InstallRoot "data"
$SQLiteDbPath = Join-Path $DataRoot "zyyz_fuping.db"

Write-Step "Prepare directories"
Ensure-Directory -Path $InstallRoot
Ensure-Directory -Path $DownloadCache
Ensure-Directory -Path $ScriptsRoot
Ensure-Directory -Path $DataRoot

Write-Step "Check and install prerequisites"
Ensure-Git -CacheDir $DownloadCache
$basePython = Ensure-Python -CacheDir $DownloadCache
Ensure-Node -CacheDir $DownloadCache
Ensure-Nginx -CacheDir $DownloadCache -NginxRoot $NginxRoot -BaseDir $InstallRoot
Refresh-Path

Write-Step "Clone or update project source"
if (Test-Path -Path (Join-Path $ProjectRoot ".git")) {
    & git -C $ProjectRoot fetch --all --prune
    & git -C $ProjectRoot pull
} else {
    if (Test-Path -Path $ProjectRoot) {
        Remove-Item -Path $ProjectRoot -Recurse -Force
    }
    & git clone $RepoUrl $ProjectRoot
}

Write-Step "Build backend environment"
$venvDir = Join-Path $ProjectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -Path $venvPython)) {
    & $basePython -m venv $venvDir
}
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $ProjectRoot "backend\requirements.txt")

Write-Step "Build frontend"
Push-Location (Join-Path $ProjectRoot "frontend")
& npm install
& npm run build
Pop-Location

$distIndex = Join-Path $ProjectRoot "frontend\dist\index.html"
if (-not (Test-Path -Path $distIndex)) {
    throw "Frontend build failed: dist/index.html not found."
}

Write-Step "Stop old runtime and select available ports"
Stop-FuheProcesses -NginxRoot $NginxRoot

$SelectedBackendPort = Get-AvailablePort -PreferredPort $BackendPort
$SelectedNginxPort = Get-AvailablePort -PreferredPort $NginxPort -ExcludePorts @($SelectedBackendPort)

if ($SelectedBackendPort -ne $BackendPort) {
    Write-Warning "Backend port $BackendPort is occupied. Switched to $SelectedBackendPort."
}
if ($SelectedNginxPort -ne $NginxPort) {
    Write-Warning "Nginx port $NginxPort is occupied. Switched to $SelectedNginxPort."
}

Write-Step "Generate runtime files"
$backendRunner = Join-Path $ScriptsRoot "run_backend.cmd"
$backendLogPath = Join-Path $ProjectRoot "logs\backend.log"
$backendCmd = @"
@echo off
cd /d "$ProjectRoot"
if not exist logs mkdir logs
set USE_SQLITE=true
set "SQLITE_DB_PATH=$SQLiteDbPath"
"$venvPython" -m uvicorn backend.app.main:app --host 0.0.0.0 --port $SelectedBackendPort >> "$backendLogPath" 2>&1
"@
Set-Content -Path $backendRunner -Value $backendCmd -Encoding ASCII

$nginxConfPath = Join-Path $NginxRoot "conf\nginx.conf"
$frontendRootForNginx = (Join-Path $ProjectRoot "frontend\dist").Replace("\", "/")
Build-NginxConfig -OutputPath $nginxConfPath -FrontendRoot $frontendRootForNginx -ListenPort $SelectedNginxPort -ApiPort $SelectedBackendPort

$targetStart = Join-Path $InstallRoot "start_fuhe.ps1"
$targetStop = Join-Path $InstallRoot "stop_fuhe.ps1"

$startTemplate = @'
param(
    [string]$InstallRoot = "__INSTALL_ROOT__",
    [int]$NginxPort = __NGINX_PORT__,
    [int]$BackendPort = __BACKEND_PORT__
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
'@

$stopTemplate = @'
param(
    [string]$InstallRoot = "__INSTALL_ROOT__"
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
'@

$startContent = $startTemplate.Replace("__INSTALL_ROOT__", $InstallRoot).Replace("__NGINX_PORT__", "$SelectedNginxPort").Replace("__BACKEND_PORT__", "$SelectedBackendPort")
$stopContent = $stopTemplate.Replace("__INSTALL_ROOT__", $InstallRoot)

Set-Content -Path $targetStart -Value $startContent -Encoding ASCII
Set-Content -Path $targetStop -Value $stopContent -Encoding ASCII

$startBatPath = Join-Path $InstallRoot "start_fuhe.bat"
$startBat = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0start_fuhe.ps1`"`r`n"
Set-Content -Path $startBatPath -Value $startBat -Encoding ASCII

$stopBatPath = Join-Path $InstallRoot "stop_fuhe.bat"
$stopBat = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0stop_fuhe.ps1`"`r`n"
Set-Content -Path $stopBatPath -Value $stopBat -Encoding ASCII

Write-Step "Start runtime"
& $targetStart -InstallRoot $InstallRoot -NginxPort $SelectedNginxPort -BackendPort $SelectedBackendPort

Write-Step "Configure firewall for LAN access"
Ensure-FirewallPort -RuleName "Fuhe Nginx $SelectedNginxPort" -Port $SelectedNginxPort
Ensure-FirewallPort -RuleName "Fuhe Backend $SelectedBackendPort" -Port $SelectedBackendPort

Start-Sleep -Seconds 2

Write-Step "Health check"
$backendHealth = "http://127.0.0.1:$SelectedBackendPort/zyfh/api/v1/health"
$frontendHealth = "http://127.0.0.1:$SelectedNginxPort/"

$backendResp = Invoke-WebRequest -Uri $backendHealth -TimeoutSec 20 -UseBasicParsing
if ($backendResp.StatusCode -ne 200) {
    throw "Backend health check failed."
}

$frontendResp = Invoke-WebRequest -Uri $frontendHealth -TimeoutSec 20 -UseBasicParsing
if ($frontendResp.StatusCode -lt 200 -or $frontendResp.StatusCode -ge 500) {
    throw "Frontend health check failed."
}

$ips = Get-LanIPList
Write-Host "`nDeployment completed successfully." -ForegroundColor Green
Write-Host "Install root: $InstallRoot"
Write-Host "Project root: $ProjectRoot"
Write-Host "Download cache: $DownloadCache"
Write-Host "SQLite DB: $SQLiteDbPath"
Write-Host "Local access: http://127.0.0.1:$SelectedNginxPort"
if ($ips -and $ips.Count -gt 0) {
    foreach ($ip in $ips) {
        Write-Host "LAN access: http://$ip`:$SelectedNginxPort"
    }
}
Write-Host "Backend docs: http://127.0.0.1:$SelectedNginxPort/docs"
Write-Host "Actual backend port: $SelectedBackendPort"
Write-Host "Actual frontend port: $SelectedNginxPort"
Write-Host "Stop command: $stopBatPath"
Write-Host "Start command: $startBatPath"
