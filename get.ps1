# Unchained one-line bootstrap for Windows (native lane - no Docker needed).
#   irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex
# Guided, Qwen-style flow: install -> pick a case -> see the verified card ->
# pick a depth -> paste your key (hidden, last) -> optionally launch. Every
# step is idempotent and safe to re-run. It never echoes, logs, or uploads the
# key, and never fetches evidence for you.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Tag, [string]$Message)
    Write-Host "[$Tag] " -ForegroundColor Cyan -NoNewline; Write-Host $Message -ForegroundColor White }
function Write-Skip { param([string]$Message)
    Write-Host "      OK already done - $Message" -ForegroundColor Green }
function Write-Info { param([string]$Message)
    Write-Host "      $Message" -ForegroundColor Gray }

Write-Host ""
Write-Host "+========================================================================+" -ForegroundColor Cyan
Write-Host "|                               UNCHAINED                                |" -ForegroundColor White
Write-Host "|            Unchained reasoning. Chained evidence.                      |" -ForegroundColor Magenta
Write-Host "|   Install -> pick a case -> see the card -> pick depth -> launch.      |" -ForegroundColor Gray
Write-Host "+========================================================================+" -ForegroundColor Cyan
Write-Host ""
Write-Host "Never reads evidence or calls OpenAI on its own. A paid run always needs" -ForegroundColor Yellow
Write-Host "the exact phrase LAUNCH GPT-5.6 SOL. Every step is safe to re-run." -ForegroundColor Yellow
Write-Host ""

if ($env:OS -ne "Windows_NT") { throw "get.ps1 is Windows-only. Use get.sh with Docker on Linux/macOS." }

# Prerequisites: Python is required; Docker is only for the optional container lane.
Write-Step "0/5" "Checking prerequisites"
foreach ($tool in @("git", "py")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required tool '$tool' was not found. Install Git for Windows and CPython 3.11 AMD64, reopen PowerShell, and rerun."
    }
}
Write-Info "Python launcher and Git found."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Info "Docker detected (optional - only used for the isolated container lane)."
} else {
    Write-Info "Docker not found - not needed for this native Windows lane."
}

# 1/5 - repository + pinned toolchain
Write-Step "1/5" "Installing Unchained (pinned CPython 3.11 toolchain)"
if (Test-Path (Join-Path (Get-Location) "setup.ps1")) {
    $repo = (Get-Location).Path
} else {
    $repo = Join-Path $env:USERPROFILE "Unchained"
    if (-not (Test-Path (Join-Path $repo "setup.ps1"))) {
        git clone https://github.com/3sk1nt4n/Unchained.git $repo
        if ($LASTEXITCODE -ne 0) { throw "git clone failed with exit code $LASTEXITCODE." }
    }
}
Set-Location $repo
$sentinelExe = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
if (Test-Path $sentinelExe) {
    Write-Skip "toolchain already installed"
} else {
    powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
    if ($LASTEXITCODE -ne 0) { throw "setup.ps1 failed with exit code $LASTEXITCODE." }
}

$knownMd5 = @{
    "DC01-memory.zip" = "64A4E2CB47138084A5C2878066B2D7B1"
    "DC01-E01.zip"    = "E57FC636E833C5F1AB58DFACE873BBDE"
}
$evidenceDir = Join-Path $env:USERPROFILE "Evidence\dc01"

function Test-Md5 {
    param([string]$Zip)
    $name = Split-Path $Zip -Leaf
    $expected = $knownMd5[$name]
    Write-Info "Verifying MD5 of $name (large file - please wait)..."
    $actual = $null
    try { $actual = (Get-FileHash -Algorithm MD5 -LiteralPath $Zip).Hash.ToUpper() }
    catch { Write-Host "      Could not read that file: $($_.Exception.Message)" -ForegroundColor Yellow; return $false }
    if ($expected -and $actual -ne $expected) {
        Write-Host "      MD5 MISMATCH for $name" -ForegroundColor Red
        Write-Host "        expected $expected" -ForegroundColor Red
        Write-Host "        actual   $actual" -ForegroundColor Red
        Write-Host "      Do not use this download; re-fetch from the official page." -ForegroundColor Red
        return $false
    }
    if ($expected) { Write-Host "      MD5 VERIFIED for $name" -ForegroundColor Green }
    return $true
}

function Get-Dc01Case {
    # Turn a downloaded DC01 zip, a folder that holds the zips, or an extracted
    # folder into a launch-ready MEMORY-ONLY case. DC01's disk ships as a split
    # EWF (E01+E02) that fails closed as two disks, so the clean path is the
    # memory image - which is where Volatility works anyway.
    Write-Info "Public DFIR Madness 001 case. You download it; I verify the MD5 and prep it."
    Write-Host "        https://dfirmadness.com/the-stolen-szechuan-sauce/" -ForegroundColor White
    Write-Host "      Publisher MD5s:  DC01-memory.zip = $($knownMd5['DC01-memory.zip'])" -ForegroundColor DarkGray
    Write-Host "                       DC01-E01.zip    = $($knownMd5['DC01-E01.zip'])" -ForegroundColor DarkGray
    if ((Read-Host "      Open the official download page now? (y/N)") -match '^[yY]') {
        Start-Process "https://dfirmadness.com/the-stolen-szechuan-sauce/"
    }
    $path = (Read-Host "      Path to DC01-memory.zip, OR a folder that holds the DC01 zips (Enter to skip)").Trim().Trim('"').Trim()
    if (-not $path) { return $null }
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host "      Path not found: $path" -ForegroundColor Yellow; return $null
    }
    $memZip = $null
    if (Test-Path -LiteralPath $path -PathType Container) {
        # A folder: prefer the memory zip; else any extracted memory image is fine as-is.
        $memZip = Get-ChildItem -LiteralPath $path -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ieq "DC01-memory.zip" } | Select-Object -First 1
        if (-not $memZip) {
            $img = Get-ChildItem -LiteralPath $path -File -Recurse -ErrorAction SilentlyContinue |
                Where-Object { $_.Extension -match '^\.(mem|raw|vmem|dmp|img)$' -and $_.Length -gt 200MB } |
                Select-Object -First 1
            if ($img) { Write-Info "Using the extracted evidence folder directly."; return $path }
            Write-Host "      No DC01-memory.zip or memory image found in that folder." -ForegroundColor Yellow
            return $null
        }
        $memZip = $memZip.FullName
    }
    elseif ($path -imatch '\.zip$') { $memZip = $path }
    else { Write-Host "      Not a .zip or a folder: $path" -ForegroundColor Yellow; return $null }

    if (-not (Test-Md5 $memZip)) { return $null }
    $memDir = Join-Path $env:USERPROFILE "Evidence\dc01-mem"
    New-Item -ItemType Directory -Force $memDir | Out-Null
    Write-Info "Extracting the memory image into $memDir ..."
    Expand-Archive -LiteralPath $memZip -DestinationPath $memDir -Force
    Write-Host "      DC01 memory case ready (disk is a split EWF; memory is the clean route)." -ForegroundColor Green
    return $memDir
}

function Get-CaseFolder {
    # One menu turn; return a candidate evidence folder path or "" (re-loop) or "Q".
    Write-Host "        1) DC01 public practice case - guided download + MD5 verify" -ForegroundColor Cyan
    Write-Host "        2) My own evidence folder (a path I'll type)" -ForegroundColor Cyan
    Write-Host "        Q) Skip the guided run for now" -ForegroundColor DarkGray
    $pick = (Read-Host "      Choose 1, 2, or Q").Trim()
    if ($pick -match '^[qQ]$') { return "Q" }
    if ($pick -match '^1$') { $c = Get-Dc01Case; if ($c) { return $c } else { return "" } }
    if ($pick -match '^2$') {
        $c = (Read-Host "      Full path to your evidence folder").Trim().Trim('"').Trim()
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
        Write-Host "      Path not found: $c" -ForegroundColor Yellow; return ""
    }
    return ""
}

# 2/5 - pick a case and keep going until one is launch-ready (or you choose Q)
Write-Step "2/5" "Pick a case"
$chosenCase = $null
while (-not $chosenCase) {
    $candidate = ""
    try { $candidate = Get-CaseFolder }
    catch { Write-Host "      $($_.Exception.Message)" -ForegroundColor Yellow; $candidate = "" }
    if ($candidate -eq "Q") { break }
    if (-not $candidate) { Write-Host "      Let's try that again." -ForegroundColor Gray; continue }
    Write-Host ""
    & $sentinelExe onboard $candidate            # shows the verified card
    if ($LASTEXITCODE -eq 0) {
        $chosenCase = $candidate
    } else {
        Write-Host "      That case is not launch-ready (see the card above). Pick another." -ForegroundColor Yellow
    }
}

if (-not $chosenCase) {
    Write-Step "3/5" "Skipped the guided run"
    Write-Host ""
    Write-Host "  Whenever you're ready (one word, any terminal):" -ForegroundColor Cyan
    Write-Host "    sentinel onboard <case-folder>                       profile locally, `$0" -ForegroundColor White
    Write-Host "    sentinel onboard <case> --launch --caps strict       LIGHT run" -ForegroundColor White
    Write-Host "    sentinel onboard <case> --launch --caps default      HEAVY run" -ForegroundColor White
    return
}

# 3/5 - choose analysis depth
Write-Step "3/5" "Choose analysis depth (model is GPT-5.6 Sol either way)"
Write-Host "    1) LIGHT " -ForegroundColor Green -NoNewline
Write-Host "- CAUTIOUS  20 tools / 100,000 tokens / 10 min / `$2.50 ceiling" -ForegroundColor White
Write-Host "    2) HEAVY " -ForegroundColor Magenta -NoNewline
Write-Host "- FLAGSHIP  60 tools / 400,000 tokens / 30 min / `$10 ceiling" -ForegroundColor White
$capsProfile = "strict"
if ((Read-Host "      Pick depth (1=LIGHT default, 2=HEAVY)") -match '^2$') { $capsProfile = "default" }
$depthName = if ($capsProfile -eq "default") { "HEAVY (FLAGSHIP)" } else { "LIGHT (CAUTIOUS)" }
Write-Host "      Selected: $depthName on GPT-5.6 Sol" -ForegroundColor Cyan

# 4/5 - OpenAI key, right before it could be spent (hidden input)
Write-Step "4/5" "OpenAI key for the paid run (hidden input, saved privately)"
$keyStatus = & $sentinelExe key --status 2>$null | Out-String
while (-not ($keyStatus -match "Key configured")) {
    if ((Read-Host "      Paste your OpenAI key now with hidden input? (Y/n)") -match '^[nN]$') {
        Write-Info "No key, no paid run. Set one any time with: sentinel key"
        break
    }
    & $sentinelExe key
    [Environment]::SetEnvironmentVariable("UNCHAINED_MODEL", "gpt-5.6", "User")
    $env:UNCHAINED_MODEL = "gpt-5.6"
    $keyStatus = & $sentinelExe key --status 2>$null | Out-String
}
if ($keyStatus -match "Key configured") { Write-Skip "key configured; every command finds it" }

# 5/5 - the live run (the LAUNCH GPT-5.6 SOL phrase is the real consent)
Write-Step "5/5" "Launch the live investigation"
if ($keyStatus -match "Key configured") {
    Write-Host "      $depthName on $chosenCase" -ForegroundColor Gray
    Write-Host "      You'll type the exact phrase LAUNCH GPT-5.6 SOL to confirm the spend." -ForegroundColor Yellow
    if ((Read-Host "      Launch now and watch it live? (Y/n)") -notmatch '^[nN]$') {
        & $sentinelExe onboard $chosenCase --launch --caps $capsProfile
    } else {
        Write-Host "      Ready when you are:" -ForegroundColor Cyan
        Write-Host "        sentinel onboard `"$chosenCase`" --launch --caps $capsProfile" -ForegroundColor White
    }
} else {
    Write-Host "      Ready once you add a key:" -ForegroundColor Cyan
    Write-Host "        sentinel key" -ForegroundColor White
    Write-Host "        sentinel onboard `"$chosenCase`" --launch --caps $capsProfile" -ForegroundColor White
}
