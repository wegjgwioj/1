param(
  [string]$OutputDir = "",
  [string]$BundleName = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDir) {
  $OutputDir = Join-Path $repoRoot "migration-bundles"
}

if (-not $BundleName) {
  $BundleName = "ev-log-migration-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss")
}

$stagingRoot = Join-Path $OutputDir "__staging__$BundleName"
$bundleRoot = Join-Path $stagingRoot $BundleName
$projectDir = Join-Path $bundleRoot "project"
$configDir = Join-Path $bundleRoot "config"
$dbDir = Join-Path $bundleRoot "db"
$runtimeDataDir = Join-Path $bundleRoot "runtime-data"
$zipPath = Join-Path $OutputDir "$BundleName.zip"
$rootEnvFile = Join-Path $repoRoot ".env"
$configIniFile = Join-Path $repoRoot "config.ini"

function Assert-CommandAvailable {
  param([string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command was not found: $Name"
  }
}

function Get-EnvFileValues {
  param([string]$Path)

  $values = @{}
  if (-not (Test-Path $Path)) {
    return $values
  }

  Get-Content $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }

    $pair = $line.Split("=", 2)
    $key = $pair[0].Trim()
    $value = $pair[1].Trim().Trim('"').Trim("'")
    if ($key) {
      $values[$key] = $value
    }
  }

  return $values
}

function Get-IniSectionValues {
  param(
    [string]$Path,
    [string]$Section
  )

  $values = @{}
  if (-not (Test-Path $Path)) {
    return $values
  }

  $currentSection = ""
  foreach ($rawLine in Get-Content $Path) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith(";") -or $line.StartsWith("#")) {
      continue
    }

    if ($line -match '^\[(.+)\]$') {
      $currentSection = $Matches[1].Trim()
      continue
    }

    if ($currentSection -ne $Section) {
      continue
    }

    if ($line -match '^(?<key>[^=]+?)\s*=\s*(?<value>.*)$') {
      $values[$Matches["key"].Trim()] = $Matches["value"].Trim()
    }
  }

  return $values
}

function Resolve-DatabaseSettings {
  $envValues = Get-EnvFileValues -Path $rootEnvFile
  $configValues = Get-IniSectionValues -Path $configIniFile -Section "sql"

  return [ordered]@{
    Host = if ($envValues.ContainsKey("DB_HOST")) { $envValues["DB_HOST"] } elseif ($configValues.ContainsKey("host")) { $configValues["host"] } else { "127.0.0.1" }
    Port = if ($envValues.ContainsKey("DB_PORT")) { [int]$envValues["DB_PORT"] } elseif ($configValues.ContainsKey("port")) { [int]$configValues["port"] } else { 3306 }
    Name = if ($envValues.ContainsKey("DB_NAME")) { $envValues["DB_NAME"] } elseif ($configValues.ContainsKey("db")) { $configValues["db"] } else { "diandong5k56la1f" }
    User = if ($envValues.ContainsKey("DB_USER")) { $envValues["DB_USER"] } elseif ($configValues.ContainsKey("user")) { $configValues["user"] } else { "root" }
    Password = if ($envValues.ContainsKey("DB_PASSWORD")) { $envValues["DB_PASSWORD"] } elseif ($configValues.ContainsKey("passwd")) { $configValues["passwd"] } else { "" }
    Charset = if ($envValues.ContainsKey("DB_CHARSET")) { $envValues["DB_CHARSET"] } elseif ($configValues.ContainsKey("charset")) { $configValues["charset"] } else { "utf8mb4" }
  }
}

function New-MySqlAuthArgs {
  param($Settings)

  $args = @("-h", $Settings.Host, "-P", "$($Settings.Port)", "-u", $Settings.User)
  if ($Settings.Password -ne "") {
    $args += "-p$($Settings.Password)"
  }
  return $args
}

function Copy-DirectoryContent {
  param(
    [string]$Source,
    [string]$Destination
  )

  if (-not (Test-Path $Source)) {
    return
  }

  if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
  }

  $items = Get-ChildItem -LiteralPath $Source -Force
  if ($items.Count -eq 0) {
    return
  }

  Copy-Item -Path $items.FullName -Destination $Destination -Recurse -Force
}

function Copy-RepoSnapshot {
  param(
    [string]$Source,
    [string]$Destination
  )

  Assert-CommandAvailable -Name "robocopy"

  $excludeDirs = @(
    (Join-Path $Source ".git"),
    (Join-Path $Source ".venv"),
    (Join-Path $Source ".idea"),
    (Join-Path $Source ".playwright-mcp"),
    (Join-Path $Source "media"),
    (Join-Path $Source "artifacts"),
    (Join-Path $Source "datasets"),
    (Join-Path $Source "migration-bundles"),
    (Join-Path $Source "templates\front\admin\node_modules"),
    (Join-Path $Source "templates\front\admin\dist")
  ) | Where-Object { $_ -and (Test-Path $_) }

  $args = @(
    $Source,
    $Destination,
    "/E",
    "/R:1",
    "/W:1",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/NP",
    "/XD"
  ) + $excludeDirs + @(
    "/XF",
    "*.out",
    "*.err",
    "*.log"
  )

  & robocopy @args | Out-Null
  if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed while creating the source snapshot."
  }
}

Assert-CommandAvailable -Name "mysqldump"

if (Test-Path $stagingRoot) {
  Remove-Item -LiteralPath $stagingRoot -Recurse -Force
}

if (Test-Path $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Path $projectDir -Force | Out-Null
New-Item -ItemType Directory -Path $configDir -Force | Out-Null
New-Item -ItemType Directory -Path $dbDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runtimeDataDir "media") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runtimeDataDir "artifacts") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runtimeDataDir "datasets") -Force | Out-Null

$dbSettings = Resolve-DatabaseSettings
$dbDumpPath = Join-Path $dbDir "diandong5k56la1f_full.sql"

Write-Host "Creating source snapshot..."
Copy-RepoSnapshot -Source $repoRoot -Destination $projectDir

Write-Host "Copying config files..."
if (Test-Path $rootEnvFile) {
  Copy-Item -LiteralPath $rootEnvFile -Destination (Join-Path $configDir ".env") -Force
}
if (Test-Path $configIniFile) {
  Copy-Item -LiteralPath $configIniFile -Destination (Join-Path $configDir "config.ini") -Force
}

Write-Host "Exporting MySQL database..."
$dumpArgs = New-MySqlAuthArgs -Settings $dbSettings
$dumpArgs += @(
  "--default-character-set=$($dbSettings.Charset)",
  "--single-transaction",
  "--routines",
  "--triggers",
  $dbSettings.Name
)
& mysqldump @dumpArgs 1> $dbDumpPath
if ($LASTEXITCODE -ne 0) {
  throw "mysqldump failed. Check MySQL connection settings in .env or config.ini."
}

Write-Host "Copying runtime data directories..."
Copy-DirectoryContent -Source (Join-Path $repoRoot "media") -Destination (Join-Path $runtimeDataDir "media")
Copy-DirectoryContent -Source (Join-Path $repoRoot "artifacts") -Destination (Join-Path $runtimeDataDir "artifacts")
Copy-DirectoryContent -Source (Join-Path $repoRoot "datasets") -Destination (Join-Path $runtimeDataDir "datasets")

$manifest = [ordered]@{
  bundleName = $BundleName
  createdAt = (Get-Date).ToString("s")
  projectRoot = $repoRoot
  database = [ordered]@{
    host = $dbSettings.Host
    port = $dbSettings.Port
    name = $dbSettings.Name
    user = $dbSettings.User
    charset = $dbSettings.Charset
  }
  includes = @(
    "project snapshot",
    ".env",
    "config.ini",
    "MySQL full dump",
    "media",
    "artifacts",
    "datasets"
  )
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $bundleRoot "manifest.json") -Encoding UTF8

if (-not (Test-Path $OutputDir)) {
  New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "Creating zip archive..."
Compress-Archive -Path (Join-Path $bundleRoot "*") -DestinationPath $zipPath -Force

Remove-Item -LiteralPath $stagingRoot -Recurse -Force

Write-Host "Migration bundle created: $zipPath"
