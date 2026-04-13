param(
  [string]$Host = "",
  [int]$Port = 0,
  [switch]$StartDockerServices,
  [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonExe = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
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

if (-not (Test-Path $pythonExe)) {
  throw "未找到虚拟环境 Python：$pythonExe"
}

if (-not $Host) {
  $Host = if ($env:APP_BACKEND_HOST) { $env:APP_BACKEND_HOST } else { "127.0.0.1" }
}

if ($Port -le 0) {
  $Port = if ($env:APP_BACKEND_PORT) { [int]$env:APP_BACKEND_PORT } else { 8082 }
}

if (-not $env:VITE_API_BASE_URL) {
  $env:VITE_API_BASE_URL = "http://$Host`:$Port"
}

if ($StartDockerServices) {
  Set-Location $repoRoot
  docker compose up -d db redis
}

Set-Location $repoRoot

if (-not $SkipChecks) {
  & $pythonExe manage.py check
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

Write-Host "Backend root: $repoRoot"
Write-Host "Using .env: $envFile"
Write-Host "Backend URL: http://$Host`:$Port"
Write-Host "Frontend API base: $($env:VITE_API_BASE_URL)"

& $pythonExe (Join-Path $repoRoot "bin\\run_backend_wsgi.py") --host $Host --port $Port
