[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path
$python = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311\Scripts\python.exe"
if (-not (Test-Path $python)) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "setup.ps1") -SkipTests
}

$demoRoot = Join-Path $env:TEMP ("sentinel-unchained-demo-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $demoRoot | Out-Null
try {
    Set-Location $root
    & $python -m unchained $demoRoot --caps strict
    $cliExit = $LASTEXITCODE
    $run = Get-ChildItem (Join-Path $root "unchained-runs") -Directory |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $run) { throw "Demo did not create a run bundle." }

    & $python -m unchained verify-run $run.FullName
    if ($LASTEXITCODE -ne 0) { throw "Demo bundle verification failed." }
    if ($cliExit -ne 2) { throw "Demo expected INVALID exit code 2, got $cliExit." }
    Write-Host ""
    Write-Host "DEMO PASSED: fail-closed run sealed a verifiable proof bundle" -ForegroundColor Green
    Write-Host "  - empty evidence was refused honestly (INVALID, exit 2) instead of faking success" -ForegroundColor Gray
    Write-Host "  - even the refusal was sealed, hash-chained, and offline-verified: VALID" -ForegroundColor Gray
    Write-Host "  (compatibility marker: DEMO_BUNDLE_VERIFIED_INVALID_INPUT)" -ForegroundColor DarkGray
    Write-Host "BUNDLE=$($run.FullName)"
}
finally {
    if (Test-Path $demoRoot) { Remove-Item $demoRoot -Recurse -Force }
}
