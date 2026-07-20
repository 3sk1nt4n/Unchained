"""Offline proof-bundle verifier acceptance and tamper tests."""

from __future__ import annotations

import hashlib
import json
import socket
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from unchained.artifacts import build_summary
from unchained.caps import CapConfig, estimate_usage_cost
from unchained.models import (
    INVESTIGATION_FINISH_TOOL_NAME,
    MAX_OPENING_TOOLS,
    EvidenceItem,
    EvidenceProfile,
    EvidenceQuote,
    EvidenceSpan,
    Finding,
    FindingStatus,
    InvestigationState,
    JudgeVerdict,
    ModelUsage,
    ToolResult,
    investigation_finish_schema,
)
from unchained.reporting import ReportDraft, render_report_markdown
from unchained.verify import (
    RECORDED_CUSTODY_NOTICE,
    RECORDED_PROVIDER_NOTICE,
    VerificationResult,
    verify_run,
)
from unchained.viewer import render_viewer_html

GENESIS_HASH = "0" * 64
_STRICT_CAPS = CapConfig(
    max_tool_calls=12,
    max_total_tokens=100_000,
    max_wall_seconds=600.0,
    max_cost_usd=2.5,
)
_FIXTURE_USAGE = ModelUsage(
    input_tokens=80,
    output_tokens=20,
    reasoning_tokens=10,
    provider_total_tokens=100,
)
_FIXTURE_CALL_COST = estimate_usage_cost(_STRICT_CAPS, _FIXTURE_USAGE, "gpt-5.6")
_CSP = (
    "default-src 'none'; script-src 'none'; connect-src 'none'; object-src 'none'; "
    "frame-src 'none'; base-uri 'none'; form-action 'none'; img-src 'none'; "
    "font-src 'none'; media-src 'none'; style-src 'unsafe-inline'"
)
_SAFE_VIEWER = (
    "<!doctype html>\n"
    '<html lang="en">\n'
    "<head>\n"
    '<meta charset="utf-8">\n'
    f'<meta http-equiv="Content-Security-Policy" content="{_CSP}">\n'
    "<title>Unchained proof</title>\n"
    "<style>body { font-family: sans-serif; }</style>\n"
    "</head>\n"
    "<body><main><h1>Unchained proof</h1></main></body>\n"
    "</html>\n"
).encode()
_REPORT_DRAFT = {
    "executive_summary": "Fixture executive summary",
    "investigative_narrative": "Fixture investigative narrative",
    "ioc_commentary": "Fixture IOC commentary",
    "limitations_commentary": "Fixture limitations commentary",
}


def _fixture_profile() -> EvidenceProfile:
    item = EvidenceItem(
        evidence_id="E001",
        path=Path("fixture-memory.raw"),
        kind="memory",
        size=1234,
        sha256="a" * 64,
        os_hint="windows",
        health="healthy",
        symbols="ready",
    )
    return EvidenceProfile(
        root=Path("."),
        os="windows",
        shape="memory-only",
        filesystems=(),
        sizes={"E001": 1234},
        health={"E001": "healthy"},
        symbols={"E001": "ready"},
        hashes={"E001": "a" * 64},
        available_tool_families=("memory",),
        capability_label="READY: windows memory analysis",
        items=(item,),
    )


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _function_call(call_id: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "call_id": call_id,
        "name": name,
        "arguments": arguments,
        "arguments_valid": True,
        "parse_error": None,
    }


def _tool_schema(name: str, argument_names: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": f"Strict fixture schema for {name}",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {key: {} for key in argument_names},
            "required": list(argument_names),
            "additionalProperties": False,
        },
    }


def _complete_report(span_id: str) -> bytes:
    return (
        "# Unchained DFIR Report - COMPLETE\n"
        "\n"
        "## Verification scope\n"
        "\n"
        "Fixture verification scope\n"
        "\n"
        "## Executive summary (model-authored, nonauthoritative)\n"
        "\n"
        f"{_REPORT_DRAFT['executive_summary']}\n"
        "\n"
        "## Investigative narrative (model-authored, nonauthoritative)\n"
        "\n"
        f"{_REPORT_DRAFT['investigative_narrative']}\n"
        "\n"
        "## Findings\n"
        "\n"
        "| ID | Finding | Severity | Investigator | Judge | Tool calls | Evidence spans |\n"
        "|---|---|---|---|---|---|---|\n"
        f"| F001 | Suspicious process | HIGH | CONFIRMED | CONFIRMED | [t2] | `{span_id}` |\n"
        "\n"
        "## IOC list\n"
        "\n"
        f"{_REPORT_DRAFT['ioc_commentary']}\n"
        "\n"
        "## Evidence spans\n"
        "\n"
        f"- `{span_id}` from [t2]\n"
        "\n"
        "## Limitations\n"
        "\n"
        f"- {_REPORT_DRAFT['limitations_commentary']}\n"
        "\n"
        "## Unresolved questions\n"
        "\n"
        "No unresolved questions were submitted.\n"
    ).encode()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _span_id(artifact_sha256: str, byte_start: int, byte_end: int) -> str:
    material = f"{artifact_sha256}:{byte_start}:{byte_end}".encode("ascii")
    return "S" + hashlib.sha256(material).hexdigest()[:24]


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


def _model_payload(
    *,
    phase: str = "investigate",
    ordinal: str = "001",
    **overrides: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "phase": phase,
        "requested_model": "gpt-5.6",
        "provider_model": "gpt-5.6-sol-2026-07-14",
        "response_id": f"resp_live_{ordinal}",
        "request_id": f"req_live_{ordinal}",
        "status": "completed",
        "incomplete_details": None,
        "error": None,
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
        "usage_error": None,
        "call_cost_usd_estimate": _FIXTURE_CALL_COST,
        "running_cost_usd_estimate": int(ordinal) * _FIXTURE_CALL_COST,
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
                "output_first_2kb": output[:2048],
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


def _complete_events(
    output: str,
    *,
    terminal_status: str,
    exit_code: int,
    model_overrides: dict[str, Any] | None,
    typed_done: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    output_bytes = output.encode("utf-8")
    output_hash = hashlib.sha256(output_bytes).hexdigest()
    output_path = f"tool-outputs/{output_hash}.txt"
    initial_hashes = {"E001": "a" * 64}
    quote = "malicious.exe"
    quote_bytes = quote.encode("utf-8")
    byte_start = output_bytes.index(quote_bytes)
    byte_end = byte_start + len(quote_bytes)
    span_id = _span_id(output_hash, byte_start, byte_end)
    finding = {
        "finding_id": "F001",
        "title": "Suspicious process",
        "summary": "Observed malicious.exe [t2]",
        "proposed_status": "CONFIRMED",
        "severity": "HIGH",
        "tool_call_ids": ["t2"],
        "supporting_spans": [
            {
                "span_id": span_id,
                "tool_call_id": "t2",
                "artifact_sha256": output_hash,
                "byte_start": byte_start,
                "byte_end": byte_end,
                "text": quote,
                "occurrence_count": 1,
            }
        ],
        "iocs": [],
        "limitations": [],
    }
    verdict = {
        "finding_id": "F001",
        "status": "CONFIRMED",
        "rationale": "The retained receipt names the process.",
        "cited_tool_call_ids": ["t2"],
        "quoted_spans": [{"span_id": span_id, "tool_call_id": "t2", "text": "malicious.exe"}],
        "annotations": [],
    }
    serializer_arguments = {
        "status": "DONE",
        "case_notes": "Plan followup based on [t1]; observed malicious process [t2]",
        "findings": [
            {
                "finding_id": "F001",
                "title": "Suspicious process",
                "summary": "Observed malicious.exe [t2]",
                "proposed_status": "CONFIRMED",
                "severity": "HIGH",
                "tool_call_ids": ["t2"],
                "supporting_quotes": [{"tool_call_id": "t2", "text": "malicious.exe"}],
                "iocs": [],
                "limitations": [],
            }
        ],
        "limitations": [],
        "unresolved_questions": [],
    }
    judgment_arguments = {"verdicts": [verdict]}
    report_arguments = {
        **_REPORT_DRAFT,
        "referenced_finding_ids": ["F001"],
        "referenced_span_ids": [span_id],
    }
    profile = _fixture_profile()
    span = EvidenceSpan(
        span_id=span_id,
        tool_call_id="t2",
        artifact_sha256=output_hash,
        byte_start=byte_start,
        byte_end=byte_end,
        text=quote,
        occurrence_count=1,
    )
    finding_model = Finding(
        finding_id="F001",
        title="Suspicious process",
        summary="Observed malicious.exe [t2]",
        proposed_status=FindingStatus.CONFIRMED,
        severity="HIGH",
        tool_call_ids=("t2",),
        supporting_spans=(span,),
    )
    verdict_model = JudgeVerdict(
        finding_id="F001",
        status=FindingStatus.CONFIRMED,
        rationale="The retained receipt names the process.",
        cited_tool_call_ids=("t2",),
        quoted_spans=(EvidenceQuote(span_id=span_id, tool_call_id="t2", text="malicious.exe"),),
    )
    state = InvestigationState(
        case_notes=serializer_arguments["case_notes"],
        findings=[finding_model],
        turns=2,
    )
    draft = ReportDraft(
        **_REPORT_DRAFT,
        referenced_finding_ids=("F001",),
        referenced_span_ids=(span_id,),
    )
    report_content = render_report_markdown(profile, state, (verdict_model,), draft).encode()
    root_contents = {
        "report.md": report_content,
        "profile.json": _json_bytes(profile.public_dict()),
        "environment.json": b"{}\n",
    }
    root_roles = {
        "report.md": ("report", "text/markdown"),
        "profile.json": ("evidence-profile", "application/json"),
        "environment.json": ("environment", "application/json"),
        "summary.json": ("summary", "application/json"),
        "viewer.html": ("proof-viewer", "text/html"),
    }
    payloads: list[tuple[str, dict[str, Any]]] = [
        ("run.created", {"caps_profile": "strict"}),
        ("caps.configured", asdict(_STRICT_CAPS)),
        (
            "custody.initial.completed",
            {"hashes": initial_hashes, "sizes": {"E001": 1234}, "file_count": 1},
        ),
        ("profile.completed", profile.public_dict()),
        (
            "investigation.started",
            {
                "profile": profile.public_dict(),
                "budget": {
                    "tool_calls": 0,
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "cache_write_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "elapsed_seconds": 0.01,
                    "estimated_cost_usd": 0.0,
                    "fired": None,
                },
            },
        ),
    ]

    def append_model(
        phase: str,
        ordinal: int,
        *,
        message: str,
        function_calls: list[dict[str, Any]],
    ) -> None:
        if phase in {"opening", "investigate"}:
            tools = [_tool_schema("windows.pslist")]
            if phase == "investigate" and typed_done:
                tools.append(investigation_finish_schema())
        else:
            call = function_calls[0]
            tools = [
                _tool_schema(
                    str(call["name"]),
                    tuple(str(key) for key in call["arguments"]),
                )
            ]
        effort, verbosity, maximum, parallel, choice = {
            "opening": ("low", "low", 4_096, True, "required"),
            "investigate": (
                "medium",
                "medium",
                4_096,
                False,
                "required" if typed_done else "auto",
            ),
            "investigation-finalize": (
                "medium",
                "low",
                12_288,
                False,
                {"type": "function", "name": "submit_investigation"},
            ),
            "judge": (
                "high",
                "low",
                12_288,
                False,
                {"type": "function", "name": "submit_judgment"},
            ),
            "report": (
                "low",
                "medium",
                8_192,
                False,
                {"type": "function", "name": "submit_report_draft"},
            ),
        }[phase]
        max_tool_calls = MAX_OPENING_TOOLS if phase == "opening" else 1
        response_payload = _model_payload(
            phase=phase,
            ordinal=f"{ordinal:03d}",
            message=message,
            function_calls=function_calls,
        )
        response_payload.update(model_overrides or {})
        request_input: list[dict[str, Any]] = []
        if phase == "investigation-finalize":
            packet = {
                "controller_request": "Serialize the completed investigation only.",
                "evidence_profile": profile.public_dict(),
                "case_notes_so_far": "Plan followup based on [t1]",
                "receipt_index": [],
            }
            request_input = [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": _canonical(packet)}],
                }
            ]
        payloads.extend(
            [
                (
                    "model.request",
                    {
                        "phase": phase,
                        "requested_model": "gpt-5.6",
                        "instructions": "Strict fixture instructions",
                        "input": request_input,
                        "tools": tools,
                        "previous_response_id": None,
                    },
                ),
                (
                    "model.request.options",
                    {
                        "phase": phase,
                        "parallel_tool_calls": parallel,
                        "tool_choice": choice,
                        "max_output_tokens": maximum,
                        **(
                            {
                                "minimum_output_tokens": (
                                    4_096
                                    if phase in {"investigate", "investigation-finalize", "judge"}
                                    else 1
                                )
                            }
                            if typed_done
                            else {}
                        ),
                        "estimated_input_tokens": 100,
                        "timeout_seconds": 30.0,
                        "store": False,
                        "include": [],
                        "reasoning_context": "current_turn",
                        "reasoning_effort": effort,
                        "text_verbosity": verbosity,
                        "max_tool_calls": max_tool_calls,
                        "prompt_cache_mode": "implicit",
                    },
                ),
                ("model.response", response_payload),
            ]
        )

    append_model(
        "opening",
        1,
        message="",
        function_calls=[_function_call("t1", "windows.pslist", {})],
    )
    payloads.extend(
        [
            (
                "tool.started",
                {
                    "tool_call_id": "t1",
                    "tool_name": "windows.pslist",
                    "arguments": {},
                    "evidence_refs": [{"evidence_id": "E001", "sha256": "a" * 64}],
                },
            ),
            (
                "tool.completed",
                {
                    "tool_call_id": "t1",
                    "tool_name": "windows.pslist",
                    "arguments": {},
                    "evidence_refs": [{"evidence_id": "E001", "sha256": "a" * 64}],
                    "status": "success",
                    "started_at": "2026-07-14T12:00:03+00:00",
                    "ended_at": "2026-07-14T12:00:04+00:00",
                    "duration_ms": 1,
                    "output_sha256": output_hash,
                    "output_first_2kb": output[:2048],
                    "output_artifact_path": output_path,
                    "output_bytes": len(output_bytes),
                    "output_encoding": "utf-8",
                    "output_media_type": "text/plain",
                    "accepted_output_complete": True,
                    "output_artifact": {
                        "path": output_path,
                        "sha256": output_hash,
                        "bytes": len(output_bytes),
                        "encoding": "utf-8",
                        "media_type": "text/plain",
                        "complete": True,
                    },
                    "error": None,
                },
            ),
            (
                "opening.completed",
                {
                    "response_id": "resp_live_001",
                    "selected": 1,
                    "executed": 1,
                    "rejected": 0,
                    "tool_call_ids": ["t1"],
                },
            ),
        ]
    )
    append_model(
        "investigate",
        2,
        message="Plan followup based on [t1]",
        function_calls=[_function_call("t2", "windows.pslist", {})],
    )
    payloads.extend(
        [
            (
                "investigator.notes.updated",
                {
                    "turn": 1,
                    "case_ledger_update": "Plan followup based on [t1]",
                    "case_ledger_update_bytes": len(b"Plan followup based on [t1]"),
                    "case_notes": "Plan followup based on [t1]",
                },
            ),
            (
                "tool.started",
                {
                    "tool_call_id": "t2",
                    "tool_name": "windows.pslist",
                    "arguments": {},
                    "evidence_refs": [{"evidence_id": "E001", "sha256": "a" * 64}],
                },
            ),
            (
                "tool.completed",
                {
                    "tool_call_id": "t2",
                    "tool_name": "windows.pslist",
                    "arguments": {},
                    "evidence_refs": [{"evidence_id": "E001", "sha256": "a" * 64}],
                    "status": "success",
                    "started_at": "2026-07-14T12:00:05+00:00",
                    "ended_at": "2026-07-14T12:00:06+00:00",
                    "duration_ms": 1,
                    "output_sha256": output_hash,
                    "output_first_2kb": output[:2048],
                    "output_artifact_path": output_path,
                    "output_bytes": len(output_bytes),
                    "output_encoding": "utf-8",
                    "output_media_type": "text/plain",
                    "accepted_output_complete": True,
                    "output_artifact": {
                        "path": output_path,
                        "sha256": output_hash,
                        "bytes": len(output_bytes),
                        "encoding": "utf-8",
                        "media_type": "text/plain",
                        "complete": True,
                    },
                    "error": None,
                },
            ),
            (
                "investigator.action",
                {
                    "turn": 1,
                    "tool_call_id": "t2",
                    "tool_name": "windows.pslist",
                    "status": "success",
                },
            ),
        ]
    )
    terminal_calls = (
        [
            _function_call(
                "finish-1",
                INVESTIGATION_FINISH_TOOL_NAME,
                {"status": "DONE"},
            )
        ]
        if typed_done
        else []
    )
    append_model(
        "investigate",
        3,
        message="" if typed_done else "DONE",
        function_calls=terminal_calls,
    )
    done_payload: dict[str, Any] = {"turn": 2, "response_id": "resp_live_003"}
    if typed_done:
        done_payload["terminal_protocol"] = "typed-DONE-v2"
        done_payload["terminal_action_call_id"] = "finish-1"
    payloads.append(("investigator.done", done_payload))
    append_model(
        "investigation-finalize",
        4,
        message="",
        function_calls=[
            _function_call("serialize-1", "submit_investigation", serializer_arguments)
        ],
    )
    payloads.append(
        (
            "investigator.finished",
            {
                "turns": 2,
                "case_ledger": "Plan followup based on [t1]",
                "case_notes": serializer_arguments["case_notes"],
                "findings": [finding],
                "limitations": [],
                "unresolved_questions": [],
            },
        )
    )
    payloads.append(("judge.started", {"finding_count": 1, "receipt_count": 2}))
    append_model(
        "judge",
        5,
        message="",
        function_calls=[_function_call("judge-1", "submit_judgment", judgment_arguments)],
    )
    payloads.append(("judge.completed", {"verdicts": [verdict]}))
    payloads.append(("report.started", {"status": "COMPLETE"}))
    append_model(
        "report",
        6,
        message="",
        function_calls=[_function_call("report-1", "submit_report_draft", report_arguments)],
    )
    payloads.extend(
        [
            (
                "report.completed",
                {
                    "status": "COMPLETE",
                    "characters": len(report_content.decode("utf-8")),
                    "renderer": "deterministic-markdown-v1",
                    "finding_ids": ["F001"],
                    "span_ids": [span_id],
                    "report_sha256": hashlib.sha256(report_content).hexdigest(),
                    "report_bytes": len(report_content),
                },
            ),
            (
                "investigation.completed",
                (
                    {
                        "status": terminal_status,
                        "finding_count": 1,
                        "verdict_count": 1,
                        "budget": {
                            "tool_calls": 2,
                            "input_tokens": 6 * _FIXTURE_USAGE.input_tokens,
                            "cached_input_tokens": 0,
                            "cache_write_tokens": 0,
                            "output_tokens": 6 * _FIXTURE_USAGE.output_tokens,
                            "total_tokens": 6 * _FIXTURE_USAGE.total_tokens,
                            "elapsed_seconds": 1.0,
                            "estimated_cost_usd": 6 * _FIXTURE_CALL_COST,
                            "fired": None,
                        },
                    }
                    if terminal_status == "COMPLETE"
                    else {"status": terminal_status}
                ),
            ),
            (
                "custody.final.completed",
                {"hashes": initial_hashes, "match": True, "mount_released": True},
            ),
        ]
    )

    def user_input(packet: dict[str, Any]) -> dict[str, Any]:
        return {
            "role": "user",
            "content": [{"type": "input_text", "text": _canonical(packet)}],
        }

    def completed_before(before: int) -> list[dict[str, Any]]:
        return [
            payload
            for index, (event_type, payload) in enumerate(payloads)
            if index < before and event_type == "tool.completed"
        ]

    def receipt_index(before: int) -> list[dict[str, Any]]:
        keys = (
            "tool_call_id",
            "tool_name",
            "arguments",
            "status",
            "evidence_refs",
            "output_sha256",
            "output_bytes",
            "accepted_output_complete",
            "error",
        )
        return [{key: receipt.get(key) for key in keys} for receipt in completed_before(before)]

    def observation(call_id: str) -> list[dict[str, Any]]:
        receipt = next(
            payload
            for event_type, payload in payloads
            if event_type == "tool.completed" and payload.get("tool_call_id") == call_id
        )
        model_output = ToolResult(
            call_id=call_id,
            tool_name=str(receipt["tool_name"]),
            arguments=dict(receipt["arguments"]),
            output=output,
            output_sha256=output_hash,
            status=str(receipt["status"]),
            started_at="",
            ended_at="",
            duration_ms=0,
        ).model_output()
        encoded = model_output.encode("utf-8")
        return [
            {
                "type": "function_call",
                "call_id": call_id,
                "name": receipt["tool_name"],
                "arguments": _canonical(receipt["arguments"]),
            },
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output_sha256": hashlib.sha256(encoded).hexdigest(),
                "output_first_2kb": encoded[:2048].decode("utf-8", errors="ignore"),
                "output_bytes": len(encoded),
            },
        ]

    def request_budget(before: int, elapsed: float) -> dict[str, Any]:
        prior_responses = [
            payload
            for index, (event_type, payload) in enumerate(payloads)
            if index < before and event_type == "model.response"
        ]
        return {
            "tool_calls": sum(
                index < before and event_type == "tool.started"
                for index, (event_type, _payload) in enumerate(payloads)
            ),
            "input_tokens": sum(
                int(response["token_counts"]["input_tokens"]) for response in prior_responses
            ),
            "cached_input_tokens": sum(
                int(response["token_counts"]["cached_input_tokens"]) for response in prior_responses
            ),
            "cache_write_tokens": sum(
                int(response["token_counts"]["cache_write_tokens"]) for response in prior_responses
            ),
            "output_tokens": sum(
                int(response["token_counts"]["output_tokens"]) for response in prior_responses
            ),
            "total_tokens": sum(
                int(response["token_counts"]["provider_total_tokens"])
                for response in prior_responses
            ),
            "elapsed_seconds": elapsed,
            "estimated_cost_usd": sum(
                float(response["call_cost_usd_estimate"]) for response in prior_responses
            ),
            "fired": None,
        }

    request_positions = [
        (index, payload)
        for index, (event_type, payload) in enumerate(payloads)
        if event_type == "model.request"
    ]
    by_phase: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, request in request_positions:
        by_phase.setdefault(str(request["phase"]), []).append((index, request))

    by_phase["opening"][0][1]["input"] = [user_input({"evidence_profile": profile.public_dict()})]
    investigate_packets = (
        (
            "",
            0,
            ["t1"],
            0.10,
        ),
        (
            "Plan followup based on [t1]",
            1,
            ["t2"],
            0.20,
        ),
    )
    for (before, request), (ledger, turns, latest_ids, elapsed) in zip(
        by_phase["investigate"],
        investigate_packets,
        strict=True,
    ):
        packet = {
            "evidence_profile": profile.public_dict(),
            "case_ledger": {
                "case_notes": ledger,
                "turns_completed": turns,
                "limitations": [],
                "unresolved_questions": [],
            },
            "receipt_index": receipt_index(before),
            "budget": request_budget(before, elapsed),
            "latest_observation_call_ids": latest_ids,
        }
        request["input"] = [
            user_input(packet),
            *(item for call_id in latest_ids for item in observation(call_id)),
        ]

    finalizer_index, finalizer_request = by_phase["investigation-finalize"][0]
    finalizer_request["input"] = [
        user_input(
            {
                "controller_request": "Serialize the completed investigation only.",
                "evidence_profile": profile.public_dict(),
                "case_notes_so_far": "Plan followup based on [t1]",
                "receipt_index": receipt_index(finalizer_index),
            }
        ),
        *observation("t1"),
        *observation("t2"),
    ]
    judge_index, judge_request = by_phase["judge"][0]
    judge_request["input"] = [
        user_input(
            {
                "evidence_profile": profile.public_dict(),
                "case_notes": serializer_arguments["case_notes"],
                "findings": [finding],
                "receipt_index": receipt_index(judge_index),
            }
        )
    ]
    _report_index, report_request = by_phase["report"][0]
    report_request["input"] = [
        user_input(
            {
                "run_status": "COMPLETE",
                "evidence_profile": profile.public_dict(),
                "case_notes": serializer_arguments["case_notes"],
                "findings": [finding],
                "judge_verdicts": [verdict],
                "limitations": [],
                "unresolved_questions": [],
            }
        )
    ]

    preterminal_events: list[dict[str, Any]] = []
    previous_hash = GENESIS_HASH
    for sequence, (event_type, payload) in enumerate(payloads, start=1):
        event = _event(sequence, previous_hash, event_type, payload)
        preterminal_events.append(event)
        previous_hash = event["entry_hash"]
    summary = build_summary(
        run_id="run-proof-001",
        entries=preterminal_events,
        status=terminal_status,
        exit_code=exit_code,
        profile=profile,
        cap=None,
        reason=None,
        mount_released=True,
    )
    root_contents["summary.json"] = _json_bytes(summary)
    root_contents["viewer.html"] = render_viewer_html(
        run_id="run-proof-001",
        status=terminal_status,
        profile=profile,
        summary=summary,
        report_markdown=report_content.decode(),
        audit_entries=preterminal_events,
    ).encode()
    payloads.extend(
        [
            *(
                (
                    "artifact.written",
                    _artifact(path, root_contents[path], role=role, media_type=media_type),
                )
                for path, (role, media_type) in root_roles.items()
            ),
            (
                "run.completed",
                {
                    "status": terminal_status,
                    "exit_code": exit_code,
                    "cap": None,
                    "reason": None,
                    "mount_released": True,
                },
            ),
        ]
    )
    events: list[dict[str, Any]] = []
    previous_hash = GENESIS_HASH
    for sequence, (event_type, payload) in enumerate(payloads, start=1):
        event = _event(sequence, previous_hash, event_type, payload)
        events.append(event)
        previous_hash = event["entry_hash"]
    return events, root_contents


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


def _rechain_audit(
    run_directory: Path,
    manifest: dict[str, Any],
    mutate: Any,
) -> None:
    entries = [
        json.loads(line)
        for line in (run_directory / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    mutate(entries)
    previous_hash = GENESIS_HASH
    for sequence, entry in enumerate(entries, start=1):
        entry["sequence"] = sequence
        entry["previous_hash"] = previous_hash
        unsigned = {key: value for key, value in entry.items() if key != "entry_hash"}
        entry["entry_hash"] = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()
        previous_hash = entry["entry_hash"]
    content = b"".join((_canonical(entry) + "\n").encode("utf-8") for entry in entries)
    (run_directory / "audit.jsonl").write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    manifest["audit"].update(
        {
            "sha256": digest,
            "bytes": len(content),
            "entry_count": len(entries),
            "final_entry_hash": entries[-1]["entry_hash"],
        }
    )
    audit_artifact = next(
        artifact for artifact in manifest["artifacts"] if artifact["path"] == "audit.jsonl"
    )
    audit_artifact["sha256"] = digest
    audit_artifact["bytes"] = len(content)
    _rewrite_manifest(run_directory, manifest)


def _replace_root_artifact(
    run_directory: Path,
    manifest: dict[str, Any],
    path: str,
    content: bytes,
    *,
    mutate_extra: Any | None = None,
) -> None:
    (run_directory / path).write_bytes(content)
    descriptor = next(artifact for artifact in manifest["artifacts"] if artifact["path"] == path)
    descriptor["sha256"] = hashlib.sha256(content).hexdigest()
    descriptor["bytes"] = len(content)

    def mutate(entries: list[dict[str, Any]]) -> None:
        write = next(
            entry
            for entry in entries
            if entry["event_type"] == "artifact.written" and entry["payload"].get("path") == path
        )
        write["payload"] = dict(descriptor)
        if mutate_extra is not None:
            mutate_extra(entries)

    _rechain_audit(run_directory, manifest, mutate)


def _build_bundle(
    run_directory: Path,
    *,
    output: str = "PID 4242 malicious.exe\n",
    terminal_status: str = "COMPLETE",
    exit_code: int = 0,
    model_payload: dict[str, Any] | None = None,
    complete_lifecycle: bool = False,
    model_overrides: dict[str, Any] | None = None,
    typed_done: bool = False,
) -> dict[str, Any]:
    run_directory.mkdir()
    output_content = output.encode("utf-8")
    output_hash = hashlib.sha256(output_content).hexdigest()
    output_path = f"tool-outputs/{output_hash}.txt"
    output_target = run_directory / Path(output_path)
    output_target.parent.mkdir()
    output_target.write_bytes(output_content)

    if complete_lifecycle:
        events, root_contents = _complete_events(
            output,
            terminal_status=terminal_status,
            exit_code=exit_code,
            model_overrides=model_overrides,
            typed_done=typed_done,
        )
    else:
        events = _events(
            output,
            terminal_status=terminal_status,
            exit_code=exit_code,
            model_payload=model_payload,
        )
        root_contents = {}
    audit_content = b"".join((_canonical(event) + "\n").encode("utf-8") for event in events)
    (run_directory / "audit.jsonl").write_bytes(audit_content)
    audit_hash = hashlib.sha256(audit_content).hexdigest()
    if complete_lifecycle:
        for relative_path, content in root_contents.items():
            (run_directory / relative_path).write_bytes(content)
    artifacts = [
        _artifact(
            "audit.jsonl",
            audit_content,
            role="audit",
            media_type="application/x-ndjson",
        ),
        _artifact(output_path, output_content, role="tool-output", media_type="text/plain"),
    ]
    if complete_lifecycle:
        root_roles = {
            "report.md": ("report", "text/markdown"),
            "profile.json": ("evidence-profile", "application/json"),
            "environment.json": ("environment", "application/json"),
            "summary.json": ("summary", "application/json"),
            "viewer.html": ("proof-viewer", "text/html"),
        }
        artifacts.extend(
            _artifact(path, root_contents[path], role=role, media_type=media_type)
            for path, (role, media_type) in root_roles.items()
        )
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
        "artifacts": artifacts,
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


def test_incomplete_synthetic_bundle_cannot_claim_strict_completion(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    _assert_failed_with(result, "strict completion requires artifact: report.md")
    _assert_failed_with(result, "model.request/model.response phase sequences differ")


def test_complete_recorded_gpt56_lifecycle_verifies_offline(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory, complete_lifecycle=True)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    assert result.passed
    assert result.ok
    assert result.run_id == "run-proof-001"
    assert result.terminal_status == "COMPLETE"
    assert result.verified_audit_entries == 44
    assert result.verified_artifacts == 7
    assert result.warnings == (RECORDED_CUSTODY_NOTICE, RECORDED_PROVIDER_NOTICE)
    assert result.public_dict()["custody"] == {
        "recorded_custody_only": True,
        "original_evidence_rehashed": False,
        "statement": RECORDED_CUSTODY_NOTICE,
    }


def test_complete_typed_done_v2_lifecycle_verifies_offline(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    assert result.passed, result.public_dict()
    assert result.terminal_status == "COMPLETE"
    assert result.verified_audit_entries == 44


def test_literal_done_v1_low_output_ceilings_remain_verifier_readable(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            if entry["event_type"] == "model.request.options" and entry["payload"]["phase"] in {
                "investigate",
                "investigation-finalize",
                "judge",
            }:
                entry["payload"]["max_output_tokens"] = 2_048

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    assert result.passed, result.public_dict()


def test_typed_done_v2_requires_audited_minimum_output_tokens(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "investigate"
        )
        del options["payload"]["minimum_output_tokens"]

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "omits typed-DONE-v2 minimum_output_tokens")


def test_typed_done_v2_rejects_output_ceiling_below_phase_minimum(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "investigate"
        )
        options["payload"]["max_output_tokens"] = 2_048

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "max_output_tokens violates the investigate phase minimum")


def test_typed_done_v2_rejects_wrong_audited_phase_minimum(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "investigate"
        )
        options["payload"]["minimum_output_tokens"] = 1

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(
        result,
        "minimum_output_tokens violates the investigate phase policy",
    )


@pytest.mark.parametrize("replacement", [{}, []])
def test_malformed_investigate_tool_choice_fails_with_specific_diagnostic(
    tmp_path: Path,
    replacement: Any,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "investigate"
        )
        options["payload"]["tool_choice"] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "investigate tool_choice must be a string")


def test_typed_done_requires_required_tool_choice(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "investigate"
        )
        options["payload"]["tool_choice"] = "auto"

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(
        result,
        "typed-DONE-v2 investigate tool_choice must be required",
    )
    assert not any("verification stopped safely" in error for error in result.errors)


@pytest.mark.parametrize("replacement", [{}, []])
def test_malformed_legacy_terminal_protocol_fails_with_specific_diagnostic(
    tmp_path: Path,
    replacement: Any,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        done = next(entry for entry in entries if entry["event_type"] == "investigator.done")
        done["payload"]["terminal_protocol"] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "legacy investigator.done terminal_protocol must be text or null")
    assert not any("verification stopped safely" in error for error in result.errors)


def test_typed_done_terminal_call_id_is_bound_and_unique(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        terminal = [
            entry
            for entry in entries
            if entry["event_type"] == "model.response"
            and entry["payload"]["phase"] == "investigate"
        ][-1]
        terminal["payload"]["function_calls"][0]["call_id"] = "t1"
        done = next(entry for entry in entries if entry["event_type"] == "investigator.done")
        done["payload"]["terminal_action_call_id"] = "t1"

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "typed terminal action reuses a forensic function call_id")


def test_typed_done_event_must_bind_terminal_action_call_id(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True, typed_done=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        done = next(entry for entry in entries if entry["event_type"] == "investigator.done")
        done["payload"]["terminal_action_call_id"] = "forged-finish"

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(
        result,
        "investigator.done terminal_action_call_id does not match terminal DONE",
    )


def test_strict_evidence_span_resolves_beyond_legacy_2kb_prefix(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    output = ("x" * 3_000) + "malicious.exe\n"
    _build_bundle(run_directory, output=output, complete_lifecycle=True)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    assert result.passed, result.public_dict()


def test_strict_reconstructs_large_model_view_delivery_envelope(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    output = ("x" * 70_000) + "malicious.exe\n"
    _build_bundle(run_directory, output=output, complete_lifecycle=True)

    result = verify_run(run_directory, require_complete=True, require_live_gpt56=True)

    assert result.passed, result.public_dict()


def test_strict_rejects_model_tool_receipt_name_mismatch_after_full_rechain(
    tmp_path: Path,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        opening = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.response" and entry["payload"]["phase"] == "opening"
        )
        opening["payload"]["function_calls"][0]["name"] = "windows.netscan"

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "tool name disagrees with its model function call")


def test_strict_rejects_phase_labels_with_no_model_function_calls(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            if entry["event_type"] == "model.response":
                entry["payload"]["function_calls"] = []

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "opening response must contain between one and 12")


@pytest.mark.parametrize(
    ("event_type", "phase", "field", "replacement", "expected"),
    [
        (
            "model.request.options",
            "opening",
            "max_tool_calls",
            20,
            "max_tool_calls violates the opening phase policy",
        ),
        (
            "model.request.options",
            "investigate",
            "prompt_cache_mode",
            "explicit",
            "prompt_cache_mode violates the investigate phase policy",
        ),
        (
            "model.request",
            "judge",
            "previous_response_id",
            "resp_replayed",
            "replays provider transcript state",
        ),
    ],
)
def test_strict_binds_stateless_phase_options(
    tmp_path: Path,
    event_type: str,
    phase: str,
    field: str,
    replacement: Any,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        event = next(
            entry
            for entry in entries
            if entry["event_type"] == event_type and entry["payload"]["phase"] == phase
        )
        event["payload"][field] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def test_strict_binds_each_visible_case_ledger_update(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        notes = next(
            entry for entry in entries if entry["event_type"] == "investigator.notes.updated"
        )
        notes["payload"]["case_ledger_update"] = "Forged update [t1]"
        notes["payload"]["case_ledger_update_bytes"] = len(b"Forged update [t1]")

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "does not bind the model ledger")


def test_complete_verification_requires_judge_quoted_spans(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        judge_response = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.response" and entry["payload"]["phase"] == "judge"
        )
        judge_response["payload"]["function_calls"][0]["arguments"]["verdicts"][0].pop(
            "quoted_spans"
        )
        judge_completed = next(
            entry for entry in entries if entry["event_type"] == "judge.completed"
        )
        judge_completed["payload"]["verdicts"][0].pop("quoted_spans")

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "quoted_spans must be an array")


def test_occurrence_count_is_recomputed_from_verified_tool_output(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        finished = next(
            entry for entry in entries if entry["event_type"] == "investigator.finished"
        )
        finished["payload"]["findings"][0]["supporting_spans"][0]["occurrence_count"] = 2

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "verified artifact contains 1")


def test_artifact_written_full_descriptor_must_match_manifest(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        write = next(
            entry
            for entry in entries
            if entry["event_type"] == "artifact.written"
            and entry["payload"]["path"] == "viewer.html"
        )
        write["payload"]["bytes"] += 1

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "descriptor does not match the manifest")


def test_manifest_consistent_active_viewer_is_rejected_before_opening(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)
    active_viewer = (
        "<!doctype html><html><head>"
        f'<meta http-equiv="Content-Security-Policy" content="{_CSP}">'
        "<title>Proof</title></head><body>"
        "<script>fetch('https://attacker.invalid')</script>"
        "</body></html>\n"
    ).encode()
    _replace_root_artifact(run_directory, manifest, "viewer.html", active_viewer)

    result = verify_run(run_directory)

    _assert_failed_with(result, "proof viewer is not inert")


def test_manifest_consistent_inert_viewer_replacement_is_rejected(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)
    _replace_root_artifact(run_directory, manifest, "viewer.html", _SAFE_VIEWER)

    result = verify_run(run_directory)

    _assert_failed_with(result, "not the exact deterministic rendering of the proof bundle")


def test_self_consistent_arbitrary_report_cannot_replace_authoritative_render(
    tmp_path: Path,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)
    original = (run_directory / "report.md").read_bytes()
    arbitrary = original.replace(
        b"Offline bundle verification cannot authenticate self-recorded provider IDs.",
        b"Offline verification authenticates every provider-issued identifier.",
    )
    assert arbitrary != original

    def update_report_receipt(entries: list[dict[str, Any]]) -> None:
        completed = next(entry for entry in entries if entry["event_type"] == "report.completed")
        completed["payload"]["characters"] = len(arbitrary.decode("utf-8"))
        completed["payload"]["report_bytes"] = len(arbitrary)
        completed["payload"]["report_sha256"] = hashlib.sha256(arbitrary).hexdigest()

    _replace_root_artifact(
        run_directory,
        manifest,
        "report.md",
        arbitrary,
        mutate_extra=update_report_receipt,
    )

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "not the exact deterministic rendering")


@pytest.mark.parametrize(
    ("phase", "field", "replacement", "expected"),
    [
        (
            "investigation-finalize",
            "case_notes",
            "Rewritten unrecorded notes [t2]",
            "case_notes differs from serializer arguments",
        ),
        (
            "judge",
            "rationale",
            "Unrecorded rationale",
            "differs from submit_judgment",
        ),
        (
            "report",
            "executive_summary",
            "Unrendered executive claim",
            "not the exact deterministic rendering",
        ),
    ],
)
def test_forced_serializer_arguments_are_bound_to_controller_outputs(
    tmp_path: Path,
    phase: str,
    field: str,
    replacement: str,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        response = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.response" and entry["payload"]["phase"] == phase
        )
        arguments = response["payload"]["function_calls"][0]["arguments"]
        if phase == "judge":
            arguments["verdicts"][0][field] = replacement
        else:
            arguments[field] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def test_profile_event_and_artifact_cannot_be_rewritten_away_from_custody(
    tmp_path: Path,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)
    profile = json.loads((run_directory / "profile.json").read_text(encoding="utf-8"))
    profile["hashes"]["E001"] = "b" * 64
    profile["evidence"][0]["sha256"] = "b" * 64

    def bind_rewritten_profile(entries: list[dict[str, Any]]) -> None:
        completed = next(entry for entry in entries if entry["event_type"] == "profile.completed")
        completed["payload"] = profile
        started = next(entry for entry in entries if entry["event_type"] == "investigation.started")
        started["payload"]["profile"] = profile

    _replace_root_artifact(
        run_directory,
        manifest,
        "profile.json",
        _json_bytes(profile),
        mutate_extra=bind_rewritten_profile,
    )

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "profile hashes do not exactly match initial custody")


@pytest.mark.parametrize(
    ("mutate_profile", "expected"),
    [
        (lambda profile: profile.update({"shape": "disk-only"}), "shape disagrees"),
        (
            lambda profile: profile.update({"filesystems": ["ntfs"], "fs": ["ntfs"]}),
            "filesystems disagree",
        ),
        (lambda profile: profile.update({"os": "linux"}), "os disagrees"),
        (
            lambda profile: profile["warnings"].append(
                "OS CONFLICT: disk and memory content disagree; "
                "OS-specific tool families are disabled."
            ),
            "route warnings disagree",
        ),
    ],
)
def test_profile_route_is_derived_from_its_evidence_inventory(
    tmp_path: Path,
    mutate_profile: Any,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)
    profile = json.loads((run_directory / "profile.json").read_text(encoding="utf-8"))
    mutate_profile(profile)

    def bind_rewritten_profile(entries: list[dict[str, Any]]) -> None:
        completed = next(entry for entry in entries if entry["event_type"] == "profile.completed")
        completed["payload"] = profile
        started = next(entry for entry in entries if entry["event_type"] == "investigation.started")
        started["payload"]["profile"] = profile

    _replace_root_artifact(
        run_directory,
        manifest,
        "profile.json",
        _json_bytes(profile),
        mutate_extra=bind_rewritten_profile,
    )

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def test_strict_rejects_function_argument_value_outside_recorded_type(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        request = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request"
            and entry["payload"]["phase"] == "investigation-finalize"
        )
        status_schema = request["payload"]["tools"][0]["parameters"]["properties"]["status"]
        status_schema["type"] = "integer"

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "argument 'status' has the wrong type")


def test_nested_tool_artifact_descriptor_is_semantically_bound(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        receipt = next(
            entry
            for entry in entries
            if entry["event_type"] == "tool.completed" and entry["payload"]["tool_call_id"] == "t2"
        )
        receipt["payload"]["output_artifact"]["complete"] = False

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "nested output_artifact is not bound")


def test_complete_response_contract_applies_without_live_provider_claim(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        response = next(entry for entry in entries if entry["event_type"] == "model.response")
        response["payload"]["status"] = "incomplete"
        response["payload"]["incomplete_details"] = {"reason": "max_output_tokens"}

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "status must equal completed")


@pytest.mark.parametrize("phase", ["opening", "investigate", "judge", "report"])
def test_strict_binds_every_controller_model_input(
    tmp_path: Path,
    phase: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        request = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request" and entry["payload"]["phase"] == phase
        )
        request["payload"]["input"] = []

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "audited user packet" if phase == "investigate" else "input is not")


def test_strict_binds_finalizer_observation_tail(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        request = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request"
            and entry["payload"]["phase"] == "investigation-finalize"
        )
        request["payload"]["input"].pop()

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "input is not the exact deterministic controller packet")


@pytest.mark.parametrize(
    ("turn", "field", "replacement", "expected"),
    [
        (0, "total_tokens", 999, "budget total_tokens differs"),
        (1, "elapsed_seconds", 0.05, "elapsed_seconds decreases"),
        (1, "elapsed_seconds", 600.0, "elapsed_seconds reaches the wall cap"),
    ],
)
def test_strict_binds_investigate_packet_budget(
    tmp_path: Path,
    turn: int,
    field: str,
    replacement: Any,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        requests = [
            entry
            for entry in entries
            if entry["event_type"] == "model.request" and entry["payload"]["phase"] == "investigate"
        ]
        text = requests[turn]["payload"]["input"][0]["content"][0]["text"]
        packet = json.loads(text)
        packet["budget"][field] = replacement
        requests[turn]["payload"]["input"][0]["content"][0]["text"] = _canonical(packet)

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def test_strict_rejects_response_usage_above_request_output_ceiling(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "opening"
        )
        options["payload"]["max_output_tokens"] = 1

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "response output_tokens exceed the audited request maximum")


def test_strict_rejects_request_timeout_above_audited_wall_cap(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        options = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.request.options"
            and entry["payload"]["phase"] == "opening"
        )
        options["payload"]["timeout_seconds"] = 601.0

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "timeout_seconds exceeds max_wall_seconds")


@pytest.mark.parametrize("status", ["capped", "rejected"])
def test_strict_rejects_unreachable_tool_receipt_in_complete_lifecycle(
    tmp_path: Path,
    status: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        receipt = next(
            entry
            for entry in entries
            if entry["event_type"] == "tool.completed" and entry["payload"]["tool_call_id"] == "t1"
        )
        receipt["payload"]["status"] = status

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "unreachable capped/rejected tool receipts")


@pytest.mark.parametrize(
    ("event_type", "field", "replacement", "expected"),
    [
        ("judge.started", "finding_count", True, "must be a nonnegative integer"),
        ("judge.started", "finding_count", 999, "finding_count differs"),
        ("judge.started", "receipt_count", 999, "receipt_count differs"),
        ("investigation.completed", "finding_count", 999, "finding_count differs"),
        ("investigation.completed", "verdict_count", 999, "verdict_count differs"),
    ],
)
def test_strict_binds_controller_lifecycle_counts(
    tmp_path: Path,
    event_type: str,
    field: str,
    replacement: int,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        event = next(entry for entry in entries if entry["event_type"] == event_type)
        event["payload"][field] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def test_strict_rejects_raw_output_items_as_duplicate_response_authority(
    tmp_path: Path,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        response = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.response" and entry["payload"]["phase"] == "opening"
        )
        response["payload"]["output_items"] = [
            {
                "type": "function_call",
                "call_id": "contradictory-call",
                "name": "windows.netscan",
                "arguments": "{}",
            }
        ]

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "does not match the normalized response shape")


def test_strict_rejects_whitespace_around_terminal_done(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        terminal = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.response"
            and entry["payload"]["phase"] == "investigate"
            and not entry["payload"]["function_calls"]
        )
        terminal["payload"]["message"] = "DONE\n"

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "terminal investigate response must be the literal DONE")


def test_strict_recomputes_cost_when_all_recorded_cost_receipts_are_zeroed(
    tmp_path: Path,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            if entry["event_type"] == "model.response":
                entry["payload"]["call_cost_usd_estimate"] = 0.0
                entry["payload"]["running_cost_usd_estimate"] = 0.0
        completed = next(
            entry for entry in entries if entry["event_type"] == "investigation.completed"
        )
        completed["payload"]["budget"]["estimated_cost_usd"] = 0.0

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "call cost disagrees with audited usage and pricing")


def test_strict_rejects_rechained_price_table_understatement(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        configured = next(entry for entry in entries if entry["event_type"] == "caps.configured")
        for field in (
            "input_usd_per_million",
            "cached_input_usd_per_million",
            "cache_write_usd_per_million",
            "output_usd_per_million",
        ):
            configured["payload"][field] = 0.0
        for entry in entries:
            if entry["event_type"] == "model.response":
                entry["payload"]["call_cost_usd_estimate"] = 0.0
                entry["payload"]["running_cost_usd_estimate"] = 0.0
        completed = next(
            entry for entry in entries if entry["event_type"] == "investigation.completed"
        )
        completed["payload"]["budget"]["estimated_cost_usd"] = 0.0

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "disagrees with code-owned GPT-5.6 pricing")


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    [
        ("tool_calls", 1, "final budget tool_calls disagrees"),
        ("input_tokens", 479, "final budget input_tokens disagrees"),
        ("total_tokens", 599, "final budget total_tokens disagrees"),
        ("estimated_cost_usd", 0.0, "estimated_cost_usd disagrees"),
        ("fired", "MAX_COST_USD", "must not record a fired cap"),
    ],
)
def test_strict_binds_final_budget_to_recomputed_accounting(
    tmp_path: Path,
    field: str,
    replacement: Any,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        completed = next(
            entry for entry in entries if entry["event_type"] == "investigation.completed"
        )
        completed["payload"]["budget"][field] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    [
        ("max_tool_calls", 1, "exceeds max_tool_calls"),
        ("max_total_tokens", 599, "exceeds max_total_tokens"),
        ("max_cost_usd", 0.005, "exceeds max_cost_usd"),
        ("max_wall_seconds", 1.0, "reaches or exceeds max_wall_seconds"),
    ],
)
def test_strict_enforces_audited_caps_against_final_budget(
    tmp_path: Path,
    field: str,
    replacement: Any,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        configured = next(entry for entry in entries if entry["event_type"] == "caps.configured")
        configured["payload"][field] = replacement

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def _insert_recovered_retry(
    entries: list[dict[str, Any]],
    *,
    status_code: int | None = 503,
    error_type: str = "ServiceUnavailableError",
    next_timeout: float = 29.75,
) -> None:
    response_index = next(
        index
        for index, entry in enumerate(entries)
        if entry["event_type"] == "model.response" and entry["payload"]["phase"] == "opening"
    )
    response = entries[response_index]

    def retry_entry(event_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            **response,
            "event_id": event_id,
            "event_type": event_type,
            "actor": "model-client",
            "payload": payload,
        }

    retry_events = [
        retry_entry(
            "retry-error-001",
            "model.attempt.error",
            {
                "phase": "opening",
                "attempt": 1,
                "max_attempts": 3,
                "retryable": True,
                "status_code": status_code,
                "request_id": "req_failed_001",
                "error_type": error_type,
                "error": "temporary provider failure",
                "billing_exposure": "unknown_after_dispatch",
            },
        ),
        retry_entry(
            "retry-scheduled-001",
            "model.retry.scheduled",
            {
                "phase": "opening",
                "attempt": 1,
                "next_attempt": 2,
                "max_attempts": 3,
                "delay_seconds": 0.25,
                "next_timeout_seconds": next_timeout,
            },
        ),
        retry_entry(
            "retry-succeeded-001",
            "model.retry.succeeded",
            {
                "phase": "opening",
                "attempt": 2,
                "max_attempts": 3,
                "response_id": response["payload"]["response_id"],
                "request_id": response["payload"]["request_id"],
                "provider_model": response["payload"]["provider_model"],
                "status": response["payload"]["status"],
            },
        ),
    ]
    entries[response_index:response_index] = retry_events


def test_strict_accepts_a_bounded_recovered_provider_retry(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    _rechain_audit(run_directory, manifest, _insert_recovered_retry)

    result = verify_run(run_directory, require_complete=True)

    assert result.passed, result.public_dict()


@pytest.mark.parametrize(
    ("status_code", "error_type", "next_timeout", "expected"),
    [
        (None, "ValueError", 29.75, "not a retryable transport type"),
        (503, "ServiceUnavailableError", 31.0, "exceeds the request timeout"),
    ],
)
def test_strict_rejects_runtime_impossible_recovered_retry(
    tmp_path: Path,
    status_code: int | None,
    error_type: str,
    next_timeout: float,
    expected: str,
) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        _insert_recovered_retry(
            entries,
            status_code=status_code,
            error_type=error_type,
            next_timeout=next_timeout,
        )

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, expected)


def test_strict_rejects_orphaned_retry_event(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        template = entries[0]
        entries.insert(
            1,
            {
                **template,
                "event_id": "orphan-retry-001",
                "event_type": "model.retry.succeeded",
                "actor": "model-client",
                "payload": {
                    "phase": "opening",
                    "attempt": 2,
                    "max_attempts": 3,
                    "response_id": "orphan",
                    "request_id": "orphan",
                    "provider_model": "gpt-5.6",
                    "status": "completed",
                },
            },
        )

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "orphaned or unbound model retry events")


def test_strict_rejects_oversized_self_consistent_case_ledger(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)
    oversized = "x" * 8193

    def mutate(entries: list[dict[str, Any]]) -> None:
        response = next(
            entry
            for entry in entries
            if entry["event_type"] == "model.response"
            and entry["payload"]["phase"] == "investigate"
            and entry["payload"]["function_calls"]
        )
        response["payload"]["message"] = oversized
        notes = next(
            entry for entry in entries if entry["event_type"] == "investigator.notes.updated"
        )
        notes["payload"] = {
            "turn": 1,
            "case_ledger_update": oversized,
            "case_ledger_update_bytes": len(oversized.encode()),
            "case_notes": oversized,
        }
        finished = next(
            entry for entry in entries if entry["event_type"] == "investigator.finished"
        )
        finished["payload"]["case_ledger"] = oversized

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "ledger update exceeds 8192 UTF-8 bytes")


def test_strict_rejects_judge_request_before_judge_started(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        started_index = next(
            index for index, entry in enumerate(entries) if entry["event_type"] == "judge.started"
        )
        started = entries.pop(started_index)
        response_index = next(
            index
            for index, entry in enumerate(entries)
            if entry["event_type"] == "model.response" and entry["payload"]["phase"] == "judge"
        )
        entries.insert(response_index + 1, started)

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "judge model transaction is outside its lifecycle phase window")


def test_complete_lifecycle_rejects_terminal_failure_events(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    manifest = _build_bundle(run_directory, complete_lifecycle=True)

    def mutate(entries: list[dict[str, Any]]) -> None:
        opening_index = next(
            index
            for index, entry in enumerate(entries)
            if entry["event_type"] == "opening.completed"
        )
        template = entries[opening_index]
        entries.insert(
            opening_index + 1,
            {
                **template,
                "event_id": "protocol-failure-001",
                "event_type": "model.protocol_error",
                "payload": {"phase": "opening", "error": "forged failure"},
            },
        )

    _rechain_audit(run_directory, manifest, mutate)

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "contains terminal failure events")


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
    _build_bundle(run_directory, complete_lifecycle=True, model_overrides=override)

    ordinary = verify_run(run_directory)
    strict = verify_run(run_directory, require_live_gpt56=True)

    assert ordinary.passed
    _assert_failed_with(strict, expected)


def test_complete_proof_rejects_luna_as_a_sol_forensic_response(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(
        run_directory,
        complete_lifecycle=True,
        model_overrides={"provider_model": "gpt-5.6-luna-2026-07-14"},
    )

    result = verify_run(run_directory, require_complete=True)

    _assert_failed_with(result, "provider_model is not GPT-5.6 Sol")


def test_strict_live_requires_complete_terminal(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(
        run_directory,
        terminal_status="PARTIAL",
        exit_code=3,
        complete_lifecycle=True,
    )

    result = verify_run(run_directory, require_live_gpt56=True)

    _assert_failed_with(result, "requires a COMPLETE run")


def test_verification_never_opens_a_network_socket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_directory = tmp_path / "run"
    _build_bundle(run_directory, complete_lifecycle=True)

    def forbidden_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("offline verifier attempted network access")

    monkeypatch.setattr(socket, "socket", forbidden_socket)

    assert verify_run(run_directory, require_live_gpt56=True).passed
