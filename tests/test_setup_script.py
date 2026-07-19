"""Static safety and onboarding contract for the Windows installer."""

from pathlib import Path


def test_setup_is_fail_closed_and_hands_off_to_guided_onboarding() -> None:
    repository = Path(__file__).resolve().parents[1]
    script = (repository / "setup.ps1").read_text(encoding="utf-8")

    assert '$ExpectedPythonVersion = "3.11.9"' in script
    assert "Set-StrictMode -Version Latest" in script
    assert '$env:OS -ne "Windows_NT"' in script
    assert "LOCALAPPDATA is unavailable" in script
    assert "function Assert-NativeSuccess" in script
    assert script.count("Assert-NativeSuccess") >= 8
    assert "It does not read evidence, ask for an API key, or call OpenAI." in script
    assert "-m unchained onboard" in script
    assert "stops for an explicit choice before any funded GPT-5.6 Sol run" in script
    assert "OPENAI_API_KEY" not in script
    assert "platform.python_implementation()" in script
    assert 'struct.calcsize("P") * 8' in script
    assert '@("AMD64", "x86_64")' in script
    assert "-I -S -c" in script
    assert script.index("platform.python_implementation()") < script.index(
        "pip install -r requirements/bootstrap.txt"
    )
