param(
  [switch]$PrepareDemoData,
  [switch]$SkipStart,
  [switch]$SkipDatabaseBootstrap
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendDir = Join-Path $repoRoot "templates\\front\\admin"
$rootEnvExample = Join-Path $repoRoot ".env.example"
$rootEnvFile = Join-Path $repoRoot ".env"
$frontendEnvExample = Join-Path $frontendDir ".env.example"
$frontendEnvFile = Join-Path $frontendDir ".env"
$venvDir = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\\python.exe"
$dbBootstrapScript = Join-Path $repoRoot "bin\\bootstrap_local_db.py"
$startProjectScript = Join-Path $repoRoot "bin\\start_project.ps1"

function Test-CommandAvailable {
  param([string]$Name)

  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Resolve-PythonBootstrapCommand {
  if (Test-CommandAvailable -Name "py") {
    try {
      & py -3.11 --version *> $null
      return @("py", "-3.11")
    } catch {
    }

    try {
      & py --version *> $null
      return @("py")
    } catch {
    }
  }

  if (Test-CommandAvailable -Name "python") {
    return @("python")
  }

  throw "Python was not found. Please install Python 3.11 and make sure 'py' or 'python' works in PowerShell."
}

function Invoke-ExternalCommand {
  param(
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$WorkingDirectory = $repoRoot
  )

  Push-Location $WorkingDirectory
  try {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
      throw "Command failed: $FilePath $($Arguments -join ' ')"
    }
  } finally {
    Pop-Location
  }
}

function Ensure-EnvFile {
  param(
    [string]$Source,
    [string]$Target
  )

  if (Test-Path $Target) {
    Write-Host "Env file already exists: $Target"
    return
  }

  Copy-Item -Path $Source -Destination $Target
  Write-Host "Created env file: $Target"
}

if (-not (Test-CommandAvailable -Name "node")) {
  throw "Node.js was not found. Please install Node.js 18 or newer."
}

if (-not (Test-CommandAvailable -Name "npm")) {
  throw "npm was not found. Please install Node.js and make sure npm is in PATH."
}

$pythonBootstrapCommand = Resolve-PythonBootstrapCommand
$pythonBootstrapExe = $pythonBootstrapCommand[0]
$pythonBootstrapArgs = if ($pythonBootstrapCommand.Length -gt 1) { $pythonBootstrapCommand[1..($pythonBootstrapCommand.Length - 1)] } else { @() }

Write-Host "Repository root: $repoRoot"
Write-Host "Starting Windows local bootstrap..."

if (-not (Test-Path $venvPython)) {
  Write-Host "No .venv found. Creating virtual environment..."
  Invoke-ExternalCommand -FilePath $pythonBootstrapExe -Arguments ($pythonBootstrapArgs + @("-m", "venv", ".venv"))
} else {
  Write-Host "Virtual environment already exists: $venvDir"
}

Write-Host "Installing backend dependencies..."
# Equivalent to: python -m pip install -r requirements.txt
Invoke-ExternalCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt")

Ensure-EnvFile -Source $rootEnvExample -Target $rootEnvFile
Ensure-EnvFile -Source $frontendEnvExample -Target $frontendEnvFile

Write-Host "Installing frontend dependencies..."
# Equivalent to: npm install
Invoke-ExternalCommand -FilePath "npm" -Arguments @("install") -WorkingDirectory $frontendDir

if ($SkipDatabaseBootstrap) {
  Write-Host "Skipping database bootstrap and migrations."
} else {
  Write-Host "Bootstrapping local MySQL database..."
  Invoke-ExternalCommand -FilePath $venvPython -Arguments @($dbBootstrapScript)

  Write-Host "Running Django migrations..."
  # Equivalent to: python manage.py migrate --fake-initial --noinput
  Invoke-ExternalCommand -FilePath $venvPython -Arguments @("manage.py", "migrate", "--fake-initial", "--noinput")

  Write-Host "Syncing feature schema..."
  Invoke-ExternalCommand -FilePath $venvPython -Arguments @("manage.py", "sync_feature_schema")

  if ($PrepareDemoData) {
    Write-Host "Preparing demo data..."
    Invoke-ExternalCommand -FilePath $venvPython -Arguments @("manage.py", "prepare_demo_data")
  } else {
    Write-Host "Use -PrepareDemoData if you also want to normalize demo data for a presentation run."
  }
}

Write-Host "Redis is optional in local mode. The backend will fall back to local memory cache if Redis is unavailable."

if ($SkipStart) {
  Write-Host "Bootstrap finished. Later you can start the project with: powershell -ExecutionPolicy Bypass -File .\\bin\\start_project.ps1"
  exit 0
}

Write-Host "Starting backend and frontend..."
Invoke-ExternalCommand -FilePath "powershell" -Arguments @(
  "-ExecutionPolicy", "Bypass",
  "-File", $startProjectScript
)
