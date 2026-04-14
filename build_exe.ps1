$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$appName = "GitHubTrendRadar"
$entryScript = "GitHubTrendRadar.pyw"
$generatedSpec = Join-Path $root "$appName.spec"

Set-Location $root

function Test-PythonModule {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ModuleName
  )

  python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)" *> $null
  return ($LASTEXITCODE -eq 0)
}

$requiredModules = @(
  @{ Name = "requests"; Import = "requests" },
  @{ Name = "beautifulsoup4"; Import = "bs4" },
  @{ Name = "pystray"; Import = "pystray" },
  @{ Name = "Pillow"; Import = "PIL" },
  @{ Name = "pyinstaller"; Import = "PyInstaller" }
)

$missingModules = @($requiredModules | Where-Object { -not (Test-PythonModule $_.Import) })

if ($missingModules.Count -gt 0) {
  Write-Host "Missing Python packages detected, installing..."
  python -m pip install -r requirements.txt pyinstaller
  if ($LASTEXITCODE -ne 0) {
    throw "pip install failed."
  }
} else {
  Write-Host "Python packages already installed, skipping pip install."
}

$running = Get-Process $appName -ErrorAction SilentlyContinue
if ($running) {
  $running | Stop-Process -Force
  Start-Sleep -Seconds 1
}

foreach ($path in @("dist", "build", "__pycache__")) {
  if (Test-Path $path) {
    Remove-Item -Recurse -Force $path
  }
}

python -m PyInstaller `
  --name $appName `
  --onefile `
  --clean `
  --noconfirm `
  --noconsole `
  $entryScript

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller build failed."
}

if (Test-Path $generatedSpec) {
  Remove-Item -LiteralPath $generatedSpec -Force
}

Write-Host ""
Write-Host "Build complete: $root\\dist\\$appName.exe"
