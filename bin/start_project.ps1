param(
  [switch]$StartDockerServices
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendDir = Join-Path $repoRoot "templates\\front\\admin"
$envFile = Join-Path $repoRoot ".env"

function Import-EnvFile {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    return
  }

  Get-Content $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }

    $pair = $line.Split("=", 2)
    $key = $pair[0].Trim()
    $value = $pair[1].Trim().Trim('"').Trim("'")
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not (Test-Path "Env:$key")) {
      Set-Item -Path "Env:$key" -Value $value
    }
  }
}

Import-EnvFile -Path $envFile

$backendHost = if ($env:APP_BACKEND_HOST) { $env:APP_BACKEND_HOST } else { "127.0.0.1" }
$backendPort = if ($env:APP_BACKEND_PORT) { [int]$env:APP_BACKEND_PORT } else { 8082 }
$frontendPort = if ($env:APP_FRONTEND_PORT) { [int]$env:APP_FRONTEND_PORT } else { 8081 }

if (-not $env:VITE_API_BASE_URL) {
  $env:VITE_API_BASE_URL = "http://$backendHost`:$backendPort"
}

$backendScript = Join-Path $repoRoot "bin\\start_backend.ps1"
$backendArgs = @(
  "-ExecutionPolicy", "Bypass",
  "-File", $backendScript,
  "-Host", $backendHost,
  "-Port", $backendPort
)

if ($StartDockerServices) {
  $backendArgs += "-StartDockerServices"
}

Write-Host "Starting backend in a separate PowerShell window..."
Start-Process -FilePath "powershell" -ArgumentList $backendArgs -WorkingDirectory $repoRoot

Write-Host "Starting frontend on http://127.0.0.1:$frontendPort"
Set-Location $frontendDir
npm run serve -- --host 0.0.0.0 --port $frontendPort
