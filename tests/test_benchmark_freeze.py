"""Focused fail-closed tests for the two-layer benchmark preregistration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "benchmark_freeze_gate.py"


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("benchmark_freeze_gate_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GATE = _load_gate()


def _copy_candidate(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    paths = set(GATE.EXPECTED_BOUND_FILES) | {GATE.FREEZE_DOCUMENT, GATE.FREEZE_GATE}
    for relative in paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, destination)
    environment = {
        "model_configuration": {"requested_model": "gpt-5.6"},
        "prompt_bundle": {
            # Historical run receipts attest the catalog only. Current prompt
            # bytes are rebuilt locally by the refresh gate.
            "sha256": "0" * 64,
        },
        "tool_catalog": {
            "count": 14,
            "sha256": "a892308eccf6c23594f355f76ace069e4d2a0d64607cc9d811cc962e6f4e009b",
        },
    }
    environment_path = tmp_path / "environment.json"
    environment_path.write_text(json.dumps(environment), encoding="utf-8")
    refreshed = GATE._refresh_candidate(root, environment_path)
    assert refreshed["status"] == "CANDIDATE_REFRESHED_NOT_REVIEWED"
    return root, environment_path


def _fact_payload(*, approximate_without_tolerance: bool = False) -> dict[str, Any]:
    categories = [
        "process",
        "network",
        "service_persistence",
        "memory_injection",
        "identity_privilege",
        "execution",
        "environment_registry",
        "process",
        "network",
        "memory_injection",
    ]
    facts = []
    for index, behavior_category in enumerate(categories, start=1):
        approximate = approximate_without_tolerance and index == 1
        facts.append(
            {
                "fact_id": f"DC01-F{index:03d}",
                "proposition": f"Frozen atomic proposition {index}.",
                "behavior_category": behavior_category,
                "observability": "observable",
                "required_tool_family": "volatility3.windows",
                "stability": "approximate" if approximate else "stable",
                "scored": True,
                "inclusion_rationale": "Observable from the memory-only route.",
                "normalized_values": {"pid": 122 + index},
                "match_mode": "numeric_tolerance" if approximate else "exact",
                "tolerance": None,
                "receipt_sufficiency_guidance": "A retained typed-tool row must show the value.",
                "source_notes": "Derived from direct evidence inspection.",
                "independent_check_notes": "Checked separately from model output.",
                "ambiguity_notes": "None identified.",
                "timestamp_basis": "Not applicable.",
            }
        )
    return {
        "schema_version": 1,
        "fact_set_id": "dc01-memory-reference-v1",
        "case_id": "CASE-A",
        "route": "windows-memory-only",
        "adjudication": {
            "kind": "project_authored_preregistered",
            "reviewer": "named reviewer",
            "notes": "Checked directly against the evidence before the scored run.",
        },
        "facts": facts,
    }


def _declare_reference_ready(
    root: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    fact_path = root / "experiment" / "reference-facts-v1.json"
    fact_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    fact_path.write_bytes(encoded)
    manifest = GATE.load_manifest(root)
    manifest["preregistration_status"] = "READY_FOR_LOCK"
    manifest["reference_fact_set"]["status"] = "READY"
    manifest["reference_fact_set"]["sha256"] = hashlib.sha256(encoded).hexdigest()
    GATE._write_manifest(root, manifest)
    return manifest


def _write_valid_lock(root: Path, manifest: dict[str, Any]) -> None:
    lock = GATE.build_lock(root, manifest, GATE.FOUNDATION_COMMIT)
    lock_path = root / manifest["lock"]["path"]
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _issue_codes(result: dict[str, Any]) -> set[str]:
    return {issue["code"] for issue in result["issues"]}


def test_dependency_lock_digest_matches_fresh_clone_bytes() -> None:
    relative = GATE.EXPECTED_DEPENDENCY_LOCK["path"]
    committed = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout

    assert b"\r\n" not in committed
    assert hashlib.sha256(committed).hexdigest() == GATE.EXPECTED_DEPENDENCY_LOCK["sha256"]
    assert (
        hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest()
        == GATE.EXPECTED_DEPENDENCY_LOCK["sha256"]
    )


def test_freeze_binds_executable_comparison_policy() -> None:
    assert {
        "scripts/benchmark_compare.py",
        "docs/QWEN-COMPARISON.v1.json",
        "docs/QWEN-COMPARISON-PROTOCOL.md",
    } <= GATE.EXPECTED_BOUND_FILES


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.stdout.strip()


def _completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["git"], returncode, stdout=stdout, stderr="")


def _install_valid_remote_git(monkeypatch: Any) -> tuple[str, str]:
    tag_object = "a" * 40
    commit = "b" * 40
    tag_ref = "refs/tags/experiment-freeze-v1"

    def fake_git(_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        command = tuple(arguments)
        responses = {
            ("remote", "get-url", "--all", "origin"): GATE.CANONICAL_ORIGIN_URL + "\n",
            ("remote", "get-url", "--push", "--all", "origin"): (GATE.CANONICAL_ORIGIN_URL + "\n"),
            ("rev-parse", "--verify", tag_ref): tag_object + "\n",
            ("cat-file", "-t", tag_ref): "tag\n",
            ("rev-parse", "--verify", f"{tag_ref}^{{commit}}"): commit + "\n",
            ("rev-parse", "--verify", "HEAD"): commit + "\n",
            ("status", "--porcelain=v1", "--untracked-files=all"): "",
        }
        assert command in responses
        return _completed(responses[command])

    monkeypatch.setattr(GATE, "_git", fake_git)
    return tag_object, commit


def test_candidate_is_not_ready_without_reference_facts_or_lock(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)

    result = GATE.evaluate(root, require_git=False)

    assert result["status"] == "NOT_READY"
    assert result["ready"] is False
    assert {
        "CANDIDATE_NOT_REVIEWED",
        "REFERENCE_FACT_SET_NOT_READY",
        "FREEZE_LOCK_NOT_READY",
    } <= _issue_codes(result)


def test_refresh_uses_historical_environment_for_catalog_only(tmp_path: Path) -> None:
    root, environment_path = _copy_candidate(tmp_path)
    historical = json.loads(environment_path.read_text(encoding="utf-8"))
    refreshed = GATE.load_manifest(root)

    assert historical["prompt_bundle"]["sha256"] == "0" * 64
    assert refreshed["prompt_bundle"]["canonical_base_sha256"] != "0" * 64


def test_default_gate_never_performs_remote_lookup(tmp_path: Path, monkeypatch: Any) -> None:
    root, _environment = _copy_candidate(tmp_path)

    def forbidden(*_arguments: Any, **_keywords: Any) -> Any:
        raise AssertionError("default gate attempted network access")

    monkeypatch.setattr(GATE, "_git_ls_remote", forbidden)
    result = GATE.evaluate(root, require_git=False)

    assert "remote_anchor" not in result


def test_bound_prompt_drift_fails_even_while_candidate_is_pending(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    prompt_path = root / "src" / "unchained" / "prompts.py"
    prompt_path.write_text(
        prompt_path.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8"
    )

    result = GATE.evaluate(root, require_git=False)

    assert result["status"] == "FAIL"
    assert "BOUND_FILE_DRIFT" in _issue_codes(result)
    assert "PROMPT_BUNDLE_DRIFT" not in _issue_codes(result)


def test_prior_exposure_cannot_understate_five_attempts(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    manifest = GATE.load_manifest(root)
    manifest["prior_exposure_disclosure"]["attempt_count"] = 1
    manifest["prior_exposure_disclosure"]["successful_forensic_executions"] = 6
    GATE._write_manifest(root, manifest)

    result = GATE.evaluate(root, require_git=False)

    assert result["status"] == "FAIL"
    assert "PRIOR_EXPOSURE_DRIFT" in _issue_codes(result)


def test_complete_reference_and_two_layer_lock_pass_content_gate(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    manifest = _declare_reference_ready(root, _fact_payload())

    before_lock = GATE.evaluate(root, require_lock=False, require_git=False)
    assert before_lock["status"] == "READY"

    _write_valid_lock(root, manifest)
    result = GATE.evaluate(root, require_git=False)

    assert result == {
        "schema_version": 1,
        "status": "READY",
        "ready": True,
        "freeze_id": "sentinel-dc01-sol-v1",
        "foundation_protocol_commit": GATE.FOUNDATION_COMMIT,
        "issues": [],
    }


def test_approximate_scored_fact_without_tolerance_fails(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    _declare_reference_ready(root, _fact_payload(approximate_without_tolerance=True))

    result = GATE.evaluate(root, require_lock=False, require_git=False)

    assert result["status"] == "FAIL"
    assert "REFERENCE_FACT_TOLERANCE" in _issue_codes(result)


def test_tiny_reference_set_withholds_qualification(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    payload = _fact_payload()
    payload["facts"] = payload["facts"][:9]
    _declare_reference_ready(root, payload)

    result = GATE.evaluate(root, require_lock=False, require_git=False)

    assert result["status"] == "FAIL"
    assert "REFERENCE_FACT_MINIMUM" in _issue_codes(result)


def test_narrow_reference_set_withholds_qualification(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    payload = _fact_payload()
    for fact in payload["facts"]:
        fact["behavior_category"] = "process"
    _declare_reference_ready(root, payload)

    result = GATE.evaluate(root, require_lock=False, require_git=False)

    assert result["status"] == "FAIL"
    assert "REFERENCE_FACT_CATEGORY_COVERAGE" in _issue_codes(result)


def test_typed_done_schema_digest_drift_fails(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    manifest = GATE.load_manifest(root)
    manifest["tools"]["finish_action_schema_sha256"] = "0" * 64
    GATE._write_manifest(root, manifest)

    result = GATE.evaluate(root, require_git=False)

    assert result["status"] == "FAIL"
    assert "FINISH_SCHEMA_DRIFT" in _issue_codes(result)


def test_lock_detects_freeze_document_drift(tmp_path: Path) -> None:
    root, _environment = _copy_candidate(tmp_path)
    manifest = _declare_reference_ready(root, _fact_payload())
    _write_valid_lock(root, manifest)
    document = root / GATE.FREEZE_DOCUMENT
    document.write_text(document.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    result = GATE.evaluate(root, require_git=False)

    assert result["status"] == "FAIL"
    assert "FREEZE_LOCK_FILE_DRIFT" in _issue_codes(result)


def test_refresh_requires_sanitized_catalog_environment(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    paths = set(GATE.EXPECTED_BOUND_FILES) | {GATE.FREEZE_DOCUMENT, GATE.FREEZE_GATE}
    for relative in paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, destination)

    result = GATE._refresh_candidate(root, None)

    assert result["status"] == "FAIL"
    assert "CATALOG_ENVIRONMENT_REQUIRED" in _issue_codes(result)


def test_transitive_local_cli_imports_are_freeze_bound() -> None:
    local_cli_modules = GATE._discover_local_cli_modules(PROJECT_ROOT)

    assert "src/unchained/onboarding.py" in local_cli_modules
    assert local_cli_modules <= GATE.EXPECTED_BOUND_FILES


def test_remote_tag_gate_binds_tag_object_and_peeled_head(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    tag_object, commit = _install_valid_remote_git(monkeypatch)
    tag_ref = "refs/tags/experiment-freeze-v1"
    monkeypatch.setattr(
        GATE,
        "_git_ls_remote",
        lambda *_arguments: _completed(f"{tag_object}\t{tag_ref}\n{commit}\t{tag_ref}^{{}}\n"),
    )
    issues: list[Any] = []

    proof = GATE._check_remote_tag_visibility(
        tmp_path,
        {"public_anchor": {"tag": "experiment-freeze-v1"}},
        issues,
    )

    assert issues == []
    assert proof == {
        "checked": True,
        "visible": True,
        "canonical_origin_url": GATE.CANONICAL_ORIGIN_URL,
        "tag": "experiment-freeze-v1",
        "tag_object": tag_object,
        "peeled_commit": commit,
        "claim": GATE.REMOTE_VISIBILITY_CLAIM,
    }


@pytest.mark.parametrize(
    ("remote_lines", "expected_code"),
    [
        (lambda tag, _commit, ref: f"{tag}\t{ref}\n", "REMOTE_ANNOTATED_TAG_REQUIRED"),
        (
            lambda _tag, commit, ref: f"{'c' * 40}\t{ref}\n{commit}\t{ref}^{{}}\n",
            "REMOTE_TAG_OBJECT_MISMATCH",
        ),
        (
            lambda tag, _commit, ref: f"{tag}\t{ref}\n{'d' * 40}\t{ref}^{{}}\n",
            "REMOTE_TAG_COMMIT_MISMATCH",
        ),
    ],
)
def test_remote_tag_gate_rejects_unpeeled_or_mismatched_refs(
    tmp_path: Path,
    monkeypatch: Any,
    remote_lines: Any,
    expected_code: str,
) -> None:
    tag_object, commit = _install_valid_remote_git(monkeypatch)
    tag_ref = "refs/tags/experiment-freeze-v1"
    monkeypatch.setattr(
        GATE,
        "_git_ls_remote",
        lambda *_arguments: _completed(remote_lines(tag_object, commit, tag_ref)),
    )
    issues: list[Any] = []

    proof = GATE._check_remote_tag_visibility(
        tmp_path,
        {"public_anchor": {"tag": "experiment-freeze-v1"}},
        issues,
    )

    assert proof["visible"] is False
    assert expected_code in {issue.code for issue in issues}


def test_remote_tag_gate_rejects_noncanonical_origin_without_network(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        GATE,
        "_git",
        lambda *_arguments: _completed("https://example.invalid/not-canonical.git\n"),
    )

    def forbidden(*_arguments: Any, **_keywords: Any) -> Any:
        raise AssertionError("origin mismatch must fail before network")

    monkeypatch.setattr(GATE, "_git_ls_remote", forbidden)
    issues: list[Any] = []

    GATE._check_remote_tag_visibility(
        tmp_path,
        {"public_anchor": {"tag": "experiment-freeze-v1"}},
        issues,
    )

    assert "REMOTE_ORIGIN_MISMATCH" in {issue.code for issue in issues}


def test_remote_tag_parser_flag_is_explicit_and_defaults_off() -> None:
    assert GATE._parser().parse_args([]).require_remote_tag is False
    assert GATE._parser().parse_args(["--require-remote-tag"]).require_remote_tag is True


def test_run_environment_requires_exact_dependency_lock_parity(tmp_path: Path) -> None:
    environment = {
        "model_configuration": {"requested_model": "gpt-5.6"},
        "prompt_bundle": {"sha256": "a" * 64},
        "tool_catalog": {"count": 14, "sha256": "b" * 64},
        "caps": GATE.EXPECTED_HARD_LIMITS,
        "dependency_lock": {
            **GATE.EXPECTED_DEPENDENCY_LOCK,
            "installed_versions_match": False,
        },
    }
    path = tmp_path / "environment.json"
    path.write_text(json.dumps(environment), encoding="utf-8")
    manifest = {
        "model": {"requested_alias": "gpt-5.6"},
        "prompt_bundle": {"canonical_base_sha256": "a" * 64},
        "tools": {"typed_catalog_count": 14, "typed_catalog_sha256": "b" * 64},
    }
    issues: list[Any] = []

    GATE._check_runtime_environment(path, manifest, issues)

    assert {issue.code for issue in issues} == {"RUN_ENVIRONMENT_DRIFT"}
    assert any("dependency_lock.installed_versions_match" in issue.message for issue in issues)


def test_git_gate_binds_prelock_source_commit_and_rejects_false_source(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    root = tmp_path / "clone"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "Freeze Test")
    _git(root, "config", "user.email", "freeze-test@example.invalid")
    (root / "foundation.txt").write_text("test protocol foundation\n", encoding="utf-8")
    _git(root, "add", "foundation.txt")
    _git(root, "commit", "--quiet", "-m", "Test protocol foundation")
    foundation_commit = _git(root, "rev-parse", "HEAD")
    monkeypatch.setattr(GATE, "FOUNDATION_COMMIT", foundation_commit)

    for relative in (GATE.FREEZE_DOCUMENT, GATE.FREEZE_GATE):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, destination)
    for relative in GATE.EXPECTED_BOUND_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, destination)
    manifest = GATE.load_manifest(root)
    manifest["foundation"]["protocol_commit"] = foundation_commit
    GATE._write_manifest(root, manifest)
    environment = {
        "model_configuration": {"requested_model": "gpt-5.6"},
        "prompt_bundle": {"sha256": manifest["prompt_bundle"]["canonical_base_sha256"]},
        "tool_catalog": {
            "count": 14,
            "sha256": "a892308eccf6c23594f355f76ace069e4d2a0d64607cc9d811cc962e6f4e009b",
        },
    }
    environment_path = tmp_path / "environment.json"
    environment_path.write_text(json.dumps(environment), encoding="utf-8")
    assert GATE._refresh_candidate(root, environment_path)["status"] == (
        "CANDIDATE_REFRESHED_NOT_REVIEWED"
    )
    manifest = _declare_reference_ready(root, _fact_payload())
    _git(root, "add", "--all")
    _git(root, "commit", "--quiet", "-m", "Bind benchmark candidate")
    source_commit = _git(root, "rev-parse", "HEAD")
    lock = GATE.build_lock(root, manifest, source_commit)
    lock_path = root / manifest["lock"]["path"]
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _git(root, "add", manifest["lock"]["path"])
    _git(root, "commit", "--quiet", "-m", "Lock benchmark candidate")

    ready = GATE.evaluate(root)
    assert ready["status"] == "READY", ready

    lock["source_commit"] = GATE.FOUNDATION_COMMIT
    without_aggregate = {key: value for key, value in lock.items() if key != "aggregate_sha256"}
    lock["aggregate_sha256"] = hashlib.sha256(
        GATE._canonical_json(without_aggregate).encode("utf-8")
    ).hexdigest()
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _git(root, "add", manifest["lock"]["path"])
    _git(root, "commit", "--quiet", "-m", "Forge lock source")

    forged = GATE.evaluate(root)
    assert forged["status"] == "FAIL"
    assert "FREEZE_LOCK_SOURCE_CONTENT_DRIFT" in _issue_codes(forged)
