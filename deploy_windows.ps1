param(
    [string]$InstallRoot = "D:\fuhe_deploy",
    [string]$RepoUrl = "https://gitee.com/daiyafeigitee/fuhe.git",
    [int]$NginxPort = 80,
    [int]$BackendPort = 8000,
    [string]$LogFile = "",
    [string]$MedicineCsv = ""
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$script:LogFile = $null
$script:TotalSteps = 10
$script:CurrentStep = 0

trap {
    Write-Log "Deployment failed: $($_.Exception.Message)" -Level ERROR
    exit 1
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")][string]$Level = "INFO"
    )
    $ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] [$Level] $Message"
    switch ($Level) {
        "WARN"  { Write-Host $line -ForegroundColor Yellow }
        "ERROR" { Write-Host $line -ForegroundColor Red }
        default { Write-Host $line }
    }
}

function Write-Step {
    param([string]$Message)
    $script:CurrentStep++
    $ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $pct = [int](($script:CurrentStep / $script:TotalSteps) * 100)
    $filled = [int]($pct / 5)
    $bar = ('#' * $filled).PadRight(20, '-')
    $header = "[Step $($script:CurrentStep)/$($script:TotalSteps)] [$bar] $($pct.ToString().PadLeft(3))%  $Message"
    Write-Host "`n$header" -ForegroundColor Cyan
    Write-Progress -Activity "Fuhe Deployment" -Status $Message -PercentComplete $pct
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
        if ($LogFile) {
            $argList += @("-LogFile", "`"$LogFile`"")
        }
        if ($MedicineCsv) {
            $argList += @("-MedicineCsv", "`"$MedicineCsv`"")
        }
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
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
    } catch {
        throw "Download failed from $Url : $($_.Exception.Message)"
    }
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

    if (Command-Exists "winget") {
        try {
            Write-Host "Installing Git with winget..."
            & winget install --id Git.Git -e --source winget --silent --accept-source-agreements --accept-package-agreements | Out-Null
            Refresh-Path
            if (Command-Exists "git") {
                return
            }
        } catch {
            Write-Log "winget install for Git failed: $($_.Exception.Message)" -Level WARN
        }
    }

    $installer = Join-Path $CacheDir "Git-64-bit.exe"

    $gitDownloadUrl = $null
    try {
        Write-Host "Resolving latest Git for Windows installer..."
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/git-for-windows/git/releases/latest" -Headers @{ "User-Agent" = "fuhe-deployer" } -UseBasicParsing
        $asset = $release.assets | Where-Object { $_.name -match '^Git-.*-64-bit\.exe$' } | Select-Object -First 1
        if ($asset -and $asset.browser_download_url) {
            $gitDownloadUrl = $asset.browser_download_url
        }
    } catch {
        Write-Log "GitHub API lookup for Git installer failed: $($_.Exception.Message)" -Level WARN
    }

    if (-not $gitDownloadUrl) {
        throw "Unable to resolve Git installer URL automatically."
    }

    Download-File -Url $gitDownloadUrl -OutFile $installer

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

    # Create runtime dirs nginx needs on first launch
    foreach ($d in @("logs", "temp")) {
        $nd = Join-Path $NginxRoot $d
        if (-not (Test-Path $nd)) { New-Item -Path $nd -ItemType Directory -Force | Out-Null }
    }
}

function Stop-FuheProcesses {
    param([string]$NginxRoot)

    $nginxExe = Join-Path $NginxRoot "nginx.exe"
    $nginxConf = Join-Path $NginxRoot "conf\nginx.conf"
    if (Test-Path -Path $nginxExe) {
        try {
            & $nginxExe -p $NginxRoot -c $nginxConf -s quit | Out-Null
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

function Get-BackendProcess {
    $pythonCandidates = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue
    foreach ($proc in $pythonCandidates) {
        if ($proc.CommandLine -and $proc.CommandLine -match "uvicorn" -and $proc.CommandLine -match "backend\.app\.main:app") {
            return $proc
        }
    }

    return $null
}

function Show-BackendLogTail {
    param(
        [string]$BackendLogPath,
        [int]$TailLines = 80
    )

    Write-Host ""
    if (Test-Path -Path $BackendLogPath) {
        Write-Host "----- backend.log (last $TailLines lines) -----" -ForegroundColor Yellow
        Get-Content -Path $BackendLogPath -Tail $TailLines -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host $_
        }
        Write-Host "----- end backend.log -----" -ForegroundColor Yellow
    } else {
        Write-Host "backend.log not found: $BackendLogPath" -ForegroundColor Yellow
    }
}

function Test-BackendImport {
    param(
        [string]$PythonExe,
        [string]$ProjectRoot,
        [string]$SQLiteDbPath
    )

    $probeFile = Join-Path $ProjectRoot ".backend_probe.py"
    $probeStdout = Join-Path $ProjectRoot ".backend_probe.stdout.log"
    $probeStderr = Join-Path $ProjectRoot ".backend_probe.stderr.log"
    $sqliteDbPathEscaped = $SQLiteDbPath.Replace("\", "\\")
    $probeContent = @"
import os
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_DB_PATH"] = r"$sqliteDbPathEscaped"
import backend.app.main
print("BACKEND_IMPORT_OK")
"@

    Set-Content -Path $probeFile -Value $probeContent -Encoding ASCII

    try {
        if (Test-Path -Path $probeStdout) { Remove-Item -Path $probeStdout -Force -ErrorAction SilentlyContinue }
        if (Test-Path -Path $probeStderr) { Remove-Item -Path $probeStderr -Force -ErrorAction SilentlyContinue }

        $oldPythonIoEncoding = $env:PYTHONIOENCODING
        $oldPythonUtf8 = $env:PYTHONUTF8
        $env:PYTHONIOENCODING = 'utf-8'
        $env:PYTHONUTF8 = '1'

        $probeProcess = Start-Process -FilePath $PythonExe `
            -ArgumentList $probeFile `
            -WorkingDirectory $ProjectRoot `
            -RedirectStandardOutput $probeStdout `
            -RedirectStandardError $probeStderr `
            -Wait `
            -PassThru `
            -WindowStyle Hidden

        $probeStdoutText = if (Test-Path -Path $probeStdout) { Get-Content -Path $probeStdout -Raw -ErrorAction SilentlyContinue } else { "" }
        $probeStderrText = if (Test-Path -Path $probeStderr) { Get-Content -Path $probeStderr -Raw -ErrorAction SilentlyContinue } else { "" }
        $probeOutputText = (($probeStdoutText, $probeStderrText) -join "`n").Trim()

        if ($probeOutputText) {
            $probeOutputText -split "`r?`n" | ForEach-Object {
                if ($_.Trim()) {
                    Write-Host $_
                }
            }
        }

        if ($probeProcess.ExitCode -ne 0 -or $probeOutputText -notmatch "BACKEND_IMPORT_OK") {
            throw "Backend import probe failed."
        }
    } finally {
        if ($null -eq $oldPythonIoEncoding) {
            Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
        } else {
            $env:PYTHONIOENCODING = $oldPythonIoEncoding
        }
        if ($null -eq $oldPythonUtf8) {
            Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
        } else {
            $env:PYTHONUTF8 = $oldPythonUtf8
        }
        if (Test-Path -Path $probeFile) {
            Remove-Item -Path $probeFile -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -Path $probeStdout) {
            Remove-Item -Path $probeStdout -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -Path $probeStderr) {
            Remove-Item -Path $probeStderr -Force -ErrorAction SilentlyContinue
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

if (-not $LogFile) {
    $defaultLogRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
    $LogFile = Join-Path $defaultLogRoot "deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
}

if ($MedicineCsv) {
    try {
        $MedicineCsv = [System.IO.Path]::GetFullPath($MedicineCsv)
    } catch {
    }
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
$script:LogFile = $LogFile
Write-Host "===== Deployment started $(Get-Date) ====="
Write-Log "Install root: $InstallRoot"
Write-Log "Download cache: $DownloadCache"
Write-Log "Log file: $script:LogFile"

Write-Step "Prepare directories"
Ensure-Directory -Path $InstallRoot
Ensure-Directory -Path $DownloadCache
Ensure-Directory -Path $ScriptsRoot
Ensure-Directory -Path $DataRoot
Write-Log "Directory check complete"

Write-Step "Check and install prerequisites"
Write-Log "Checking Git..."
Ensure-Git -CacheDir $DownloadCache
Write-Log "Git ready: $(git --version 2>$null)"
Write-Log "Checking Python..."
$basePython = Ensure-Python -CacheDir $DownloadCache
Write-Log "Python ready: $basePython"
Write-Log "Checking Node.js..."
Ensure-Node -CacheDir $DownloadCache
Write-Log "Node.js ready: $(node --version 2>$null)"
Write-Log "Checking Nginx..."
Ensure-Nginx -CacheDir $DownloadCache -NginxRoot $NginxRoot -BaseDir $InstallRoot
Write-Log "Nginx ready: $NginxRoot"
Refresh-Path
Write-Log "PATH refreshed"

Write-Step "Clone or update project source"
$RemoteUpdated = $false
if (Test-Path -Path (Join-Path $ProjectRoot ".git")) {
    Write-Log "Existing repo found, pulling latest changes..."
    $headBefore = (& git -C $ProjectRoot rev-parse HEAD 2>$null).Trim()
    & git -C $ProjectRoot fetch --all --prune
    & git -C $ProjectRoot pull
    $headAfter = (& git -C $ProjectRoot rev-parse HEAD 2>$null).Trim()
    if ($headBefore -and $headAfter -and ($headBefore -ne $headAfter)) {
        $RemoteUpdated = $true
        Write-Log "Remote update detected: $headBefore -> $headAfter"
    } else {
        Write-Log "No remote code changes detected."
    }
    Write-Log "Project update complete: $ProjectRoot"
} else {
    Write-Log "First deployment, cloning from $RepoUrl..."
    if (Test-Path -Path $ProjectRoot) {
        Remove-Item -Path $ProjectRoot -Recurse -Force
    }
    & git clone $RepoUrl $ProjectRoot
    $RemoteUpdated = $true
    Write-Log "Fresh clone completed. Full backend/frontend rebuild required."
    Write-Log "Project clone complete: $ProjectRoot"
}

Write-Step "Build backend environment"
$venvDir = Join-Path $ProjectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -Path $venvPython)) {
    Write-Log "Creating virtual environment: $venvDir"
    & $basePython -m venv $venvDir
    Write-Log "Virtual environment created"
} else {
    Write-Log "Virtual environment already exists, skipping creation: $venvDir"
}
$reqFile = Join-Path $ProjectRoot "backend\requirements.txt"
$reqHashFile = Join-Path $venvDir ".req_hash"
$reqHash = (Get-FileHash $reqFile -Algorithm MD5).Hash
$skipPip = $false
if ($RemoteUpdated) {
    Write-Log "Remote code updated. Forcing backend dependency rebuild."
} else {
    if (Test-Path -Path $reqHashFile) {
        if ((Get-Content $reqHashFile -Raw).Trim() -eq $reqHash) {
            Write-Log "requirements.txt unchanged (hash: $reqHash), skipping pip install"
            $skipPip = $true
        }
    }
}
if (-not $skipPip) {
    Write-Log "Upgrading pip..."
    & $venvPython -m pip install --upgrade pip
    Write-Log "Installing backend dependencies (requirements.txt)..."
    & $venvPython -m pip install -r $reqFile
    Write-Log "Backend dependencies installed"
    try { Set-Content -Path $reqHashFile -Value $reqHash -Encoding ASCII } catch {}
}

$importScript = Join-Path $ProjectRoot "backend\tools\import_tcm_medicine_dict.py"
if ($MedicineCsv) {
    if (-not (Test-Path -Path $MedicineCsv)) {
        throw "Medicine CSV not found: $MedicineCsv"
    }
    if (-not (Test-Path -Path $importScript)) {
        throw "CSV import script not found: $importScript"
    }

    Write-Log "Importing medicine CSV into deployed SQLite..."
    Write-Log "CSV: $MedicineCsv"
    Write-Log "DB : $SQLiteDbPath"
    & $venvPython $importScript --db $SQLiteDbPath --input $MedicineCsv --encoding utf-8-sig
    if ($LASTEXITCODE -ne 0) {
        throw "Medicine CSV import failed."
    }
    Write-Log "Medicine CSV import completed"
} else {
    Write-Log "No medicine CSV provided. Skip dictionary import."
}

Write-Step "Build frontend"
$frontendDir = Join-Path $ProjectRoot "frontend"
$nodeModulesDir = Join-Path $frontendDir "node_modules"
$distIndex = Join-Path $frontendDir "dist\index.html"

Push-Location $frontendDir
try {
    if ($RemoteUpdated) {
        Write-Log "Remote code updated. Forcing frontend rebuild (npm install + npm run build)."
        & npm install
        Write-Log "npm install complete"
        & npm run build
        Write-Log "Frontend build complete"
    } else {
        if (Test-Path -Path $nodeModulesDir) {
            Write-Log "node_modules already exists, skipping npm install"
        } else {
            Write-Log "Installing frontend dependencies with npm install..."
            & npm install
            Write-Log "npm install complete"
        }

        if (Test-Path -Path $distIndex) {
            Write-Log "Frontend dist already exists, skipping npm run build"
        } else {
            Write-Log "Building frontend with npm run build..."
            & npm run build
            Write-Log "Frontend build complete"
        }
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -Path $distIndex)) {
    Write-Log "Frontend build failed: dist/index.html not found" -Level ERROR
    throw "Frontend build failed: dist/index.html not found."
}
Write-Log "Frontend artifact confirmed: $distIndex"

Write-Step "Stop old runtime and select available ports"
Write-Log "Stopping existing services..."
Stop-FuheProcesses -NginxRoot $NginxRoot
Write-Log "Existing services stopped"

$SelectedBackendPort = Get-AvailablePort -PreferredPort $BackendPort
$SelectedNginxPort = Get-AvailablePort -PreferredPort $NginxPort -ExcludePorts @($SelectedBackendPort)

if ($SelectedBackendPort -ne $BackendPort) {
    Write-Warning "Backend port $BackendPort is occupied. Switched to $SelectedBackendPort."
    Write-Log "Backend port $BackendPort is occupied. Switched to $SelectedBackendPort" -Level WARN
} else {
    Write-Log "Backend port: $SelectedBackendPort"
}
if ($SelectedNginxPort -ne $NginxPort) {
    Write-Warning "Nginx port $NginxPort is occupied. Switched to $SelectedNginxPort."
    Write-Log "Nginx port $NginxPort is occupied. Switched to $SelectedNginxPort" -Level WARN
} else {
    Write-Log "Nginx port: $SelectedNginxPort"
}

Write-Step "Generate runtime files"
$backendRunner = Join-Path $ScriptsRoot "run_backend.cmd"
$backendLogPath = Join-Path $ProjectRoot "logs\backend.log"
$backendCmd = @(
    '@echo off',
    "cd /d `"$ProjectRoot`"",
    'if not exist logs mkdir logs',
    'set PYTHONIOENCODING=utf-8',
    'set PYTHONUTF8=1',
    'set USE_SQLITE=true',
    "set `"SQLITE_DB_PATH=$SQLiteDbPath`"",
    "`"$venvPython`" -m uvicorn backend.app.main:app --host 0.0.0.0 --port $SelectedBackendPort >> `"$backendLogPath`" 2>&1"
) -join "`r`n"
Set-Content -Path $backendRunner -Value $backendCmd -Encoding ASCII
Write-Log "Backend launcher created: $backendRunner"

$nginxConfPath = Join-Path $NginxRoot "conf\nginx.conf"
$frontendRootForNginx = (Join-Path $ProjectRoot "frontend\dist").Replace("\", "/")
Build-NginxConfig -OutputPath $nginxConfPath -FrontendRoot $frontendRootForNginx -ListenPort $SelectedNginxPort -ApiPort $SelectedBackendPort
Write-Log "Nginx config created: $nginxConfPath"

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

# Ensure nginx runtime dirs exist (required before first launch)
foreach ($d in @("logs", "temp", "temp\client_body", "temp\proxy", "temp\fastcgi", "temp\scgi", "temp\uwsgi")) {
    $nd = Join-Path $NginxRoot $d
    if (-not (Test-Path $nd)) { New-Item -Path $nd -ItemType Directory -Force | Out-Null }
}

$NginxConfFile = Join-Path $NginxRoot "conf\nginx.conf"
$nginxArgs = @("-p", $NginxRoot, "-c", $NginxConfFile)
Start-Process -FilePath $NginxExe -ArgumentList $nginxArgs -WorkingDirectory $NginxRoot -WindowStyle Hidden
Start-Sleep -Seconds 1

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
    $NginxConfFile = Join-Path $NginxRoot "conf\nginx.conf"
    & $NginxExe -p $NginxRoot -c $NginxConfFile -s quit | Out-Null
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
Write-Log "Start script: $targetStart"
Write-Log "Stop script: $targetStop"

$startBatPath = Join-Path $InstallRoot "start_fuhe.bat"
$startBat = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0start_fuhe.ps1`"`r`n"
Set-Content -Path $startBatPath -Value $startBat -Encoding ASCII
Write-Log "Start shortcut: $startBatPath"

$stopBatPath = Join-Path $InstallRoot "stop_fuhe.bat"
$stopBat = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0stop_fuhe.ps1`"`r`n"
Set-Content -Path $stopBatPath -Value $stopBat -Encoding ASCII
Write-Log "Stop shortcut: $stopBatPath"

Write-Log "Running backend import preflight..."
try {
    Test-BackendImport -PythonExe $venvPython -ProjectRoot $ProjectRoot -SQLiteDbPath $SQLiteDbPath
} catch {
    if ($skipPip) {
        Write-Log "Backend import preflight failed after skipped pip install. Reinstalling backend dependencies once..." -Level WARN
        & $venvPython -m pip install -r $reqFile
        try { Set-Content -Path $reqHashFile -Value $reqHash -Encoding ASCII } catch {}
        Test-BackendImport -PythonExe $venvPython -ProjectRoot $ProjectRoot -SQLiteDbPath $SQLiteDbPath
    } else {
        throw
    }
}
Write-Log "Backend import preflight passed"

Write-Step "Start runtime"
Write-Log "Starting services..."

# Ensure nginx runtime dirs exist
foreach ($d in @("logs", "temp", "temp\client_body", "temp\proxy", "temp\fastcgi", "temp\scgi", "temp\uwsgi")) {
    $nd = Join-Path $NginxRoot $d
    if (-not (Test-Path $nd)) { New-Item -Path $nd -ItemType Directory -Force | Out-Null }
}

# Start backend (hidden background window)
$backendLogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $backendLogDir)) { New-Item -Path $backendLogDir -ItemType Directory -Force | Out-Null }
if (Test-Path -Path $backendLogPath) { Remove-Item -Path $backendLogPath -Force -ErrorAction SilentlyContinue }
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$backendRunner`"" -WindowStyle Hidden
Start-Sleep -Seconds 3

$backendProc = Get-BackendProcess
if (-not $backendProc) {
    Write-Log "Backend process exited immediately after launch" -Level ERROR
    Show-BackendLogTail -BackendLogPath $backendLogPath
    throw "Backend process did not stay running."
}
Write-Log "Backend process started: PID $($backendProc.ProcessId)"

# Start nginx (background, with explicit prefix and config)
$nginxArgs = @("-p", $NginxRoot, "-c", $nginxConfPath)
Start-Process -FilePath (Join-Path $NginxRoot "nginx.exe") -ArgumentList $nginxArgs -WorkingDirectory $NginxRoot -WindowStyle Hidden
Write-Log "Nginx process started"
Start-Sleep -Seconds 2

Write-Log "Service start command executed"

Write-Step "Configure firewall for LAN access"
Write-Log "Configuring firewall rules..."
Ensure-FirewallPort -RuleName "Fuhe Nginx $SelectedNginxPort" -Port $SelectedNginxPort
Ensure-FirewallPort -RuleName "Fuhe Backend $SelectedBackendPort" -Port $SelectedBackendPort
Write-Log "Firewall rules configured. Frontend port: $SelectedNginxPort, Backend port: $SelectedBackendPort"

Start-Sleep -Seconds 2

Write-Step "Health check"
$backendHealth = "http://127.0.0.1:$SelectedBackendPort/zyfh/api/v1/health"
$frontendHealth = "http://127.0.0.1:$SelectedNginxPort/"

Write-Log "Waiting for backend to become ready (up to 60s)..."
$backendResp = $null
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    if (-not (Get-BackendProcess)) {
        Write-Host "  Backend process is no longer running."
        break
    }

    try {
        $backendResp = Invoke-WebRequest -Uri $backendHealth -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($backendResp.StatusCode -eq 200) { break }
    } catch {
        Write-Host "  Backend not ready yet, retrying... ($($_.Exception.Message))"
        Start-Sleep -Seconds 3
    }
}
if (-not $backendResp -or $backendResp.StatusCode -ne 200) {
    Write-Log "Backend health check failed after 60s" -Level ERROR
    Show-BackendLogTail -BackendLogPath $backendLogPath
    throw "Backend health check failed."
}
Write-Log "Backend health check passed, HTTP $($backendResp.StatusCode)"

Write-Log "Checking frontend: $frontendHealth"
$frontendResp = Invoke-WebRequest -Uri $frontendHealth -TimeoutSec 20 -UseBasicParsing
if ($frontendResp.StatusCode -lt 200 -or $frontendResp.StatusCode -ge 500) {
    Write-Log "Frontend health check failed, HTTP $($frontendResp.StatusCode)" -Level ERROR
    throw "Frontend health check failed."
}
Write-Log "Frontend health check passed, HTTP $($frontendResp.StatusCode)"

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
Write-Host "Deploy log: $script:LogFile" -ForegroundColor DarkGray
Write-Log "Deployment completed"
Write-Host "===== Deployment completed $(Get-Date) ====="
Write-Progress -Activity "Fuhe Deployment" -Completed
