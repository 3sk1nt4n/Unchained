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

function Invoke-Dc01Verify {
    # Guided public practice case: verify a downloaded DC01 .zip by MD5, then onboard.
    Write-Info "Public DFIR Madness 001 case. Download it yourself; I verify the MD5."
    Write-Host "        https://dfirmadness.com/the-stolen-szechuan-sauce/" -ForegroundColor White
    Write-Host "      Publisher MD5s:  DC01-memory.zip = $($knownMd5['DC01-memory.zip'])" -ForegroundColor DarkGray
    Write-Host "                       DC01-E01.zip    = $($knownMd5['DC01-E01.zip'])" -ForegroundColor DarkGray
    if ((Read-Host "      Open the official download page now? (y/N)") -match '^[yY]') {
        Start-Process "https://dfirmadness.com/the-stolen-szechuan-sauce/"
    }
    $zip = (Read-Host "      Full path to a downloaded DC01 .zip (Enter to skip)").Trim().Trim('"').Trim()
    if (-not $zip) { return $null }
    if (-not (Test-Path -LiteralPath $zip -PathType Leaf) -or ($zip -notmatch '\.zip$')) {
        Write-Host "      Not a .zip file: $zip (skipping)." -ForegroundColor Yellow; return $null
    }
    $name = Split-Path $zip -Leaf
    Write-Info "Computing MD5 of $name (large file - please wait)..."
    $actual = $null
    try { $actual = (Get-FileHash -Algorithm MD5 -LiteralPath $zip).Hash.ToUpper() }
    catch { Write-Host "      Could not read that file: $($_.Exception.Message)" -ForegroundColor Yellow; return $null }
    $expected = $knownMd5[$name]
    if ($expected -and $actual -ne $expected) {
        Write-Host "      MD5 MISMATCH for $name" -ForegroundColor Red
        Write-Host "        expected $expected" -ForegroundColor Red
        Write-Host "        actual   $actual" -ForegroundColor Red
        Write-Host "      Do not use this download; re-fetch from the official page." -ForegroundColor Red
        return $null
    }
    if ($expected) { Write-Host "      MD5 VERIFIED for $name" -ForegroundColor Green }
    else { Write-Host "      No known MD5 for '$name' - extracting anyway." -ForegroundColor Yellow }
    New-Item -ItemType Directory -Force $evidenceDir | Out-Null
    Write-Info "Extracting into $evidenceDir ..."
    Expand-Archive -LiteralPath $zip -DestinationPath $evidenceDir -Force
    return $evidenceDir
}

function Find-Cases {
    # Shallow scan of common locations for folders that hold evidence images.
    $exts = @(".mem", ".raw", ".vmem", ".dmp", ".img", ".e01", ".dd")
    $roots = @("$env:USERPROFILE\Evidence", "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop")
    $hits = New-Object System.Collections.Generic.List[string]
    foreach ($r in $roots) {
        if (-not (Test-Path $r)) { continue }
        foreach ($d in (Get-ChildItem $r -Directory -ErrorAction SilentlyContinue)) {
            $img = Get-ChildItem $d.FullName -File -ErrorAction SilentlyContinue |
                Where-Object { ($exts -contains $_.Extension.ToLower()) -and $_.Length -gt 100MB } |
                Select-Object -First 1
            if ($img -and -not $hits.Contains($d.FullName)) { $hits.Add($d.FullName) }
        }
    }
    return ($hits | Select-Object -First 6)
}

# 2/5 - pick your first case, then see the verified card + depth options
Write-Step "2/5" "Pick your first case (you'll see a verified card next)"
$chosenCase = $null
try {
    $detected = @(Find-Cases)
    $i = 0
    if ($detected.Count -gt 0) {
        Write-Host "      Cases I found on your machine:" -ForegroundColor Gray
        foreach ($c in $detected) { $i++; Write-Host "        $i) $c" -ForegroundColor White }
    }
    Write-Host "        S) Built-in synthetic sample (instant, `$0)" -ForegroundColor White
    Write-Host "        D) DC01 public practice case (guided download + MD5 verify)" -ForegroundColor White
    Write-Host "        P) A folder path I'll type" -ForegroundColor White
    Write-Host "        W) Just show me the welcome" -ForegroundColor White
    $pick = (Read-Host "      Choose").Trim()
    if ($pick -match '^[0-9]+$' -and [int]$pick -ge 1 -and [int]$pick -le $detected.Count) {
        $chosenCase = $detected[[int]$pick - 1]
    }
    elseif ($pick -match '^[sS]$') { $chosenCase = (Join-Path $repo "docker\fixtures") }
    elseif ($pick -match '^[dD]$') { $chosenCase = Invoke-Dc01Verify }
    elseif ($pick -match '^[pP]$') {
        $chosenCase = (Read-Host "      Full path to your evidence folder").Trim().Trim('"').Trim()
        if ($chosenCase -and -not (Test-Path -LiteralPath $chosenCase)) {
            Write-Host "      Path not found: $chosenCase" -ForegroundColor Yellow; $chosenCase = $null
        }
    }
}
catch {
    Write-Host "      Case picker skipped ($($_.Exception.Message))." -ForegroundColor Yellow
    $chosenCase = $null
}

$caseReady = $false
if ($chosenCase) {
    & $sentinelExe onboard $chosenCase
    $caseReady = ($LASTEXITCODE -eq 0)
} else {
    & $sentinelExe onboard
}

# 3/5 - choose analysis depth (only meaningful if the case is launch-ready)
Write-Step "3/5" "Choose analysis depth"
$capsProfile = "strict"
if ($caseReady) {
    Write-Host "    LIGHT " -ForegroundColor Green -NoNewline
    Write-Host "- CAUTIOUS  20 tools / 100,000 tokens / 10 min / `$2.50 ceiling" -ForegroundColor White
    Write-Host "    HEAVY " -ForegroundColor Magenta -NoNewline
    Write-Host "- FLAGSHIP  60 tools / 400,000 tokens / 30 min / `$10 ceiling" -ForegroundColor White
    Write-Host "      Both run the same GPT-5.6 Sol investigator - this only sets ceilings." -ForegroundColor Gray
    if ((Read-Host "      Pick depth for your run (1=LIGHT default, 2=HEAVY)") -match '^2$') {
        $capsProfile = "default"
    }
    $depthName = if ($capsProfile -eq "default") { "HEAVY (FLAGSHIP)" } else { "LIGHT (CAUTIOUS)" }
    Write-Host "      Selected: $depthName" -ForegroundColor Cyan
} else {
    Write-Info "No launch-ready case selected yet - depth applies once you onboard real evidence."
}

# 4/5 - OpenAI key, asked LAST, right before it could be spent (hidden input)
Write-Step "4/5" "OpenAI key for paid runs (hidden, saved privately, found automatically)"
$keyStatus = & $sentinelExe key --status 2>$null | Out-String
if ($keyStatus -match "Key configured") {
    Write-Skip "a key is already configured"
} else {
    if ((Read-Host "      Set up your OpenAI key now with hidden input? (y/N)") -match '^[yY]') {
        & $sentinelExe key
        [Environment]::SetEnvironmentVariable("UNCHAINED_MODEL", "gpt-5.6", "User")
        $env:UNCHAINED_MODEL = "gpt-5.6"
    } else {
        Write-Info "Skipped - run 'sentinel key' any time. Everything so far stayed local and free."
    }
}

# 5/5 - optional guided launch (the LAUNCH GPT-5.6 SOL phrase is the real consent)
Write-Step "5/5" "Ready"
$keyStatus = & $sentinelExe key --status 2>$null | Out-String
if ($caseReady -and ($keyStatus -match "Key configured")) {
    if ((Read-Host "      Launch a real GPT-5.6 Sol investigation now? (y/N)") -match '^[yY]') {
        Write-Host "      You'll be asked to type the exact phrase LAUNCH GPT-5.6 SOL." -ForegroundColor Yellow
        & $sentinelExe onboard $chosenCase --launch --caps $capsProfile
    }
}
Write-Host ""
Write-Host "  One-word cheat sheet (any terminal):" -ForegroundColor Cyan
Write-Host "    sentinel onboard <case-folder>                       profile locally, `$0" -ForegroundColor White
Write-Host "    sentinel key --status                                confirm the saved key" -ForegroundColor White
Write-Host "    sentinel onboard <case> --launch --caps strict       LIGHT run" -ForegroundColor White
Write-Host "    sentinel onboard <case> --launch --caps default      HEAVY run" -ForegroundColor White
