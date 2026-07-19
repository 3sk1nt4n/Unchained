# Unchained one-line bootstrap for Windows.
#   irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex
# Clones the repo, runs the pinned installer, optionally captures your OpenAI
# key with hidden input, guides the public practice case, and hands off to the
# guided onboarding. Every step is idempotent: re-running it detects work that
# is already done and skips it. It never echoes, logs, or uploads the key, and
# never fetches evidence for you.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Tag, [string]$Message)
    Write-Host "[$Tag] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message -ForegroundColor White
}
function Write-Skip {
    param([string]$Message)
    Write-Host "      " -NoNewline
    Write-Host "OK already done - $Message" -ForegroundColor Green
}

Write-Host ""
Write-Host "+========================================================================+" -ForegroundColor Cyan
Write-Host "|                               UNCHAINED                                |" -ForegroundColor White
Write-Host "|            Unchained reasoning. Chained evidence.                      |" -ForegroundColor Magenta
Write-Host "|      One command: install, prove health, walk into your first case.    |" -ForegroundColor Gray
Write-Host "+========================================================================+" -ForegroundColor Cyan
Write-Host ""
Write-Host "This bootstrap never reads evidence and never sends anything to OpenAI." -ForegroundColor Yellow
Write-Host "A paid run always requires the exact interactive phrase LAUNCH GPT-5.6 SOL." -ForegroundColor Yellow
Write-Host "Native Windows lane: only Python 3.11 is needed - no Docker required." -ForegroundColor Gray
Write-Host "Every step is safe to re-run - finished work is detected and skipped." -ForegroundColor Gray
Write-Host ""

if ($env:OS -ne "Windows_NT") {
    throw "get.ps1 supports Windows only. Use get.sh with Docker on Linux/macOS."
}
foreach ($tool in @("git", "py")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required tool '$tool' was not found. Install Git for Windows and CPython 3.11 AMD64, reopen PowerShell, and rerun."
    }
}

# 1/6 - repository
Write-Step "1/6" "Getting the repository"
if (Test-Path (Join-Path (Get-Location) "setup.ps1")) {
    $repo = (Get-Location).Path
    Write-Skip "using the current checkout: $repo"
}
else {
    $repo = Join-Path $env:USERPROFILE "Unchained"
    if (Test-Path (Join-Path $repo "setup.ps1")) {
        Write-Skip "reusing the existing checkout: $repo"
    }
    else {
        git clone https://github.com/3sk1nt4n/Unchained.git $repo
        if ($LASTEXITCODE -ne 0) { throw "git clone failed with exit code $LASTEXITCODE." }
    }
}
Set-Location $repo

# Resolve the sentinel launcher (installed exe or the PATH shim).
$sentinelExe = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311\Scripts\sentinel.exe"

# 2/6 - pinned isolated environment
Write-Step "2/6" "Installing the pinned CPython 3.11 toolchain (no key, no evidence)"
if (Test-Path $sentinelExe) {
    Write-Skip "toolchain already installed ($sentinelExe)"
}
else {
    powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
    if ($LASTEXITCODE -ne 0) { throw "setup.ps1 failed with exit code $LASTEXITCODE." }
}

# 3/6 - optional hidden key setup (delegated to the tested `sentinel key`)
Write-Step "3/6" "OpenAI key for paid runs (one-time hidden paste)"
$keyStatus = & $sentinelExe key --status 2>$null | Out-String
if ($keyStatus -match "Key configured") {
    Write-Skip "a key is already configured; every command finds it automatically"
}
else {
    Write-Host "      Paste once, saved privately, found automatically by every command." -ForegroundColor Gray
    Write-Host "      Press Enter on an empty prompt to skip and stay fully offline." -ForegroundColor Gray
    $doKey = Read-Host "      Set up your OpenAI key now? (Y/n)"
    if ($doKey -notmatch '^[nN]') {
        & $sentinelExe key
        [Environment]::SetEnvironmentVariable("UNCHAINED_MODEL", "gpt-5.6", "User")
        $env:UNCHAINED_MODEL = "gpt-5.6"
    }
    else {
        Write-Host "      Skipped. Everything below stays local and free." -ForegroundColor Green
    }
}

# 4/6 - the guided walk-in (shows the welcome + a real case card exactly once)
Write-Step "4/6" "Your guided walk-in (zero key, zero spend)"
Write-Host "      Profile the built-in synthetic sample now, or just see the welcome." -ForegroundColor Gray
$trySample = Read-Host "      Profile the built-in sample? (Y = yes / n = welcome only)"
if ($trySample -match '^[nN]') {
    & $sentinelExe onboard
}
else {
    & $sentinelExe onboard (Join-Path $repo "docker\fixtures")
}

# 5/6 - public practice case: guided download + MD5 verify + auto-onboard
Write-Step "5/6" "Public practice case (DFIR Madness 001 - optional)"
$evidenceDir = Join-Path $env:USERPROFILE "Evidence\dc01"
$knownMd5 = @{
    "DC01-memory.zip" = "64A4E2CB47138084A5C2878066B2D7B1"
    "DC01-E01.zip"    = "E57FC636E833C5F1AB58DFACE873BBDE"
}
if (Test-Path $evidenceDir) {
    $ready = Get-ChildItem $evidenceDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -gt 500MB }
    if ($ready) { Write-Skip "evidence already present in $evidenceDir" }
}
Write-Host "      Point me at evidence you already have - a downloaded DC01 .zip OR an" -ForegroundColor Gray
Write-Host "      evidence folder (memory/disk images). A .zip is MD5-verified first;" -ForegroundColor Gray
Write-Host "      a folder is onboarded directly. Unchained never fetches evidence for you." -ForegroundColor Gray
Write-Host "        Official page: https://dfirmadness.com/the-stolen-szechuan-sauce/" -ForegroundColor White
Write-Host "      Publisher MD5s:  DC01-memory.zip = $($knownMd5['DC01-memory.zip'])" -ForegroundColor DarkGray
Write-Host "                       DC01-E01.zip    = $($knownMd5['DC01-E01.zip'])" -ForegroundColor DarkGray
# This whole step is optional and must never crash the bootstrap.
try {
    $openCase = Read-Host "      Open the official download page in your browser now? (y/N)"
    if ($openCase -match '^[yY]') {
        Start-Process "https://dfirmadness.com/the-stolen-szechuan-sauce/"
    }
    $evPath = ""
    $haveEv = Read-Host "      Onboard evidence now - a .zip or an evidence folder? (y/N)"
    if ($haveEv -match '^[yY]') {
        $evPath = (Read-Host "      Paste the full path (e.g. C:\Users\You\Downloads\DC01-memory.zip or a folder)").Trim().Trim('"').Trim()
    }
    if (-not $evPath) {
        Write-Host "      Skipped - onboard any time with: sentinel onboard <folder>" -ForegroundColor Green
    }
    elseif (Test-Path -LiteralPath $evPath -PathType Container) {
        Write-Host "      Folder detected - onboarding it directly (local, `$0)..." -ForegroundColor Gray
        & $sentinelExe onboard $evPath
    }
    elseif ((Test-Path -LiteralPath $evPath -PathType Leaf) -and ($evPath -match '\.zip$')) {
        $name = Split-Path $evPath -Leaf
        Write-Host "      Computing MD5 of $name (large file - please wait)..." -ForegroundColor Gray
        $actual = $null
        try { $actual = (Get-FileHash -Algorithm MD5 -LiteralPath $evPath).Hash.ToUpper() }
        catch { Write-Host "      Could not read that file: $($_.Exception.Message)" -ForegroundColor Yellow }
        $expected = $knownMd5[$name]
        if ($actual -and $expected -and $actual -eq $expected) {
            Write-Host "      MD5 VERIFIED for $name ($actual)" -ForegroundColor Green
            New-Item -ItemType Directory -Force $evidenceDir | Out-Null
            Write-Host "      Extracting into $evidenceDir ..." -ForegroundColor Gray
            Expand-Archive -LiteralPath $evPath -DestinationPath $evidenceDir -Force
            Write-Host "      Onboarding the verified case (local, `$0)..." -ForegroundColor Gray
            & $sentinelExe onboard $evidenceDir
        }
        elseif ($actual -and $expected) {
            Write-Host "      MD5 MISMATCH for $name" -ForegroundColor Red
            Write-Host "        expected $expected" -ForegroundColor Red
            Write-Host "        actual   $actual" -ForegroundColor Red
            Write-Host "      Do not use this download; re-fetch from the official page." -ForegroundColor Red
        }
        elseif ($actual) {
            Write-Host "      No known MD5 for '$name'. Extracting and onboarding anyway..." -ForegroundColor Yellow
            New-Item -ItemType Directory -Force $evidenceDir | Out-Null
            Expand-Archive -LiteralPath $evPath -DestinationPath $evidenceDir -Force
            & $sentinelExe onboard $evidenceDir
        }
    }
    else {
        Write-Host "      Not a folder or a .zip file: $evPath (skipping)." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "      Practice-case step skipped ($($_.Exception.Message))." -ForegroundColor Yellow
    Write-Host "      No problem - onboard any time with: sentinel onboard <folder>" -ForegroundColor Green
}

# 6/6 - you're ready
Write-Step "6/6" "You're ready - here's your one-word cheat sheet"
Write-Host ""
Write-Host "  sentinel onboard <case-folder>       profile one case locally, `$0" -ForegroundColor White
Write-Host "  sentinel onboard $evidenceDir      the public practice case, `$0" -ForegroundColor White
Write-Host "  sentinel key --status                confirm the saved key" -ForegroundColor White
Write-Host ""
Write-Host "  Ready for a real investigation? Pick a depth and launch:" -ForegroundColor Cyan
Write-Host "    LIGHT  " -ForegroundColor Green -NoNewline
Write-Host "sentinel onboard <case> --launch --caps strict   (20 tools / `$2.50 ceiling)" -ForegroundColor White
Write-Host "    HEAVY  " -ForegroundColor Magenta -NoNewline
Write-Host "sentinel onboard <case> --launch --caps default  (60 tools / `$10 ceiling)" -ForegroundColor White
Write-Host "    Both run GPT-5.6 Sol; you then type LAUNCH GPT-5.6 SOL to confirm." -ForegroundColor Gray
