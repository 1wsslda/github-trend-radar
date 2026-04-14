$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir
$installerScript = Join-Path $root "packaging\GitSonar.iss"
$installerOutput = Join-Path $root "artifacts\dist\installer\GitSonarSetup.exe"
Set-Location $root

function Resolve-Iscc {
  $candidate = Get-Command iscc -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
  if ($candidate) { return $candidate }

  foreach ($fallback in @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
  )) {
    if (Test-Path $fallback) {
      return $fallback
    }
  }

  return $null
}

& (Join-Path $scriptDir "build_exe.ps1")
if ($LASTEXITCODE -ne 0) {
  throw "EXE build failed."
}

$iscc = Resolve-Iscc
if (-not $iscc) {
  Write-Host "Inno Setup not found, installing with winget..."
  winget install -e --id JRSoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup installation failed."
  }
  $iscc = Resolve-Iscc
}

if (-not $iscc) {
  throw "Unable to locate Inno Setup compiler: ISCC.exe"
}

& $iscc $installerScript
if ($LASTEXITCODE -ne 0) {
  throw "Installer build failed."
}

Write-Host ""
Write-Host "Setup complete: $installerOutput"
