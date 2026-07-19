"""Static guards for the one-line bootstrap scripts."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def test_windows_bootstrap_is_key_safe_and_hands_off_to_onboarding() -> None:
    script = (_REPO / "get.ps1").read_text(encoding="utf-8")

    assert "Read-Host" in script and "-AsSecureString" in script
    assert "icacls" in script
    assert "OPENAI_API_KEY_FILE" in script
    assert "UNCHAINED_MODEL" in script
    assert "setup.ps1" in script
    assert "sentinel.exe" in script or "sentinel onboard" in script
    assert "LAUNCH GPT-5.6 SOL" in script

    # The captured key must never be echoed or interpolated into output.
    assert not re.search(r"Write-Host[^\n]*\$plainKey", script)
    assert not re.search(r"Write-Host[^\n]*\$secureKey", script)
    # No hardcoded provider credential shape anywhere.
    assert not re.search(r"sk-[A-Za-z0-9]{10,}", script)
    # The zeroing/free path for the secure string must exist.
    assert "ZeroFreeBSTR" in script
    # Samples: the built-in fixture is offered, the public case is guided —
    # and evidence is never auto-downloaded by the bootstrap.
    assert "docker\\fixtures" in script
    assert "dfirmadness.com/the-stolen-szechuan-sauce" in script
    assert not re.search(r"(Invoke-WebRequest|Start-BitsTransfer|curl)[^\n]*dfirmadness", script)


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
