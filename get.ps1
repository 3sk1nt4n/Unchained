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
Write-Host "|        Install -> pick a case -> add your key -> launch live.          |" -ForegroundColor Gray
Write-Host "+========================================================================+" -ForegroundColor Cyan
Write-Host ""
Write-Host "Never reads evidence or calls OpenAI on its own. A paid run always needs" -ForegroundColor Yellow
Write-Host "the exact phrase LAUNCH GPT-5.6 SOL. Every step is safe to re-run." -ForegroundColor Yellow
Write-Host ""

if ($env:OS -ne "Windows_NT") { throw "get.ps1 is Windows-only. Use get.sh with Docker on Linux/macOS." }

# Prerequisites: Python is required; Docker is only for the optional container lane.
Write-Step "0/4" "Checking prerequisites"
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
Write-Step "1/4" "Installing Unchained (pinned CPython 3.11 toolchain)"
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

function Expand-EvidenceZip {
    # Verify (when the MD5 is known) then extract one zip into $Dest.
    param([string]$Zip, [string]$Dest)
    if ($knownMd5.ContainsKey((Split-Path $Zip -Leaf))) {
        if (-not (Test-Md5 $Zip)) { return $false }
    }
    New-Item -ItemType Directory -Force $Dest | Out-Null
    Write-Info "Extracting $(Split-Path $Zip -Leaf) into $Dest ..."
    Expand-Archive -LiteralPath $Zip -DestinationPath $Dest -Force
    return $true
}

function Resolve-EvidenceFolder {
    # Turn ANY path - a .zip, a folder that holds zips, or an already-extracted
    # folder - into a launch-ready evidence folder. If a memory-image zip is
    # present, extract just that for a clean case (DC01's disk is a split EWF
    # that fails closed as two disks, and memory is where Volatility works).
    param([string]$Path)
    $Path = $Path.Trim().Trim('"').Trim()
    if (-not $Path) { return $null }
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "      Path not found: $Path" -ForegroundColor Yellow; return $null
    }

    # A single .zip file
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        if ($Path -inotmatch '\.zip$') {
            Write-Host "      Give a folder or a .zip file." -ForegroundColor Yellow; return $null
        }
        $dest = Join-Path $env:USERPROFILE ("Evidence\" + [IO.Path]::GetFileNameWithoutExtension($Path))
        if (Expand-EvidenceZip $Path $dest) { return $dest } else { return $null }
    }

    # A folder: are there zips to prepare, or already-extracted images?
    $zips = @(Get-ChildItem -LiteralPath $Path -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -ieq '.zip' })
    if ($zips.Count -gt 0) {
        $memZip = $zips | Where-Object { $_.Name -imatch 'memory|[-_]mem\b|[-_]mem\.' } | Select-Object -First 1
        if ($memZip) {
            Write-Host "      Found $($memZip.Name) - preparing a clean memory case." -ForegroundColor Cyan
            $dest = Join-Path $env:USERPROFILE "Evidence\dc01-mem"
            if (Expand-EvidenceZip $memZip.FullName $dest) { return $dest } else { return $null }
        }
        Write-Host "      Found $($zips.Count) zip(s) but no memory-image zip in that folder." -ForegroundColor Yellow
        if ((Read-Host "      Extract them all and try to onboard? (y/N)") -match '^[yY]') {
            $dest = Join-Path $env:USERPROFILE ("Evidence\" + (Split-Path $Path -Leaf) + "-prepared")
            $ok = $true
            foreach ($z in $zips) { if (-not (Expand-EvidenceZip $z.FullName $dest)) { $ok = $false } }
            if ($ok) { return $dest } else { return $null }
        }
        return $null
    }

    $img = Get-ChildItem -LiteralPath $Path -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -match '^\.(mem|raw|vmem|dmp|img|e01|dd)$' -and $_.Length -gt 200MB } |
        Select-Object -First 1
    if ($img) { return $Path }   # already-extracted evidence folder
    Write-Host "      No evidence images or zips found in $Path." -ForegroundColor Yellow
    return $null
}

function Get-CaseFolder {
    # One menu turn; return a resolved evidence folder, "" (re-loop), or "Q".
    Write-Host "        1) DC01 public practice case - guided download + MD5 verify" -ForegroundColor Cyan
    Write-Host "        2) Evidence I already have (a .zip, a folder of zips, or images)" -ForegroundColor Cyan
    Write-Host "        Q) Skip the guided run for now" -ForegroundColor DarkGray
    $pick = (Read-Host "      Choose 1, 2, or Q").Trim().Trim('"')
    if ($pick -match '^[qQ]$') { return "Q" }
    # If they pasted a path instead of a menu number, just use it.
    if ($pick -and (Test-Path -LiteralPath $pick)) {
        $c = Resolve-EvidenceFolder $pick
        if ($c) { return $c } else { return "" }
    }
    if ($pick -match '^1$') {
        Write-Info "Public DFIR Madness 001. You download it; I verify the MD5 and prep it."
        Write-Host "        https://dfirmadness.com/the-stolen-szechuan-sauce/" -ForegroundColor White
        Write-Host "      Publisher MD5s:  DC01-memory.zip = $($knownMd5['DC01-memory.zip'])" -ForegroundColor DarkGray
        Write-Host "                       DC01-E01.zip    = $($knownMd5['DC01-E01.zip'])" -ForegroundColor DarkGray
        if ((Read-Host "      Open the official download page now? (y/N)") -match '^[yY]') {
            Start-Process "https://dfirmadness.com/the-stolen-szechuan-sauce/"
        }
        $p = (Read-Host "      Path to DC01-memory.zip OR the folder that holds the DC01 zips (Enter to skip)")
        if (-not $p.Trim()) { return "" }
        $c = Resolve-EvidenceFolder $p
        if ($c) { return $c } else { return "" }
    }
    if ($pick -match '^2$') {
        $p = (Read-Host "      Path to your .zip, folder of zips, or evidence folder")
        if (-not $p.Trim()) { return "" }
        $c = Resolve-EvidenceFolder $p
        if ($c) { return $c } else { return "" }
    }
    return ""
}

# 2/4 - pick a case (loop until we have one, or Q to stop)
Write-Step "2/4" "Pick a case"
$chosenCase = $null
while (-not $chosenCase) {
    $candidate = ""
    try { $candidate = Get-CaseFolder }
    catch { Write-Host "      $($_.Exception.Message)" -ForegroundColor Yellow; $candidate = "" }
    if ($candidate -eq "Q") { break }
    if ($candidate) { $chosenCase = $candidate }
    else { Write-Host "      Let's try that again." -ForegroundColor Gray }
}
if (-not $chosenCase) {
    Write-Host ""
    Write-Host "  No case picked. Whenever you're ready, one word does everything:" -ForegroundColor Cyan
    Write-Host "    sentinel" -ForegroundColor White
    Write-Host "    (it asks for the case, the depth, and the launch phrase for you)" -ForegroundColor Gray
    return
}

# 3/4 - OpenAI key (hidden paste), before anything can be spent
Write-Step "3/4" "OpenAI key for the paid run (hidden input, saved privately)"
$keyStatus = & $sentinelExe key --status 2>$null | Out-String
while (-not ($keyStatus -match "Key configured")) {
    if ((Read-Host "      Paste your OpenAI key now with hidden input? (Y/n)") -match '^[nN]$') {
        Write-Info "No key, no paid run. Add one any time with: sentinel key"
        break
    }
    & $sentinelExe key
    [Environment]::SetEnvironmentVariable("UNCHAINED_MODEL", "gpt-5.6", "User")
    $env:UNCHAINED_MODEL = "gpt-5.6"
    $keyStatus = & $sentinelExe key --status 2>$null | Out-String
}
if ($keyStatus -match "Key configured") { Write-Skip "key configured; every command finds it" }

# 4/4 - pick the model, then the live run. onboard --launch shows the card,
# asks LIGHT/HEAVY (spending ceilings), takes the exact phrase, and runs live.
Write-Step "4/4" "Choose your model, then launch"
if ($keyStatus -match "Key configured") {
    Write-Host ""
    # Title rule only (fixed width, always aligns). The option lines below carry
    # double-width emoji, so they deliberately have NO right border - that avoids
    # the spill you get when emoji width pushes a fixed-width box out of line.
    Write-Host "   ┌─ HOW DO YOU WANT TO RUN? ──────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "   └────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "     1) " -ForegroundColor DarkCyan -NoNewline
    Write-Host "💚 REHEARSE  " -ForegroundColor Green -NoNewline
    Write-Host "gpt-5.6-luna" -ForegroundColor White -NoNewline
    Write-Host "   ~cents · practice, non-official" -ForegroundColor Gray
    Write-Host "     2) " -ForegroundColor DarkCyan -NoNewline
    Write-Host "⚡ REAL RUN  " -ForegroundColor Magenta -NoNewline
    Write-Host "gpt-5.6 Sol " -ForegroundColor White -NoNewline
    Write-Host "   costs more · official bundle" -ForegroundColor Gray
    Write-Host ""
    $modelPick = (Read-Host "   Pick 1 (rehearse - recommended first) or 2 (real Sol)").Trim()
    # No blanket cap override here: LIGHT stays an honest $2.50 / 100k-token
    # ceiling and HEAVY an honest $10 / 400k, so the case card never advertises
    # one ceiling and then enforces another. If a full lifecycle needs more, the
    # depth pick (HEAVY) or a deliberate MAX_TOTAL_TOKENS raise is the honest lever.
    if ($modelPick -eq "2") {
        [Environment]::SetEnvironmentVariable("UNCHAINED_ALLOW_TEST_MODEL", $null, "Process")
        $env:UNCHAINED_ALLOW_TEST_MODEL = $null
        $env:UNCHAINED_MODEL = "gpt-5.6"
        Write-Host "   ⚡ REAL Sol run selected - this produces your official bundle." -ForegroundColor Magenta
    } else {
        $env:UNCHAINED_ALLOW_TEST_MODEL = "1"
        $env:UNCHAINED_MODEL = "gpt-5.6-luna"
        Write-Host "   💚 REHEARSAL on Luna selected - cheap and clearly non-official." -ForegroundColor Green
    }
    Write-Host "   Next: the case card, a LIGHT/HEAVY spending pick, then type" -ForegroundColor Gray
    Write-Host "   the exact phrase " -ForegroundColor Gray -NoNewline
    Write-Host "LAUNCH GPT-5.6 SOL" -ForegroundColor Yellow -NoNewline
    Write-Host " to confirm the spend." -ForegroundColor Gray
    Write-Host ""
    & $sentinelExe onboard $chosenCase --launch --caps strict
} else {
    Write-Host "      Ready once you add a key. Then one word does everything:" -ForegroundColor Cyan
    Write-Host "        sentinel key" -ForegroundColor White
    Write-Host "        sentinel" -ForegroundColor White
}
