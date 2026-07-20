[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$root = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path
$python = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311\Scripts\python.exe"
if (-not (Test-Path $python)) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "setup.ps1") -SkipTests
    if ($LASTEXITCODE -ne 0) { throw "setup.ps1 failed with exit code $LASTEXITCODE." }
}

# This demo proves the fail-closed SEAL + offline-VERIFY path on empty evidence.
# It never contacts OpenAI: empty evidence is refused during local profiling,
# before any model call. A placeholder key only satisfies model construction and
# is never sent anywhere.
$env:UNCHAINED_MODEL = "gpt-5.6-luna"
$env:UNCHAINED_ALLOW_TEST_MODEL = "1"
$env:OPENAI_API_KEY = "sk-demo-placeholder-never-sent"

$runsDir = Join-Path $root "unchained-runs"
$before = @()
if (Test-Path $runsDir) {
    $before = Get-ChildItem $runsDir -Directory | Select-Object -ExpandProperty FullName
}

$demoRoot = Join-Path $env:TEMP ("sentinel-unchained-demo-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $demoRoot | Out-Null
try {
    Set-Location $root
    & $python -m unchained $demoRoot --caps strict
    $cliExit = $LASTEXITCODE
    if ($cliExit -ne 2) {
        throw "Demo expected INVALID exit code 2 for empty evidence, got $cliExit."
    }

    # Verify EXACTLY the bundle this run created (diff against the pre-run set),
    # never merely the newest folder - so a stale bundle can never be validated
    # and reported as this run's result.
    $after = @()
    if (Test-Path $runsDir) {
        $after = Get-ChildItem $runsDir -Directory | Select-Object -ExpandProperty FullName
    }
    $new = @($after | Where-Object { $before -notcontains $_ })
    if ($new.Count -lt 1) { throw "Demo did not create a new run bundle." }
    $run = $new[0]

    & $python -m unchained verify-run $run
    if ($LASTEXITCODE -ne 0) { throw "Demo bundle verification failed for $run." }

    Write-Host ""
    Write-Host "DEMO PASSED: fail-closed run sealed a verifiable proof bundle" -ForegroundColor Green
    Write-Host "  - empty evidence was refused honestly (INVALID, exit 2) - zero OpenAI calls" -ForegroundColor Gray
    Write-Host "  - even the refusal was sealed, hash-chained, and offline-verified: VALID" -ForegroundColor Gray
    Write-Host "  (compatibility marker: DEMO_BUNDLE_VERIFIED_INVALID_INPUT)" -ForegroundColor DarkGray
    Write-Host "BUNDLE=$run"
}
finally {
    if (Test-Path $demoRoot) { Remove-Item $demoRoot -Recurse -Force }
}
