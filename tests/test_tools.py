"""Typed runner acceptance tests using in-memory fake forensic tools."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest

import unchained._tool_worker as tool_worker_module
import unchained.tools as tools_module
from unchained.audit import AuditLog
from unchained.caps import CapConfig, CapExceeded, CapKind, RunBudget
from unchained.models import EvidenceItem, EvidenceProfile, FunctionCall
from unchained.tools import (
    _EVENT_LOG_MAX_RETURN_BYTES,
    _WORKER_MAX_RESPONSE_BYTES,
    ToolDefinition,
    ToolProtocolError,
    ToolRegistry,
    _run_isolated_worker,
    _tsk_executor,
)

EMPTY_PARAMETERS = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}


def test_opening_batch_really_executes_tools_in_parallel(tmp_path: Path) -> None:
    """Both fake tools must reach a barrier before either can return successfully."""

    barrier = threading.Barrier(2, timeout=2.0)
    thread_ids: set[int] = set()
    observations_lock = threading.Lock()

    def executor(arguments: dict[str, object]) -> str:
        assert arguments == {}
        with observations_lock:
            thread_ids.add(threading.get_ident())
        barrier.wait()
        return "raw fake output"

    definitions = tuple(
        ToolDefinition(
            name=name,
            description=f"Fake {name} forensic collector.",
            parameters=EMPTY_PARAMETERS,
            families=("memory",),
            os_families=("windows",),
            executor=executor,
        )
        for name in ("windows.pslist", "windows.netscan")
    )
    budget = RunBudget(
        CapConfig(
            max_tool_calls=2,
            max_total_tokens=10_000,
            max_wall_seconds=30.0,
            max_cost_usd=10.0,
        )
    )
    audit_path = tmp_path / "audit.jsonl"

    with AuditLog(audit_path, "parallel-test", fsync=False) as audit:
        registry = ToolRegistry(definitions=definitions, audit=audit, budget=budget)
        results = registry.execute_batch(
            (
                FunctionCall(call_id="call-a", name="windows.pslist", arguments={}),
                FunctionCall(call_id="call-b", name="windows.netscan", arguments={}),
            )
        )

    assert [result.call_id for result in results] == ["call-a", "call-b"]
    assert all(result.status == "success" for result in results)
    assert all(result.output == "raw fake output" for result in results)
    assert len(thread_ids) == 2
    assert budget.snapshot().tool_calls == 2

    entries = AuditLog.verify(audit_path)
    assert sum(entry["event_type"] == "tool.started" for entry in entries) == 2
    assert sum(entry["event_type"] == "tool.completed" for entry in entries) == 2


def test_private_worker_returns_json_normalized_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The disposable worker returns one decoded value through its sealed envelope."""

    monkeypatch.setenv("UNCHAINED_TEST_TOOL_WORKER", "1")
    result = _run_isolated_worker(
        {
            "action": "test",
            "operation": "echo",
            "value": {"status": "ok", "records": [1, "two"]},
        },
        2.0,
    )

    assert result == {"status": "ok", "records": [1, "two"]}


def test_private_worker_timeout_returns_promptly_and_kills_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A blocked child is forcibly reaped rather than delaying the runner."""

    monkeypatch.setenv("UNCHAINED_TEST_TOOL_WORKER", "1")
    started = time.monotonic()
    result = _run_isolated_worker(
        {"action": "test", "operation": "block"},
        0.05,
    )

    assert time.monotonic() - started < 2.0
    assert isinstance(result, dict)
    assert result["status"] == "timeout"
    assert "0.050s" in str(result["error"])


def test_private_worker_rejects_arbitrary_import_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither a module nor function supplied in JSON can expand the allowlist."""

    monkeypatch.setenv("UNCHAINED_TEST_TOOL_WORKER", "1")
    result = _run_isolated_worker(
        {
            "action": "direct",
            "tool": "arbitrary",
            "module": "os",
            "function": "system",
            "arguments": {},
        },
        2.0,
    )

    assert isinstance(result, dict)
    assert result["status"] == "error"
    assert "allowlisted" in str(result["error"])


def test_private_worker_rejects_arbitrary_tsk_executables() -> None:
    """The TSK action accepts fixed metadata tools, never a caller-supplied binary."""

    result = _run_isolated_worker(
        {
            "action": "tsk",
            "tool": "powershell",
            "evidence_path": str(Path.cwd().resolve()),
            "arguments": {},
        },
        2.0,
    )

    assert isinstance(result, dict)
    assert result["status"] == "error"
    assert "allowlisted" in str(result["error"])


def test_tsk_executor_routes_a_sealed_spec_through_the_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The parent passes a tool name and evidence path, not an executable command."""

    captured: list[tuple[dict[str, object], RunBudget | None]] = []
    budget = RunBudget(CapConfig())

    def fake_worker(spec: dict[str, object], received_budget: RunBudget | None) -> object:
        captured.append((spec, received_budget))
        return {"status": "ok"}

    monkeypatch.setattr("unchained.tools._run_qwen_worker", fake_worker)
    executor = _tsk_executor(
        "fsstat",
        "C:/evidence/disk.E01",
        budget,
        filesystem_offset=0,
    )

    assert executor({}) == {"status": "ok"}
    assert captured == [
        (
            {
                "action": "tsk",
                "tool": "fsstat",
                "evidence_path": "C:/evidence/disk.E01",
                "arguments": {},
                "sector_offset": 0,
            },
            budget,
        )
    ]


def test_tsk_fsstat_receives_the_exact_classified_partition_offset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Byte offsets stay code-owned and cross the worker boundary as TSK sectors."""

    captured: list[dict[str, object]] = []

    def fake_worker(spec: dict[str, object], _budget: RunBudget | None) -> object:
        captured.append(spec)
        return {"status": "ok"}

    monkeypatch.setattr(tools_module, "_run_qwen_worker", fake_worker)
    executor = _tsk_executor(
        "fsstat",
        "C:/evidence/disk.E01",
        None,
        filesystem_offset=16 * 512,
    )

    assert executor({}) == {"status": "ok"}
    assert captured[0]["sector_offset"] == 16


def test_tsk_worker_invokes_partition_aware_fsstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The sealed sector reaches fsstat as an argv token, never model arguments."""

    disk = tmp_path / "disk.raw"
    disk.write_bytes(b"disk")
    captured: list[list[str]] = []

    class Completed:
        returncode = 0
        stdout = "File System Type: Ext4"
        stderr = ""

    def fake_run(command: list[str], **_options: object) -> Completed:
        captured.append(command)
        return Completed()

    monkeypatch.setattr(tool_worker_module.shutil, "which", lambda _name: "/usr/bin/fsstat")
    monkeypatch.setattr(tool_worker_module.subprocess, "run", fake_run)

    result = tool_worker_module._run_tsk(
        {
            "tool": "fsstat",
            "evidence_path": str(disk.resolve()),
            "arguments": {},
            "sector_offset": 16,
            "timeout_seconds": 5.0,
        }
    )

    assert result["status"] == "ok"
    assert captured == [["/usr/bin/fsstat", "-o", "16", str(disk.resolve())]]


def test_fsstat_is_withheld_when_no_matched_filesystem_offset_is_known(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unresolved container can expose topology tools, but not ambiguous fsstat."""

    disk = tmp_path / "opaque.E01"
    disk.write_bytes(b"opaque")
    item = EvidenceItem(
        evidence_id="E001",
        path=disk,
        kind="disk",
        size=disk.stat().st_size,
        sha256="0" * 64,
        filesystem=None,
        filesystem_offset=None,
        os_hint="windows",
    )
    profile = EvidenceProfile(
        root=tmp_path,
        os="windows",
        shape="disk-only",
        filesystems=(),
        sizes={"E001": item.size},
        health={"E001": item.health},
        symbols={"E001": item.symbols},
        hashes={"E001": item.sha256},
        available_tool_families=("sleuthkit",),
        capability_label="synthetic",
        items=(item,),
    )
    monkeypatch.setattr(
        tools_module,
        "_load_qwen_catalog",
        lambda _budget: {"direct": {}, "volatility_plugins": {}},
    )
    monkeypatch.setattr(tools_module.shutil, "which", lambda _name: "/usr/bin/tool")

    definitions = tools_module.load_reference_tools(profile)
    names = {definition.name for definition in definitions}

    assert "tsk_fsstat" not in names
    assert {"tsk_img_stat", "tsk_mmls"}.issubset(names)


def test_private_worker_does_not_inherit_host_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forensic parser children receive runtime paths, not unrelated secrets."""

    monkeypatch.setenv("UNCHAINED_TEST_TOOL_WORKER", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-cross-boundary")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "must-not-cross-boundary")
    monkeypatch.setenv("HTTPS_PROXY", "http://credential.invalid")
    result = _run_isolated_worker(
        {
            "action": "test",
            "operation": "environment",
            "keys": [
                "OPENAI_API_KEY",
                "AWS_SECRET_ACCESS_KEY",
                "HTTPS_PROXY",
                "PATH",
                "SIFT_EVENT_LOG_FORCE_BUDGET",
                "SIFT_EVENT_LOG_MAX_RETURN_BYTES",
            ],
        },
        2.0,
    )

    assert isinstance(result, dict)
    assert result["OPENAI_API_KEY"] is None
    assert result["AWS_SECRET_ACCESS_KEY"] is None
    assert result["HTTPS_PROXY"] is None
    assert result["PATH"]
    assert os.path.normcase(result["PATH"].split(os.pathsep)[0]) == os.path.normcase(
        os.path.dirname(os.path.abspath(sys.executable))
    )
    assert result["SIFT_EVENT_LOG_FORCE_BUDGET"] == "1"
    assert result["SIFT_EVENT_LOG_MAX_RETURN_BYTES"] == str(_EVENT_LOG_MAX_RETURN_BYTES)


def test_private_worker_rejects_oversized_protocol_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A parser cannot force the parent to buffer an unbounded JSON line."""

    monkeypatch.setenv("UNCHAINED_TEST_TOOL_WORKER", "1")
    result = _run_isolated_worker(
        {
            "action": "test",
            "operation": "echo",
            "value": "x" * (_WORKER_MAX_RESPONSE_BYTES + 1),
        },
        5.0,
    )

    assert isinstance(result, dict)
    assert result["status"] == "error"
    assert "transport boundary" in str(result["error"])


def test_tool_call_ids_are_claimed_atomically_and_never_reused(tmp_path: Path) -> None:
    """A duplicate batch starts nothing and a completed receipt id stays reserved."""

    definitions = tuple(
        ToolDefinition(
            name=name,
            description=name,
            parameters=EMPTY_PARAMETERS,
            families=("memory",),
            os_families=("windows",),
            executor=lambda _arguments: "ok",
        )
        for name in ("one", "two")
    )
    budget = RunBudget(
        CapConfig(
            max_tool_calls=4,
            max_total_tokens=1_000,
            max_wall_seconds=30,
            max_cost_usd=1,
        )
    )
    audit_path = tmp_path / "audit.jsonl"
    duplicate_batch = (
        FunctionCall(call_id="same", name="one", arguments={}),
        FunctionCall(call_id="same", name="two", arguments={}),
    )

    with AuditLog(audit_path, "call-id-test", fsync=False) as audit:
        registry = ToolRegistry(definitions, audit, budget)
        with pytest.raises(ToolProtocolError, match="duplicate tool call_id"):
            registry.execute_batch(duplicate_batch)
        assert budget.snapshot().tool_calls == 0

        result = registry.execute(duplicate_batch[0])
        assert result.status == "success"
        with pytest.raises(ToolProtocolError, match="already used"):
            registry.execute(duplicate_batch[0])
        with pytest.raises(ToolProtocolError, match="already used"):
            registry.rejected(duplicate_batch[1], "duplicate")

    entries = AuditLog.verify(audit_path)
    assert [entry["event_type"] for entry in entries] == ["tool.started", "tool.completed"]
    assert budget.snapshot().tool_calls == 1


def test_capped_opening_calls_receive_complete_unstarted_receipts(tmp_path: Path) -> None:
    """Every model-issued call is receipted even when batch reservation is denied."""

    executed: list[str] = []

    def executor(_arguments: dict[str, object]) -> str:
        executed.append("ran")
        return "must not run"

    definitions = tuple(
        ToolDefinition(
            name=name,
            description="Fake bounded forensic collector.",
            parameters=EMPTY_PARAMETERS,
            families=("memory",),
            os_families=("windows",),
            executor=executor,
        )
        for name in ("windows.pslist", "windows.netscan")
    )
    budget = RunBudget(
        CapConfig(
            max_tool_calls=1,
            max_total_tokens=10_000,
            max_wall_seconds=30.0,
            max_cost_usd=10.0,
        )
    )
    calls = tuple(
        FunctionCall(call_id=f"capped-{index}", name=name, arguments={})
        for index, name in enumerate(("windows.pslist", "windows.netscan"), start=1)
    )
    audit_path = tmp_path / "audit.jsonl"

    with AuditLog(audit_path, "capped-receipts", fsync=False) as audit:
        registry = ToolRegistry(definitions, audit, budget)
        with pytest.raises(CapExceeded) as raised:
            registry.execute_batch(calls)

    assert raised.value.kind is CapKind.TOOL_CALLS
    assert executed == []
    entries = AuditLog.verify(audit_path)
    receipts = [entry for entry in entries if entry["event_type"] == "tool.completed"]
    assert [entry["payload"]["tool_call_id"] for entry in receipts] == [
        "capped-1",
        "capped-2",
    ]
    assert all(entry["payload"]["status"] == "capped" for entry in receipts)
    assert all(entry["payload"]["output_sha256"] for entry in receipts)
    assert all("MAX_TOOL_CALLS" in entry["payload"]["output_first_2kb"] for entry in receipts)
