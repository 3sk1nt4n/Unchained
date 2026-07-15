"""Offline proof-bundle verifier acceptance and tamper tests."""

from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path
from typing import Any

import pytest

from unchained.verify import RECORDED_CUSTODY_NOTICE, VerificationResult, verify_run

GENESIS_HASH = "0" * 64


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _event(
    sequence: int,
    previous_hash: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    run_id: str = "run-proof-001",
) -> dict[str, Any]:
    unsigned = {
        "schema_version": 1,
        "run_id": run_id,
        "sequence": sequence,
        "event_id": f"event-{sequence:03d}",
        "event_type": event_type,
        "actor": "test-fixture",
        "timestamp_utc": f"2026-07-14T12:00:{sequence:02d}+00:00",
        "elapsed_ms": sequence * 10,
        "previous_hash": previous_hash,
        "payload": payload,
    }
    digest = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()
    return {**unsigned, "entry_hash": digest}


def _model_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "phase": "investigate",
        "requested_model": "gpt-5.6",
        "provider_model": "gpt-5.6-sol-2026-07-14",
        "model": "gpt-5.6",
        "response_id": "resp_live_001",
        "request_id": "req_live_001",
        "status": "completed",
        "message": "PLAN then ACT",
        "function_calls": [],
        "token_counts": {
            "input_tokens": 80,
            "output_tokens": 20,
            "cached_input_tokens": 0,
            "cache_write_tokens": 0,
            "reasoning_tokens": 10,
            "provider_total_tokens": 100,
        },
    }
    payload.update(overrides)
    return payload


def _events(
    output: str,
    *,
    terminal_status: str = "COMPLETE",
    exit_code: int = 0,
    model_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    output_bytes = output.encode("utf-8")
    output_hash = hashlib.sha256(output_bytes).hexdigest()
    output_path = f"tool-outputs/{output_hash}.txt"
    initial_hashes = {"E001": "a" * 64}
    payloads = [
        ("run.created", {"caps_profile": "strict"}),
        (
            "custody.initial.completed",
            {"hashes": initial_hashes, "sizes": {"E001": 1234}, "file_count": 1},
        ),
        ("model.response", model_payload or _model_payload()),
        ("tool.started", {"tool_call_id": "t1", "tool_name": "windows.pslist", "arguments": {}}),
        (
            "tool.completed",
            {
                "tool_call_id": "t1",
                "tool_name": "windows.pslist",
                "arguments": {},
                "status": "success",
                "started_at": "2026-07-14T12:00:03+00:00",
                "ended_at": "2026-07-14T12:00:04+00:00",
                "duration_ms": 1,
                "output_sha256": output_hash,
                "output_first_2kb": output,
                "output_artifact_path": output_path,
                "output_bytes": len(output_bytes),
                "output_encoding": "utf-8",
                "output_media_type": "text/plain",
                "accepted_output_complete": True,
                "error": None,
            },
        ),
        (
            "investigator.finished",
            {
                "turns": 1,
                "case_notes": "Suspicious process [t1]",
                "findings": [
                    {
                        "finding_id": "F001",
                        "title": "Suspicious process",
                        "summary": "Observed malicious.exe [t1]",
                        "proposed_status": "CONFIRMED",
                        "severity": "HIGH",
                        "tool_call_ids": ["t1"],
                        "iocs": [],
                        "limitations": [],
                    }
                ],
                "limitations": [],
                "unresolved_questions": [],
            },
        ),
        (
            "judge.completed",
            {
                "verdicts": [
                    {
                        "finding_id": "F001",
                        "status": "CONFIRMED",
                        "rationale": "The retained receipt names the process.",
                        "cited_tool_call_ids": ["t1"],
                        "quoted_spans": [{"tool_call_id": "t1", "text": "malicious.exe"}],
                        "annotations": [],
                    }
                ]
            },
        ),
        (
            "custody.final.completed",
            {"hashes": initial_hashes, "match": True, "mount_released": True},
        ),
        (
            "run.completed",
            {"status": terminal_status, "exit_code": exit_code, "cap": None},
        ),
    ]
    events: list[dict[str, Any]] = []
    previous_hash = GENESIS_HASH
    for sequence, (event_type, payload) in enumerate(payloads, start=1):
        event = _event(sequence, previous_hash, event_type, payload)
        events.append(event)
        previous_hash = event["entry_hash"]
    return events


def _artifact(path: str, content: bytes, *, role: str, media_type: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "media_type": media_type,
        "encoding": "utf-8",
        "required": True,
    }


def _rewrite_manifest(run_directory: Path, manifest: dict[str, Any]) -> None:
    content = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    (run_directory / "manifest.json").write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    (run_directory / "manifest.sha256").write_text(
        f"{digest}  manifest.json\n",
        encoding="ascii",
        newline="",
    )


def _build_bundle(
    run_directory: Path,
    *,
    output: str = "PID 4242 malicious.exe\n",
    terminal_status: str = "COMPLETE",
    exit_code: int = 0,
    model_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_directory.mkdir()
    output_content = output.encode("utf-8")
    output_hash = hashlib.sha256(output_content).hexdigest()
    output_path = f"tool-outputs/{output_hash}.txt"
    output_target = run_directory / Path(output_path)
    output_target.parent.mkdir()
    output_target.write_bytes(output_content)

    events = _events(
        output,
        terminal_status=terminal_status,
        exit_code=exit_code,
        model_payload=model_payload,
    )
    audit_content = b"".join((_canonical(event) + "\n").encode("utf-8") for event in events)
    (run_directory / "audit.jsonl").write_bytes(audit_content)
    audit_hash = hashlib.sha256(audit_content).hexdigest()
    manifest = {
        "schema_version": 1,
        "layout_version": 1,
        "run_id": "run-proof-001",
        "terminal": {"status": terminal_status, "exit_code": exit_code},
        "audit": {
            "path": "audit.jsonl",
            "sha256": audit_hash,
            "bytes": len(audit_content),
            "entry_count": len(events),
            "final_entry_hash": events[-1]["entry_hash"],
        },
        "artifacts": [
            _artifact(
                "audit.jsonl",
                audit_content,
                role="audit",
                media_type="application/x-ndjson",
            ),
            _artifact(output_path, output_content, role="tool-output", media_type="text/plain"),
        ],
        "excluded_from_self_manifest": [
            "manifest.json",
            "manifest.sha256",
            "verifier-output.txt",
        ],
    }
    _rewrite_manifest(run_directory, manifest)
    return manifest


def _assert_failed_with(result: VerificationResult, fragment: str) -> None:
    assert not result.passed
    assert any(fragment.lower() in error.lower() for error in result.errors), result.public_dict()


def test_synthetic_complete_live_bundle_verifies_offline(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    assert result.passed
    assert result.ok
    assert result.run_id == "run-proof-001"
    assert result.terminal_status == "COMPLETE"
    assert result.verified_audit_entries == 9
    assert result.verified_artifacts == 2
    assert result.warnings == (RECORDED_CUSTODY_NOTICE,)
    assert result.public_dict()["custody"] == {
        "recorded_custody_only": True,
        "original_evidence_rehashed": False,
        "statement": RECORDED_CUSTODY_NOTICE,
    }


def test_tampered_tool_blob_is_rejected(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory)
    output_path = next(
        artifact["path"] for artifact in manifest["artifacts"] if artifact["role"] == "tool-output"
    )
    (run_directory / Path(output_path)).write_text("tampered\n", encoding="utf-8")

    result = verify_run(run_directory)

    _assert_failed_with(result, "artifact SHA-256 mismatch")


def test_tampered_audit_is_rejected_independently(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory)
    audit = run_directory / "audit.jsonl"
    audit.write_bytes(audit.read_bytes().replace(b"malicious.exe", b"malicious.dll", 1))

    result = verify_run(run_directory)

    _assert_failed_with(result, "audit.jsonl SHA-256 does not match manifest")
    assert any("entry hash mismatch" in error for error in result.errors)


def test_manifest_path_traversal_is_rejected_even_with_fresh_checksum(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory)
    manifest["artifacts"][1]["path"] = "../outside.txt"
    _rewrite_manifest(run_directory, manifest)

    result = verify_run(run_directory)

    _assert_failed_with(result, "unsafe bundle path")


def test_detached_manifest_checksum_must_be_exact(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory)
    (run_directory / "manifest.sha256").write_text("0" * 64 + " *manifest.json\n")

    result = verify_run(run_directory)

    _assert_failed_with(result, "must exactly equal")


def test_extra_unreferenced_tool_blob_is_rejected(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory)
    (run_directory / "tool-outputs" / "extra.txt").write_text("not receipted", encoding="utf-8")

    result = verify_run(run_directory)

    _assert_failed_with(result, "unreferenced tool-output file")


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"provider_model": None}, "provider_model"),
        (
            {
                "token_counts": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_input_tokens": 0,
                    "cache_write_tokens": 0,
                    "reasoning_tokens": 0,
                    "provider_total_tokens": 0,
                }
            },
            "provider_total_tokens",
        ),
        ({"is_replay": True}, "fake or replayed"),
    ],
)
def test_strict_live_gpt56_rejects_unproven_provider_receipts(
    tmp_path: Path,
    override: dict[str, Any],
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    payload = _model_payload(**override)
    _build_bundle(run_directory, model_payload=payload)

    ordinary = verify_run(run_directory)
    strict = verify_run(run_directory, require_live_gpt56=True)

    assert ordinary.passed
    _assert_failed_with(strict, expected)


def test_strict_live_requires_complete_terminal(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory, terminal_status="PARTIAL", exit_code=3)

    result = verify_run(run_directory, require_live_gpt56=True)

    _assert_failed_with(result, "requires a COMPLETE run")


def test_verification_never_opens_a_network_socket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory)

    def forbidden_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("offline verifier attempted network access")

    monkeypatch.setattr(socket, "socket", forbidden_socket)

    assert verify_run(run_directory, require_live_gpt56=True).passed
