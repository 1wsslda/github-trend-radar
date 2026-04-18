$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir
$appName = "GitSonar"
$legacyAppName = "GitHubTrendRadar"
$entryScript = Join-Path $root "src\gitsonar\__main__.py"
$artifactsRoot = Join-Path $root "artifacts"
$distPath = Join-Path $artifactsRoot "dist"
$buildPath = Join-Path $artifactsRoot "build"
$specPath = Join-Path $artifactsRoot "spec"
$generatedSpec = Join-Path $specPath "$appName.spec"

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
  python -m pip install -r (Join-Path $root "requirements.txt") pyinstaller
  if ($LASTEXITCODE -ne 0) {
    throw "pip install failed."
  }
} else {
  Write-Host "Python packages already installed, skipping pip install."
}

$running = Get-Process -Name $appName, $legacyAppName -ErrorAction SilentlyContinue
if ($running) {
  $running | Stop-Process -Force
  Start-Sleep -Seconds 1
}

foreach ($path in @($distPath, $buildPath, $specPath, (Join-Path $root "__pycache__"))) {
  if (Test-Path $path) {
    Remove-Item -Recurse -Force $path
  }
}

foreach ($path in @((Join-Path $root "dist"), (Join-Path $root "build"))) {
  if (Test-Path $path) {
    try {
      Remove-Item -Recurse -Force $path
    } catch {
      Write-Warning "Skipping legacy path cleanup: $path"
    }
  }
}

New-Item -ItemType Directory -Force -Path $artifactsRoot, $distPath, $buildPath, $specPath | Out-Null

python -m PyInstaller `
  --name $appName `
  --onefile `
  --clean `
  --noconfirm `
  --noconsole `
  --distpath $distPath `
  --workpath $buildPath `
  --specpath $specPath `
  $entryScript

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller build failed."
}

if (Test-Path $generatedSpec) {
  Remove-Item -LiteralPath $generatedSpec -Force
}

Write-Host ""
Write-Host "Build complete: $distPath\$appName.exe"
