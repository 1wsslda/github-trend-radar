param(
  [string]$DistRoot = "",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir

if (-not $DistRoot) {
  $DistRoot = Join-Path $root "artifacts\dist"
}

function Get-Sha256Hex {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  if (Get-Command Get-FileHash -ErrorAction SilentlyContinue) {
    try {
      return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    } catch {
      # Some minimal PowerShell hosts omit Get-FileHash or expose a broken shim.
    }
  }

  $stream = [System.IO.File]::OpenRead($Path)
  try {
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
      return [System.BitConverter]::ToString($sha256.ComputeHash($stream)).Replace("-", "").ToLowerInvariant()
    } finally {
      $sha256.Dispose()
    }
  } finally {
    $stream.Dispose()
  }
}

$artifactSpecs = @(
  @{ Path = "GitSonar.exe"; Kind = "portable-exe" },
  @{ Path = "installer\GitSonarSetup.exe"; Kind = "installer" }
)

$artifacts = @()
foreach ($spec in $artifactSpecs) {
  $relativePath = [string]$spec.Path
  $fullPath = Join-Path $DistRoot $relativePath
  if (-not (Test-Path -LiteralPath $fullPath)) {
    continue
  }

  $file = Get-Item -LiteralPath $fullPath
  $hash = Get-Sha256Hex -Path $file.FullName
  $artifacts += [ordered]@{
    path = $relativePath.Replace("\", "/")
    kind = [string]$spec.Kind
    size = $file.Length
    sha256 = $hash
  }
}

if ($artifacts.Count -eq 0) {
  Write-Host "No release artifacts found under $DistRoot."
  exit 0
}

$manifest = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  artifacts = $artifacts
}

$json = $manifest | ConvertTo-Json -Depth 6

if ($DryRun) {
  Write-Output $json
  exit 0
}

New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null
$manifestPath = Join-Path $DistRoot "release-manifest.json"
$sumsPath = Join-Path $DistRoot "SHA256SUMS.txt"

Set-Content -LiteralPath $manifestPath -Value $json -Encoding UTF8
$sumLines = $artifacts | ForEach-Object { "$($_.sha256)  $($_.path)" }
Set-Content -LiteralPath $sumsPath -Value $sumLines -Encoding ASCII

Write-Host "Release manifest written: $manifestPath"
Write-Host "SHA256 sums written: $sumsPath"
