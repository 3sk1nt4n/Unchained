# unchained.ps1 - one command that walks you through a whole case.
#
# This is the friendly front door: it finds the isolated toolchain that
# setup.ps1 created, then hands off to the self-driving `sentinel` flow
# (welcome -> one question -> verified card -> depth -> explicit launch ->
# live run -> verify/view). No flags, no environment variables to set.
#
# First time here?  Run  .\setup.ps1  once (installs + verifies everything),
# then run  .\unchained.ps1  to start.  Any extra arguments are passed straight
# through to sentinel (e.g.  .\unchained.ps1 verify <bundle>).
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassThruArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    Write-Host "unchained.ps1 is the Windows launcher. On Linux/macOS use ./unchained.sh (Docker path)." -ForegroundColor Yellow
    exit 2
}

$venv = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311"
$sentinelExe = Join-Path $venv "Scripts\sentinel.exe"

# Prefer the isolated venv entry point; fall back to a `sentinel` already on PATH
# (the setup.ps1 shim), so this works in a fresh shell right after install.
if (Test-Path $sentinelExe) {
    $launcher = $sentinelExe
}
elseif (Get-Command sentinel -ErrorAction SilentlyContinue) {
    $launcher = "sentinel"
}
else {
    Write-Host ""
    Write-Host "Unchained is not installed yet. One command sets it up:" -ForegroundColor Yellow
    Write-Host "  .\setup.ps1" -ForegroundColor White
    Write-Host "Then run  .\unchained.ps1  again to start your first case." -ForegroundColor Gray
    exit 2
}

# No arguments = the self-driving guided flow. Extra args pass through verbatim.
if ($PassThruArgs -and $PassThruArgs.Count -gt 0) {
    & $launcher @PassThruArgs
}
else {
    & $launcher
}
exit $LASTEXITCODE
