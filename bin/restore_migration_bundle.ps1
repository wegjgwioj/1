param(
  [Parameter(Mandatory = $true)]
  [string]$BundlePath,
  [string]$TargetDir = "",
  [switch]$SkipDatabaseImport,
  [switch]$SkipBootstrap
)

$ErrorActionPreference = "Stop"

if (-not $TargetDir) {
  $TargetDir = (Get-Location).Path
}

$TargetDir = [System.IO.Path]::GetFullPath($TargetDir)
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("ev-log-restore-" + [guid]::NewGuid().ToString("N"))
$extractDir = Join-Path $tempRoot "bundle"

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
  param([string]$RepoRoot)

  $envValues = Get-EnvFileValues -Path (Join-Path $RepoRoot ".env")
  $configValues = Get-IniSectionValues -Path (Join-Path $RepoRoot "config.ini") -Section "sql"

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

if (-not (Test-Path $BundlePath)) {
  throw "Bundle not found: $BundlePath"
}

if (Test-Path $tempRoot) {
  Remove-Item -LiteralPath $tempRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

Write-Host "Expanding migration bundle..."
Expand-Archive -LiteralPath $BundlePath -DestinationPath $extractDir -Force

Write-Host "Restoring source snapshot..."
Copy-DirectoryContent -Source (Join-Path $extractDir "project") -Destination $TargetDir

Write-Host "Restoring config files..."
$bundleEnvFile = Join-Path $extractDir "config\.env"
$bundleConfigIni = Join-Path $extractDir "config\config.ini"
if (Test-Path $bundleEnvFile) {
  Copy-Item -LiteralPath $bundleEnvFile -Destination (Join-Path $TargetDir ".env") -Force
}
if (Test-Path $bundleConfigIni) {
  Copy-Item -LiteralPath $bundleConfigIni -Destination (Join-Path $TargetDir "config.ini") -Force
}

Write-Host "Restoring runtime data..."
Copy-DirectoryContent -Source (Join-Path $extractDir "runtime-data\media") -Destination (Join-Path $TargetDir "media")
Copy-DirectoryContent -Source (Join-Path $extractDir "runtime-data\artifacts") -Destination (Join-Path $TargetDir "artifacts")
Copy-DirectoryContent -Source (Join-Path $extractDir "runtime-data\datasets") -Destination (Join-Path $TargetDir "datasets")

if (-not $SkipDatabaseImport) {
  Assert-CommandAvailable -Name "mysql"

  $dbSettings = Resolve-DatabaseSettings -RepoRoot $TargetDir
  $authArgs = New-MySqlAuthArgs -Settings $dbSettings
  $collation = if ($dbSettings.Charset -eq "utf8mb4") { "utf8mb4_unicode_ci" } else { "utf8_general_ci" }
  $createSql = "CREATE DATABASE IF NOT EXISTS ``$($dbSettings.Name)`` DEFAULT CHARACTER SET $($dbSettings.Charset) COLLATE $collation;"

  Write-Host "Creating target database if needed..."
  & mysql @authArgs --execute=$createSql
  if ($LASTEXITCODE -ne 0) {
    throw "mysql failed while creating the target database."
  }

  $dumpPath = Join-Path $extractDir "db\diandong5k56la1f_full.sql"
  if (-not (Test-Path $dumpPath)) {
    throw "Database dump not found in migration bundle: $dumpPath"
  }

  Write-Host "Importing MySQL dump..."
  Get-Content -LiteralPath $dumpPath -Encoding UTF8 | & mysql @authArgs $dbSettings.Name
  if ($LASTEXITCODE -ne 0) {
    throw "mysql failed while importing the database dump."
  }
}

if (-not $SkipBootstrap) {
  $bootstrapScript = Join-Path $TargetDir "bin\bootstrap_local.ps1"
  if (-not (Test-Path $bootstrapScript)) {
    throw "bootstrap_local.ps1 was not restored to the target directory."
  }

  Write-Host "Running dependency bootstrap..."
  & powershell -ExecutionPolicy Bypass -File $bootstrapScript -SkipStart
  if ($LASTEXITCODE -ne 0) {
    throw "bootstrap_local.ps1 failed during restore."
  }
}

Remove-Item -LiteralPath $tempRoot -Recurse -Force

Write-Host "Migration restore finished. You can now run: powershell -ExecutionPolicy Bypass -File .\bin\start_project.ps1"
