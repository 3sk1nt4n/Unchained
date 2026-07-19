"""Structured report contract and deterministic, inert Markdown renderer."""

from __future__ import annotations

import html
import json
import re
import string
from dataclasses import dataclass
from typing import Any

from .models import (
    EvidenceProfile,
    Finding,
    InvestigationState,
    JsonValue,
    JudgeVerdict,
)


class ReportProtocolError(ValueError):
    """Raised when a model-authored report draft violates its reference contract."""


REPORT_RENDERER_ID = "deterministic-markdown-v1"


@dataclass(frozen=True, slots=True)
class ReportDraft:
    """Narrative-only material; code owns findings, citations, and layout."""

    executive_summary: str
    investigative_narrative: str
    ioc_commentary: str
    limitations_commentary: str
    referenced_finding_ids: tuple[str, ...]
    referenced_span_ids: tuple[str, ...]


def report_draft_schema() -> dict[str, JsonValue]:
    return {
        "type": "function",
        "name": "submit_report_draft",
        "description": (
            "Submit narrative prose and references only. The controller renders all "
            "authoritative findings, verdicts, citations, IOCs, and limitations."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "executive_summary": {"type": "string"},
                "investigative_narrative": {"type": "string"},
                "ioc_commentary": {"type": "string"},
                "limitations_commentary": {"type": "string"},
                "referenced_finding_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "referenced_span_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "executive_summary",
                "investigative_narrative",
                "ioc_commentary",
                "limitations_commentary",
                "referenced_finding_ids",
                "referenced_span_ids",
            ],
            "additionalProperties": False,
        },
    }


def parse_report_draft(
    raw: dict[str, JsonValue],
    findings: tuple[Finding, ...],
    verdicts: tuple[JudgeVerdict, ...],
) -> ReportDraft:
    prose_fields = (
        "executive_summary",
        "investigative_narrative",
        "ioc_commentary",
        "limitations_commentary",
    )
    prose: dict[str, str] = {}
    for field in prose_fields:
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ReportProtocolError(f"report draft {field} must be nonempty text")
        prose[field] = value.strip()

    finding_ids = _string_array(raw.get("referenced_finding_ids"), "referenced_finding_ids")
    span_ids = _string_array(raw.get("referenced_span_ids"), "referenced_span_ids")
    expected_findings = {finding.finding_id for finding in findings}
    expected_spans = {quote.span_id for verdict in verdicts for quote in verdict.quoted_spans}
    if set(finding_ids) != expected_findings:
        raise ReportProtocolError(
            "report draft finding references do not match adjudicated findings; "
            f"missing={sorted(expected_findings - set(finding_ids))}, "
            f"extra={sorted(set(finding_ids) - expected_findings)}"
        )
    if set(span_ids) != expected_spans:
        raise ReportProtocolError(
            "report draft span references do not match judged evidence; "
            f"missing={sorted(expected_spans - set(span_ids))}, "
            f"extra={sorted(set(span_ids) - expected_spans)}"
        )
    return ReportDraft(
        executive_summary=prose["executive_summary"],
        investigative_narrative=prose["investigative_narrative"],
        ioc_commentary=prose["ioc_commentary"],
        limitations_commentary=prose["limitations_commentary"],
        referenced_finding_ids=tuple(finding_ids),
        referenced_span_ids=tuple(span_ids),
    )


def _string_array(raw: Any, field: str) -> list[str]:
    if not isinstance(raw, list) or any(not isinstance(value, str) or not value for value in raw):
        raise ReportProtocolError(f"report draft {field} must be a nonempty-string array")
    values = [str(value) for value in raw]
    if len(values) != len(set(values)):
        raise ReportProtocolError(f"report draft {field} contains duplicates")
    return values


def render_report_markdown(
    profile: EvidenceProfile,
    state: InvestigationState,
    verdicts: tuple[JudgeVerdict, ...],
    draft: ReportDraft,
) -> str:
    """Render authoritative rows and evidence references without model formatting."""

    findings = tuple(state.findings)
    verdict_by_id = {verdict.finding_id: verdict for verdict in verdicts}
    lines = [
        "# Unchained DFIR Report - COMPLETE",
        "",
        "## Verification scope",
        "",
        (
            "This system has no deterministic validator by design. Code verifies protocol "
            "structure, custody receipts, exact evidence spans, and status monotonicity; "
            "forensic meaning still requires analyst review."
        ),
        "",
        "## Case profile",
        "",
        f"- OS route: `{_inline(profile.os)}`",
        f"- Evidence shape: `{_inline(profile.shape)}`",
        f"- Capability: {_text(profile.capability_label)}",
        f"- Evidence items: {len(profile.items)}",
        f"- Ready tool families: {_text(', '.join(profile.available_tool_families) or 'none')}",
        "",
        "## Executive summary (model-authored, nonauthoritative)",
        "",
        _text(draft.executive_summary),
        "",
        "## Investigative narrative (model-authored, nonauthoritative)",
        "",
        _text(draft.investigative_narrative),
        "",
        "## Findings",
        "",
        "| ID | Finding | Severity | Investigator | Judge | Tool calls | Evidence spans |",
        "|---|---|---|---|---|---|---|",
    ]
    for finding in findings:
        verdict = verdict_by_id[finding.finding_id]
        calls = " ".join(f"[{_inline(call_id)}]" for call_id in finding.tool_call_ids)
        spans = " ".join(f"`{_inline(span.span_id)}`" for span in finding.supporting_spans)
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(finding.finding_id),
                    _cell(finding.title),
                    _inline(finding.severity),
                    _inline(finding.proposed_status.value),
                    _inline(verdict.status.value),
                    calls or "none",
                    spans or "none",
                )
            )
            + " |"
        )

    lines.extend(["", "## IOC list", ""])
    ioc_rows = [(finding.finding_id, ioc) for finding in findings for ioc in finding.iocs]
    if ioc_rows:
        lines.extend(["| Finding | IOC |", "|---|---|"])
        lines.extend(f"| {_cell(finding_id)} | {_cell(ioc)} |" for finding_id, ioc in ioc_rows)
    else:
        lines.append("No structured IOCs were submitted.")
    lines.extend(["", _text(draft.ioc_commentary), "", "## Evidence spans", ""])
    spans = [span for finding in findings for span in finding.supporting_spans]
    if spans:
        for span in spans:
            lines.extend(
                [
                    (
                        f"- `{_inline(span.span_id)}` from [{_inline(span.tool_call_id)}], "
                        f"artifact `{_inline(span.artifact_sha256)}`, bytes "
                        f"{span.byte_start}:{span.byte_end}, occurrences {span.occurrence_count}"
                    ),
                    f"  - Evidence text: {_text(span.text)}",
                ]
            )
    else:
        lines.append("No finding evidence spans were submitted.")

    lines.extend(["", "## Limitations", ""])
    limitations = [
        *state.limitations,
        *(value for finding in findings for value in finding.limitations),
        *(value for verdict in verdicts for value in verdict.annotations),
    ]
    if limitations:
        lines.extend(f"- {_text(value)}" for value in dict.fromkeys(limitations))
    else:
        lines.append("- No additional structured limitations were submitted.")
    lines.extend(
        [
            f"- {_text(draft.limitations_commentary)}",
            "- Offline bundle verification cannot authenticate self-recorded provider IDs.",
            (
                "- Recorded custody verification is not a fresh rehash of originals by an "
                "offline recipient."
            ),
            "",
            "## Unresolved questions",
            "",
        ]
    )
    if state.unresolved_questions:
        lines.extend(f"- {_text(value)}" for value in state.unresolved_questions)
    else:
        lines.append("No unresolved questions were submitted.")
    return "\n".join(lines).rstrip() + "\n"


def _inline(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_.:+/@-]", "_", str(value))


def _cell(value: object) -> str:
    # _text already escapes every Markdown punctuation character, including the
    # table delimiter. Escaping the pipe twice would make the delimiter active.
    return _text(value)


def _text(value: object) -> str:
    """Render arbitrary model/evidence text as inert, single-paragraph Markdown."""

    serialized = json.dumps(str(value), ensure_ascii=False)[1:-1]
    serialized = re.sub(
        r"(?i)\b([a-z][a-z0-9+.-]{1,31})://",
        lambda match: f"{match.group(1)}[:]//",
        serialized,
    )
    serialized = re.sub(r"(?i)\bwww\.", "www[.]", serialized)
    serialized = html.escape(serialized, quote=True)
    return re.sub(f"([{re.escape(string.punctuation)}])", r"\\\1", serialized)
