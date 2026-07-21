"""Static guards for the one-line bootstrap scripts."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def test_windows_bootstrap_is_key_safe_and_hands_off_to_onboarding() -> None:
    script = (_REPO / "get.ps1").read_text(encoding="utf-8")

    # Key setup is delegated to the tested, hidden-input `sentinel key` command,
    # not re-implemented inline. The bootstrap must not capture the raw key.
    assert "key --status" in script
    assert "sentinel key" in script or "$sentinelExe key" in script
    assert "UNCHAINED_MODEL" in script
    assert "setup.ps1" in script
    assert "sentinel.exe" in script or "sentinel onboard" in script
    assert "1 = quick Terra test" in script

    # No inline plaintext key handling and no hardcoded credential shape.
    assert "PtrToStringBSTR" not in script
    assert not re.search(r"sk-[A-Za-z0-9]{10,}", script)
    # Samples: the built-in fixture is offered, the public case is guided —
    # and evidence is never auto-downloaded by the bootstrap.
    assert "dfirmadness.com/the-stolen-szechuan-sauce" in script
    assert not re.search(r"(Invoke-WebRequest|Start-BitsTransfer|curl)[^\n]*dfirmadness", script)
    # DC01 is verify-and-onboard, never a hardcoded download: MD5 check gates it.
    assert "Get-FileHash -Algorithm MD5" in script
    assert "64A4E2CB47138084A5C2878066B2D7B1" in script
    assert "MD5 MISMATCH" in script
    # Idempotency without staleness: finished steps are detected (Write-Skip),
    # but the install ALWAYS runs so a freshly cloned/pulled fix reaches the venv
    # instead of an old installed copy silently persisting.
    assert "function Write-Skip" in script
    assert "ALWAYS (re)install" in script
    # The clone update must route git's stderr through cmd.exe (Windows
    # PowerShell 5.1 + EAP Stop otherwise dies on fetch progress) and must
    # recover a diverged clone instead of stranding the user on stale code.
    assert 'pull --quiet --ff-only >nul 2>&1"' in script
    assert "reset --quiet --hard origin/main" in script


def test_posix_bootstrap_is_key_safe_and_uses_the_offline_lane() -> None:
    script = (_REPO / "get.sh").read_text(encoding="utf-8")

    assert script.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in script
    assert "read -rs KEY" in script
    assert "chmod 600" in script
    assert "umask 177" in script
    assert "OPENAI_API_KEY_FILE" in script
    assert "docker compose build" in script
    assert "docker compose run --rm offline" in script

    # The captured key must never be echoed back; the only allowed use of the
    # variable in an output command is the redirected write into the key file.
    assert not re.search(r"echo[^\n]*\$KEY\b", script)
    assert not re.search(r"printf[^\n]*\$KEY\b(?![^\n]*>)", script)
    assert not re.search(r"sk-[A-Za-z0-9]{10,}", script)
    # NO_COLOR and non-tty streams must disable color.
    assert "NO_COLOR" in script
    # Samples: fixture lane offered, public case guided, never auto-downloaded.
    assert "profile /evidence" in script
    assert "dfirmadness.com/the-stolen-szechuan-sauce" in script
    assert not re.search(r"(curl|wget)[^\n]*dfirmadness", script)
    # One-word command shim for the offline lane.
    assert ".local/bin" in script
    assert "chmod +x" in script
    # Idempotency: prebuilt image and existing key file are detected and skipped.
    assert "docker image inspect" in script
    assert "skip()" in script
