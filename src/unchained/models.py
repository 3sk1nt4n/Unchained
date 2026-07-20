"""Small, dependency-free domain models shared by the Unchained runtime."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol, TypeAlias

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
OsFamily: TypeAlias = Literal["windows", "linux", "macos", "unknown"]
EvidenceShape: TypeAlias = Literal["memory-only", "disk-only", "both", "logs-only", "unknown"]
MODEL_TOOL_OUTPUT_MAX_BYTES = 64 * 1024
# Deterministic per-observation model view sizes. Both the agent (when building a
# request) and the offline verifier (when reconstructing it) use these exact caps,
# so every request stays byte-for-byte reproducible AND the whole lifecycle fits a
# bounded token budget: a 12-tool opening at 64 KiB each would alone consume ~130k
# tokens, busting even the HEAVY profile before the loop could finish. The full
# tool outputs are always retained on disk as the citation source.
#
# INVESTIGATE uses the default (JSON) model_output view; FINALIZE uses the RAW
# quotable view so each supporting quote resolves to an exact byte range.
INVESTIGATE_OBSERVATION_VIEW_BYTES = 16 * 1024
FINALIZE_OBSERVATION_VIEW_BYTES = 16 * 1024
CASE_LEDGER_UPDATE_MAX_BYTES = 8_192
INVESTIGATION_FINISH_TOOL_NAME = "finish_investigation"
# Maximum high-value typed tools GPT-5.6 may fire in the all-or-none parallel
# opening. Raised past a memory-only floor so a cross-domain opening can span
# both memory and disk high-value views in one shot.
MAX_OPENING_TOOLS = 12
OS_EVIDENCE_CONFLICT_WARNING = (
    "OS CONFLICT: disk and memory content disagree; OS-specific tool families are disabled."
)
LOG_PRIMARY_OS_CONFLICT_WARNING = "Standalone log OS hints conflict with the primary evidence OS."
LOG_OS_CONFLICT_WARNING = "Standalone logs contain conflicting OS hints."
EVIDENCE_ROUTE_WARNINGS = frozenset(
    {
        OS_EVIDENCE_CONFLICT_WARNING,
        LOG_PRIMARY_OS_CONFLICT_WARNING,
        LOG_OS_CONFLICT_WARNING,
    }
)


def investigation_finish_schema() -> dict[str, JsonValue]:
    """Return the one strict, non-forensic action that terminates investigation."""

    return {
        "type": "function",
        "name": INVESTIGATION_FINISH_TOOL_NAME,
        "description": (
            "End adaptive investigation only when no further forensic call can "
            "materially change the conclusions."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["DONE"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
    }


def matches_json_schema_type(value: JsonValue, expected: JsonValue) -> bool:
    """Apply the runtime's supported JSON Schema primitive-type contract."""

    if expected is None:
        return True
    choices = expected if isinstance(expected, list) else [expected]
    for choice in choices:
        if choice == "null" and value is None:
            return True
        if choice == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if choice == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if choice == "string" and isinstance(value, str):
            return True
        if choice == "boolean" and isinstance(value, bool):
            return True
        if choice == "array" and isinstance(value, list):
            return True
        if choice == "object" and isinstance(value, dict):
            return True
    return False


class RunStatus(StrEnum):
    """Terminal run state used by the CLI and report header."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FATAL = "FATAL"
    INVALID = "INVALID"


class FindingStatus(StrEnum):
    """Investigator proposal and judge verdict vocabulary."""

    CONFIRMED = "CONFIRMED"
    NEEDS_REVIEW = "NEEDS-REVIEW"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """One original input file and its deterministic classification."""

    evidence_id: str
    path: Path
    kind: Literal["memory", "disk", "log", "unknown"]
    size: int
    sha256: str
    filesystem: str | None = None
    filesystem_offset: int | None = None
    os_hint: OsFamily = "unknown"
    health: str = "unknown"
    symbols: str = "not-applicable"
    available: bool = True
    warnings: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, JsonValue]:
        """Return a model-safe view; local paths stay inside the trusted runner."""

        data = asdict(self)
        data.pop("path", None)
        data["warnings"] = list(self.warnings)
        return data

    def local_dict(self) -> dict[str, JsonValue]:
        """Return the model-safe view plus the runner-local evidence path."""

        return {**self.public_dict(), "path": str(self.path)}


class _EvidenceRouteItem(Protocol):
    """Minimum deterministic facts needed to derive the public route."""

    kind: Literal["memory", "disk", "log", "unknown"]
    os_hint: OsFamily


def derive_evidence_shape(items: Iterable[_EvidenceRouteItem]) -> EvidenceShape:
    """Derive the case shape solely from classified evidence kinds."""

    kinds = {item.kind for item in items}
    if "memory" in kinds and "disk" in kinds:
        return "both"
    if "memory" in kinds:
        return "memory-only"
    if "disk" in kinds:
        return "disk-only"
    if "log" in kinds:
        return "logs-only"
    return "unknown"


def reconcile_evidence_os(
    items: Iterable[_EvidenceRouteItem],
) -> tuple[OsFamily, tuple[str, ...]]:
    """Reconcile strong memory/disk hints and weaker standalone-log hints."""

    materialized = tuple(items)
    disk_hints = {item.os_hint for item in materialized if item.kind == "disk"}
    memory_hints = {item.os_hint for item in materialized if item.kind == "memory"}
    log_hints = {item.os_hint for item in materialized if item.kind == "log"}
    disk_hints.discard("unknown")
    memory_hints.discard("unknown")
    log_hints.discard("unknown")
    strong_hints = disk_hints | memory_hints
    warnings: list[str] = []
    if len(strong_hints) > 1:
        warnings.append(OS_EVIDENCE_CONFLICT_WARNING)
        return "unknown", tuple(warnings)
    if strong_hints:
        resolved = next(iter(strong_hints))
        if log_hints and any(value != resolved for value in log_hints):
            warnings.append(LOG_PRIMARY_OS_CONFLICT_WARNING)
        return resolved, tuple(warnings)
    if len(log_hints) == 1:
        return next(iter(log_hints)), tuple(warnings)
    if len(log_hints) > 1:
        warnings.append(LOG_OS_CONFLICT_WARNING)
    return "unknown", tuple(warnings)


def derive_filesystems(items: Iterable[EvidenceItem]) -> tuple[str, ...]:
    """Return the canonical sorted filesystem set represented by the inventory."""

    return tuple(sorted({item.filesystem for item in items if item.filesystem is not None}))


@dataclass(frozen=True, slots=True)
class EvidenceProfile:
    """The complete deterministic Step-0 result handed to the investigator."""

    root: Path
    os: OsFamily
    shape: EvidenceShape
    filesystems: tuple[str, ...]
    sizes: dict[str, int]
    health: dict[str, str]
    symbols: dict[str, str]
    hashes: dict[str, str]
    available_tool_families: tuple[str, ...]
    capability_label: str
    items: tuple[EvidenceItem, ...]
    mount_path: Path | None = None
    warnings: tuple[str, ...] = ()

    @property
    def memory_items(self) -> tuple[EvidenceItem, ...]:
        return tuple(item for item in self.items if item.kind == "memory" and item.available)

    @property
    def disk_items(self) -> tuple[EvidenceItem, ...]:
        return tuple(item for item in self.items if item.kind == "disk" and item.available)

    @property
    def fs(self) -> tuple[str, ...]:
        """Expose the prompt's canonical ``fs`` field without duplicating state."""

        return self.filesystems

    def public_dict(self) -> dict[str, JsonValue]:
        """Return the bounded profile representation sent to the model."""

        return {
            "os": self.os,
            "shape": self.shape,
            "fs": list(self.filesystems),
            "filesystems": list(self.filesystems),
            "sizes": dict(self.sizes),
            "health": dict(self.health),
            "symbols": dict(self.symbols),
            "hashes": dict(self.hashes),
            "available_tool_families": list(self.available_tool_families),
            "capability_label": self.capability_label,
            "warnings": list(self.warnings),
            "evidence": [item.public_dict() for item in self.items],
        }


@dataclass(frozen=True, slots=True)
class FunctionCall:
    """A parsed Responses API function call."""

    call_id: str
    name: str
    arguments: dict[str, JsonValue]
    arguments_valid: bool = True
    parse_error: str | None = None


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """Observed token usage for one model response."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    provider_total_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Return the most conservative provider or component total."""

        return max(self.provider_total_tokens, self.input_tokens + self.output_tokens)


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Provider-neutral response used by the agent and offline fakes."""

    response_id: str
    provider_model: str | None = None
    text: str = ""
    function_calls: tuple[FunctionCall, ...] = ()
    usage: ModelUsage = ModelUsage()
    output_items: tuple[dict[str, JsonValue], ...] = ()
    request_id: str | None = None
    status: str = "completed"
    incomplete_details: JsonValue = None
    error: JsonValue = None
    usage_error: str | None = None


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Immutable receipt returned by the trusted tool runner."""

    call_id: str
    tool_name: str
    arguments: dict[str, JsonValue]
    output: str
    output_sha256: str
    status: Literal["success", "error", "timeout", "not-applicable", "rejected", "capped"]
    started_at: str
    ended_at: str
    duration_ms: int
    error: str | None = None

    def model_output(self, max_bytes: int | None = None) -> str:
        """Return a byte-bounded view while retaining the full accepted output on disk.

        ``max_bytes`` bounds THIS view (clamped to ``[256, MODEL_TOOL_OUTPUT_MAX_BYTES]``)
        so a batch of large observations can be fed to one request without
        exceeding the total-token cap. The full accepted output is always
        retained on disk and remains the citation source; only the model's
        prefix view shrinks, and the delivery receipt records the applied cap.
        """

        cap = MODEL_TOOL_OUTPUT_MAX_BYTES
        if max_bytes is not None:
            cap = max(256, min(int(max_bytes), MODEL_TOOL_OUTPUT_MAX_BYTES))
        accepted_bytes = len(self.output.encode("utf-8"))
        if accepted_bytes <= cap:
            return self.output

        def render(prefix_characters: int) -> str:
            return json.dumps(
                {
                    "accepted_output_prefix": self.output[:prefix_characters],
                    "delivery_receipt": {
                        "accepted_output_bytes": accepted_bytes,
                        "accepted_output_sha256": self.output_sha256,
                        "model_view_complete": False,
                        "model_view_max_bytes": cap,
                        "model_view_prefix_characters": prefix_characters,
                        "selection": "native-order UTF-8 prefix",
                    },
                },
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )

        low = 0
        high = len(self.output)
        best = render(0)
        while low <= high:
            middle = (low + high) // 2
            candidate = render(middle)
            if len(candidate.encode("utf-8")) <= cap:
                best = candidate
                low = middle + 1
            else:
                high = middle - 1
        return best

    def quotable_view(self, max_bytes: int | None = None) -> str:
        """Return a RAW UTF-8 prefix of the accepted output for exact quoting.

        Unlike :meth:`model_output`, this never wraps the text in JSON, so any
        substring the model copies from the view is a byte-exact substring of
        the full retained output and resolves to an exact byte range. Used only
        by the serialization phase, where the model mints supporting quotes;
        the full output stays on disk as the custody source. The prefix is cut
        on a UTF-8 character boundary so it never splits a multibyte glyph.
        """

        cap = MODEL_TOOL_OUTPUT_MAX_BYTES
        if max_bytes is not None:
            cap = max(256, min(int(max_bytes), MODEL_TOOL_OUTPUT_MAX_BYTES))
        encoded = self.output.encode("utf-8")
        if len(encoded) <= cap:
            return self.output
        clipped = encoded[:cap]
        # Drop any trailing bytes of a partially cut multibyte character.
        while clipped and (clipped[-1] & 0xC0) == 0x80:
            clipped = clipped[:-1]
        if clipped and clipped[-1] >= 0x80:
            clipped = clipped[:-1]
        return clipped.decode("utf-8", errors="ignore")


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    """Byte-located investigator evidence resolved against one retained output."""

    span_id: str
    tool_call_id: str
    artifact_sha256: str
    byte_start: int
    byte_end: int
    text: str
    occurrence_count: int

    def public_dict(self) -> dict[str, JsonValue]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Finding:
    """One investigator-produced finding before or after judge review."""

    finding_id: str
    title: str
    summary: str
    proposed_status: FindingStatus
    severity: str
    tool_call_ids: tuple[str, ...]
    supporting_spans: tuple[EvidenceSpan, ...] = ()
    iocs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any],
        index: int,
        *,
        supporting_spans: tuple[EvidenceSpan, ...] = (),
    ) -> Finding:
        """Normalize a model-provided finding while preserving model semantics."""

        raw_status = str(data.get("proposed_status") or "NEEDS-REVIEW").upper().replace("_", "-")
        try:
            status = FindingStatus(raw_status)
        except ValueError:
            status = FindingStatus.NEEDS_REVIEW
        return cls(
            finding_id=str(data.get("finding_id") or f"F{index:03d}"),
            title=str(data.get("title") or "Untitled finding"),
            summary=str(data.get("summary") or ""),
            proposed_status=status,
            severity=str(data.get("severity") or "UNKNOWN").upper(),
            tool_call_ids=tuple(str(value) for value in data.get("tool_call_ids") or ()),
            supporting_spans=supporting_spans,
            iocs=tuple(str(value) for value in data.get("iocs") or ()),
            limitations=tuple(str(value) for value in data.get("limitations") or ()),
        )

    def public_dict(self) -> dict[str, JsonValue]:
        data = asdict(self)
        data["proposed_status"] = self.proposed_status.value
        for key in ("tool_call_ids", "iocs", "limitations"):
            data[key] = list(data[key])
        data["supporting_spans"] = [span.public_dict() for span in self.supporting_spans]
        return data


@dataclass(frozen=True, slots=True)
class EvidenceQuote:
    """Exact bounded receipt text used by the fresh judge for one verdict."""

    span_id: str
    tool_call_id: str
    text: str

    def public_dict(self) -> dict[str, JsonValue]:
        """Return the quote in the stable proof-bundle representation."""

        return {
            "span_id": self.span_id,
            "tool_call_id": self.tool_call_id,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class JudgeVerdict:
    """Fresh-model adjudication for one existing investigator finding."""

    finding_id: str
    status: FindingStatus
    rationale: str
    cited_tool_call_ids: tuple[str, ...]
    quoted_spans: tuple[EvidenceQuote, ...]
    annotations: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, JsonValue]:
        data = asdict(self)
        data["status"] = self.status.value
        data["cited_tool_call_ids"] = list(self.cited_tool_call_ids)
        data["quoted_spans"] = [quote.public_dict() for quote in self.quoted_spans]
        data["annotations"] = list(self.annotations)
        return data


@dataclass(slots=True)
class InvestigationState:
    """Mutable run-local scratchpad owned by the investigator controller."""

    case_notes: str = ""
    findings: list[Finding] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    turns: int = 0
