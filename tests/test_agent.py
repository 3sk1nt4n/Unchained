"""End-to-end controller tests with fake model and fake typed forensic tool."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import ManualClock
from unchained.agent import (
    MAX_CASE_LEDGER_UPDATE_BYTES,
    AgentProtocolError,
    UnchainedAgent,
    _parse_investigation,
    _parse_verdicts,
    _response_history_items,
    _submit_judgment_schema,
)
from unchained.audit import AuditLog
from unchained.caps import CapConfig, CapKind, RunBudget
from unchained.model import ModelRequest
from unchained.models import (
    INVESTIGATION_FINISH_TOOL_NAME,
    EvidenceItem,
    EvidenceProfile,
    FindingStatus,
    FunctionCall,
    ModelResponse,
    ModelUsage,
    RunStatus,
)
from unchained.prompts import INVESTIGATOR_PROMPT
from unchained.tools import ToolDefinition, ToolRegistry

EMPTY_PARAMETERS = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}


def test_response_history_removes_provider_only_function_status() -> None:
    response = SimpleNamespace(
        output_items=(
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "vol_pstree",
                "arguments": "{}",
                "status": "completed",
            },
            {"type": "reasoning", "status": "completed", "summary": []},
        )
    )

    history = _response_history_items(response)

    assert history[0] == {
        "type": "function_call",
        "call_id": "call-1",
        "name": "vol_pstree",
        "arguments": "{}",
    }
    assert history[1]["status"] == "completed"


def profile(tmp_path: Path) -> EvidenceProfile:
    evidence = tmp_path / "memory.bin"
    evidence.write_bytes(b"PAGEDUMP" + b"\0" * 64)
    item = EvidenceItem(
        evidence_id="evidence-001",
        path=evidence,
        kind="memory",
        size=evidence.stat().st_size,
        sha256="0" * 64,
        os_hint="windows",
        health="ready",
        symbols="ready",
    )
    return EvidenceProfile(
        root=tmp_path,
        os="windows",
        shape="memory-only",
        filesystems=(),
        sizes={item.evidence_id: item.size},
        health={item.evidence_id: "ready"},
        symbols={item.evidence_id: "ready"},
        hashes={item.evidence_id: item.sha256},
        available_tool_families=("memory",),
        capability_label="Windows tested path",
        items=(item,),
    )


def tool_definition(
    name: str = "windows.pslist",
    executor: object | None = None,
) -> ToolDefinition:
    run_tool = executor if callable(executor) else lambda arguments: "PID 4 System"
    return ToolDefinition(
        name=name,
        description=f"Return fake records from {name}.",
        parameters=EMPTY_PARAMETERS,
        families=("memory",),
        os_families=("windows",),
        executor=run_tool,
    )


def tool_names(request: ModelRequest) -> set[str]:
    return {
        str(schema.get("name"))
        for schema in request.tools
        if schema.get("type") == "function" and schema.get("name")
    }


def evidence_source(output: str, *, status: str = "success") -> dict[str, str]:
    return {
        "status": status,
        "output": output,
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }


@dataclass
class FakeInvestigatorModel:
    """Script decisions from request capabilities without calling a provider."""

    usage: ModelUsage = ModelUsage(input_tokens=10, output_tokens=5)
    always_request_tool: bool = False
    opening_tool_names: tuple[str, ...] = ("windows.pslist",)
    terminal_text: str = "DONE"
    typed_terminal_status: str = "DONE"
    typed_terminal_call_id: str | None = None
    done_with_tool: bool = False
    done_with_tool_text: str = "DONE"
    loop_update: str = (
        "The prior receipt leaves execution timing unresolved [opening-tool]; "
        "another process view can still change the conclusion."
    )
    requests: list[ModelRequest] = field(default_factory=list)

    @property
    def model_id(self) -> str:
        return "fake-gpt-5.6"

    def create(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        index = len(self.requests)
        names = tool_names(request)

        if "submit_report_draft" in names:
            report_packet = json.loads(str(request.input_items[0]["content"][0]["text"]))
            finding_ids = [finding["finding_id"] for finding in report_packet["findings"]]
            span_ids = [
                quote["span_id"]
                for verdict in report_packet["judge_verdicts"]
                for quote in verdict["quoted_spans"]
            ]
            return ModelResponse(
                response_id=f"response-{index}",
                function_calls=(
                    FunctionCall(
                        call_id=f"report-{index}",
                        name="submit_report_draft",
                        arguments={
                            "executive_summary": "The execution claim remains unsupported.",
                            "investigative_narrative": (
                                "The process listing was reviewed without corroborating execution."
                            ),
                            "ioc_commentary": "No independently supported IOCs were identified.",
                            "limitations_commentary": (
                                "Only the supplied process-list evidence span was adjudicated."
                            ),
                            "referenced_finding_ids": finding_ids,
                            "referenced_span_ids": span_ids,
                        },
                    ),
                ),
                usage=self.usage,
            )

        if "submit_judgment" in names:
            judge_packet = json.loads(str(request.input_items[0]["content"][0]["text"]))
            opening_span = next(
                span
                for span in judge_packet["findings"][0]["supporting_spans"]
                if span["tool_call_id"] == "opening-tool"
            )
            return ModelResponse(
                response_id=f"response-{index}",
                function_calls=(
                    FunctionCall(
                        call_id=f"judge-{index}",
                        name="submit_judgment",
                        arguments={
                            "verdicts": [
                                {
                                    "finding_id": "F001",
                                    "status": "UNSUPPORTED",
                                    "rationale": "The cited process list does not prove execution.",
                                    "cited_tool_call_ids": ["opening-tool"],
                                    "quoted_spans": [
                                        {
                                            "span_id": opening_span["span_id"],
                                            "tool_call_id": "opening-tool",
                                            "text": opening_span["text"],
                                        }
                                    ],
                                    "annotations": ["Acquire corroborating execution artifacts."],
                                }
                            ]
                        },
                    ),
                ),
                usage=self.usage,
            )

        if not names:
            return ModelResponse(
                response_id=f"response-{index}",
                text=(
                    "## Narrative\n\nThe claimed execution is unsupported [opening-tool].\n\n"
                    "## Findings\n\n"
                    "| ID | Status | Tool calls |\n|---|---|---|\n"
                    "| F001 | UNSUPPORTED | [opening-tool] |\n\n"
                    "## IOC list\n\nNo independently supported IOCs.\n\n"
                    "## Limitations\n\n"
                    "This system has no deterministic validator by design."
                ),
                usage=self.usage,
            )

        if request.phase == "investigation-finalize":
            opening_output = next(
                str(item["output"])
                for item in request.input_items
                if item.get("type") == "function_call_output"
                and item.get("call_id") == "opening-tool"
            )
            return ModelResponse(
                response_id=f"response-{index}",
                function_calls=(
                    FunctionCall(
                        call_id=f"done-{index}",
                        name="submit_investigation",
                        arguments={
                            "status": "DONE",
                            "case_notes": (
                                "System is present in the process listing [opening-tool]."
                            ),
                            "findings": [
                                {
                                    "finding_id": "F001",
                                    "title": "Unproven execution claim",
                                    "summary": (
                                        "A process listing was over-interpreted [opening-tool]."
                                    ),
                                    "proposed_status": "CONFIRMED",
                                    "severity": "HIGH",
                                    "tool_call_ids": ["opening-tool"],
                                    "supporting_quotes": [
                                        {
                                            "tool_call_id": "opening-tool",
                                            "text": opening_output,
                                        }
                                    ],
                                    "iocs": [],
                                    "limitations": [],
                                }
                            ],
                            "limitations": [],
                            "unresolved_questions": [],
                        },
                    ),
                ),
                usage=self.usage,
            )

        if request.phase == "investigate" and not self.always_request_tool:
            if self.done_with_tool:
                return ModelResponse(
                    response_id=f"response-{index}",
                    text=self.done_with_tool_text,
                    function_calls=(
                        FunctionCall(
                            call_id="ambiguous-loop-tool",
                            name="windows.pslist",
                            arguments={},
                        ),
                    ),
                    usage=self.usage,
                )
            if self.terminal_text == "DONE":
                return ModelResponse(
                    response_id=f"response-{index}",
                    function_calls=(
                        FunctionCall(
                            call_id=(
                                self.typed_terminal_call_id
                                if self.typed_terminal_call_id is not None
                                else f"finish-{index}"
                            ),
                            name=INVESTIGATION_FINISH_TOOL_NAME,
                            arguments={"status": self.typed_terminal_status},
                        ),
                    ),
                    usage=self.usage,
                )
            return ModelResponse(
                response_id=f"response-{index}",
                text=self.terminal_text,
                usage=self.usage,
            )

        opening_calls = tuple(
            FunctionCall(
                call_id="opening-tool" if offset == 0 else f"opening-tool-{offset + 1}",
                name=name,
                arguments={},
            )
            for offset, name in enumerate(self.opening_tool_names)
        )
        return ModelResponse(
            response_id=f"response-{index}",
            text="" if index == 1 else self.loop_update,
            function_calls=(
                opening_calls
                if index == 1
                else (
                    FunctionCall(
                        call_id=f"loop-tool-{index}",
                        name="windows.pslist",
                        arguments={},
                    ),
                )
            ),
            usage=self.usage,
        )


def build_agent(
    tmp_path: Path,
    *,
    model: FakeInvestigatorModel,
    budget: RunBudget,
) -> tuple[UnchainedAgent, AuditLog]:
    audit = AuditLog(tmp_path / "audit.jsonl", "agent-test", fsync=False)
    registry = ToolRegistry(definitions=(tool_definition(),), audit=audit, budget=budget)
    return UnchainedAgent(model=model, tools=registry, audit=audit, budget=budget), audit


def test_fresh_judge_downgrades_deliberately_unsupported_finding(tmp_path: Path) -> None:
    model = FakeInvestigatorModel()
    budget = RunBudget(CapConfig())
    agent, audit = build_agent(tmp_path, model=model, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.COMPLETE
    assert run.findings[0].proposed_status is FindingStatus.CONFIRMED
    assert run.verdicts[0].finding_id == "F001"
    assert run.verdicts[0].status is FindingStatus.UNSUPPORTED
    assert run.verdicts[0].cited_tool_call_ids == ("opening-tool",)
    assert run.verdicts[0].quoted_spans[0].text == "PID 4 System"
    assert "no deterministic validator by design" in run.report_markdown.lower()

    judge_requests = [
        request for request in model.requests if "submit_judgment" in tool_names(request)
    ]
    assert len(judge_requests) == 1
    assert judge_requests[0].previous_response_id is None
    judge_instructions = " ".join(judge_requests[0].instructions.split())
    assert "exact byte range" in judge_instructions
    assert "supplied span_id" in judge_instructions
    assert "copied VERBATIM" in judge_instructions
    assert "contiguous substring of that span" in judge_instructions
    assert "at most 1024 UTF-8 bytes" in judge_instructions

    phases = [request.phase for request in model.requests]
    assert phases == [
        "opening",
        "investigate",
        "investigation-finalize",
        "judge",
        "report",
    ]
    assert all(request.include == () for request in model.requests)
    loop_request = model.requests[1]
    assert loop_request.parallel_tool_calls is False
    assert loop_request.tool_choice == "required"
    assert loop_request.minimum_output_tokens == 4_096
    assert INVESTIGATION_FINISH_TOOL_NAME in tool_names(loop_request)
    assert "submit_investigation" not in tool_names(loop_request)
    loop_instructions = " ".join(loop_request.instructions.split())
    assert "case-ledger update" in loop_instructions
    assert "empty message text is rejected" in loop_instructions
    assert loop_request.text_verbosity == "medium"
    assert "8,192 UTF-8 bytes" in loop_instructions
    finalizer_request = model.requests[2]
    assert finalizer_request.tool_choice == {
        "type": "function",
        "name": "submit_investigation",
    }
    assert finalizer_request.reasoning_context == "current_turn"
    finalizer_instructions = " ".join(finalizer_request.instructions.split())
    assert "called finish_investigation with status DONE" in finalizer_instructions
    assert "because you output DONE" not in finalizer_instructions
    assert tool_names(finalizer_request) == {"submit_investigation"}
    opening_packet = json.loads(str(model.requests[0].input_items[0]["content"][0]["text"]))
    judge_packet = json.loads(str(model.requests[3].input_items[0]["content"][0]["text"]))
    assert "available_catalog" not in opening_packet
    assert "available_catalog" not in judge_packet
    assert "audit_tool_receipts" not in judge_packet
    assert run.findings[0].supporting_spans[0].byte_start == 0
    assert run.verdicts[0].quoted_spans[0].span_id == run.findings[0].supporting_spans[0].span_id
    assert [request.reasoning_effort for request in model.requests] == [
        "low",
        "medium",
        "medium",
        "high",
        "low",
    ]
    assert [request.max_output_tokens for request in model.requests] == [
        4_096,
        4_096,
        12_288,
        12_288,
        8_192,
    ]
    assert [request.minimum_output_tokens for request in model.requests] == [
        1,
        4_096,
        4_096,
        4_096,
        1,
    ]

    entries = AuditLog.verify(audit.path)
    assert [
        entry["payload"]["phase"] for entry in entries if entry["event_type"] == "model.request"
    ] == ["opening", "investigate", "investigation-finalize", "judge", "report"]
    assert [
        entry["payload"]["phase"] for entry in entries if entry["event_type"] == "model.response"
    ] == ["opening", "investigate", "investigation-finalize", "judge", "report"]
    assert sum(entry["event_type"] == "tool.started" for entry in entries) == 1
    assert sum(entry["event_type"] == "tool.completed" for entry in entries) == 1
    assert sum(entry["event_type"] == "investigator.done" for entry in entries) == 1
    done = next(entry for entry in entries if entry["event_type"] == "investigator.done")
    assert done["payload"]["terminal_protocol"] == "typed-DONE-v2"
    assert done["payload"]["terminal_action_call_id"] == "finish-2"
    finished = next(entry for entry in entries if entry["event_type"] == "investigator.finished")
    assert finished["payload"]["case_notes"] != "DONE"
    report_completed = next(entry for entry in entries if entry["event_type"] == "report.completed")
    returned_report = run.report_markdown.encode("utf-8")
    assert run.report_markdown.endswith("\n")
    assert (
        report_completed["payload"]["report_sha256"] == hashlib.sha256(returned_report).hexdigest()
    )
    assert report_completed["payload"]["report_bytes"] == len(returned_report)


@pytest.mark.parametrize(
    ("loop_update", "message"),
    [
        (" \t\r\n ", "nonempty visible case-ledger update"),
        ("\x00\u200b", "nonempty visible case-ledger update"),
        (
            "€" * ((MAX_CASE_LEDGER_UPDATE_BYTES // 3) + 1),
            f"exceeds {MAX_CASE_LEDGER_UPDATE_BYTES} UTF-8 bytes",
        ),
    ],
)
def test_investigate_tool_call_rejects_missing_or_oversized_ledger_update(
    tmp_path: Path,
    loop_update: str,
    message: str,
) -> None:
    model = FakeInvestigatorModel(always_request_tool=True, loop_update=loop_update)
    agent, audit = build_agent(tmp_path, model=model, budget=RunBudget(CapConfig()))

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.partial_reason is not None and message in run.partial_reason
    entries = AuditLog.verify(audit.path)
    assert sum(entry["event_type"] == "tool.started" for entry in entries) == 1
    assert not any(entry["event_type"] == "investigator.notes.updated" for entry in entries)
    protocol_error = next(
        entry for entry in entries if entry["event_type"] == "model.protocol_error"
    )
    assert message in protocol_error["payload"]["reason"]


def test_investigate_tool_call_accepts_update_at_exact_utf8_limit(tmp_path: Path) -> None:
    update = "€" * (MAX_CASE_LEDGER_UPDATE_BYTES // 3) + "aa"
    assert len(update.encode("utf-8")) == MAX_CASE_LEDGER_UPDATE_BYTES
    model = FakeInvestigatorModel(always_request_tool=True, loop_update=update)
    budget = RunBudget(CapConfig(max_tool_calls=1))
    agent, audit = build_agent(tmp_path, model=model, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.cap is not None and run.cap.kind is CapKind.TOOL_CALLS
    notes = next(
        entry
        for entry in AuditLog.verify(audit.path)
        if entry["event_type"] == "investigator.notes.updated"
    )
    assert notes["payload"]["case_ledger_update"] == update
    assert notes["payload"]["case_ledger_update_bytes"] == MAX_CASE_LEDGER_UPDATE_BYTES


def test_investigator_rejects_a_turn_without_one_typed_action(tmp_path: Path) -> None:
    model = FakeInvestigatorModel(terminal_text="Investigation complete")
    budget = RunBudget(CapConfig())
    agent, audit = build_agent(tmp_path, model=model, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.cap is None
    assert run.partial_reason == "investigator must issue exactly one typed action"
    assert all(request.phase != "investigation-finalize" for request in model.requests)


def test_investigator_rejects_noncanonical_typed_done(tmp_path: Path) -> None:
    model = FakeInvestigatorModel(typed_terminal_status="done")
    agent, audit = build_agent(tmp_path, model=model, budget=RunBudget(CapConfig()))

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.partial_reason == "typed terminal action must contain only status DONE"
    assert all(request.phase != "investigation-finalize" for request in model.requests)


@pytest.mark.parametrize(
    ("call_id", "expected"),
    [
        ("", "typed terminal action call_id must be nonempty"),
        (
            "opening-tool",
            "typed terminal action call_id must be distinct from forensic call_ids",
        ),
    ],
)
def test_investigator_rejects_invalid_typed_terminal_call_id(
    tmp_path: Path,
    call_id: str,
    expected: str,
) -> None:
    model = FakeInvestigatorModel(typed_terminal_call_id=call_id)
    agent, audit = build_agent(tmp_path, model=model, budget=RunBudget(CapConfig()))

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.partial_reason == expected
    assert all(request.phase != "investigation-finalize" for request in model.requests)


@pytest.mark.parametrize("terminal_text", [" DONE", "DONE ", "DONE\n", "\nDONE\n"])
def test_investigator_rejects_whitespace_surrounded_done(
    tmp_path: Path,
    terminal_text: str,
) -> None:
    model = FakeInvestigatorModel(terminal_text=terminal_text)
    agent, audit = build_agent(tmp_path, model=model, budget=RunBudget(CapConfig()))

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.partial_reason == "investigator must issue exactly one typed action"
    assert all(request.phase != "investigation-finalize" for request in model.requests)


@pytest.mark.parametrize("done_text", ["DONE", " DONE", "DONE ", "\nDONE\n"])
def test_done_like_text_cannot_accompany_a_tool_call(
    tmp_path: Path,
    done_text: str,
) -> None:
    model = FakeInvestigatorModel(done_with_tool=True, done_with_tool_text=done_text)
    budget = RunBudget(CapConfig())
    agent, audit = build_agent(tmp_path, model=model, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.partial_reason == "raw DONE is not a terminal action under typed-DONE-v2"
    entries = AuditLog.verify(audit.path)
    assert sum(entry["event_type"] == "tool.started" for entry in entries) == 1
    assert all(
        entry.get("payload", {}).get("tool_call_id") != "ambiguous-loop-tool" for entry in entries
    )


def test_structured_findings_reject_uncited_and_invented_citations() -> None:
    baseline = {
        "status": "DONE",
        "case_notes": "The listing does not establish execution [t17].",
        "findings": [
            {
                "finding_id": "F001",
                "title": "Dead-end execution hypothesis",
                "summary": "The listing does not establish execution [t17].",
                "proposed_status": "UNSUPPORTED",
                "severity": "LOW",
                "tool_call_ids": ["t17"],
                "supporting_quotes": [
                    {"tool_call_id": "t17", "text": "does not establish execution"}
                ],
                "iocs": [],
                "limitations": [],
            }
        ],
        "limitations": [],
        "unresolved_questions": [],
    }
    sources = {"t17": evidence_source("The listing does not establish execution.")}
    parsed = _parse_investigation(baseline, 2, sources)
    assert parsed.findings[0].proposed_status is FindingStatus.UNSUPPORTED

    uncited = {
        **baseline,
        "findings": [
            {
                **baseline["findings"][0],
                "tool_call_ids": [],
                "supporting_quotes": [],
            }
        ],
    }
    with pytest.raises(AgentProtocolError, match="has no tool-call citation"):
        _parse_investigation(uncited, 2, sources)

    invented = {
        **baseline,
        "findings": [
            {
                **baseline["findings"][0],
                "summary": "The listing does not establish execution [t17] [invented].",
            }
        ],
    }
    with pytest.raises(AgentProtocolError, match="inline citations do not match"):
        _parse_investigation(invented, 2, sources)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"rationale": ""}, "without a rationale"),
        ({"cited_tool_call_ids": []}, "without a tool-call citation"),
        ({"cited_tool_call_ids": ["t17", "t17"]}, "duplicated tool-call citations"),
        ({"cited_tool_call_ids": ["t18"]}, "outside F001"),
    ],
)
def test_judge_requires_proof_for_every_verdict(
    tmp_path: Path,
    override: dict[str, object],
    message: str,
) -> None:
    finding = _parse_investigation(
        {
            "status": "DONE",
            "case_notes": "The hypothesis is not established [t17].",
            "findings": [
                {
                    "finding_id": "F001",
                    "title": "Unsupported hypothesis",
                    "summary": "The hypothesis is not established [t17].",
                    "proposed_status": "UNSUPPORTED",
                    "severity": "LOW",
                    "tool_call_ids": ["t17"],
                    "supporting_quotes": [{"tool_call_id": "t17", "text": "not established"}],
                    "iocs": [],
                    "limitations": [],
                }
            ],
            "limitations": [],
            "unresolved_questions": [],
        },
        2,
        {
            "t17": evidence_source("The hypothesis is not established."),
            "t18": evidence_source("unrelated receipt"),
        },
    ).findings[0]
    raw_verdict = {
        "finding_id": "F001",
        "status": "UNSUPPORTED",
        "rationale": "The receipt does not prove the hypothesis.",
        "cited_tool_call_ids": ["t17"],
        "quoted_spans": [
            {
                "span_id": finding.supporting_spans[0].span_id,
                "tool_call_id": "t17",
                "text": "not established",
            }
        ],
        "annotations": [],
        **override,
    }
    audit_path = tmp_path / f"judge-{message.replace(' ', '-')}.jsonl"
    with (
        AuditLog(audit_path, "judge-proof-test", fsync=False) as audit,
        pytest.raises(AgentProtocolError, match=message),
    ):
        _parse_verdicts(
            {"verdicts": [raw_verdict]},
            (finding,),
            {
                "t17": {
                    "tool_call_id": "t17",
                    "status": "success",
                    "output_first_2kb": "The hypothesis is not established.",
                },
                "t18": {
                    "tool_call_id": "t18",
                    "status": "success",
                    "output_first_2kb": "unrelated receipt",
                },
            },
            audit,
        )


def test_judge_schema_requires_strict_bounded_evidence_quotes() -> None:
    schema = _submit_judgment_schema()
    verdict_schema = schema["parameters"]["properties"]["verdicts"]["items"]
    assert "quoted_spans" in verdict_schema["required"]
    quote_schema = verdict_schema["properties"]["quoted_spans"]["items"]
    assert quote_schema == {
        "type": "object",
        "properties": {
            "span_id": {"type": "string"},
            "tool_call_id": {"type": "string"},
            "text": {"type": "string"},
        },
        "required": ["span_id", "tool_call_id", "text"],
        "additionalProperties": False,
    }


@pytest.mark.parametrize(
    ("quoted_spans", "message"),
    [
        (None, "malformed quoted spans"),
        (["not-an-object"], "malformed quoted span"),
        ([{"tool_call_id": "", "text": "proof"}], "without a tool-call id"),
        ([{"tool_call_id": "t17", "text": "   "}], "empty quoted span"),
        (
            [{"tool_call_id": "t17", "text": "é" * 513}],
            "more than 1024 UTF-8 bytes",
        ),
        (
            [{"tool_call_id": "t18", "text": "other proof"}],
            "outside its citations",
        ),
        (
            [
                {"tool_call_id": "t17", "text": "exact proof"},
                {"tool_call_id": "t17", "text": "exact proof"},
            ],
            "duplicated an evidence quote",
        ),
        ([{"tool_call_id": "t17", "text": "invented proof"}], "does not resolve"),
    ],
)
def test_judge_rejects_invalid_evidence_quotes(
    tmp_path: Path,
    quoted_spans: object,
    message: str,
) -> None:
    finding = _parse_investigation(
        {
            "status": "DONE",
            "case_notes": "The exact proof is bounded [t17].",
            "findings": [
                {
                    "finding_id": "F001",
                    "title": "Bounded claim",
                    "summary": "The exact proof is bounded [t17].",
                    "proposed_status": "NEEDS-REVIEW",
                    "severity": "LOW",
                    "tool_call_ids": ["t17"],
                    "supporting_quotes": [
                        {"tool_call_id": "t17", "text": "prefix exact proof suffix"}
                    ],
                    "iocs": [],
                    "limitations": [],
                }
            ],
            "limitations": [],
            "unresolved_questions": [],
        },
        1,
        {"t17": evidence_source("prefix exact proof suffix")},
    ).findings[0]
    if isinstance(quoted_spans, list):
        quoted_spans = [
            {**value, "span_id": finding.supporting_spans[0].span_id}
            if isinstance(value, dict)
            else value
            for value in quoted_spans
        ]
    raw_verdict = {
        "finding_id": "F001",
        "status": "NEEDS-REVIEW",
        "rationale": "The bounded excerpt is not independently sufficient.",
        "cited_tool_call_ids": ["t17"],
        "quoted_spans": quoted_spans,
        "annotations": [],
    }
    receipts = {
        "t17": {
            "tool_call_id": "t17",
            "status": "success",
            "output_excerpt": "prefix exact proof suffix",
        },
        "t18": {
            "tool_call_id": "t18",
            "status": "success",
            "output_excerpt": "other proof",
        },
    }
    with (
        AuditLog(tmp_path / "quote-invalid.jsonl", "quote-invalid", fsync=False) as audit,
        pytest.raises(AgentProtocolError, match=message),
    ):
        _parse_verdicts({"verdicts": [raw_verdict]}, (finding,), receipts, audit)


def test_judge_requires_a_resolving_quote_for_every_citation(tmp_path: Path) -> None:
    finding = _parse_investigation(
        {
            "status": "DONE",
            "case_notes": "Two receipts constrain the claim [t17] [t18].",
            "findings": [
                {
                    "finding_id": "F001",
                    "title": "Two-receipt claim",
                    "summary": "Two receipts constrain the claim [t17] [t18].",
                    "proposed_status": "CONFIRMED",
                    "severity": "LOW",
                    "tool_call_ids": ["t17", "t18"],
                    "supporting_quotes": [
                        {"tool_call_id": "t17", "text": "first exact span"},
                        {"tool_call_id": "t18", "text": "legacy exact span"},
                    ],
                    "iocs": [],
                    "limitations": [],
                }
            ],
            "limitations": [],
            "unresolved_questions": [],
        },
        1,
        {
            "t17": evidence_source("first exact span"),
            "t18": evidence_source("legacy exact span"),
        },
    ).findings[0]
    spans = {span.tool_call_id: span for span in finding.supporting_spans}
    receipts = {
        "t17": {
            "tool_call_id": "t17",
            "status": "success",
            "output_excerpt": "first exact span",
        },
        "t18": {
            "tool_call_id": "t18",
            "status": "success",
            "output_first_2kb": "legacy exact span",
        },
    }
    base = {
        "finding_id": "F001",
        "status": "CONFIRMED",
        "rationale": "Both bounded receipt excerpts support the claim.",
        "cited_tool_call_ids": ["t17", "t18"],
        "annotations": [],
    }
    with (
        AuditLog(tmp_path / "quote-omitted.jsonl", "quote-omitted", fsync=False) as audit,
        pytest.raises(AgentProtocolError, match="omitted exact evidence quotes.*t18"),
    ):
        _parse_verdicts(
            {
                "verdicts": [
                    {
                        **base,
                        "quoted_spans": [
                            {
                                "span_id": spans["t17"].span_id,
                                "tool_call_id": "t17",
                                "text": "exact span",
                            }
                        ],
                    }
                ]
            },
            (finding,),
            receipts,
            audit,
        )

    with AuditLog(tmp_path / "quote-valid.jsonl", "quote-valid", fsync=False) as audit:
        verdicts = _parse_verdicts(
            {
                "verdicts": [
                    {
                        **base,
                        "quoted_spans": [
                            {
                                "span_id": spans["t17"].span_id,
                                "tool_call_id": "t17",
                                "text": "first exact span",
                            },
                            {
                                "span_id": spans["t18"].span_id,
                                "tool_call_id": "t18",
                                "text": "legacy exact span",
                            },
                        ],
                    }
                ]
            },
            (finding,),
            receipts,
            audit,
        )
    assert verdicts[0].public_dict()["quoted_spans"] == [
        {
            "span_id": spans["t17"].span_id,
            "tool_call_id": "t17",
            "text": "first exact span",
        },
        {
            "span_id": spans["t18"].span_id,
            "tool_call_id": "t18",
            "text": "legacy exact span",
        },
    ]


def test_prompt_two_canonical_rules_are_regression_protected() -> None:
    normalized = " ".join(INVESTIGATOR_PROMPT.split())
    assert "no shell" in normalized
    assert "no internet" in normalized
    assert "broad, high-value opening" in normalized
    assert "memory is UNAVAILABLE" in normalized
    assert "[t17]" in normalized
    assert "Dead ends are findings too" in normalized
    assert "strict finish_investigation action" in normalized
    assert "status exactly DONE" in normalized
    assert "Do not emit raw DONE text" in normalized


def test_agent_opening_book_traverses_parallel_batch_path(tmp_path: Path) -> None:
    barrier = threading.Barrier(2, timeout=2.0)
    thread_ids: set[int] = set()
    lock = threading.Lock()

    def synchronized_tool(arguments: dict[str, object]) -> str:
        assert arguments == {}
        with lock:
            thread_ids.add(threading.get_ident())
        barrier.wait()
        return "raw opening output"

    model = FakeInvestigatorModel(opening_tool_names=("windows.pslist", "windows.netscan"))
    budget = RunBudget(CapConfig())
    audit = AuditLog(tmp_path / "audit.jsonl", "opening-agent-test", fsync=False)
    registry = ToolRegistry(
        definitions=(
            tool_definition("windows.pslist", synchronized_tool),
            tool_definition("windows.netscan", synchronized_tool),
        ),
        audit=audit,
        budget=budget,
    )
    agent = UnchainedAgent(model=model, tools=registry, audit=audit, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.COMPLETE
    assert len(thread_ids) == 2
    opening_events = [
        entry for entry in AuditLog.verify(audit.path) if entry["event_type"] == "opening.completed"
    ]
    assert len(opening_events) == 1
    assert opening_events[0]["payload"]["executed"] == 2


def test_opening_book_runs_each_distinct_function_at_most_once(tmp_path: Path) -> None:
    """Different PID arguments do not turn one function into multiple opening tools."""

    executed: list[dict[str, object]] = []

    @dataclass
    class RepeatedFunctionModel:
        @property
        def model_id(self) -> str:
            return "fake-gpt-5.6"

        def create(self, _request: ModelRequest) -> ModelResponse:
            return ModelResponse(
                response_id="repeat-opening",
                function_calls=(
                    FunctionCall(
                        call_id="pid-one",
                        name="windows.cmdline",
                        arguments={"pid": 1},
                    ),
                    FunctionCall(
                        call_id="pid-two",
                        name="windows.cmdline",
                        arguments={"pid": 2},
                    ),
                ),
                usage=ModelUsage(input_tokens=10, output_tokens=5),
            )

    definition = ToolDefinition(
        name="windows.cmdline",
        description="Return a command line for one PID.",
        parameters={
            "type": "object",
            "properties": {"pid": {"type": "integer"}},
            "required": ["pid"],
            "additionalProperties": False,
        },
        families=("memory",),
        os_families=("windows",),
        executor=lambda arguments: executed.append(arguments) or "cmd.exe",
    )
    audit = AuditLog(tmp_path / "audit.jsonl", "distinct-opening", fsync=False)
    budget = RunBudget(CapConfig())
    registry = ToolRegistry((definition,), audit, budget)
    agent = UnchainedAgent(
        model=RepeatedFunctionModel(),
        tools=registry,
        audit=audit,
        budget=budget,
    )

    try:
        with pytest.raises(AgentProtocolError, match="duplicated tool"):
            agent._opening(profile(tmp_path))  # noqa: SLF001
    finally:
        audit.close()

    assert executed == []
    entries = AuditLog.verify(tmp_path / "audit.jsonl")
    assert entries[-1]["event_type"] == "model.protocol_error"


@pytest.mark.parametrize(
    ("cap_kind", "config_overrides", "usage", "advance_wall"),
    [
        (CapKind.TOOL_CALLS, {"max_tool_calls": 1}, ModelUsage(10, 5), False),
        (CapKind.TOTAL_TOKENS, {"max_total_tokens": 10}, ModelUsage(6, 5), False),
        (
            CapKind.COST_USD,
            {
                "max_cost_usd": 0.50,
                "input_usd_per_million": 1_000_000.0,
                "output_usd_per_million": 1_000_000.0,
            },
            ModelUsage(input_tokens=1),
            False,
        ),
        (CapKind.WALL_SECONDS, {"max_wall_seconds": 1.0}, ModelUsage(10, 5), True),
    ],
)
def test_agent_loop_gracefully_terminates_on_every_cap(
    tmp_path: Path,
    cap_kind: CapKind,
    config_overrides: dict[str, int | float],
    usage: ModelUsage,
    advance_wall: bool,
) -> None:
    values: dict[str, int | float] = {
        "max_tool_calls": 100,
        "max_total_tokens": 1_000_000,
        "max_wall_seconds": 30.0,
        "max_cost_usd": 1_000.0,
    }
    values.update(config_overrides)
    clock = ManualClock()
    budget = RunBudget(CapConfig(**values), clock=clock)
    if advance_wall:
        clock.advance(1.0)
    model = FakeInvestigatorModel(usage=usage, always_request_tool=True)
    agent, audit = build_agent(tmp_path, model=model, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.cap is not None
    assert run.cap.kind is cap_kind
    assert "PARTIAL" in run.report_markdown
    assert budget.fired is cap_kind


def test_low_remaining_output_budget_stops_by_cap_before_typed_terminal(
    tmp_path: Path,
) -> None:
    # The opening can complete, but the next reasoning phase cannot retain its
    # deterministic 4,096-token response allocation.
    budget = RunBudget(
        CapConfig(
            max_tool_calls=100,
            max_total_tokens=4_500,
            max_wall_seconds=30.0,
            max_cost_usd=1_000.0,
        )
    )
    model = FakeInvestigatorModel()
    agent, audit = build_agent(tmp_path, model=model, budget=budget)

    try:
        run = agent.run(profile(tmp_path))
    finally:
        audit.close()

    assert run.status is RunStatus.PARTIAL
    assert run.cap is not None and run.cap.kind is CapKind.TOTAL_TOKENS
    entries = AuditLog.verify(audit.path)
    assert not any(entry["event_type"] == "model.protocol_error" for entry in entries)
