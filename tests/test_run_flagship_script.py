"""Safe flagship PowerShell wrapper tests using its non-executable fixture seam."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is unavailable")

EXPECTED_SHA256 = "8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62"
EXPECTED_BYTES = 2_147_483_648
EXPECTED_LOCK_SHA256 = "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7"
FREEZE_COMMIT = "a" * 40
PRIVATE_SENTINELS = (
    "PRIVATE_EVIDENCE_DIRECTORY",
    "PRIVATE_OPENAI_KEY_FILE",
    "PRIVATE_OUTPUT_DIRECTORY",
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture_directory(
    tmp_path: Path,
    *,
    evidence_sha256: str = EXPECTED_SHA256,
    evidence_bytes: int = EXPECTED_BYTES,
    lock_sha256: str = EXPECTED_LOCK_SHA256,
    installed_versions_match: bool = True,
) -> Path:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    write_json(
        fixture / "python.json",
        {"implementation": "CPython", "version": "3.11.9", "version_info": [3, 11, 9]},
    )
    write_json(
        fixture / "dependency-lock.json",
        {
            "path": "requirements/pylock.windows-amd64-cp311.toml",
            "sha256": lock_sha256,
            "target": "windows-amd64-cp311",
            "installed_versions_match": installed_versions_match,
        },
    )
    write_json(
        fixture / "doctor.json",
        {
            "ready_for_live_run": True,
            "configured_model": "gpt-5.6",
            "openai_api_key_source": "file",
            "python": "3.11.9",
            "secrets_printed": False,
        },
    )
    profile = {
        "os": "windows",
        "shape": "memory-only",
        "hashes": {"E001": evidence_sha256},
        "health": {"E001": "ready"},
        "symbols": {"E001": "ready"},
        "evidence": [
            {
                "evidence_id": "E001",
                "kind": "memory",
                "size": evidence_bytes,
                "os_hint": "windows",
                "available": True,
                "health": "ready",
                "symbols": "ready",
                "sha256": evidence_sha256,
            }
        ],
    }
    write_json(
        fixture / "profile.json",
        {
            "profile": profile,
            "custody": {"match": True, "hashes": {"E001": evidence_sha256}},
            "openai_called": False,
        },
    )
    write_json(
        fixture / "caps.json",
        {
            "profile": "default",
            "max_tool_calls": 60,
            "max_total_tokens": 400_000,
            "max_wall_seconds": 1_800.0,
            "max_cost_usd": 10.0,
        },
    )
    write_json(
        fixture / "git.json",
        {
            "clean": True,
            "head": FREEZE_COMMIT,
            "freeze_tag": "experiment-freeze-v1",
            "tag_commit": FREEZE_COMMIT,
        },
    )
    return fixture


def run_script(repo: Path, fixture: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    assert POWERSHELL is not None
    command = [
        POWERSHELL,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(repo / "scripts" / "run_flagship.ps1"),
        "-EvidenceDirectory",
        PRIVATE_SENTINELS[0],
        "-OpenAIKeyFile",
        PRIVATE_SENTINELS[1],
        "-OutputDirectory",
        PRIVATE_SENTINELS[2],
        "-TestFixtureDirectory",
        str(fixture),
        *extra,
    ]
    return subprocess.run(
        command,
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_flagship_fixture_preflight_is_sanitized_and_never_executes(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = run_script(repo, fixture_directory(tmp_path))
    combined = result.stdout + result.stderr

    assert result.returncode == 0, combined
    assert "Runtime: CPython 3.11.9" in combined
    assert "Model request: gpt-5.6" in combined
    assert (
        "Dependency lock: requirements/pylock.windows-amd64-cp311.toml; "
        f"sha256={EXPECTED_LOCK_SHA256}" in combined
    )
    assert "windows / memory-only / E001 / health ready / symbols ready" in combined
    assert EXPECTED_SHA256 in combined
    assert f"Evidence bytes: {EXPECTED_BYTES}" in combined
    assert (
        f"Freeze gate: tag=experiment-freeze-v1; commit={FREEZE_COMMIT}; worktree=clean"
    ) in combined
    assert (
        "Frozen bounded caps: tools=60; total_tokens=400000; wall_seconds=1800; max_cost_usd=10"
    ) in combined
    assert "no evidence, credential, or model was accessed" in combined
    assert all(value not in combined for value in PRIVATE_SENTINELS)
    script = (repo / "scripts" / "run_flagship.ps1").read_text(encoding="utf-8")
    assert "benchmark_freeze_gate.py" in script
    assert '"--require-tag", "--json"' in script
    assert '"--require-tag", "--require-remote-tag", "--json"' in script
    execute_stop = script.index("if (-not $Execute)")
    remote_gate = script.index('"--require-remote-tag"')
    model_run = script.index("-m unchained run")
    assert execute_stop < remote_gate < model_run
    post_run_gate = script.index("$postRunGitGate = Get-ActualGitGate")
    metrics_write = script.index("Write-SanitizedMetrics $bundleDirectory")
    only_metrics_gate = script.index("Assert-OnlyMetricsCreatedAfterValidation $gitGate")
    assert model_run < post_run_gate < metrics_write < only_metrics_gate


def test_flagship_progress_stream_uses_exact_allowlist_and_suppresses_raw_output(
    tmp_path: Path,
) -> None:
    repo = Path(__file__).resolve().parents[1]
    fixture = fixture_directory(tmp_path)
    safe_lines = [
        "[sentinel] profiling and hashing the evidence set",
        "[sentinel] model pipeline finished with status COMPLETE",
    ]
    suppressed_lines = [
        "provider response: PRIVATE_PROVIDER_TEXT",
        "[sentinel] PRIVATE_PROVIDER_TEXT",
        *PRIVATE_SENTINELS,
    ]
    write_json(fixture / "progress.json", {"lines": [*safe_lines, *suppressed_lines]})

    result = run_script(repo, fixture)
    combined = result.stdout + result.stderr

    assert result.returncode == 0, combined
    assert all(line in combined for line in safe_lines)
    assert all(line not in combined for line in suppressed_lines)

    script = (repo / "scripts" / "run_flagship.ps1").read_text(encoding="utf-8")
    assert "$AllowedFlagshipProgress.Contains($line)" in script
    assert "model pipeline finished with status (COMPLETE|PARTIAL|FATAL|INVALID)" in script
    assert 'StartsWith("[sentinel]")' not in script
    assert "ForEach-Object { Write-SanitizedFlagshipProgress $_ }" in script
    assert "$runExitCode = $LASTEXITCODE" in script
    assert "$runLines" not in script
    assert "$Error.RemoveAt(0)" in script


def test_flagship_fixture_seam_cannot_execute(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = run_script(repo, fixture_directory(tmp_path), "-Execute")
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "test fixture seam cannot be used with -Execute" in combined
    assert all(value not in combined for value in PRIVATE_SENTINELS)


def test_flagship_isolated_python_blocks_cwd_and_pythonpath_shadowing(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = (repo / "scripts" / "run_flagship.ps1").read_text(encoding="utf-8")
    assert "& $pythonExecutable -I -m unchained run" in script
    assert "& $pythonExecutable -I -m unchained view" in script
    assert '"PYTHONPATH"' in script
    assert '[Environment]::SetEnvironmentVariable($name, $null, "Process")' in script
    assert script.index("$sourceIdentityRaw = Invoke-CapturedPython") < script.index(
        "$evidenceRoot = Resolve-ExistingRealDirectory"
    )

    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "json.py").write_text("raise RuntimeError('shadow imported')\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(shadow)
    isolated = subprocess.run(
        [sys.executable, "-I", "-c", "import json; print(json.__name__)"],
        cwd=shadow,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert isolated.returncode == 0, isolated.stderr
    assert isolated.stdout.strip() == "json"


def test_flagship_preflight_rejects_wrong_frozen_evidence_digest(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = run_script(repo, fixture_directory(tmp_path, evidence_sha256="b" * 64))
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Evidence SHA-256 does not match the frozen flagship digest" in combined
    assert all(value not in combined for value in PRIVATE_SENTINELS)


def test_flagship_preflight_rejects_wrong_frozen_evidence_size(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = run_script(repo, fixture_directory(tmp_path, evidence_bytes=EXPECTED_BYTES - 1))
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "E001 is not a ready Windows-memory route" in combined
    assert all(value not in combined for value in PRIVATE_SENTINELS)


def test_flagship_preflight_rejects_cap_drift(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    fixture = fixture_directory(tmp_path)
    write_json(
        fixture / "caps.json",
        {
            "profile": "default",
            "max_tool_calls": 59,
            "max_total_tokens": 400_000,
            "max_wall_seconds": 1_800.0,
            "max_cost_usd": 10.0,
        },
    )
    result = run_script(repo, fixture)
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "differs from the frozen bounded flagship caps" in combined
    assert all(value not in combined for value in PRIVATE_SENTINELS)


@pytest.mark.parametrize(
    ("lock_sha256", "installed_versions_match"),
    [("b" * 64, True), (EXPECTED_LOCK_SHA256, False)],
)
def test_flagship_preflight_rejects_dependency_lock_drift(
    tmp_path: Path,
    lock_sha256: str,
    installed_versions_match: bool,
) -> None:
    repo = Path(__file__).resolve().parents[1]
    fixture = fixture_directory(
        tmp_path,
        lock_sha256=lock_sha256,
        installed_versions_match=installed_versions_match,
    )

    result = run_script(repo, fixture)
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Dependency lock path, digest, target, or installed-version parity differs" in combined
    assert all(value not in combined for value in PRIVATE_SENTINELS)
