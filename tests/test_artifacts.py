"""Atomic core-artifact and manifest construction tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from unchained.artifacts import (
    ArtifactError,
    ArtifactRef,
    ArtifactStore,
    build_manifest,
    capture_environment,
    safe_relative_path,
    write_manifest_pair,
)
from unchained.audit import GENESIS_HASH


def test_artifact_store_preserves_exact_bytes_and_replaces_atomically(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path, fsync=False)
    exact = "first\r\nsecond\nemoji: 四\n"

    reference = store.write_text(
        "nested/report.md",
        exact,
        role="report",
        media_type="text/markdown",
    )

    assert (tmp_path / "nested" / "report.md").read_bytes() == exact.encode("utf-8")
    assert reference.sha256 == hashlib.sha256(exact.encode("utf-8")).hexdigest()
    assert reference.bytes == len(exact.encode("utf-8"))
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize(
    "unsafe",
    ("../escape", "/absolute", "C:/drive", "back\\slash", "./dot", "double//slash"),
)
def test_artifact_paths_fail_closed(unsafe: str) -> None:
    with pytest.raises(ArtifactError, match="artifact path"):
        safe_relative_path(unsafe)


def test_environment_capture_is_allowlisted_and_never_dumps_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-never-appear")
    monkeypatch.setenv("PRIVATE_UNRELATED_VALUE", "also-must-never-appear")

    captured = capture_environment(
        run_id="run-001",
        project_directory=tmp_path,
        requested_model="gpt-5.6",
        caps_profile="strict",
        caps={"max_tool_calls": 12},
        tool_schemas=({"type": "function", "name": "windows.pslist"},),
    )
    rendered = json.dumps(captured)

    assert "must-never-appear" not in rendered
    assert "also-must-never-appear" not in rendered
    assert captured["privacy"] == {
        "environment_allowlist_only": True,
        "secrets_recorded": False,
        "absolute_evidence_path_recorded": False,
        "username_recorded": False,
        "hostname_recorded": False,
    }
    assert captured["model_configuration"]["requested_model"] == "gpt-5.6"


def test_manifest_is_explicit_non_self_referential_and_detached(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path, fsync=False)
    report = store.write_text("report.md", "# Report\n", role="report", media_type="text/markdown")
    audit_content = b'{"event_type":"run.completed"}\n'
    audit = store.write_bytes(
        "audit.jsonl",
        audit_content,
        role="audit",
        media_type="application/x-ndjson",
        encoding="utf-8",
    )
    terminal_entry = {
        "event_type": "run.completed",
        "sequence": 1,
        "entry_hash": "a" * 64,
        "payload": {"status": "PARTIAL", "exit_code": 3},
    }

    manifest = build_manifest(
        run_id="run-001",
        status="PARTIAL",
        exit_code=3,
        audit_ref=audit,
        audit_entries=[terminal_entry],
        artifacts=[report],
    )
    manifest_ref, checksum_ref = write_manifest_pair(store, manifest)

    paths = [entry["path"] for entry in manifest["artifacts"]]
    assert paths == ["audit.jsonl", "report.md"]
    assert manifest["audit"]["genesis_hash"] == GENESIS_HASH
    assert "manifest.json" not in paths
    assert "manifest.sha256" not in paths
    assert (tmp_path / "manifest.sha256").read_text(encoding="utf-8") == (
        f"{manifest_ref.sha256}  manifest.json\n"
    )
    assert (
        checksum_ref.sha256
        == hashlib.sha256((tmp_path / "manifest.sha256").read_bytes()).hexdigest()
    )


def test_manifest_rejects_duplicate_and_self_referential_artifacts(tmp_path: Path) -> None:
    audit = ArtifactRef("audit", "audit.jsonl", "a" * 64, 1, "application/x-ndjson", "utf-8")
    duplicate = ArtifactRef("report", "report.md", "b" * 64, 1, "text/markdown", "utf-8")
    terminal = {
        "event_type": "run.completed",
        "sequence": 1,
        "entry_hash": "c" * 64,
        "payload": {},
    }
    with pytest.raises(ArtifactError, match="not unique"):
        build_manifest(
            run_id="run",
            status="PARTIAL",
            exit_code=3,
            audit_ref=audit,
            audit_entries=[terminal],
            artifacts=[duplicate, duplicate],
        )

    self_reference = ArtifactRef(
        "manifest", "manifest.json", "d" * 64, 1, "application/json", "utf-8"
    )
    with pytest.raises(ArtifactError, match="cannot be manifested"):
        build_manifest(
            run_id="run",
            status="PARTIAL",
            exit_code=3,
            audit_ref=audit,
            audit_entries=[terminal],
            artifacts=[self_reference],
        )
