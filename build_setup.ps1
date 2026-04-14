$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
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

& "$root\build_exe.ps1"
if ($LASTEXITCODE -ne 0) {
  throw "EXE build failed."
}

$iscc = Resolve-Iscc
if (-not $iscc) {
  Write-Host "Inno Setup 未安装，开始用 winget 安装..."
  winget install -e --id JRSoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup installation failed."
  }
  $iscc = Resolve-Iscc
}

if (-not $iscc) {
  throw "未找到 Inno Setup 编译器 ISCC.exe"
}

& $iscc ".\GitHubTrendRadar.iss"
if ($LASTEXITCODE -ne 0) {
  throw "Installer build failed."
}

Write-Host ""
Write-Host "Setup complete: $root\dist\installer\GitHubTrendRadarSetup.exe"
