# Unchained one-line bootstrap for Windows.
#   irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex
# Clones the repo, runs the pinned installer, optionally captures your OpenAI
# key with hidden input, and hands off to the guided onboarding.
# It never echoes, logs, or uploads the key, and never reads evidence.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Tag, [string]$Message)
    Write-Host "[$Tag] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message -ForegroundColor White
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
Write-Host ""

if ($env:OS -ne "Windows_NT") {
    throw "get.ps1 supports Windows only. Use get.sh with Docker on Linux/macOS."
}
foreach ($tool in @("git", "py")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required tool '$tool' was not found. Install Git for Windows and CPython 3.11 AMD64, reopen PowerShell, and rerun."
    }
}

# 1/4 - repository
Write-Step "1/4" "Getting the repository"
if (Test-Path (Join-Path (Get-Location) "setup.ps1")) {
    $repo = (Get-Location).Path
    Write-Host "      Using the current checkout: $repo" -ForegroundColor Gray
}
else {
    $repo = Join-Path $env:USERPROFILE "Unchained"
    if (-not (Test-Path (Join-Path $repo "setup.ps1"))) {
        git clone https://github.com/3sk1nt4n/Unchained.git $repo
        if ($LASTEXITCODE -ne 0) { throw "git clone failed with exit code $LASTEXITCODE." }
    }
    else {
        Write-Host "      Reusing the existing checkout: $repo" -ForegroundColor Gray
    }
}
Set-Location $repo

# 2/4 - pinned isolated environment
Write-Step "2/4" "Installing the pinned CPython 3.11 toolchain (no key, no evidence)"
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
if ($LASTEXITCODE -ne 0) { throw "setup.ps1 failed with exit code $LASTEXITCODE." }

# 3/4 - optional hidden key capture
Write-Step "3/4" "Optional: store your OpenAI key for live runs (hidden input)"
Write-Host "      The key is written to a private local file and referenced through" -ForegroundColor Gray
Write-Host "      OPENAI_API_KEY_FILE. It is never echoed, never committed, never logged." -ForegroundColor Gray
Write-Host "      Press Enter on an empty prompt to skip and stay fully offline." -ForegroundColor Gray
$secureKey = Read-Host "      Paste key (input stays hidden)" -AsSecureString
if ($secureKey.Length -gt 0) {
    $keyDirectory = Join-Path $env:LOCALAPPDATA "sentinel-unchained"
    $keyFile = Join-Path $keyDirectory "openai_api_key"
    New-Item -ItemType Directory -Force $keyDirectory | Out-Null
    $marshal = [System.Runtime.InteropServices.Marshal]
    $pointer = $marshal::SecureStringToBSTR($secureKey)
    try {
        $plainKey = $marshal::PtrToStringBSTR($pointer)
        [System.IO.File]::WriteAllText($keyFile, $plainKey.Trim() + "`n")
        $plainKey = $null
    }
    finally {
        $marshal::ZeroFreeBSTR($pointer)
    }
    icacls $keyFile /inheritance:r /grant:r "${env:USERNAME}:(R,W)" | Out-Null
    [Environment]::SetEnvironmentVariable("OPENAI_API_KEY_FILE", $keyFile, "User")
    [Environment]::SetEnvironmentVariable("UNCHAINED_MODEL", "gpt-5.6", "User")
    $env:OPENAI_API_KEY_FILE = $keyFile
    $env:UNCHAINED_MODEL = "gpt-5.6"
    Write-Host "      Saved to $keyFile (owner-only ACL); OPENAI_API_KEY_FILE set." -ForegroundColor Green
    Write-Host "      Model pinned to gpt-5.6 (Sol investigator). The cheap Luna canary" -ForegroundColor Gray
    Write-Host "      is available any time via: sentinel smoke-openai" -ForegroundColor Gray
}
else {
    Write-Host "      Skipped. Everything below stays local and free." -ForegroundColor Green
}

# 4/5 - ready-made samples
Write-Step "4/5" "Ready-made samples"
$sentinel = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
Write-Host "      A safe synthetic sample ships in the repo - no download, no key, no spend." -ForegroundColor Gray
$trySample = Read-Host "      Profile the built-in sample now? (Y/n)"
if ($trySample -notmatch '^[nN]') {
    & $sentinel onboard (Join-Path $repo "docker\fixtures")
}
Write-Host ""
Write-Host "      Real practice case: DFIR Madness 001 'The Stolen Szechuan Sauce'" -ForegroundColor Gray
Write-Host "      (public Windows memory + disk images; download it yourself from the" -ForegroundColor Gray
Write-Host "      official page - Unchained never fetches evidence for you):" -ForegroundColor Gray
Write-Host "        https://dfirmadness.com/the-stolen-szechuan-sauce/" -ForegroundColor White
Write-Host "      Publisher's MD5 checksums for the core files (verify your download;" -ForegroundColor Gray
Write-Host "      Unchained then takes SHA-256 custody itself during onboarding):" -ForegroundColor Gray
Write-Host "        DC01-memory.zip  64A4E2CB47138084A5C2878066B2D7B1" -ForegroundColor DarkGray
Write-Host "        DC01-E01.zip     E57FC636E833C5F1AB58DFACE873BBDE" -ForegroundColor DarkGray
$evidenceDir = Join-Path $env:USERPROFILE "Evidence\dc01"
Write-Host "      Suggested extract location: $evidenceDir" -ForegroundColor Gray
$openCase = Read-Host "      Open the official case page in your browser now? (y/N)"
if ($openCase -match '^[yY]') {
    New-Item -ItemType Directory -Force $evidenceDir | Out-Null
    Start-Process "https://dfirmadness.com/the-stolen-szechuan-sauce/"
}

# 5/5 - guided onboarding
Write-Step "5/5" "Opening the guided onboarding (zero-key, zero-spend welcome)"
& $sentinel onboard
Write-Host ""
Write-Host "Next moves:" -ForegroundColor Cyan
Write-Host "  sentinel onboard <one-case-evidence-folder>          local case card, `$0" -ForegroundColor White
Write-Host "  sentinel onboard $evidenceDir       the public practice case" -ForegroundColor White
Write-Host "  sentinel smoke-openai                                cheap Luna canary" -ForegroundColor White
Write-Host "  sentinel onboard <evidence> --launch --caps strict   LIGHT - CAUTIOUS ceilings" -ForegroundColor White
Write-Host "  sentinel onboard <evidence> --launch --caps default  HEAVY - FLAGSHIP ceilings" -ForegroundColor White
