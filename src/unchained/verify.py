"""Standard-library, offline verification for Unchained proof bundles.

The verifier proves the internal integrity and consistency of a completed run
directory.  It deliberately does not import the OpenAI SDK, forensic tools, or
evidence-mounting code, and it never contacts a network service.  In
particular, custody checks below validate the custody receipts recorded in the
audit log.  They do not rehash original evidence that is not in the bundle.
"""

from __future__ import annotations

import codecs
import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .artifacts import build_summary
from .caps import CapConfig, estimate_usage_cost
from .models import (
    CASE_LEDGER_UPDATE_MAX_BYTES,
    EVIDENCE_ROUTE_WARNINGS,
    INVESTIGATION_FINISH_TOOL_NAME,
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
    derive_evidence_shape,
    derive_filesystems,
    investigation_finish_schema,
    matches_json_schema_type,
    reconcile_evidence_os,
)
from .reporting import (
    REPORT_RENDERER_ID,
    ReportProtocolError,
    parse_report_draft,
    render_report_markdown,
)
from .viewer import render_viewer_html
from .viewer_policy import validate_inert_viewer_html

GENESIS_HASH = "0" * 64
SCHEMA_VERSION = 1
LAYOUT_VERSION = 1
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_QUOTE_BYTES = 1024
MAX_EXCERPT_BYTES = 2048
MAX_CASE_LEDGER_UPDATE_BYTES = CASE_LEDGER_UPDATE_MAX_BYTES
TOOL_OUTPUT_DIRECTORY = "tool-outputs"
RECORDED_CUSTODY_NOTICE = (
    "Verification is limited to recorded custody receipts; the original evidence was not rehashed."
)
RECORDED_PROVIDER_NOTICE = (
    "Offline verification validates recorded OpenAI response metadata; it cannot authenticate "
    "those receipts with the provider."
)

_REQUIRED_COMPLETE_ARTIFACTS = {
    "audit.jsonl": "audit",
    "report.md": "report",
    "profile.json": "evidence-profile",
    "environment.json": "environment",
    "summary.json": "summary",
    "viewer.html": "proof-viewer",
}
_REQUIRED_COMPLETE_EVENTS = (
    "run.created",
    "caps.configured",
    "custody.initial.completed",
    "profile.completed",
    "investigation.started",
    "opening.completed",
    "investigator.done",
    "investigator.finished",
    "judge.started",
    "judge.completed",
    "report.started",
    "report.completed",
    "investigation.completed",
    "custody.final.completed",
    "run.completed",
)
_MODEL_PHASE_PREFIX = ("opening",)
_MODEL_PHASE_SUFFIX = ("investigation-finalize", "judge", "report")

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_INLINE_CITATION_RE = re.compile(r"\[([^\[\]\r\n]+)\]")
_ALLOWED_TOOL_STATUSES = frozenset(
    {"success", "error", "timeout", "not-applicable", "rejected", "capped"}
)
_FINDING_RANK = {"UNSUPPORTED": 0, "NEEDS-REVIEW": 1, "CONFIRMED": 2}
_AUDIT_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "run_id",
        "sequence",
        "event_id",
        "event_type",
        "actor",
        "timestamp_utc",
        "elapsed_ms",
        "previous_hash",
        "payload",
        "entry_hash",
    }
)
_USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "cache_write_tokens",
    "reasoning_tokens",
    "provider_total_tokens",
)
_CAP_CONFIG_FIELDS = (
    "max_tool_calls",
    "max_total_tokens",
    "max_wall_seconds",
    "max_cost_usd",
    "input_usd_per_million",
    "cached_input_usd_per_million",
    "cache_write_usd_per_million",
    "output_usd_per_million",
)
_CAP_PRICE_FIELDS = _CAP_CONFIG_FIELDS[4:]
_BUDGET_FIELDS = (
    "tool_calls",
    "input_tokens",
    "cached_input_tokens",
    "cache_write_tokens",
    "output_tokens",
    "total_tokens",
    "elapsed_seconds",
    "estimated_cost_usd",
    "fired",
)
_RETRYABLE_TRANSPORT_ERROR_TYPES = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "BrokenPipeError",
        "ConnectionAbortedError",
        "ConnectionError",
        "ConnectionRefusedError",
        "ConnectionResetError",
        "TimeoutError",
    }
)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Machine-readable result returned by :func:`verify_run`."""

    passed: bool
    run_directory: str
    run_id: str | None
    terminal_status: str | None
    exit_code: int | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    verified_artifacts: int
    verified_audit_entries: int
    recorded_custody_only: bool = True

    @property
    def ok(self) -> bool:
        """Alias useful to callers that conventionally test ``result.ok``."""

        return self.passed

    def public_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation with the custody boundary."""

        return {
            "schema_version": SCHEMA_VERSION,
            "passed": self.passed,
            "run_directory": self.run_directory,
            "run_id": self.run_id,
            "terminal": {
                "status": self.terminal_status,
                "exit_code": self.exit_code,
            },
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "verified_artifacts": self.verified_artifacts,
            "verified_audit_entries": self.verified_audit_entries,
            "custody": {
                "recorded_custody_only": self.recorded_custody_only,
                "original_evidence_rehashed": False,
                "statement": RECORDED_CUSTODY_NOTICE,
            },
        }


@dataclass(frozen=True, slots=True)
class _FileFact:
    path: Path
    sha256: str
    byte_count: int
    prefix: bytes
    valid_utf8: bool
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class _Artifact:
    role: str
    path: str
    sha256: str
    byte_count: int
    media_type: str
    encoding: str | None
    required: bool


@dataclass(frozen=True, slots=True)
class _ToolReceipt:
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    status: str
    artifact_path: str
    excerpt: str
    fact: _FileFact
    evidence_refs: tuple[tuple[str, str], ...]
    start_index: int
    complete_index: int


@dataclass(frozen=True, slots=True)
class _EvidenceSpan:
    span_id: str
    call_id: str
    artifact_sha256: str
    byte_start: int
    byte_end: int
    text: str
    occurrence_count: int


@dataclass(frozen=True, slots=True)
class _ModelAccounting:
    input_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class _DuplicateJsonKey(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _strict_json_loads(value: str) -> Any:
    return json.loads(
        value,
        object_pairs_hook=_object_without_duplicates,
        parse_constant=_reject_nonfinite,
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _is_lower_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _span_id(artifact_sha256: str, byte_start: int, byte_end: int) -> str:
    material = f"{artifact_sha256}:{byte_start}:{byte_end}".encode("ascii")
    return "S" + hashlib.sha256(material).hexdigest()[:24]


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a nonempty string")
    if "\\" in value or ":" in value or "\x00" in value:
        raise ValueError(f"unsafe bundle path: {value!r}")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError(f"unsafe bundle path: {value!r}")
    if candidate.as_posix() != value:
        raise ValueError(f"bundle path is not normalized POSIX: {value!r}")
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


class _Verifier:
    def __init__(
        self,
        run_directory: Path,
        *,
        require_complete: bool,
        require_live_gpt56: bool,
    ) -> None:
        self.input_directory = run_directory
        self.root = run_directory
        self.require_complete = require_complete
        self.require_live_gpt56 = require_live_gpt56
        self.errors: list[str] = []
        self.warnings: list[str] = [RECORDED_CUSTODY_NOTICE]
        self.run_id: str | None = None
        self.terminal_status: str | None = None
        self.exit_code: int | None = None
        self.verified_artifacts = 0
        self.verified_audit_entries = 0
        self._root_resolved: Path | None = None
        self._artifact_facts: dict[str, _FileFact] = {}
        self._artifacts: dict[str, _Artifact] = {}
        self._verified_content: dict[Path, bytes] = {}
        self._profile_public: dict[str, Any] | None = None
        self._profile: EvidenceProfile | None = None
        self._retry_event_indices: set[int] = set()

    def error(self, message: str) -> None:
        if message not in self.errors:
            self.errors.append(message)

    def finish(self) -> VerificationResult:
        return VerificationResult(
            passed=not self.errors,
            run_directory=str(self.input_directory),
            run_id=self.run_id,
            terminal_status=self.terminal_status,
            exit_code=self.exit_code,
            errors=tuple(self.errors),
            warnings=tuple(self.warnings),
            verified_artifacts=self.verified_artifacts,
            verified_audit_entries=self.verified_audit_entries,
        )

    def run(self) -> None:
        if not self._prepare_root():
            return
        manifest_bytes = self._read_small_regular("manifest.json", MAX_MANIFEST_BYTES)
        if manifest_bytes is None:
            return
        manifest = self._parse_manifest(manifest_bytes)
        if manifest is None:
            return
        self._verify_detached_checksum(manifest_bytes)
        artifacts = self._parse_artifacts(manifest)
        self._verify_artifacts(artifacts)
        entries = self._verify_audit(manifest)
        if entries is None:
            return
        self.verified_audit_entries = len(entries)
        terminal_valid = self._verify_terminal(manifest, entries)
        receipts = self._verify_tools(entries)
        self._verify_citations(entries, receipts)
        self._verify_custody(entries)
        profile = self._verify_profile_binding(
            entries,
            required=self.require_complete or self.require_live_gpt56,
        )
        self._verify_tool_evidence_bindings(
            entries,
            receipts,
            required=self.require_complete or self.require_live_gpt56,
        )
        if self.require_complete and self.terminal_status != "COMPLETE":
            self.error("strict completion requires terminal status COMPLETE")
        if self.require_complete or self.require_live_gpt56:
            self._verify_complete_lifecycle(entries, receipts)
        if self.require_live_gpt56:
            self.warnings.append(RECORDED_PROVIDER_NOTICE)
            if self.terminal_status != "COMPLETE":
                self.error("strict live GPT-5.6 verification requires a COMPLETE run")
            self._verify_live_gpt56(entries)
        self._verify_viewer(entries, profile)
        if not terminal_valid:
            self.error("terminal audit and manifest metadata are inconsistent")

    def _prepare_root(self) -> bool:
        try:
            candidate = self.input_directory.expanduser().absolute()
            info = candidate.lstat()
        except OSError as exc:
            self.error(f"run directory is unavailable: {exc}")
            return False
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            self.error("run directory must be a real, non-symlink directory")
            return False
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            self.error(f"run directory could not be resolved: {exc}")
            return False
        self.root = candidate
        self._root_resolved = resolved
        return True

    def _target(self, relative_path: str, *, must_exist: bool = True) -> Path | None:
        try:
            normalized = _safe_relative_path(relative_path)
        except ValueError as exc:
            self.error(str(exc))
            return None
        current = self.root
        parts = PurePosixPath(normalized).parts
        for index, part in enumerate(parts):
            current = current / part
            try:
                info = current.lstat()
            except FileNotFoundError:
                if must_exist:
                    self.error(f"required bundle path is missing: {normalized}")
                return current
            except OSError as exc:
                self.error(f"bundle path could not be inspected ({normalized}): {exc}")
                return None
            if stat.S_ISLNK(info.st_mode):
                self.error(f"bundle path contains a symlink: {normalized}")
                return None
            if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
                self.error(f"bundle path parent is not a directory: {normalized}")
                return None
        if must_exist:
            try:
                resolved = current.resolve(strict=True)
            except OSError as exc:
                self.error(f"bundle path could not be resolved ({normalized}): {exc}")
                return None
            assert self._root_resolved is not None
            if not _is_within(resolved, self._root_resolved):
                self.error(f"bundle path escapes the run directory: {normalized}")
                return None
        return current

    def _read_small_regular(self, relative_path: str, limit: int) -> bytes | None:
        target = self._target(relative_path)
        if target is None or not target.exists():
            return None
        try:
            info = target.lstat()
        except OSError as exc:
            self.error(f"file could not be inspected ({relative_path}): {exc}")
            return None
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            self.error(f"bundle file is not a regular non-symlink file: {relative_path}")
            return None
        if info.st_size > limit:
            self.error(f"bundle file exceeds verification limit: {relative_path}")
            return None
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            fd = os.open(target, flags)
            try:
                opened = os.fstat(fd)
                if not stat.S_ISREG(opened.st_mode):
                    self.error(f"bundle file changed type while opening: {relative_path}")
                    return None
                if (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino):
                    self.error(f"bundle file changed while opening: {relative_path}")
                    return None
                chunks: list[bytes] = []
                remaining = limit + 1
                while remaining:
                    chunk = os.read(fd, min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
            finally:
                os.close(fd)
        except OSError as exc:
            self.error(f"bundle file could not be read ({relative_path}): {exc}")
            return None
        content = b"".join(chunks)
        if len(content) > limit:
            self.error(f"bundle file exceeds verification limit: {relative_path}")
            return None
        return content

    def _parse_manifest(self, content: bytes) -> dict[str, Any] | None:
        try:
            text = content.decode("utf-8")
            value = _strict_json_loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.error(f"manifest.json is not strict UTF-8 JSON: {exc}")
            return None
        if not isinstance(value, dict):
            self.error("manifest.json must contain one JSON object")
            return None
        if value.get("schema_version") != SCHEMA_VERSION:
            self.error("manifest schema_version must equal 1")
        if value.get("layout_version") != LAYOUT_VERSION:
            self.error("manifest layout_version must equal 1")
        run_id = value.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            self.error("manifest run_id must be a nonempty string")
        else:
            self.run_id = run_id
        terminal = value.get("terminal")
        if not isinstance(terminal, dict):
            self.error("manifest terminal must be an object")
        else:
            status_value = terminal.get("status")
            exit_value = terminal.get("exit_code")
            if not isinstance(status_value, str) or not status_value:
                self.error("manifest terminal.status must be a nonempty string")
            else:
                self.terminal_status = status_value
            if not _is_int(exit_value):
                self.error("manifest terminal.exit_code must be an integer")
            else:
                self.exit_code = exit_value
        exclusions = value.get("excluded_from_self_manifest")
        if not isinstance(exclusions, list) or any(
            not isinstance(item, str) for item in exclusions
        ):
            self.error("excluded_from_self_manifest must be a string array")
        else:
            if len(exclusions) != len(set(exclusions)):
                self.error("excluded_from_self_manifest contains duplicates")
            missing = {"manifest.json", "manifest.sha256"} - set(exclusions)
            if missing:
                self.error(
                    "excluded_from_self_manifest must include manifest.json and manifest.sha256"
                )
        return value

    def _verify_detached_checksum(self, manifest_bytes: bytes) -> None:
        checksum = self._read_small_regular("manifest.sha256", 256)
        if checksum is None:
            return
        expected_digest = hashlib.sha256(manifest_bytes).hexdigest()
        expected = f"{expected_digest}  manifest.json\n".encode("ascii")
        if checksum != expected:
            self.error("manifest.sha256 must exactly equal '<lower sha256>  manifest.json\\n'")

    def _parse_artifacts(self, manifest: dict[str, Any]) -> list[_Artifact]:
        raw_artifacts = manifest.get("artifacts")
        if not isinstance(raw_artifacts, list):
            self.error("manifest artifacts must be an array")
            return []
        excluded_raw = manifest.get("excluded_from_self_manifest")
        excluded = set(excluded_raw) if isinstance(excluded_raw, list) else set()
        parsed: list[_Artifact] = []
        paths: set[str] = set()
        for index, raw in enumerate(raw_artifacts):
            label = f"manifest artifact {index}"
            if not isinstance(raw, dict):
                self.error(f"{label} must be an object")
                continue
            try:
                path = _safe_relative_path(raw.get("path"))
            except ValueError as exc:
                self.error(f"{label}: {exc}")
                continue
            if path in paths:
                self.error(f"manifest contains duplicate artifact path: {path}")
                continue
            paths.add(path)
            if path in excluded or path in {"manifest.json", "manifest.sha256"}:
                self.error(f"self-manifest exclusion was listed as an artifact: {path}")
            role = raw.get("role")
            digest = raw.get("sha256")
            byte_count = raw.get("bytes")
            media_type = raw.get("media_type")
            encoding = raw.get("encoding")
            required = raw.get("required")
            valid = True
            if not isinstance(role, str) or not role:
                self.error(f"{label} role must be a nonempty string")
                valid = False
            if not _is_lower_sha256(digest):
                self.error(f"{label} sha256 must be lowercase hexadecimal")
                valid = False
            if not _is_int(byte_count) or byte_count < 0:
                self.error(f"{label} bytes must be a nonnegative integer")
                valid = False
            if not isinstance(media_type, str) or not media_type:
                self.error(f"{label} media_type must be a nonempty string")
                valid = False
            if encoding is not None and not isinstance(encoding, str):
                self.error(f"{label} encoding must be a string or null")
                valid = False
            if not isinstance(required, bool):
                self.error(f"{label} required must be a boolean")
                valid = False
            if valid:
                parsed.append(
                    _Artifact(
                        role=role,
                        path=path,
                        sha256=digest,
                        byte_count=byte_count,
                        media_type=media_type,
                        encoding=encoding,
                        required=required,
                    )
                )
        self._artifacts = {artifact.path: artifact for artifact in parsed}
        return parsed

    def _hash_regular(self, relative_path: str, *, validate_utf8: bool) -> _FileFact | None:
        target = self._target(relative_path)
        if target is None or not target.exists():
            return None
        try:
            info = target.lstat()
        except OSError as exc:
            self.error(f"artifact could not be inspected ({relative_path}): {exc}")
            return None
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            self.error(f"artifact is not a regular non-symlink file: {relative_path}")
            return None
        digest = hashlib.sha256()
        byte_count = 0
        prefix = bytearray()
        decoder = codecs.getincrementaldecoder("utf-8")("strict") if validate_utf8 else None
        utf8_valid = True
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            fd = os.open(target, flags)
            try:
                opened = os.fstat(fd)
                if not stat.S_ISREG(opened.st_mode):
                    self.error(f"artifact changed type while opening: {relative_path}")
                    return None
                if (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino):
                    self.error(f"artifact changed while opening: {relative_path}")
                    return None
                while True:
                    chunk = os.read(fd, 1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    byte_count += len(chunk)
                    if len(prefix) < MAX_EXCERPT_BYTES:
                        prefix.extend(chunk[: MAX_EXCERPT_BYTES - len(prefix)])
                    if decoder is not None and utf8_valid:
                        try:
                            decoder.decode(chunk, final=False)
                        except UnicodeDecodeError:
                            utf8_valid = False
                if decoder is not None and utf8_valid:
                    try:
                        decoder.decode(b"", final=True)
                    except UnicodeDecodeError:
                        utf8_valid = False
            finally:
                os.close(fd)
        except OSError as exc:
            self.error(f"artifact could not be read ({relative_path}): {exc}")
            return None
        if validate_utf8 and not utf8_valid:
            self.error(f"artifact declared UTF-8 contains invalid bytes: {relative_path}")
        return _FileFact(
            target,
            digest.hexdigest(),
            byte_count,
            bytes(prefix),
            utf8_valid,
            opened.st_dev,
            opened.st_ino,
        )

    def _verify_artifacts(self, artifacts: list[_Artifact]) -> None:
        for artifact in artifacts:
            target = self._target(artifact.path, must_exist=artifact.required)
            if target is None:
                continue
            if not target.exists():
                if artifact.required:
                    self.error(f"required artifact is missing: {artifact.path}")
                continue
            validate_utf8 = artifact.encoding is not None and artifact.encoding.lower() == "utf-8"
            fact = self._hash_regular(artifact.path, validate_utf8=validate_utf8)
            if fact is None:
                continue
            self._artifact_facts[artifact.path] = fact
            if fact.byte_count != artifact.byte_count:
                self.error(f"artifact byte count mismatch: {artifact.path}")
            if fact.sha256 != artifact.sha256:
                self.error(f"artifact SHA-256 mismatch: {artifact.path}")
            if fact.byte_count == artifact.byte_count and fact.sha256 == artifact.sha256:
                self.verified_artifacts += 1

    def _read_verified_fact(self, fact: _FileFact, *, label: str) -> bytes | None:
        """Reopen one verified artifact and prove identity and content again.

        Initial manifest verification and later semantic checks must not trust
        two unrelated pathname opens.  The second read therefore has to match
        the original device/inode pair, byte count, and digest before any of its
        bytes are used for a quote, span, report, or viewer decision.
        """

        cached = self._verified_content.get(fact.path)
        if cached is not None:
            return cached
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            fd = os.open(fact.path, flags)
            try:
                opened = os.fstat(fd)
                if not stat.S_ISREG(opened.st_mode):
                    self.error(f"{label} changed type during verified reread")
                    return None
                if (opened.st_dev, opened.st_ino) != (fact.device, fact.inode):
                    self.error(f"{label} changed identity during verified reread")
                    return None
                chunks: list[bytes] = []
                remaining = fact.byte_count + 1
                while remaining:
                    chunk = os.read(fd, min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
            finally:
                os.close(fd)
        except OSError as exc:
            self.error(f"{label} could not be reread safely: {exc}")
            return None
        content = b"".join(chunks)
        if len(content) != fact.byte_count:
            self.error(f"{label} byte count changed during verified reread")
            return None
        if hashlib.sha256(content).hexdigest() != fact.sha256:
            self.error(f"{label} digest changed during verified reread")
            return None
        self._verified_content[fact.path] = content
        return content

    def _read_verified_json_object(self, path: str, *, label: str) -> dict[str, Any] | None:
        fact = self._artifact_facts.get(path)
        if fact is None:
            return None
        content = self._read_verified_fact(fact, label=label)
        if content is None:
            return None
        try:
            value = _strict_json_loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.error(f"{label} is not strict UTF-8 JSON: {exc}")
            return None
        if not isinstance(value, dict):
            self.error(f"{label} must contain one JSON object")
            return None
        return value

    def _verify_canonical_json_artifact(
        self,
        path: str,
        value: dict[str, Any],
        *,
        label: str,
    ) -> None:
        fact = self._artifact_facts.get(path)
        if fact is None:
            return
        content = self._read_verified_fact(fact, label=label)
        if content is None:
            return
        expected = (
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        if content != expected:
            self.error(f"{label} is not in the deterministic JSON artifact encoding")

    def _verify_profile_binding(
        self,
        entries: list[dict[str, Any]],
        *,
        required: bool,
    ) -> EvidenceProfile | None:
        profile_artifact = self._artifacts.get("profile.json")
        matches = [entry for entry in entries if entry.get("event_type") == "profile.completed"]
        if profile_artifact is None and not matches:
            if required:
                self.error("strict completion requires a bound evidence profile")
            return None
        if profile_artifact is None:
            self.error("profile.completed has no manifested profile.json artifact")
            return None
        if len(matches) != 1:
            self.error(
                "profile binding requires exactly one profile.completed event; "
                f"found {len(matches)}"
            )
            return None
        event_profile = matches[0].get("payload")
        if not isinstance(event_profile, dict):
            self.error("profile.completed payload must be an object")
            return None
        public = self._read_verified_json_object("profile.json", label="profile.json")
        if public is None:
            return None
        self._verify_canonical_json_artifact("profile.json", public, label="profile.json")
        if public != event_profile:
            self.error("profile.json does not exactly match profile.completed")
            return None
        investigation_started = self._event_payload(entries, "investigation.started")
        if investigation_started is not None and investigation_started.get("profile") != public:
            self.error("investigation.started profile does not match the verified profile")
        self._profile_public = public
        profile = self._profile_from_public(public)
        if profile is None:
            return None

        initial = self._event_payload(entries, "custody.initial.completed")
        if initial is not None:
            hashes = initial.get("hashes")
            sizes = initial.get("sizes")
            if public.get("hashes") != hashes:
                self.error("profile hashes do not exactly match initial custody")
            if public.get("sizes") != sizes:
                self.error("profile sizes do not exactly match initial custody")
            if initial.get("file_count") != len(profile.items):
                self.error("profile evidence count does not match initial custody")
        self._profile = profile
        return profile

    def _profile_from_public(self, raw: dict[str, Any]) -> EvidenceProfile | None:
        required = {
            "os",
            "shape",
            "fs",
            "filesystems",
            "sizes",
            "health",
            "symbols",
            "hashes",
            "available_tool_families",
            "capability_label",
            "warnings",
            "evidence",
        }
        if set(raw) != required:
            self.error("profile.json does not match the public evidence-profile shape")
            return None
        os_family = raw.get("os")
        shape = raw.get("shape")
        filesystems = raw.get("filesystems")
        fs_alias = raw.get("fs")
        sizes = raw.get("sizes")
        health = raw.get("health")
        symbols = raw.get("symbols")
        hashes = raw.get("hashes")
        families = raw.get("available_tool_families")
        capability = raw.get("capability_label")
        warnings = raw.get("warnings")
        evidence = raw.get("evidence")
        if os_family not in {"windows", "linux", "macos", "unknown"}:
            self.error("profile.json os is invalid")
            return None
        if shape not in {"memory-only", "disk-only", "both", "logs-only", "unknown"}:
            self.error("profile.json shape is invalid")
            return None
        if (
            not isinstance(filesystems, list)
            or any(not isinstance(value, str) for value in filesystems)
            or fs_alias != filesystems
        ):
            self.error("profile.json filesystems/fs are malformed or inconsistent")
            return None
        if not all(isinstance(value, dict) for value in (sizes, health, symbols, hashes)):
            self.error("profile.json indexed evidence facts must be objects")
            return None
        if (
            not isinstance(families, list)
            or any(not isinstance(value, str) or not value for value in families)
            or len(families) != len(set(families))
            or not isinstance(capability, str)
            or not capability
            or not isinstance(warnings, list)
            or any(not isinstance(value, str) for value in warnings)
            or not isinstance(evidence, list)
        ):
            self.error("profile.json capability, warnings, or evidence inventory is malformed")
            return None

        items: list[EvidenceItem] = []
        seen: set[str] = set()
        item_keys = {
            "evidence_id",
            "kind",
            "size",
            "sha256",
            "filesystem",
            "filesystem_offset",
            "os_hint",
            "health",
            "symbols",
            "available",
            "warnings",
        }
        for ordinal, value in enumerate(evidence):
            label = f"profile.json evidence[{ordinal}]"
            if not isinstance(value, dict) or set(value) != item_keys:
                self.error(f"{label} does not match the public evidence-item shape")
                return None
            evidence_id = value.get("evidence_id")
            kind = value.get("kind")
            size = value.get("size")
            digest = value.get("sha256")
            filesystem = value.get("filesystem")
            filesystem_offset = value.get("filesystem_offset")
            os_hint = value.get("os_hint")
            item_health = value.get("health")
            item_symbols = value.get("symbols")
            available = value.get("available")
            item_warnings = value.get("warnings")
            if not isinstance(evidence_id, str) or not evidence_id or evidence_id in seen:
                self.error(f"{label} has an empty or duplicate evidence_id")
                return None
            if kind not in {"memory", "disk", "log", "unknown"}:
                self.error(f"{label} kind is invalid")
                return None
            if not _is_int(size) or size < 0 or not _is_lower_sha256(digest):
                self.error(f"{label} size or SHA-256 is invalid")
                return None
            if filesystem is not None and not isinstance(filesystem, str):
                self.error(f"{label} filesystem must be text or null")
                return None
            if filesystem_offset is not None and (
                not _is_int(filesystem_offset) or filesystem_offset < 0
            ):
                self.error(f"{label} filesystem_offset is invalid")
                return None
            if (
                os_hint not in {"windows", "linux", "macos", "unknown"}
                or not isinstance(item_health, str)
                or not isinstance(item_symbols, str)
                or not isinstance(available, bool)
                or not isinstance(item_warnings, list)
                or any(not isinstance(item, str) for item in item_warnings)
            ):
                self.error(f"{label} route, health, symbols, or warnings are malformed")
                return None
            if (
                sizes.get(evidence_id) != size
                or hashes.get(evidence_id) != digest
                or health.get(evidence_id) != item_health
                or symbols.get(evidence_id) != item_symbols
            ):
                self.error(f"{label} disagrees with the profile's indexed facts")
                return None
            seen.add(evidence_id)
            items.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    path=Path(evidence_id),
                    kind=kind,
                    size=size,
                    sha256=digest,
                    filesystem=filesystem,
                    filesystem_offset=filesystem_offset,
                    os_hint=os_hint,
                    health=item_health,
                    symbols=item_symbols,
                    available=available,
                    warnings=tuple(item_warnings),
                )
            )
        if set(sizes) != seen or set(hashes) != seen or set(health) != seen or set(symbols) != seen:
            self.error("profile.json indexed evidence facts do not match its inventory")
            return None
        derived_shape = derive_evidence_shape(items)
        if shape != derived_shape:
            self.error(
                "profile.json shape disagrees with its evidence inventory: "
                f"recorded {shape!r}, derived {derived_shape!r}"
            )
        derived_filesystems = list(derive_filesystems(items))
        if filesystems != derived_filesystems:
            self.error(
                "profile.json filesystems disagree with its evidence inventory: "
                f"recorded {filesystems!r}, derived {derived_filesystems!r}"
            )
        derived_os, derived_route_warnings = reconcile_evidence_os(items)
        if os_family != derived_os:
            self.error(
                "profile.json os disagrees with its evidence hints: "
                f"recorded {os_family!r}, derived {derived_os!r}"
            )
        recorded_route_warnings = tuple(
            warning for warning in warnings if warning in EVIDENCE_ROUTE_WARNINGS
        )
        if recorded_route_warnings != derived_route_warnings:
            self.error(
                "profile.json route warnings disagree with its evidence hints: "
                f"recorded {recorded_route_warnings!r}, derived {derived_route_warnings!r}"
            )
        profile = EvidenceProfile(
            root=Path("."),
            os=os_family,
            shape=shape,
            filesystems=tuple(filesystems),
            sizes=dict(sizes),
            health=dict(health),
            symbols=dict(symbols),
            hashes=dict(hashes),
            available_tool_families=tuple(families),
            capability_label=capability,
            items=tuple(items),
            warnings=tuple(warnings),
        )
        if profile.public_dict() != raw:
            self.error("profile.json is not a canonical public evidence profile")
            return None
        return profile

    def _verify_viewer(
        self,
        entries: list[dict[str, Any]],
        profile: EvidenceProfile | None,
    ) -> None:
        viewers = [
            artifact for artifact in self._artifacts.values() if artifact.role == "proof-viewer"
        ]
        if not viewers:
            return
        if len(viewers) != 1:
            self.error("bundle must contain at most one proof-viewer artifact")
            return
        viewer = viewers[0]
        if viewer.path != "viewer.html":
            self.error("proof-viewer artifact path must equal viewer.html")
        if viewer.media_type.lower() != "text/html":
            self.error("proof-viewer artifact media type must equal text/html")
        if viewer.encoding is None or viewer.encoding.lower() != "utf-8":
            self.error("proof-viewer artifact encoding must equal utf-8")
        fact = self._artifact_facts.get(viewer.path)
        if fact is None:
            return
        content = self._read_verified_fact(fact, label="proof viewer")
        if content is None:
            return
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            self.error("proof viewer is not valid UTF-8")
            return
        for policy_error in validate_inert_viewer_html(text):
            self.error(f"proof viewer is not inert: {policy_error}")

        summary = self._read_verified_json_object("summary.json", label="summary.json")
        report_fact = self._artifact_facts.get("report.md")
        completed = self._event_payload(entries, "run.completed")
        if summary is None or report_fact is None or completed is None:
            self.error("proof viewer cannot be rebound to summary, report, and run.completed")
            return
        report_content = self._read_verified_fact(report_fact, label="report.md")
        if report_content is None:
            return
        try:
            report = report_content.decode("utf-8")
        except UnicodeDecodeError:
            self.error("report.md is not valid UTF-8")
            return
        first_write = next(
            (
                index
                for index, entry in enumerate(entries)
                if entry.get("event_type") == "artifact.written"
            ),
            None,
        )
        completed_index = self._event_index(entries, "run.completed")
        boundary = first_write if first_write is not None else completed_index
        if boundary is None:
            self.error("proof viewer has no deterministic pre-artifact audit boundary")
            return
        prefix = entries[:boundary]
        expected_summary = build_summary(
            run_id=self.run_id or "",
            entries=prefix,
            status=self.terminal_status or "",
            exit_code=self.exit_code if self.exit_code is not None else -1,
            profile=profile,
            cap=completed.get("cap") if isinstance(completed.get("cap"), str) else None,
            reason=(completed.get("reason") if isinstance(completed.get("reason"), str) else None),
            mount_released=completed.get("mount_released") is True,
        )
        if summary != expected_summary:
            self.error("summary.json is not the deterministic summary of the verified audit prefix")
        self._verify_canonical_json_artifact("summary.json", expected_summary, label="summary.json")
        expected = render_viewer_html(
            run_id=self.run_id or "",
            status=self.terminal_status or "",
            profile=profile,
            summary=expected_summary,
            report_markdown=report,
            audit_entries=prefix,
        ).encode("utf-8")
        if content != expected:
            self.error("viewer.html is not the exact deterministic rendering of the proof bundle")

    def _audit_contract(self, manifest: dict[str, Any]) -> dict[str, Any] | None:
        audit = manifest.get("audit")
        if not isinstance(audit, dict):
            self.error("manifest audit must be an object")
            return None
        if audit.get("path") != "audit.jsonl":
            self.error("manifest audit.path must equal 'audit.jsonl'")
        if not _is_lower_sha256(audit.get("sha256")):
            self.error("manifest audit.sha256 must be lowercase hexadecimal")
        if not _is_int(audit.get("bytes")) or audit.get("bytes", -1) < 0:
            self.error("manifest audit.bytes must be a nonnegative integer")
        if not _is_int(audit.get("entry_count")) or audit.get("entry_count", 0) < 1:
            self.error("manifest audit.entry_count must be a positive integer")
        if not _is_lower_sha256(audit.get("final_entry_hash")):
            self.error("manifest audit.final_entry_hash must be lowercase hexadecimal")
        artifact = self._artifacts.get("audit.jsonl")
        if artifact is not None:
            if artifact.sha256 != audit.get("sha256"):
                self.error("audit descriptor SHA-256 disagrees with artifacts entry")
            if artifact.byte_count != audit.get("bytes"):
                self.error("audit descriptor byte count disagrees with artifacts entry")
        return audit

    def _verify_audit(self, manifest: dict[str, Any]) -> list[dict[str, Any]] | None:
        contract = self._audit_contract(manifest)
        if contract is None:
            return None
        target = self._target("audit.jsonl")
        if target is None or not target.exists():
            return None
        try:
            info = target.lstat()
        except OSError as exc:
            self.error(f"audit.jsonl could not be inspected: {exc}")
            return None
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            self.error("audit.jsonl must be a regular non-symlink file")
            return None
        entries: list[dict[str, Any]] = []
        event_ids: set[str] = set()
        previous_hash = GENESIS_HASH
        digest = hashlib.sha256()
        total_bytes = 0
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            fd = os.open(target, flags)
            with os.fdopen(fd, "rb", closefd=True) as handle:
                opened = os.fstat(handle.fileno())
                if not stat.S_ISREG(opened.st_mode):
                    self.error("audit.jsonl changed type while opening")
                    return None
                if (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino):
                    self.error("audit.jsonl changed while opening")
                    return None
                for expected_sequence, raw_line in enumerate(handle, start=1):
                    digest.update(raw_line)
                    total_bytes += len(raw_line)
                    if not raw_line.endswith(b"\n"):
                        self.error(f"audit.jsonl line {expected_sequence} is missing its newline")
                        continue
                    try:
                        line = raw_line[:-1].decode("utf-8")
                        record = _strict_json_loads(line)
                    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                        self.error(f"audit.jsonl line {expected_sequence} is invalid: {exc}")
                        continue
                    if not isinstance(record, dict):
                        self.error(f"audit.jsonl line {expected_sequence} is not an object")
                        continue
                    missing_keys = _AUDIT_REQUIRED_KEYS - set(record)
                    if missing_keys:
                        self.error(
                            f"audit.jsonl line {expected_sequence} lacks required fields: "
                            f"{sorted(missing_keys)}"
                        )
                        continue
                    if record.get("schema_version") != SCHEMA_VERSION:
                        self.error(f"audit.jsonl line {expected_sequence} schema_version is not 1")
                    if record.get("run_id") != self.run_id:
                        self.error(f"audit.jsonl line {expected_sequence} run_id mismatch")
                    if record.get("sequence") != expected_sequence:
                        self.error(f"audit.jsonl sequence mismatch at line {expected_sequence}")
                    event_id = record.get("event_id")
                    if not isinstance(event_id, str) or not event_id:
                        self.error(f"audit.jsonl line {expected_sequence} has no event_id")
                    elif event_id in event_ids:
                        self.error(f"audit.jsonl duplicate event_id: {event_id}")
                    else:
                        event_ids.add(event_id)
                    if not isinstance(record.get("event_type"), str) or not record.get(
                        "event_type"
                    ):
                        self.error(f"audit.jsonl line {expected_sequence} has no event_type")
                    if record.get("previous_hash") != previous_hash:
                        self.error(f"audit.jsonl hash-link mismatch at line {expected_sequence}")
                    entry_hash = record.get("entry_hash")
                    if not _is_lower_sha256(entry_hash):
                        self.error(f"audit.jsonl line {expected_sequence} has invalid entry_hash")
                    unsigned = {key: value for key, value in record.items() if key != "entry_hash"}
                    try:
                        expected_hash = hashlib.sha256(
                            _canonical_json(unsigned).encode("utf-8")
                        ).hexdigest()
                    except (TypeError, ValueError) as exc:
                        self.error(
                            f"audit.jsonl line {expected_sequence} is not canonicalizable: {exc}"
                        )
                        expected_hash = ""
                    if entry_hash != expected_hash:
                        self.error(f"audit.jsonl entry hash mismatch at line {expected_sequence}")
                    if isinstance(entry_hash, str):
                        previous_hash = entry_hash
                    entries.append(record)
        except OSError as exc:
            self.error(f"audit.jsonl could not be read: {exc}")
            return None
        if total_bytes != contract.get("bytes"):
            self.error("audit.jsonl byte count does not match manifest")
        if digest.hexdigest() != contract.get("sha256"):
            self.error("audit.jsonl SHA-256 does not match manifest")
        if len(entries) != contract.get("entry_count"):
            self.error("audit.jsonl entry count does not match manifest")
        if not entries:
            self.error("audit.jsonl contains no valid records")
            return entries
        if entries[-1].get("entry_hash") != contract.get("final_entry_hash"):
            self.error("audit final entry hash does not match manifest")
        return entries

    def _verify_terminal(self, manifest: dict[str, Any], entries: list[dict[str, Any]]) -> bool:
        completed = [entry for entry in entries if entry.get("event_type") == "run.completed"]
        valid = True
        if len(completed) != 1:
            self.error("audit must contain exactly one run.completed event")
            return False
        if entries[-1] is not completed[0]:
            self.error("run.completed must be the final audit event")
            valid = False
        payload = completed[0].get("payload")
        if not isinstance(payload, dict):
            self.error("run.completed payload must be an object")
            return False
        terminal = manifest.get("terminal")
        if not isinstance(terminal, dict):
            return False
        if payload.get("status") != terminal.get("status"):
            self.error("run.completed status does not match manifest terminal")
            valid = False
        if payload.get("exit_code") != terminal.get("exit_code"):
            self.error("run.completed exit_code does not match manifest terminal")
            valid = False
        return valid

    def _receipt_excerpt(self, payload: dict[str, Any], call_id: str) -> str | None:
        excerpt = payload.get("output_excerpt")
        legacy = payload.get("output_first_2kb")
        if excerpt is not None and legacy is not None and excerpt != legacy:
            self.error(f"tool receipt {call_id} has conflicting excerpt fields")
        selected = excerpt if excerpt is not None else legacy
        if not isinstance(selected, str):
            self.error(f"tool receipt {call_id} has no text output excerpt")
            return None
        return selected

    @staticmethod
    def _largest_utf8_prefix(prefix: bytes) -> str | None:
        candidate = prefix[:MAX_EXCERPT_BYTES]
        while True:
            try:
                return candidate.decode("utf-8")
            except UnicodeDecodeError as exc:
                if exc.start == 0 and not candidate:
                    return None
                if exc.end < len(candidate):
                    return None
                candidate = candidate[: exc.start]

    def _verify_tools(self, entries: list[dict[str, Any]]) -> dict[str, _ToolReceipt]:
        started: dict[str, tuple[int, str, Any, tuple[tuple[str, str], ...]]] = {}
        completed: dict[str, tuple[int, dict[str, Any]]] = {}
        for index, entry in enumerate(entries):
            event_type = entry.get("event_type")
            if event_type not in {"tool.started", "tool.completed"}:
                continue
            payload = entry.get("payload")
            if not isinstance(payload, dict):
                self.error(f"{event_type} payload must be an object")
                continue
            call_id = payload.get("tool_call_id")
            name = payload.get("tool_name")
            arguments = payload.get("arguments")
            evidence_refs = self._parse_evidence_refs(
                payload.get("evidence_refs"),
                f"{event_type} {call_id}",
            )
            if not isinstance(call_id, str) or not call_id:
                self.error(f"{event_type} has an empty tool_call_id")
                continue
            if not isinstance(name, str) or not name:
                self.error(f"{event_type} {call_id} has an empty tool_name")
            if not isinstance(arguments, dict):
                self.error(f"{event_type} {call_id} arguments must be an object")
            if event_type == "tool.started":
                if call_id in started:
                    self.error(f"tool call has duplicate started events: {call_id}")
                else:
                    started[call_id] = (
                        index,
                        name if isinstance(name, str) else "",
                        arguments,
                        evidence_refs,
                    )
            else:
                if call_id in completed:
                    self.error(f"tool call has duplicate completed events: {call_id}")
                else:
                    completed[call_id] = (index, payload)

        for call_id in sorted(set(started) | set(completed)):
            start = started.get(call_id)
            completion = completed.get(call_id)
            if start is None:
                self.error(f"tool completion has no preceding start: {call_id}")
                continue
            if completion is None:
                self.error(f"tool start has no completion: {call_id}")
                continue
            start_index, start_name, start_arguments, start_evidence_refs = start
            completion_index, payload = completion
            if start_index >= completion_index:
                self.error(f"tool completion does not follow its start: {call_id}")
            if payload.get("tool_name") != start_name:
                self.error(f"tool name changed between start and completion: {call_id}")
            if payload.get("arguments") != start_arguments:
                self.error(f"tool arguments changed between start and completion: {call_id}")
            completion_evidence_refs = self._parse_evidence_refs(
                payload.get("evidence_refs"),
                f"tool.completed {call_id}",
            )
            if completion_evidence_refs != start_evidence_refs:
                self.error(f"tool evidence binding changed between start and completion: {call_id}")

        receipts: dict[str, _ToolReceipt] = {}
        referenced_paths: set[str] = set()
        for call_id, (complete_index, payload) in completed.items():
            start_record = started.get(call_id)
            if start_record is None:
                continue
            status_value = payload.get("status")
            if status_value not in _ALLOWED_TOOL_STATUSES:
                self.error(f"tool receipt {call_id} has an invalid status: {status_value!r}")
                continue
            path_value = payload.get("output_artifact_path")
            try:
                artifact_path = _safe_relative_path(path_value)
            except ValueError as exc:
                self.error(f"tool receipt {call_id}: {exc}")
                continue
            if not artifact_path.startswith(f"{TOOL_OUTPUT_DIRECTORY}/"):
                self.error(f"tool receipt {call_id} output is outside tool-outputs")
            referenced_paths.add(artifact_path)
            artifact = self._artifacts.get(artifact_path)
            if artifact is None:
                self.error(f"tool output is absent from manifest artifacts: {artifact_path}")
                continue
            fact = self._artifact_facts.get(artifact_path)
            if fact is None:
                self.error(f"tool output artifact is unavailable: {artifact_path}")
                continue
            receipt_digest = payload.get("output_sha256")
            receipt_bytes = payload.get("output_bytes")
            receipt_media = payload.get("output_media_type")
            receipt_encoding = payload.get("output_encoding")
            if receipt_digest != fact.sha256 or receipt_digest != artifact.sha256:
                self.error(f"tool receipt SHA-256 mismatch: {call_id}")
            if receipt_bytes != fact.byte_count or receipt_bytes != artifact.byte_count:
                self.error(f"tool receipt byte count mismatch: {call_id}")
            if receipt_media != artifact.media_type:
                self.error(f"tool receipt media type mismatch: {call_id}")
            if not isinstance(receipt_media, str) or not receipt_media:
                self.error(f"tool receipt {call_id} has no media type")
            if receipt_encoding != "utf-8":
                self.error(f"tool receipt {call_id} encoding must equal utf-8")
            if artifact.encoding is not None and artifact.encoding.lower() != "utf-8":
                self.error(f"manifest encoding disagrees with tool receipt: {artifact_path}")
            if payload.get("accepted_output_complete") is not True:
                self.error(f"tool receipt {call_id} does not attest complete accepted output")
            nested = payload.get("output_artifact")
            expected_nested = {
                "path": artifact_path,
                "sha256": receipt_digest,
                "bytes": receipt_bytes,
                "encoding": receipt_encoding,
                "media_type": receipt_media,
                "complete": True,
            }
            if nested != expected_nested:
                self.error(f"tool receipt {call_id} nested output_artifact is not bound")
            expected_suffix = ".json" if receipt_media == "application/json" else ".txt"
            if PurePosixPath(artifact_path).name != f"{receipt_digest}{expected_suffix}":
                self.error(f"tool receipt {call_id} output path is not content-addressed")
            excerpt = self._receipt_excerpt(payload, call_id)
            expected_excerpt = self._largest_utf8_prefix(fact.prefix) if fact.valid_utf8 else None
            if expected_excerpt is None:
                self.error(f"tool output has no valid UTF-8 prefix: {call_id}")
                continue
            if excerpt != expected_excerpt:
                self.error(f"tool receipt excerpt is not the exact <=2048-byte prefix: {call_id}")
            if excerpt is None:
                continue
            evidence_refs = self._parse_evidence_refs(
                payload.get("evidence_refs"),
                f"tool.completed {call_id}",
            )
            start_index, start_name, start_arguments, _start_refs = start_record
            receipts[call_id] = _ToolReceipt(
                call_id=call_id,
                tool_name=start_name,
                arguments=start_arguments if isinstance(start_arguments, dict) else {},
                status=status_value,
                artifact_path=artifact_path,
                excerpt=excerpt,
                fact=fact,
                evidence_refs=evidence_refs,
                start_index=start_index,
                complete_index=complete_index,
            )
        self._verify_tool_output_inventory(referenced_paths)
        return receipts

    def _parse_evidence_refs(
        self,
        raw: Any,
        label: str,
    ) -> tuple[tuple[str, str], ...]:
        if raw is None:
            return ()
        if not isinstance(raw, list):
            self.error(f"{label} evidence_refs must be an array")
            return ()
        parsed: list[tuple[str, str]] = []
        seen: set[str] = set()
        for index, value in enumerate(raw):
            if not isinstance(value, dict):
                self.error(f"{label} evidence_refs[{index}] must be an object")
                continue
            evidence_id = value.get("evidence_id")
            digest = value.get("sha256")
            if not isinstance(evidence_id, str) or not evidence_id:
                self.error(f"{label} evidence_refs[{index}] has no evidence_id")
                continue
            if evidence_id in seen:
                self.error(f"{label} contains duplicate evidence_id {evidence_id!r}")
                continue
            if not _is_lower_sha256(digest):
                self.error(f"{label} evidence_refs[{index}] has an invalid SHA-256")
                continue
            seen.add(evidence_id)
            parsed.append((evidence_id, digest))
        return tuple(parsed)

    def _verify_tool_output_inventory(self, referenced_paths: set[str]) -> None:
        tool_directory = self.root / TOOL_OUTPUT_DIRECTORY
        try:
            info = tool_directory.lstat()
        except FileNotFoundError:
            if referenced_paths:
                self.error("tool-outputs directory is missing")
            return
        except OSError as exc:
            self.error(f"tool-outputs directory could not be inspected: {exc}")
            return
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            self.error("tool-outputs must be a real, non-symlink directory")
            return
        actual: set[str] = set()
        for directory, directory_names, file_names in os.walk(tool_directory, followlinks=False):
            base = Path(directory)
            for name in list(directory_names):
                candidate = base / name
                try:
                    candidate_info = candidate.lstat()
                except OSError as exc:
                    self.error(f"tool-output directory could not be inspected: {exc}")
                    directory_names.remove(name)
                    continue
                if stat.S_ISLNK(candidate_info.st_mode):
                    relative = candidate.relative_to(self.root).as_posix()
                    self.error(f"tool-output inventory contains a symlink: {relative}")
                    directory_names.remove(name)
                elif not stat.S_ISDIR(candidate_info.st_mode):
                    relative = candidate.relative_to(self.root).as_posix()
                    self.error(f"tool-output inventory contains a non-directory: {relative}")
                    directory_names.remove(name)
            for name in file_names:
                candidate = base / name
                relative = candidate.relative_to(self.root).as_posix()
                try:
                    candidate_info = candidate.lstat()
                except OSError as exc:
                    self.error(f"tool output could not be inspected ({relative}): {exc}")
                    continue
                if stat.S_ISLNK(candidate_info.st_mode) or not stat.S_ISREG(candidate_info.st_mode):
                    self.error(f"tool-output inventory contains a non-regular file: {relative}")
                    continue
                actual.add(relative)
                if name.endswith(".tmp") or name.startswith(".") and ".tmp" in name:
                    self.error(f"temporary tool-output file survived finalization: {relative}")
        for relative in sorted(actual - referenced_paths):
            self.error(f"unreferenced tool-output file: {relative}")
        for relative in sorted(referenced_paths - actual):
            self.error(f"referenced tool-output file is missing: {relative}")

    @staticmethod
    def _inline_citations(value: str) -> set[str]:
        return {match.strip() for match in _INLINE_CITATION_RE.findall(value)}

    def _file_contains(self, fact: _FileFact, needle: bytes) -> bool:
        if not needle:
            return False
        content = self._read_verified_fact(fact, label=f"tool output {fact.path.name}")
        return content is not None and needle in content

    def _verify_citations(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
    ) -> None:
        investigator_events = [
            entry for entry in entries if entry.get("event_type") == "investigator.finished"
        ]
        judge_events = [entry for entry in entries if entry.get("event_type") == "judge.completed"]
        if len(investigator_events) > 1:
            self.error("audit contains multiple investigator.finished events")
        if len(judge_events) > 1:
            self.error("audit contains multiple judge.completed events")
        if self.terminal_status == "COMPLETE":
            if len(investigator_events) != 1:
                self.error("COMPLETE run requires exactly one investigator.finished event")
            if len(judge_events) != 1:
                self.error("COMPLETE run requires exactly one judge.completed event")
        if not investigator_events:
            if judge_events:
                self.error("judge verdicts exist without investigator findings")
            return
        investigator_payload = investigator_events[-1].get("payload")
        if not isinstance(investigator_payload, dict):
            self.error("investigator.finished payload must be an object")
            return
        raw_findings = investigator_payload.get("findings")
        if not isinstance(raw_findings, list):
            self.error("investigator.finished findings must be an array")
            return
        findings: dict[str, dict[str, Any]] = {}
        evidence_spans: dict[str, dict[str, _EvidenceSpan]] = {}
        for index, raw in enumerate(raw_findings):
            if not isinstance(raw, dict):
                self.error(f"investigator finding {index} must be an object")
                continue
            finding_id = raw.get("finding_id")
            if not isinstance(finding_id, str) or not finding_id:
                self.error(f"investigator finding {index} has no finding_id")
                continue
            if finding_id in findings:
                self.error(f"duplicate investigator finding_id: {finding_id}")
                continue
            findings[finding_id] = raw
            proposed = raw.get("proposed_status")
            if proposed not in _FINDING_RANK:
                self.error(f"finding {finding_id} has invalid proposed_status")
            citations = raw.get("tool_call_ids")
            if (
                not isinstance(citations, list)
                or not citations
                or any(not isinstance(call_id, str) or not call_id for call_id in citations)
            ):
                self.error(f"finding {finding_id} must cite one or more tool calls")
                continue
            if len(citations) != len(set(citations)):
                self.error(f"finding {finding_id} contains duplicate tool citations")
            unknown = set(citations) - set(receipts)
            if unknown:
                self.error(f"finding {finding_id} cites unknown tool calls: {sorted(unknown)}")
            summary = raw.get("summary")
            if not isinstance(summary, str):
                self.error(f"finding {finding_id} summary must be a string")
            elif self._inline_citations(summary) != set(citations):
                self.error(f"finding {finding_id} inline citations do not match tool_call_ids")
            if proposed == "CONFIRMED" and not any(
                receipts.get(call_id) is not None and receipts[call_id].status == "success"
                for call_id in citations
            ):
                self.error(f"confirmed finding {finding_id} cites no successful tool receipt")
            evidence_spans[finding_id] = self._verify_supporting_spans(
                finding_id,
                raw.get("supporting_spans"),
                citations if isinstance(citations, list) else [],
                receipts,
                required=self.require_complete or self.require_live_gpt56,
            )

        if not judge_events:
            return
        judge_payload = judge_events[-1].get("payload")
        if not isinstance(judge_payload, dict):
            self.error("judge.completed payload must be an object")
            return
        raw_verdicts = judge_payload.get("verdicts")
        if not isinstance(raw_verdicts, list):
            self.error("judge.completed verdicts must be an array")
            return
        verdicts: dict[str, dict[str, Any]] = {}
        for index, raw in enumerate(raw_verdicts):
            if not isinstance(raw, dict):
                self.error(f"judge verdict {index} must be an object")
                continue
            finding_id = raw.get("finding_id")
            if not isinstance(finding_id, str) or not finding_id:
                self.error(f"judge verdict {index} has no finding_id")
                continue
            if finding_id in verdicts:
                self.error(f"judge duplicated verdict for finding: {finding_id}")
                continue
            verdicts[finding_id] = raw
        if set(verdicts) != set(findings):
            missing = sorted(set(findings) - set(verdicts))
            extra = sorted(set(verdicts) - set(findings))
            self.error(
                f"judge verdict set does not match findings; missing={missing}, extra={extra}"
            )
        for finding_id, verdict in verdicts.items():
            finding = findings.get(finding_id)
            if finding is None:
                continue
            status_value = verdict.get("status")
            proposed = finding.get("proposed_status")
            if status_value not in _FINDING_RANK:
                self.error(f"judge verdict {finding_id} has invalid status")
            elif (
                proposed in _FINDING_RANK and _FINDING_RANK[status_value] > _FINDING_RANK[proposed]
            ):
                self.error(f"judge upgraded finding {finding_id}")
            rationale = verdict.get("rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                self.error(f"judge verdict {finding_id} has no rationale")
            cited = verdict.get("cited_tool_call_ids")
            if (
                not isinstance(cited, list)
                or not cited
                or any(not isinstance(call_id, str) or not call_id for call_id in cited)
            ):
                self.error(f"judge verdict {finding_id} must cite one or more tool calls")
                continue
            if len(cited) != len(set(cited)):
                self.error(f"judge verdict {finding_id} contains duplicate citations")
            finding_citations = finding.get("tool_call_ids")
            finding_set = set(finding_citations) if isinstance(finding_citations, list) else set()
            if not set(cited).issubset(finding_set):
                self.error(f"judge verdict {finding_id} cites outside the finding")
            unknown = set(cited) - set(receipts)
            if unknown:
                self.error(f"judge verdict {finding_id} cites unknown calls: {sorted(unknown)}")
            if status_value == "CONFIRMED" and not any(
                receipts.get(call_id) is not None and receipts[call_id].status == "success"
                for call_id in cited
            ):
                self.error(f"judge confirmed {finding_id} without a successful receipt")
            self._verify_quotes(
                finding_id,
                verdict.get("quoted_spans"),
                cited,
                receipts,
                evidence_spans.get(finding_id, {}),
            )

    def _verify_supporting_spans(
        self,
        finding_id: str,
        raw_spans: Any,
        cited: list[str],
        receipts: dict[str, _ToolReceipt],
        *,
        required: bool,
    ) -> dict[str, _EvidenceSpan]:
        if raw_spans is None and not required:
            return {}
        if not isinstance(raw_spans, list):
            self.error(f"finding {finding_id} supporting_spans must be an array")
            return {}
        if len(raw_spans) > 12:
            self.error(f"finding {finding_id} exceeds twelve supporting spans")
        parsed: dict[str, _EvidenceSpan] = {}
        quoted_calls: set[str] = set()
        per_call: dict[str, int] = {}
        cited_set = {value for value in cited if isinstance(value, str)}
        for index, raw in enumerate(raw_spans):
            label = f"investigator span {finding_id}/{index}"
            if not isinstance(raw, dict):
                self.error(f"{label} must be an object")
                continue
            span_id = raw.get("span_id")
            call_id = raw.get("tool_call_id")
            artifact_sha256 = raw.get("artifact_sha256")
            byte_start = raw.get("byte_start")
            byte_end = raw.get("byte_end")
            text = raw.get("text")
            occurrence_count = raw.get("occurrence_count")
            if not isinstance(span_id, str) or not span_id:
                self.error(f"{label} has no span_id")
                continue
            if span_id in parsed:
                self.error(f"finding {finding_id} contains duplicate span_id {span_id!r}")
                continue
            if not isinstance(call_id, str) or not call_id:
                self.error(f"{label} has no tool_call_id")
                continue
            if call_id not in cited_set:
                self.error(f"{label} is outside finding citations")
                continue
            if not _is_lower_sha256(artifact_sha256):
                self.error(f"{label} has an invalid artifact SHA-256")
                continue
            if (
                not _is_int(byte_start)
                or not _is_int(byte_end)
                or byte_start < 0
                or byte_end <= byte_start
            ):
                self.error(f"{label} has an invalid byte range")
                continue
            if not isinstance(text, str) or not text.strip():
                self.error(f"{label} has empty text")
                continue
            try:
                encoded = text.encode("utf-8")
            except UnicodeEncodeError:
                self.error(f"{label} text is not UTF-8")
                continue
            if len(encoded) > MAX_QUOTE_BYTES:
                self.error(f"{label} exceeds 1024 UTF-8 bytes")
            if byte_end - byte_start != len(encoded):
                self.error(f"{label} byte range length does not match its UTF-8 text")
            if not _is_int(occurrence_count) or occurrence_count < 1:
                self.error(f"{label} occurrence_count must be a positive integer")
            receipt = receipts.get(call_id)
            if receipt is None:
                continue
            if artifact_sha256 != receipt.fact.sha256:
                self.error(f"{label} artifact SHA-256 disagrees with its tool output")
            expected_id = _span_id(artifact_sha256, byte_start, byte_end)
            if span_id != expected_id:
                self.error(f"{label} span_id does not match its artifact and byte range")
            exact = self._file_slice(receipt.fact, byte_start, byte_end - byte_start)
            if exact != encoded:
                self.error(f"{label} byte range does not resolve in the full tool output")
            content = self._read_verified_fact(
                receipt.fact,
                label=f"tool output {receipt.fact.path.name}",
            )
            actual_occurrences = content.count(encoded) if content is not None else None
            if actual_occurrences is not None and occurrence_count != actual_occurrences:
                self.error(
                    f"{label} occurrence_count is {occurrence_count}, "
                    f"but the verified artifact contains {actual_occurrences}"
                )
            per_call[call_id] = per_call.get(call_id, 0) + 1
            if per_call[call_id] > 4:
                self.error(f"finding {finding_id} exceeds four spans for {call_id}")
            quoted_calls.add(call_id)
            parsed[span_id] = _EvidenceSpan(
                span_id=span_id,
                call_id=call_id,
                artifact_sha256=artifact_sha256,
                byte_start=byte_start,
                byte_end=byte_end,
                text=text,
                occurrence_count=occurrence_count,
            )
        if required:
            missing = cited_set - quoted_calls
            if missing:
                self.error(
                    f"finding {finding_id} omits supporting spans for calls: {sorted(missing)}"
                )
        return parsed

    def _file_slice(self, fact: _FileFact, offset: int, length: int) -> bytes | None:
        content = self._read_verified_fact(fact, label=f"tool output {fact.path.name}")
        if content is None:
            return None
        return content[offset : offset + length]

    def _verify_quotes(
        self,
        finding_id: str,
        raw_quotes: Any,
        cited: list[str],
        receipts: dict[str, _ToolReceipt],
        spans: dict[str, _EvidenceSpan],
    ) -> None:
        if not isinstance(raw_quotes, list):
            self.error(f"judge verdict {finding_id} quoted_spans must be an array")
            return
        quoted_calls: set[str] = set()
        seen: set[tuple[str, str, str]] = set()
        for index, raw in enumerate(raw_quotes):
            if not isinstance(raw, dict):
                self.error(f"judge quote {finding_id}/{index} must be an object")
                continue
            call_id = raw.get("tool_call_id")
            span_id = raw.get("span_id")
            text = raw.get("text")
            if spans and (not isinstance(span_id, str) or not span_id):
                self.error(f"judge quote {finding_id}/{index} has no span_id")
                continue
            if not isinstance(call_id, str) or not call_id:
                self.error(f"judge quote {finding_id}/{index} has no tool_call_id")
                continue
            if not isinstance(text, str) or not text.strip():
                self.error(f"judge quote {finding_id}/{index} has empty text")
                continue
            try:
                encoded = text.encode("utf-8")
            except UnicodeEncodeError:
                self.error(f"judge quote {finding_id}/{index} is not UTF-8")
                continue
            if len(encoded) > MAX_QUOTE_BYTES:
                self.error(f"judge quote {finding_id}/{index} exceeds 1024 UTF-8 bytes")
            normalized_span_id = span_id if isinstance(span_id, str) else ""
            pair = (normalized_span_id, call_id, text)
            if pair in seen:
                self.error(f"judge verdict {finding_id} contains a duplicate quoted span")
            seen.add(pair)
            if call_id not in cited:
                self.error(f"judge quote {finding_id}/{index} is outside cited calls")
                continue
            receipt = receipts.get(call_id)
            if receipt is None:
                continue
            quoted_calls.add(call_id)
            if spans:
                span = spans.get(normalized_span_id)
                if span is None:
                    self.error(f"judge quote {finding_id}/{index} cites unknown span {span_id!r}")
                elif span.call_id != call_id:
                    self.error(f"judge quote {finding_id}/{index} span belongs to another call")
                elif text not in span.text:
                    self.error(f"judge quote {finding_id}/{index} is absent from investigator span")
            elif text not in receipt.excerpt:
                self.error(f"judge quote {finding_id}/{index} is absent from receipt excerpt")
            if not self._file_contains(receipt.fact, encoded):
                self.error(f"judge quote {finding_id}/{index} is absent from full tool output")
        missing = set(cited) - quoted_calls
        if missing:
            self.error(f"judge verdict {finding_id} omits quotes for calls: {sorted(missing)}")

    def _verify_custody(self, entries: list[dict[str, Any]]) -> None:
        initial = [
            entry for entry in entries if entry.get("event_type") == "custody.initial.completed"
        ]
        final = [entry for entry in entries if entry.get("event_type") == "custody.final.completed"]
        mismatches = [
            entry
            for entry in entries
            if entry.get("event_type") in {"custody.mismatch", "mount.release_failed"}
        ]
        if self.terminal_status == "COMPLETE":
            if len(initial) != 1:
                self.error("COMPLETE run requires exactly one custody.initial.completed event")
            if len(final) != 1:
                self.error("COMPLETE run requires exactly one custody.final.completed event")
            if mismatches:
                self.error("COMPLETE run contains a custody or mount failure event")
        if not initial or not final:
            return
        initial_payload = initial[-1].get("payload")
        final_payload = final[-1].get("payload")
        if not isinstance(initial_payload, dict) or not isinstance(final_payload, dict):
            self.error("custody completion payloads must be objects")
            return
        if final_payload.get("match") is not True:
            self.error("final recorded custody receipt does not report match=true")
        if final_payload.get("mount_released") is not True:
            self.error("final recorded custody receipt does not report mount_released=true")
        initial_hashes = initial_payload.get("hashes")
        final_hashes = final_payload.get("hashes")
        if not isinstance(initial_hashes, dict) or not isinstance(final_hashes, dict):
            self.error("custody receipts must contain hash maps")
        elif initial_hashes != final_hashes:
            self.error("initial and final recorded custody hashes differ")
        if entries.index(initial[-1]) >= entries.index(final[-1]):
            self.error("final custody receipt does not follow initial custody receipt")

    def _verify_tool_evidence_bindings(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
        *,
        required: bool,
    ) -> None:
        initial = [
            entry for entry in entries if entry.get("event_type") == "custody.initial.completed"
        ]
        if not initial:
            if required:
                self.error("strict completion cannot bind tools without initial custody hashes")
            return
        payload = initial[-1].get("payload")
        hashes = payload.get("hashes") if isinstance(payload, dict) else None
        if not isinstance(hashes, dict):
            if required:
                self.error("strict completion initial custody hashes are unavailable")
            return
        for call_id, receipt in receipts.items():
            if receipt.status in {"rejected", "capped"}:
                continue
            if required and not receipt.evidence_refs:
                self.error(f"strict completion tool receipt has no evidence binding: {call_id}")
                continue
            for evidence_id, digest in receipt.evidence_refs:
                expected = hashes.get(evidence_id)
                if expected is None:
                    self.error(f"tool receipt {call_id} binds unknown evidence id: {evidence_id}")
                elif expected != digest:
                    self.error(
                        f"tool receipt {call_id} input SHA-256 disagrees with custody "
                        f"for {evidence_id}"
                    )

    @staticmethod
    def _gpt56_sol_model(value: Any) -> bool:
        return isinstance(value, str) and (
            value == "gpt-5.6" or value == "gpt-5.6-sol" or value.startswith("gpt-5.6-sol-")
        )

    def _verify_complete_lifecycle(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
    ) -> None:
        """Require the complete serialized protocol, not just a COMPLETE label.

        This establishes bundle self-consistency.  It deliberately does not
        claim that an offline verifier can authenticate provider-issued IDs.
        """

        for path, role in _REQUIRED_COMPLETE_ARTIFACTS.items():
            artifact = self._artifacts.get(path)
            if artifact is None:
                self.error(f"strict completion requires artifact: {path}")
                continue
            if artifact.role != role:
                self.error(
                    f"strict completion artifact {path} must have role {role!r}, "
                    f"not {artifact.role!r}"
                )
            if artifact.required is not True:
                self.error(f"strict completion artifact must be required: {path}")
            if path not in self._artifact_facts:
                self.error(f"strict completion artifact was not verified: {path}")

        event_positions: dict[str, int] = {}
        for event_type in _REQUIRED_COMPLETE_EVENTS:
            matches = [
                index
                for index, entry in enumerate(entries)
                if entry.get("event_type") == event_type
            ]
            if len(matches) != 1:
                self.error(
                    f"strict completion requires exactly one {event_type} event; "
                    f"found {len(matches)}"
                )
            else:
                event_positions[event_type] = matches[0]
        ordered_positions = [
            event_positions[event_type]
            for event_type in _REQUIRED_COMPLETE_EVENTS
            if event_type in event_positions
        ]
        if ordered_positions != sorted(ordered_positions):
            self.error("strict completion lifecycle events are out of protocol order")
        failure_events = {
            "model.error",
            "model.protocol_error",
            "model.retry.skipped",
            "cap.fired",
            "run.preflight_failed",
            "run.failed",
            "run.interrupted",
            "custody.mismatch",
            "mount.release_failed",
            "bundle.finalization_failed",
        }
        present_failures = sorted(
            {
                str(entry.get("event_type"))
                for entry in entries
                if entry.get("event_type") in failure_events
            }
        )
        if present_failures:
            self.error(f"strict completion contains terminal failure events: {present_failures}")
        unreachable_receipts = sorted(
            call_id
            for call_id, receipt in receipts.items()
            if receipt.status in {"capped", "rejected"}
        )
        if unreachable_receipts:
            self.error(
                "strict completion contains unreachable capped/rejected tool receipts: "
                f"{unreachable_receipts}"
            )

        request_records = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "model.request"
        ]
        option_records = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "model.request.options"
        ]
        response_records = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "model.response"
        ]
        request_events = [entry for _index, entry in request_records]
        option_events = [entry for _index, entry in option_records]
        response_events = [entry for _index, entry in response_records]
        typed_done_protocol = self._uses_typed_done_protocol(request_events)
        request_phases = self._model_phases(request_events, "model.request")
        option_phases = self._model_phases(option_events, "model.request.options")
        response_phases = self._model_phases(response_events, "model.response")
        if request_phases != response_phases:
            self.error("strict completion model.request/model.response phase sequences differ")
        if option_phases != response_phases:
            self.error("strict completion model.request.options phase sequence is incomplete")
        self._verify_model_phase_sequence(response_phases)
        cap_config = self._verify_cap_configuration(entries)
        accounting = self._verify_recorded_response_contract(response_records, cap_config)
        self._verify_final_budget(entries, receipts, cap_config, accounting)

        for transaction_index, (request_record, option_record, response_record) in enumerate(
            zip(request_records, option_records, response_records, strict=False)
        ):
            request_index, request = request_record
            option_index, option = option_record
            response_index, response = response_record
            if option_index != request_index + 1:
                self.error(
                    "strict completion requires model.request.options immediately after its request"
                )
            self._verify_model_transaction_window(
                entries,
                option_index=option_index,
                response_index=response_index,
                phase=(
                    response_phases[transaction_index]
                    if transaction_index < len(response_phases)
                    else ""
                ),
                response=response,
                request_timeout=(
                    option.get("payload", {}).get("timeout_seconds")
                    if isinstance(option.get("payload"), dict)
                    else None
                ),
            )
            self._verify_model_request_contract(request, response)
            self._verify_model_options_contract(
                option,
                cap_config,
                typed_done_protocol=typed_done_protocol,
            )
            self._verify_response_options_binding(option, response)

        self._verify_phase_windows(entries, request_records, response_records)
        self._verify_no_orphan_retry_events(entries)

        opening_catalogs = [
            entry.get("payload", {}).get("tools")
            for entry in request_events
            if isinstance(entry.get("payload"), dict) and entry["payload"].get("phase") == "opening"
        ]
        investigate_catalogs = [
            entry.get("payload", {}).get("tools")
            for entry in request_events
            if isinstance(entry.get("payload"), dict)
            and entry["payload"].get("phase") == "investigate"
        ]
        if opening_catalogs and investigate_catalogs:
            opening_catalog = opening_catalogs[0]
            typed_catalog = (
                [*opening_catalog, investigation_finish_schema()]
                if isinstance(opening_catalog, list)
                else None
            )
            if any(
                catalog != opening_catalog and catalog != typed_catalog
                for catalog in investigate_catalogs
            ):
                self.error(
                    "investigate requests must use the opening forensic catalog plus only "
                    "the canonical typed-DONE action"
                )
            if any(catalog != investigate_catalogs[0] for catalog in investigate_catalogs[1:]):
                self.error("investigate requests do not share one immutable action catalog")

        self._verify_artifact_write_receipts(entries)
        self._verify_model_controller_bindings(entries, receipts)
        self._verify_lifecycle_counts(entries, receipts)

    def _verify_cap_configuration(self, entries: list[dict[str, Any]]) -> CapConfig | None:
        """Decode audited caps while pinning the non-configurable GPT-5.6 prices."""

        payload = self._event_payload(entries, "caps.configured")
        if payload is None:
            self.error("strict completion caps.configured payload must be an object")
            return None
        if set(payload) != set(_CAP_CONFIG_FIELDS):
            self.error("strict completion caps.configured does not match the cap shape")
            return None

        valid = True
        for field in ("max_tool_calls", "max_total_tokens"):
            value = payload.get(field)
            if not _is_int(value) or value < 1:
                self.error(f"caps.configured {field} must be a positive integer")
                valid = False
        max_wall = payload.get("max_wall_seconds")
        if not _is_finite_number(max_wall) or float(max_wall) < 0.001:
            self.error("caps.configured max_wall_seconds must be at least 0.001")
            valid = False
        max_cost = payload.get("max_cost_usd")
        if not _is_finite_number(max_cost) or float(max_cost) < 0:
            self.error("caps.configured max_cost_usd must be a nonnegative number")
            valid = False

        owned = CapConfig()
        for field in _CAP_PRICE_FIELDS:
            value = payload.get(field)
            if not _is_finite_number(value) or float(value) < 0:
                self.error(f"caps.configured {field} must be a nonnegative number")
                valid = False
            elif float(value) != float(getattr(owned, field)):
                self.error(f"caps.configured {field} disagrees with code-owned GPT-5.6 pricing")
                valid = False

        if not valid:
            return None
        return CapConfig(
            max_tool_calls=int(payload["max_tool_calls"]),
            max_total_tokens=int(payload["max_total_tokens"]),
            max_wall_seconds=float(payload["max_wall_seconds"]),
            max_cost_usd=float(payload["max_cost_usd"]),
            input_usd_per_million=float(payload["input_usd_per_million"]),
            cached_input_usd_per_million=float(payload["cached_input_usd_per_million"]),
            cache_write_usd_per_million=float(payload["cache_write_usd_per_million"]),
            output_usd_per_million=float(payload["output_usd_per_million"]),
        )

    def _verify_final_budget(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
        cap_config: CapConfig | None,
        accounting: _ModelAccounting,
    ) -> None:
        """Bind recomputed tool/model accounting to the terminal budget snapshot."""

        initial_elapsed: float | None = None
        started = self._event_payload(entries, "investigation.started")
        initial_budget = started.get("budget") if started is not None else None
        if not isinstance(initial_budget, dict) or set(initial_budget) != set(_BUDGET_FIELDS):
            self.error("strict completion initial budget does not match BudgetSnapshot")
        else:
            for field in (
                "tool_calls",
                "input_tokens",
                "cached_input_tokens",
                "cache_write_tokens",
                "output_tokens",
                "total_tokens",
            ):
                value = initial_budget.get(field)
                if not _is_int(value) or value != 0:
                    self.error(f"strict completion initial budget {field} must equal zero")
            initial_cost = initial_budget.get("estimated_cost_usd")
            if not _is_finite_number(initial_cost) or float(initial_cost) != 0:
                self.error("strict completion initial budget estimated_cost_usd must equal zero")
            if initial_budget.get("fired") is not None:
                self.error("strict completion initial budget must not record a fired cap")
            initial_elapsed_raw = initial_budget.get("elapsed_seconds")
            if not _is_finite_number(initial_elapsed_raw) or float(initial_elapsed_raw) < 0:
                self.error("strict completion initial budget elapsed_seconds is invalid")
            else:
                initial_elapsed = float(initial_elapsed_raw)

        payload = self._event_payload(entries, "investigation.completed")
        if payload is None:
            self.error("strict completion investigation.completed payload must be an object")
            return
        if payload.get("status") != "COMPLETE":
            return
        expected_payload_shape = {"status", "finding_count", "verdict_count", "budget"}
        if set(payload) != expected_payload_shape:
            self.error("strict completion investigation.completed does not match its final shape")
        for field in ("finding_count", "verdict_count"):
            value = payload.get(field)
            if not _is_int(value) or value < 0:
                self.error(f"investigation.completed {field} must be a nonnegative integer")

        budget = payload.get("budget")
        if not isinstance(budget, dict) or set(budget) != set(_BUDGET_FIELDS):
            self.error("strict completion final budget does not match BudgetSnapshot")
            return
        integer_expectations = {
            "tool_calls": len(receipts),
            "input_tokens": accounting.input_tokens,
            "cached_input_tokens": accounting.cached_input_tokens,
            "cache_write_tokens": accounting.cache_write_tokens,
            "output_tokens": accounting.output_tokens,
            "total_tokens": accounting.total_tokens,
        }
        for field, expected in integer_expectations.items():
            value = budget.get(field)
            if not _is_int(value) or value < 0:
                self.error(f"final budget {field} must be a nonnegative integer")
            elif value != expected:
                self.error(f"final budget {field} disagrees with recomputed accounting")
        elapsed = budget.get("elapsed_seconds")
        if not _is_finite_number(elapsed) or float(elapsed) < 0:
            self.error("final budget elapsed_seconds must be a nonnegative number")
        elif initial_elapsed is not None and float(elapsed) < initial_elapsed:
            self.error("final budget elapsed_seconds precedes the initial budget snapshot")
        recorded_cost = budget.get("estimated_cost_usd")
        if not _is_finite_number(recorded_cost) or float(recorded_cost) < 0:
            self.error("final budget estimated_cost_usd must be a nonnegative number")
        elif not math.isclose(
            float(recorded_cost),
            accounting.estimated_cost_usd,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            self.error("final budget estimated_cost_usd disagrees with recomputed accounting")
        if budget.get("fired") is not None:
            self.error("strict completion final budget must not record a fired cap")

        if cap_config is None:
            return
        if _is_int(budget.get("tool_calls")) and budget["tool_calls"] > cap_config.max_tool_calls:
            self.error("final budget exceeds max_tool_calls")
        if (
            _is_int(budget.get("total_tokens"))
            and budget["total_tokens"] > cap_config.max_total_tokens
        ):
            self.error("final budget exceeds max_total_tokens")
        if _is_finite_number(recorded_cost) and float(recorded_cost) > cap_config.max_cost_usd:
            self.error("final budget exceeds max_cost_usd")
        if _is_finite_number(elapsed) and float(elapsed) >= cap_config.max_wall_seconds:
            self.error("final budget reaches or exceeds max_wall_seconds")

    def _verify_lifecycle_counts(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
    ) -> None:
        """Bind controller summary counts to the serialized collections."""

        investigator = self._event_payload(entries, "investigator.finished")
        judge_started = self._event_payload(entries, "judge.started")
        judge_completed = self._event_payload(entries, "judge.completed")
        completed = self._event_payload(entries, "investigation.completed")
        if not all(
            isinstance(value, dict)
            for value in (investigator, judge_started, judge_completed, completed)
        ):
            return
        findings = investigator.get("findings")
        verdicts = judge_completed.get("verdicts")
        if not isinstance(findings, list) or not isinstance(verdicts, list):
            return
        if set(judge_started) != {"finding_count", "receipt_count"}:
            self.error("judge.started does not match its canonical count shape")
        started_findings = judge_started.get("finding_count")
        started_receipts = judge_started.get("receipt_count")
        if not _is_int(started_findings) or started_findings < 0:
            self.error("judge.started finding_count must be a nonnegative integer")
        elif started_findings != len(findings):
            self.error("judge.started finding_count differs from serialized findings")
        if not _is_int(started_receipts) or started_receipts < 0:
            self.error("judge.started receipt_count must be a nonnegative integer")
        elif started_receipts != len(receipts):
            self.error("judge.started receipt_count differs from verified tool receipts")
        if completed.get("finding_count") != len(findings):
            self.error("investigation.completed finding_count differs from serialized findings")
        if completed.get("verdict_count") != len(verdicts):
            self.error("investigation.completed verdict_count differs from judge verdicts")

    def _verify_recorded_response_contract(
        self,
        records: list[tuple[int, dict[str, Any]]],
        cap_config: CapConfig | None,
    ) -> _ModelAccounting:
        response_ids: set[str] = set()
        request_ids: set[str] = set()
        running_cost = 0.0
        total_input = 0
        total_cached = 0
        total_cache_write = 0
        total_output = 0
        total_tokens = 0
        for _index, entry in records:
            sequence = entry.get("sequence")
            payload = entry.get("payload")
            label = f"model.response sequence {sequence}"
            if not isinstance(payload, dict):
                self.error(f"{label} payload must be an object")
                continue
            expected_shape = {
                "phase",
                "requested_model",
                "provider_model",
                "response_id",
                "request_id",
                "status",
                "incomplete_details",
                "error",
                "message",
                "function_calls",
                "token_counts",
                "usage_error",
                "call_cost_usd_estimate",
                "running_cost_usd_estimate",
            }
            if set(payload) != expected_shape:
                self.error(f"{label} does not match the normalized response shape")
            requested = payload.get("requested_model")
            provider = payload.get("provider_model")
            if not self._gpt56_sol_model(requested):
                self.error(f"{label} requested_model is not GPT-5.6 Sol")
            if not self._gpt56_sol_model(provider):
                self.error(f"{label} provider_model is not GPT-5.6 Sol")
            if payload.get("status") != "completed":
                self.error(f"{label} status must equal completed")
            if payload.get("incomplete_details") is not None or payload.get("error") is not None:
                self.error(f"{label} records incomplete or provider-error details")
            if payload.get("usage_error") is not None:
                self.error(f"{label} records a usage protocol error")
            if not isinstance(payload.get("message"), str):
                self.error(f"{label} message must be text")
            if not isinstance(payload.get("function_calls"), list):
                self.error(f"{label} function_calls must be an array")
            response_id = payload.get("response_id")
            request_id = payload.get("request_id")
            if not isinstance(response_id, str) or not response_id:
                self.error(f"{label} has no response_id")
            elif response_id in response_ids:
                self.error(f"{label} reuses response_id {response_id!r}")
            else:
                response_ids.add(response_id)
            if not isinstance(request_id, str) or not request_id:
                self.error(f"{label} has no request_id")
            elif request_id in request_ids:
                self.error(f"{label} reuses request_id {request_id!r}")
            else:
                request_ids.add(request_id)
            counts = payload.get("token_counts")
            usage: ModelUsage | None = None
            if not isinstance(counts, dict) or set(counts) != set(_USAGE_FIELDS):
                self.error(f"{label} token_counts do not match the normalized usage shape")
            else:
                for field in _USAGE_FIELDS:
                    value = counts.get(field)
                    if not _is_int(value) or value < 0:
                        self.error(f"{label} {field} must be a nonnegative integer")
                input_tokens = counts.get("input_tokens")
                output_tokens = counts.get("output_tokens")
                provider_total = counts.get("provider_total_tokens")
                if (
                    _is_int(input_tokens)
                    and _is_int(output_tokens)
                    and _is_int(provider_total)
                    and provider_total != input_tokens + output_tokens
                ):
                    self.error(f"{label} provider_total_tokens is internally inconsistent")
                cached = counts.get("cached_input_tokens")
                if _is_int(cached) and _is_int(input_tokens) and cached > input_tokens:
                    self.error(f"{label} cached_input_tokens exceeds input_tokens")
                cache_write = counts.get("cache_write_tokens")
                if (
                    _is_int(cached)
                    and _is_int(cache_write)
                    and _is_int(input_tokens)
                    and cached + cache_write > input_tokens
                ):
                    self.error(f"{label} cache read/write tokens exceed input_tokens")
                if all(
                    _is_int(counts.get(field)) and counts[field] >= 0 for field in _USAGE_FIELDS
                ):
                    usage = ModelUsage(**{field: counts[field] for field in _USAGE_FIELDS})
                    total_input += usage.input_tokens
                    total_cached += usage.cached_input_tokens
                    total_cache_write += usage.cache_write_tokens
                    total_output += usage.output_tokens
                    total_tokens += usage.total_tokens
            for field in ("call_cost_usd_estimate", "running_cost_usd_estimate"):
                value = payload.get(field)
                if not _is_finite_number(value) or float(value) < 0:
                    self.error(f"{label} {field} must be a nonnegative number")
            call_cost = payload.get("call_cost_usd_estimate")
            recorded_running = payload.get("running_cost_usd_estimate")
            if (
                cap_config is not None
                and usage is not None
                and _is_finite_number(call_cost)
                and _is_finite_number(recorded_running)
            ):
                model_id = requested if isinstance(requested, str) else "gpt-5.6"
                expected_call = estimate_usage_cost(cap_config, usage, model_id)
                if not math.isclose(
                    float(call_cost),
                    expected_call,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                ):
                    self.error(f"{label} call cost disagrees with audited usage and pricing")
                running_cost += expected_call
                if not math.isclose(
                    float(recorded_running),
                    running_cost,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                ):
                    self.error(f"{label} running cost disagrees with recomputed call costs")

        return _ModelAccounting(
            input_tokens=total_input,
            cached_input_tokens=total_cached,
            cache_write_tokens=total_cache_write,
            output_tokens=total_output,
            total_tokens=total_tokens,
            estimated_cost_usd=running_cost,
        )

    def _verify_model_transaction_window(
        self,
        entries: list[dict[str, Any]],
        *,
        option_index: int,
        response_index: int,
        phase: str,
        response: dict[str, Any],
        request_timeout: Any,
    ) -> None:
        if response_index <= option_index:
            self.error(f"{phase} model.response does not follow its request options")
            return
        between = entries[option_index + 1 : response_index]
        if not between:
            return
        self._retry_event_indices.update(range(option_index + 1, response_index))
        if len(between) < 3 or len(between) % 2 != 1:
            self.error(f"{phase} model transaction contains an invalid retry event sequence")
            return
        failed_attempts = (len(between) - 1) // 2
        if failed_attempts > 2:
            self.error(f"{phase} model transaction exceeds the two-retry hard limit")
        max_attempts: int | None = None
        previous_retry_timeout: float | None = None
        for offset in range(failed_attempts):
            attempt = offset + 1
            error_entry = between[offset * 2]
            scheduled_entry = between[offset * 2 + 1]
            if error_entry.get("event_type") != "model.attempt.error":
                self.error(f"{phase} retry attempt {attempt} omits model.attempt.error")
                continue
            if scheduled_entry.get("event_type") != "model.retry.scheduled":
                self.error(f"{phase} retry attempt {attempt} omits model.retry.scheduled")
                continue
            error_payload = error_entry.get("payload")
            scheduled_payload = scheduled_entry.get("payload")
            if not isinstance(error_payload, dict) or not isinstance(scheduled_payload, dict):
                self.error(f"{phase} retry attempt {attempt} payload is malformed")
                continue
            if set(error_payload) != {
                "phase",
                "attempt",
                "max_attempts",
                "retryable",
                "status_code",
                "request_id",
                "error_type",
                "error",
                "billing_exposure",
            }:
                self.error(f"{phase} model.attempt.error {attempt} has the wrong shape")
            if set(scheduled_payload) != {
                "phase",
                "attempt",
                "next_attempt",
                "max_attempts",
                "delay_seconds",
                "next_timeout_seconds",
            }:
                self.error(f"{phase} model.retry.scheduled {attempt} has the wrong shape")
            candidate_max = error_payload.get("max_attempts")
            if candidate_max not in {2, 3} or candidate_max <= attempt:
                self.error(f"{phase} retry attempt {attempt} has an invalid max_attempts")
            elif max_attempts is None:
                max_attempts = candidate_max
            elif candidate_max != max_attempts:
                self.error(f"{phase} retry attempts disagree on max_attempts")
            if (
                error_payload.get("phase") != phase
                or error_payload.get("attempt") != attempt
                or error_payload.get("retryable") is not True
                or error_payload.get("billing_exposure") != "unknown_after_dispatch"
            ):
                self.error(f"{phase} model.attempt.error {attempt} is not retry-safe")
            if (
                not isinstance(error_payload.get("error_type"), str)
                or not error_payload.get("error_type")
                or not isinstance(error_payload.get("error"), str)
                or not error_payload.get("error")
                or (
                    error_payload.get("request_id") is not None
                    and not isinstance(error_payload.get("request_id"), str)
                )
            ):
                self.error(f"{phase} model.attempt.error {attempt} metadata is malformed")
            if (
                scheduled_payload.get("phase") != phase
                or scheduled_payload.get("attempt") != attempt
                or scheduled_payload.get("next_attempt") != attempt + 1
                or scheduled_payload.get("max_attempts") != candidate_max
            ):
                self.error(f"{phase} model.retry.scheduled {attempt} is inconsistent")
            delay = scheduled_payload.get("delay_seconds")
            if delay != 0.25 * (2 ** (attempt - 1)):
                self.error(f"{phase} model.retry.scheduled {attempt} has an invalid backoff")
            next_timeout = scheduled_payload.get("next_timeout_seconds")
            if (
                not isinstance(next_timeout, (int, float))
                or isinstance(next_timeout, bool)
                or next_timeout <= 0
            ):
                self.error(f"{phase} model.retry.scheduled {attempt} has no positive timeout")
            status_code = error_payload.get("status_code")
            if status_code is not None and (
                not _is_int(status_code)
                or (status_code not in {408, 409, 429} and status_code < 500)
            ):
                self.error(f"{phase} model.attempt.error {attempt} has a nontransient status")
            if (
                status_code is None
                and error_payload.get("error_type") not in _RETRYABLE_TRANSPORT_ERROR_TYPES
            ):
                self.error(
                    f"{phase} model.attempt.error {attempt} is not a retryable transport type"
                )
            if _is_finite_number(next_timeout):
                if not _is_finite_number(request_timeout) or float(next_timeout) > float(
                    request_timeout
                ):
                    self.error(
                        f"{phase} model.retry.scheduled {attempt} exceeds the request timeout"
                    )
                if (
                    previous_retry_timeout is not None
                    and float(next_timeout) > previous_retry_timeout
                ):
                    self.error(
                        f"{phase} model.retry.scheduled {attempt} increases the retry timeout"
                    )
                previous_retry_timeout = float(next_timeout)

        succeeded = between[-1]
        succeeded_payload = succeeded.get("payload")
        response_payload = response.get("payload")
        final_attempt = failed_attempts + 1
        if succeeded.get("event_type") != "model.retry.succeeded" or not isinstance(
            succeeded_payload, dict
        ):
            self.error(f"{phase} recovered transaction omits model.retry.succeeded")
            return
        if not isinstance(response_payload, dict):
            return
        if set(succeeded_payload) != {
            "phase",
            "attempt",
            "max_attempts",
            "response_id",
            "request_id",
            "provider_model",
            "status",
        }:
            self.error(f"{phase} model.retry.succeeded has the wrong shape")
        if (
            succeeded_payload.get("phase") != phase
            or succeeded_payload.get("attempt") != final_attempt
            or succeeded_payload.get("max_attempts") != max_attempts
            or succeeded_payload.get("response_id") != response_payload.get("response_id")
            or succeeded_payload.get("request_id") != response_payload.get("request_id")
            or succeeded_payload.get("provider_model") != response_payload.get("provider_model")
            or succeeded_payload.get("status") != response_payload.get("status")
        ):
            self.error(f"{phase} model.retry.succeeded does not bind the accepted response")

    def _verify_no_orphan_retry_events(self, entries: list[dict[str, Any]]) -> None:
        retry_types = {
            "model.attempt.error",
            "model.retry.scheduled",
            "model.retry.succeeded",
            "model.retry.skipped",
        }
        actual = {
            index for index, entry in enumerate(entries) if entry.get("event_type") in retry_types
        }
        if actual != self._retry_event_indices:
            self.error("strict completion contains orphaned or unbound model retry events")

    def _verify_phase_windows(
        self,
        entries: list[dict[str, Any]],
        requests: list[tuple[int, dict[str, Any]]],
        responses: list[tuple[int, dict[str, Any]]],
    ) -> None:
        boundaries = {
            "opening": ("investigation.started", "opening.completed"),
            "investigate": ("opening.completed", "investigator.done"),
            "investigation-finalize": ("investigator.done", "investigator.finished"),
            "judge": ("judge.started", "judge.completed"),
            "report": ("report.started", "report.completed"),
        }
        for (request_index, request), (response_index, response) in zip(
            requests, responses, strict=False
        ):
            request_payload = request.get("payload")
            response_payload = response.get("payload")
            phase = request_payload.get("phase") if isinstance(request_payload, dict) else None
            if not isinstance(phase, str) or phase not in boundaries:
                continue
            start_event, end_event = boundaries[phase]
            start = self._event_index(entries, start_event)
            end = self._event_index(entries, end_event)
            if start is None or end is None:
                continue
            if not (start < request_index < response_index < end):
                self.error(f"{phase} model transaction is outside its lifecycle phase window")
            if isinstance(response_payload, dict) and response_payload.get("phase") != phase:
                self.error(f"{phase} response crosses a lifecycle phase boundary")

    def _verify_model_request_contract(
        self,
        request: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        payload = request.get("payload")
        sequence = request.get("sequence")
        label = f"model.request sequence {sequence}"
        if not isinstance(payload, dict):
            self.error(f"{label} payload must be an object")
            return
        required = {
            "phase",
            "requested_model",
            "instructions",
            "input",
            "tools",
            "previous_response_id",
        }
        if set(payload) != required:
            self.error(f"{label} does not match the audited request shape")
        if not self._gpt56_sol_model(payload.get("requested_model")):
            self.error(f"{label} requested_model is not GPT-5.6 Sol")
        if not isinstance(payload.get("instructions"), str) or not payload["instructions"].strip():
            self.error(f"{label} instructions must be nonempty text")
        if not isinstance(payload.get("input"), (list, str)):
            self.error(f"{label} input must be an array or text")
        if payload.get("previous_response_id") is not None:
            self.error(f"{label} replays provider transcript state")
        response_payload = response.get("payload")
        if isinstance(response_payload, dict):
            if response_payload.get("phase") != payload.get("phase"):
                self.error(f"{label} phase differs from its model.response")
            if response_payload.get("requested_model") != payload.get("requested_model"):
                self.error(f"{label} requested_model differs from its model.response")
        tools = payload.get("tools")
        if not isinstance(tools, list) or not tools:
            self.error(f"{label} tools must be a nonempty typed catalog")
            return
        schema_by_name: dict[str, dict[str, Any]] = {}
        for ordinal, schema in enumerate(tools):
            schema_label = f"{label} tools[{ordinal}]"
            if not isinstance(schema, dict):
                self.error(f"{schema_label} must be an object")
                continue
            if set(schema) != {"type", "name", "description", "parameters", "strict"}:
                self.error(f"{schema_label} does not match the strict function-tool shape")
            name = schema.get("name")
            if schema.get("type") != "function" or schema.get("strict") is not True:
                self.error(f"{schema_label} is not a strict function tool")
            if not isinstance(name, str) or not name:
                self.error(f"{schema_label} has no name")
                continue
            if name in schema_by_name:
                self.error(f"{label} duplicates tool schema {name!r}")
            schema_by_name[name] = schema
            if not isinstance(schema.get("description"), str) or not schema["description"].strip():
                self.error(f"{schema_label} has no description")
            parameters = schema.get("parameters")
            if not isinstance(parameters, dict) or set(parameters) != {
                "type",
                "properties",
                "required",
                "additionalProperties",
            }:
                self.error(f"{schema_label} parameters do not match the strict object shape")
                continue
            properties = parameters.get("properties")
            parameter_required = parameters.get("required")
            if (
                parameters.get("type") != "object"
                or not isinstance(properties, dict)
                or not isinstance(parameter_required, list)
                or any(not isinstance(value, str) for value in parameter_required)
                or set(parameter_required) != set(properties)
                or parameters.get("additionalProperties") is not False
            ):
                self.error(f"{schema_label} parameters are not closed and fully required")

        for call in self._response_calls(response, require_valid=False):
            name = call.get("name")
            schema = schema_by_name.get(name) if isinstance(name, str) else None
            if schema is None:
                self.error(f"{label} did not expose response function {name!r}")
                continue
            arguments = call.get("arguments")
            parameters = schema.get("parameters")
            required_names = parameters.get("required") if isinstance(parameters, dict) else None
            properties = parameters.get("properties") if isinstance(parameters, dict) else None
            if not isinstance(arguments, dict):
                continue
            if isinstance(required_names, list) and set(arguments) != set(required_names):
                self.error(f"{label} response arguments do not match schema for {name!r}")
            if not isinstance(properties, dict):
                continue
            for argument_name, value in arguments.items():
                property_schema = properties.get(argument_name)
                if isinstance(property_schema, dict) and not matches_json_schema_type(
                    value, property_schema.get("type")
                ):
                    self.error(
                        f"{label} response argument {argument_name!r} has the wrong "
                        f"type for {name!r}"
                    )

    def _verify_model_options_contract(
        self,
        entry: dict[str, Any],
        cap_config: CapConfig | None,
        *,
        typed_done_protocol: bool,
    ) -> None:
        payload = entry.get("payload")
        sequence = entry.get("sequence")
        label = f"model.request.options sequence {sequence}"
        if not isinstance(payload, dict):
            self.error(f"{label} payload must be an object")
            return
        legacy_required = {
            "phase",
            "parallel_tool_calls",
            "tool_choice",
            "max_output_tokens",
            "estimated_input_tokens",
            "timeout_seconds",
            "store",
            "include",
            "reasoning_context",
            "reasoning_effort",
            "text_verbosity",
            "max_tool_calls",
            "prompt_cache_mode",
        }
        current_required = legacy_required | {"minimum_output_tokens"}
        payload_keys = set(payload)
        if typed_done_protocol:
            if payload_keys != current_required:
                self.error(f"{label} does not match the typed-DONE-v2 audited options shape")
        elif payload_keys not in (legacy_required, current_required):
            self.error(f"{label} does not match a supported audited options shape")
        phase = payload.get("phase")
        policies: dict[str, tuple[Any, ...]] = {
            "opening": (True, "required", 2_048, "low", "low", 6),
            "investigate": (False, "required", 4_096, "medium", "low", 1),
            "investigation-finalize": (
                False,
                {"type": "function", "name": "submit_investigation"},
                12_288,
                "medium",
                "low",
                1,
            ),
            "judge": (
                False,
                {"type": "function", "name": "submit_judgment"},
                12_288,
                "high",
                "low",
                1,
            ),
            "report": (
                False,
                {"type": "function", "name": "submit_report_draft"},
                8_192,
                "low",
                "medium",
                1,
            ),
        }
        policy = policies.get(phase) if isinstance(phase, str) else None
        if policy is None:
            return
        parallel, choice, maximum, effort, verbosity, maximum_calls = policy
        exact = {
            "parallel_tool_calls": parallel,
            "tool_choice": choice,
            "store": False,
            "include": [],
            "reasoning_context": "current_turn",
            "reasoning_effort": effort,
            "text_verbosity": verbosity,
            "max_tool_calls": maximum_calls,
            "prompt_cache_mode": "implicit",
        }
        for field, expected in exact.items():
            if field == "tool_choice" and phase == "investigate":
                investigate_choice = payload.get(field)
                if not isinstance(investigate_choice, str):
                    self.error(f"{label} investigate tool_choice must be a string")
                elif typed_done_protocol and investigate_choice != "required":
                    self.error(f"{label} typed-DONE-v2 investigate tool_choice must be required")
                elif not typed_done_protocol and investigate_choice not in (
                    "auto",
                    "required",
                ):
                    self.error(f"{label} tool_choice violates the investigate phase policy")
                continue
            if payload.get(field) != expected:
                self.error(f"{label} {field} violates the {phase} phase policy")
        output_tokens = payload.get("max_output_tokens")
        if not _is_int(output_tokens) or not 1 <= output_tokens <= maximum:
            self.error(f"{label} max_output_tokens violates the {phase} hard ceiling")
        phase_minimum = {
            "investigate": 4_096,
            "investigation-finalize": 4_096,
            "judge": 4_096,
        }.get(phase, 1)
        has_minimum = "minimum_output_tokens" in payload
        audited_minimum = payload.get("minimum_output_tokens")
        if typed_done_protocol and not has_minimum:
            self.error(f"{label} omits typed-DONE-v2 minimum_output_tokens")
        if has_minimum:
            if not _is_int(audited_minimum) or audited_minimum < 1:
                self.error(f"{label} minimum_output_tokens must be a positive integer")
            elif audited_minimum != phase_minimum:
                self.error(f"{label} minimum_output_tokens violates the {phase} phase policy")
        if (
            (typed_done_protocol or has_minimum)
            and _is_int(output_tokens)
            and output_tokens < phase_minimum
        ):
            self.error(f"{label} max_output_tokens violates the {phase} phase minimum")
        estimated = payload.get("estimated_input_tokens")
        if not _is_int(estimated) or estimated < 1:
            self.error(f"{label} estimated_input_tokens must be positive")
        timeout = payload.get("timeout_seconds")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            self.error(f"{label} timeout_seconds must be positive")
        elif cap_config is not None and float(timeout) > cap_config.max_wall_seconds:
            self.error(f"{label} timeout_seconds exceeds max_wall_seconds")

    def _verify_response_options_binding(
        self,
        option: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        option_payload = option.get("payload")
        response_payload = response.get("payload")
        if not isinstance(option_payload, dict) or not isinstance(response_payload, dict):
            return
        maximum = option_payload.get("max_output_tokens")
        counts = response_payload.get("token_counts")
        output_tokens = counts.get("output_tokens") if isinstance(counts, dict) else None
        if _is_int(maximum) and _is_int(output_tokens) and output_tokens > maximum:
            phase = response_payload.get("phase")
            self.error(f"{phase} response output_tokens exceed the audited request maximum")

    @staticmethod
    def _artifact_dict(artifact: _Artifact) -> dict[str, Any]:
        return {
            "role": artifact.role,
            "path": artifact.path,
            "sha256": artifact.sha256,
            "bytes": artifact.byte_count,
            "media_type": artifact.media_type,
            "encoding": artifact.encoding,
            "required": artifact.required,
        }

    def _verify_artifact_write_receipts(self, entries: list[dict[str, Any]]) -> None:
        expected_order = [
            "report.md",
            "profile.json",
            "environment.json",
            "summary.json",
            "viewer.html",
        ]
        expected_paths = set(expected_order)
        writes: dict[str, int] = {}
        ordered_writes: list[tuple[int, str]] = []
        final_custody = self._event_index(entries, "custody.final.completed")
        run_completed = self._event_index(entries, "run.completed")
        for index, entry in enumerate(entries):
            if entry.get("event_type") != "artifact.written":
                continue
            payload = entry.get("payload")
            if not isinstance(payload, dict):
                self.error("strict completion artifact.written payload must be an object")
                continue
            path = payload.get("path")
            if not isinstance(path, str) or not path:
                self.error("strict completion artifact.written receipt has no path")
                continue
            if path in writes:
                self.error(f"strict completion duplicated artifact.written receipt: {path}")
            writes[path] = index
            ordered_writes.append((index, path))
            artifact = self._artifacts.get(path)
            if artifact is None:
                self.error(f"artifact.written receipt names an unmanifested artifact: {path}")
                continue
            expected = self._artifact_dict(artifact)
            if payload != expected:
                self.error(
                    f"artifact.written descriptor does not match the manifest artifact: {path}"
                )
            if final_custody is not None and index <= final_custody:
                self.error(f"artifact.written receipt precedes final custody: {path}")
            if run_completed is not None and index >= run_completed:
                self.error(f"artifact.written receipt does not precede run.completed: {path}")
        missing = expected_paths - set(writes)
        extra = set(writes) - expected_paths
        if missing:
            self.error(
                f"strict completion audit omits artifact.written receipts for: {sorted(missing)}"
            )
        if extra:
            self.error(
                "strict completion contains unexpected artifact.written receipts for: "
                f"{sorted(extra)}"
            )
        if [path for _index, path in ordered_writes] != expected_order:
            self.error("strict completion root artifact receipts are not in renderer order")
        indices = [index for index, _path in ordered_writes]
        if indices and indices != list(range(indices[0], indices[0] + len(indices))):
            self.error("strict completion root artifact receipts are not contiguous")
        if final_custody is not None and indices and indices[0] != final_custody + 1:
            self.error("strict completion root artifact block does not follow final custody")
        if run_completed is not None and indices and indices[-1] != run_completed - 1:
            self.error("strict completion root artifact block does not end at run.completed")

    @staticmethod
    def _event_index(entries: list[dict[str, Any]], event_type: str) -> int | None:
        matches = [
            index for index, entry in enumerate(entries) if entry.get("event_type") == event_type
        ]
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def _event_payload(entries: list[dict[str, Any]], event_type: str) -> dict[str, Any] | None:
        matches = [entry for entry in entries if entry.get("event_type") == event_type]
        if len(matches) != 1:
            return None
        payload = matches[0].get("payload")
        return payload if isinstance(payload, dict) else None

    def _response_calls(
        self,
        entry: dict[str, Any],
        *,
        require_valid: bool,
    ) -> tuple[dict[str, Any], ...]:
        payload = entry.get("payload")
        sequence = entry.get("sequence")
        label = f"model.response sequence {sequence}"
        if not isinstance(payload, dict):
            self.error(f"{label} payload must be an object")
            return ()
        raw_calls = payload.get("function_calls")
        if not isinstance(raw_calls, list):
            self.error(f"{label} function_calls must be an array")
            return ()
        calls: list[dict[str, Any]] = []
        seen: set[str] = set()
        required_keys = {"call_id", "name", "arguments", "arguments_valid", "parse_error"}
        for ordinal, raw in enumerate(raw_calls):
            call_label = f"{label} function_calls[{ordinal}]"
            if not isinstance(raw, dict):
                self.error(f"{call_label} must be an object")
                continue
            if set(raw) != required_keys:
                self.error(f"{call_label} does not match the normalized function-call shape")
            call_id = raw.get("call_id")
            name = raw.get("name")
            arguments = raw.get("arguments")
            arguments_valid = raw.get("arguments_valid")
            parse_error = raw.get("parse_error")
            if not isinstance(call_id, str) or not call_id:
                self.error(f"{call_label} has no call_id")
                continue
            if call_id in seen:
                self.error(f"{label} duplicates function call_id {call_id!r}")
            seen.add(call_id)
            if not isinstance(name, str) or not name:
                self.error(f"{call_label} has no function name")
            if not isinstance(arguments, dict):
                self.error(f"{call_label} arguments must be an object")
            if not isinstance(arguments_valid, bool):
                self.error(f"{call_label} arguments_valid must be a boolean")
            if parse_error is not None and not isinstance(parse_error, str):
                self.error(f"{call_label} parse_error must be text or null")
            if require_valid and (arguments_valid is not True or parse_error is not None):
                self.error(f"{call_label} is not a valid structured function call")
            calls.append(raw)
        return tuple(calls)

    @staticmethod
    def _response_message(entry: dict[str, Any]) -> str | None:
        payload = entry.get("payload")
        message = payload.get("message") if isinstance(payload, dict) else None
        return message if isinstance(message, str) else None

    def _bind_call_to_receipt(
        self,
        call: dict[str, Any],
        receipts: dict[str, _ToolReceipt],
        *,
        after_index: int,
        before_index: int,
        label: str,
    ) -> _ToolReceipt | None:
        call_id = call.get("call_id")
        if not isinstance(call_id, str):
            return None
        receipt = receipts.get(call_id)
        if receipt is None:
            self.error(f"{label} has no complete tool receipt: {call_id}")
            return None
        if receipt.tool_name != call.get("name"):
            self.error(f"{label} tool name disagrees with its model function call: {call_id}")
        if receipt.arguments != call.get("arguments"):
            self.error(f"{label} arguments disagree with its model function call: {call_id}")
        if not (after_index < receipt.start_index < receipt.complete_index < before_index):
            self.error(f"{label} receipt is outside its controller turn: {call_id}")
        return receipt

    def _verify_model_controller_bindings(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
    ) -> None:
        responses = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "model.response"
        ]
        if len(responses) < 5:
            return
        all_call_ids: list[str] = []

        opening_index, opening_response = responses[0]
        opening_calls = self._response_calls(opening_response, require_valid=True)
        if not 1 <= len(opening_calls) <= 6:
            self.error("opening response must contain between one and six typed function calls")
        opening_names = [call.get("name") for call in opening_calls]
        if len(opening_names) != len(set(opening_names)):
            self.error("opening response must select distinct typed function tools")
        opening_completed_index = self._event_index(entries, "opening.completed")
        opening_payload = self._event_payload(entries, "opening.completed")
        if opening_completed_index is not None and opening_payload is not None:
            opening_ids = [call.get("call_id") for call in opening_calls]
            if opening_payload.get("tool_call_ids") != opening_ids:
                self.error("opening.completed tool_call_ids do not match the opening response")
            if opening_payload.get("selected") != len(opening_calls):
                self.error("opening.completed selected count does not match the opening response")
            if opening_payload.get("response_id") != self._response_id(opening_response):
                self.error("opening.completed response_id does not match the opening response")
            for call in opening_calls:
                receipt = self._bind_call_to_receipt(
                    call,
                    receipts,
                    after_index=opening_index,
                    before_index=opening_completed_index,
                    label="opening function call",
                )
                call_id = call.get("call_id")
                if isinstance(call_id, str):
                    all_call_ids.append(call_id)
                if receipt is not None and receipt.status == "rejected":
                    self.error("strict completion cannot preserve a rejected opening call")
            if opening_payload.get("rejected") != 0:
                self.error("opening.completed rejected count must equal zero")
            if opening_payload.get("executed") != len(opening_calls):
                self.error("opening.completed executed count does not match tool receipts")

        investigate_responses = responses[1:-3]
        investigate_request_records = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "model.request"
            and isinstance(entry.get("payload"), dict)
            and entry["payload"].get("phase") == "investigate"
        ]
        investigate_request_indices = [index for index, _entry in investigate_request_records]
        typed_done_protocol = self._uses_typed_done_protocol(
            [entry for _index, entry in investigate_request_records]
        )
        investigate_options = [
            entry.get("payload")
            for entry in entries
            if entry.get("event_type") == "model.request.options"
            and isinstance(entry.get("payload"), dict)
            and entry["payload"].get("phase") == "investigate"
        ]
        expected_choice = "required" if typed_done_protocol else "auto"
        if any(option.get("tool_choice") != expected_choice for option in investigate_options):
            self.error(
                "investigate tool_choice does not match its literal-DONE or typed-DONE catalog"
            )
        action_events = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "investigator.action"
        ]
        nonterminal_calls: list[tuple[int, int, dict[str, Any], _ToolReceipt | None, str, int]] = []
        terminal_action_call_id: str | None = None
        for ordinal, (response_index, response) in enumerate(investigate_responses, start=1):
            is_terminal = ordinal == len(investigate_responses)
            calls = self._response_calls(response, require_valid=True)
            message = self._response_message(response)
            if is_terminal:
                if typed_done_protocol:
                    if len(calls) != 1:
                        self.error(
                            "terminal investigate response must contain one typed-DONE action"
                        )
                    elif calls[0].get("name") != INVESTIGATION_FINISH_TOOL_NAME or calls[0].get(
                        "arguments"
                    ) != {"status": "DONE"}:
                        self.error(
                            "terminal investigate response does not contain canonical typed DONE"
                        )
                    else:
                        call_id = calls[0].get("call_id")
                        if isinstance(call_id, str) and call_id:
                            terminal_action_call_id = call_id
                else:
                    if calls:
                        self.error(
                            "legacy terminal investigate response must not contain a function call"
                        )
                    if message != "DONE":
                        self.error("terminal investigate response must be the literal DONE")
                continue
            if len(calls) != 1:
                self.error("each nonterminal investigate response must contain one function call")
                continue
            if calls[0].get("name") == INVESTIGATION_FINISH_TOOL_NAME:
                self.error("typed-DONE action may appear only on the terminal investigate turn")
                continue
            if message is None or not message.strip() or message.strip() == "DONE":
                self.error(
                    "each nonterminal investigate response must include a visible ledger update"
                )
            update = message.strip() if message else ""
            if update and not any(
                character.isprintable() and not character.isspace() for character in update
            ):
                self.error(f"investigate turn {ordinal} ledger update has no visible text")
            try:
                update_bytes = len(update.encode("utf-8"))
            except UnicodeEncodeError:
                self.error(f"investigate turn {ordinal} ledger update is not valid UTF-8")
                update_bytes = MAX_CASE_LEDGER_UPDATE_BYTES + 1
            if update_bytes > MAX_CASE_LEDGER_UPDATE_BYTES:
                self.error(
                    f"investigate turn {ordinal} ledger update exceeds "
                    f"{MAX_CASE_LEDGER_UPDATE_BYTES} UTF-8 bytes"
                )
            next_index = investigate_responses[ordinal][0]
            receipt = self._bind_call_to_receipt(
                calls[0],
                receipts,
                after_index=response_index,
                before_index=next_index,
                label=f"investigate turn {ordinal}",
            )
            call_id = calls[0].get("call_id")
            if isinstance(call_id, str):
                all_call_ids.append(call_id)
            nonterminal_calls.append(
                (ordinal, response_index, calls[0], receipt, update, update_bytes)
            )

        note_events = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.get("event_type") == "investigator.notes.updated"
        ]
        if len(note_events) != len(nonterminal_calls):
            self.error("investigator.notes.updated count does not match nonterminal model turns")
        else:
            cumulative_notes = ""
            for (note_index, note), (
                turn,
                response_index,
                _call,
                receipt,
                update,
                update_bytes,
            ) in zip(note_events, nonterminal_calls, strict=True):
                cumulative_notes = (
                    update if not cumulative_notes else f"{cumulative_notes}\n\n{update}"
                )
                payload = note.get("payload")
                expected = {
                    "turn": turn,
                    "case_ledger_update": update,
                    "case_ledger_update_bytes": update_bytes,
                    "case_notes": cumulative_notes,
                }
                if payload != expected:
                    self.error(
                        f"investigator.notes.updated does not bind the model ledger on turn {turn}"
                    )
                if note_index <= response_index:
                    self.error(f"case-ledger update precedes its model response on turn {turn}")
                if receipt is not None and note_index >= receipt.start_index:
                    self.error(f"case-ledger update does not precede tool execution on turn {turn}")

        if len(action_events) != len(nonterminal_calls):
            self.error("investigator.action count does not match nonterminal model turns")
        else:
            for (action_index, action), (
                turn,
                _response_index,
                call,
                receipt,
                _update,
                _update_bytes,
            ) in zip(action_events, nonterminal_calls, strict=True):
                payload = action.get("payload")
                call_id = call.get("call_id")
                if not isinstance(payload, dict):
                    self.error("investigator.action payload must be an object")
                    continue
                expected = {
                    "turn": turn,
                    "tool_call_id": call_id,
                    "tool_name": call.get("name"),
                    "status": receipt.status if receipt is not None else payload.get("status"),
                }
                if payload != expected:
                    self.error(f"investigator.action does not match model/tool turn {turn}")
                if receipt is not None and action_index <= receipt.complete_index:
                    self.error(f"investigator.action precedes tool completion on turn {turn}")
                next_request_index = (
                    investigate_request_indices[turn]
                    if turn < len(investigate_request_indices)
                    else investigate_responses[turn][0]
                )
                if action_index >= next_request_index:
                    self.error(f"investigator.action escapes controller turn {turn}")

        if investigate_responses:
            terminal_index, terminal_response = investigate_responses[-1]
            done_index = self._event_index(entries, "investigator.done")
            done_payload = self._event_payload(entries, "investigator.done")
            finalizer_index = responses[-3][0]
            if done_index is not None and not (terminal_index < done_index < finalizer_index):
                self.error("investigator.done is outside the terminal DONE boundary")
            if done_payload is not None:
                if done_payload.get("turn") != len(investigate_responses):
                    self.error("investigator.done turn count does not match investigate responses")
                if done_payload.get("response_id") != self._response_id(terminal_response):
                    self.error("investigator.done response_id does not match terminal DONE")
                terminal_protocol = done_payload.get("terminal_protocol")
                if typed_done_protocol:
                    if not isinstance(terminal_protocol, str):
                        self.error("typed investigator.done terminal_protocol must be text")
                    elif terminal_protocol != "typed-DONE-v2":
                        self.error("investigator.done does not identify the typed-DONE-v2 protocol")
                    recorded_call_id = done_payload.get("terminal_action_call_id")
                    if not isinstance(recorded_call_id, str) or not recorded_call_id:
                        self.error(
                            "typed investigator.done terminal_action_call_id must be nonempty text"
                        )
                    elif recorded_call_id != terminal_action_call_id:
                        self.error(
                            "investigator.done terminal_action_call_id does not match terminal DONE"
                        )
                else:
                    if terminal_protocol is not None and not isinstance(terminal_protocol, str):
                        self.error(
                            "legacy investigator.done terminal_protocol must be text or null"
                        )
                    elif terminal_protocol not in (None, "literal-DONE-v1"):
                        self.error(
                            "legacy investigator.done has an invalid terminal protocol label"
                        )

        if terminal_action_call_id is not None and terminal_action_call_id in (
            set(all_call_ids) | set(receipts)
        ):
            self.error("typed terminal action reuses a forensic function call_id")

        if len(all_call_ids) != len(set(all_call_ids)):
            self.error("model responses reuse a forensic function call_id")
        if set(all_call_ids) != set(receipts):
            missing = sorted(set(all_call_ids) - set(receipts))
            extra = sorted(set(receipts) - set(all_call_ids))
            self.error(
                "tool receipt set does not match opening/adaptive model calls; "
                f"missing={missing}, extra={extra}"
            )

        expected_ledger = "\n\n".join(value[-2] for value in nonterminal_calls)
        opening_input_ids = [
            call_id
            for call_id in (call.get("call_id") for call in opening_calls)
            if isinstance(call_id, str)
        ]
        adaptive_input_ids = [
            call_id
            for call_id in (value[2].get("call_id") for value in nonterminal_calls)
            if isinstance(call_id, str)
        ]
        ledger_updates = [value[-2] for value in nonterminal_calls]
        self._verify_phase_request_inputs(
            entries,
            receipts,
            opening_input_ids,
            adaptive_input_ids,
            ledger_updates,
        )
        self._verify_finalizer_binding(
            entries,
            responses[-3],
            len(investigate_responses),
            expected_ledger,
        )
        self._verify_judge_binding(entries, responses[-2])
        self._verify_report_binding(entries, responses[-1])

    def _verify_phase_request_inputs(
        self,
        entries: list[dict[str, Any]],
        receipts: dict[str, _ToolReceipt],
        opening_call_ids: list[str],
        adaptive_call_ids: list[str],
        ledger_updates: list[str],
    ) -> None:
        """Reconstruct every controller-owned model packet and observation receipt."""

        requests: dict[str, list[tuple[int, dict[str, Any]]]] = {}
        for index, entry in enumerate(entries):
            if entry.get("event_type") != "model.request":
                continue
            payload = entry.get("payload")
            phase = payload.get("phase") if isinstance(payload, dict) else None
            if isinstance(phase, str):
                requests.setdefault(phase, []).append((index, entry))

        profile = self._profile_public
        if profile is None:
            self.error("strict model input binding has no verified evidence profile")
            return

        opening = requests.get("opening", [])
        if len(opening) != 1:
            self.error("opening has no unique audited request input")
        else:
            self._verify_exact_request_input(
                opening[0][1],
                {"evidence_profile": profile},
                (),
                receipts,
                label="opening request",
            )

        investigate = requests.get("investigate", [])
        expected_turns = len(adaptive_call_ids) + 1
        if len(investigate) != expected_turns:
            self.error("investigate request count does not match adaptive controller turns")
        started = self._event_payload(entries, "investigation.started")
        started_budget = started.get("budget") if isinstance(started, dict) else None
        started_elapsed = (
            started_budget.get("elapsed_seconds") if isinstance(started_budget, dict) else None
        )
        previous_elapsed = float(started_elapsed) if _is_finite_number(started_elapsed) else None
        for ordinal, (request_index, request) in enumerate(investigate):
            label = f"investigate request turn {ordinal + 1}"
            packet = self._model_user_packet(request, label=label)
            if packet is None:
                continue
            if set(packet) != {
                "evidence_profile",
                "case_ledger",
                "receipt_index",
                "budget",
                "latest_observation_call_ids",
            }:
                self.error(f"{label} user packet has the wrong fields")
            prior_updates = ledger_updates[:ordinal]
            ledger = "\n\n".join(prior_updates)
            latest_ids = opening_call_ids if ordinal == 0 else [adaptive_call_ids[ordinal - 1]]
            expected_receipts = self._receipt_index_before(entries, request_index)
            expected_ledger = {
                "case_notes": ledger,
                "turns_completed": ordinal,
                "limitations": [],
                "unresolved_questions": [],
            }
            if packet.get("evidence_profile") != profile:
                self.error(f"{label} uses a different evidence profile")
            if packet.get("case_ledger") != expected_ledger:
                self.error(f"{label} does not contain the cumulative case ledger")
            if packet.get("receipt_index") != expected_receipts:
                self.error(f"{label} receipt_index differs from prior tool receipts")
            if packet.get("latest_observation_call_ids") != latest_ids:
                self.error(f"{label} latest observation IDs are unbound")
            previous_elapsed = self._verify_request_budget(
                entries,
                request_index,
                packet.get("budget"),
                previous_elapsed,
                label=label,
            )
            expected_packet = {
                "evidence_profile": profile,
                "case_ledger": expected_ledger,
                "receipt_index": expected_receipts,
                "budget": packet.get("budget"),
                "latest_observation_call_ids": latest_ids,
            }
            self._verify_exact_request_input(
                request,
                expected_packet,
                tuple(latest_ids),
                receipts,
                label=label,
            )

        completed = self._event_payload(entries, "investigation.completed")
        final_budget = completed.get("budget") if isinstance(completed, dict) else None
        final_elapsed = (
            final_budget.get("elapsed_seconds") if isinstance(final_budget, dict) else None
        )
        if (
            previous_elapsed is not None
            and _is_finite_number(final_elapsed)
            and previous_elapsed > float(final_elapsed)
        ):
            self.error("investigate request budget elapsed time exceeds the final budget")

        all_call_ids = [*opening_call_ids, *adaptive_call_ids]
        expected_ledger = "\n\n".join(ledger_updates)
        finalizer = requests.get("investigation-finalize", [])
        if len(finalizer) != 1:
            self.error("investigation-finalize has no unique audited request input")
        else:
            finalizer_index, finalizer_request = finalizer[0]
            self._verify_exact_request_input(
                finalizer_request,
                {
                    "controller_request": "Serialize the completed investigation only.",
                    "evidence_profile": profile,
                    "case_notes_so_far": expected_ledger,
                    "receipt_index": self._receipt_index_before(entries, finalizer_index),
                },
                tuple(all_call_ids),
                receipts,
                label="investigation-finalize request",
            )

        investigator = self._event_payload(entries, "investigator.finished")
        judge = requests.get("judge", [])
        if len(judge) != 1:
            self.error("judge has no unique audited request input")
        elif investigator is not None:
            judge_index, judge_request = judge[0]
            self._verify_exact_request_input(
                judge_request,
                {
                    "evidence_profile": profile,
                    "case_notes": investigator.get("case_notes"),
                    "findings": investigator.get("findings"),
                    "receipt_index": self._receipt_index_before(entries, judge_index),
                },
                (),
                receipts,
                label="judge request",
            )

        judge_completed = self._event_payload(entries, "judge.completed")
        report = requests.get("report", [])
        if len(report) != 1:
            self.error("report has no unique audited request input")
        elif investigator is not None and judge_completed is not None:
            _report_index, report_request = report[0]
            self._verify_exact_request_input(
                report_request,
                {
                    "run_status": "COMPLETE",
                    "evidence_profile": profile,
                    "case_notes": investigator.get("case_notes"),
                    "findings": investigator.get("findings"),
                    "judge_verdicts": judge_completed.get("verdicts"),
                    "limitations": investigator.get("limitations"),
                    "unresolved_questions": investigator.get("unresolved_questions"),
                },
                (),
                receipts,
                label="report request",
            )

    def _verify_exact_request_input(
        self,
        request: dict[str, Any],
        packet: dict[str, Any],
        observation_call_ids: tuple[str, ...],
        receipts: dict[str, _ToolReceipt],
        *,
        label: str,
    ) -> None:
        expected: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": _canonical_json(packet)}],
            }
        ]
        expected.extend(self._verified_observation_items(observation_call_ids, receipts))
        payload = request.get("payload")
        actual = payload.get("input") if isinstance(payload, dict) else None
        if actual != expected:
            self.error(f"{label} input is not the exact deterministic controller packet")

    def _verified_observation_items(
        self,
        call_ids: tuple[str, ...],
        receipts: dict[str, _ToolReceipt],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for call_id in call_ids:
            receipt = receipts.get(call_id)
            if receipt is None:
                self.error(f"model observation references unknown tool receipt: {call_id}")
                continue
            content = self._read_verified_fact(
                receipt.fact,
                label=f"tool output {receipt.fact.path.name}",
            )
            if content is None:
                continue
            try:
                output = content.decode("utf-8")
            except UnicodeDecodeError:
                self.error(f"tool observation output is not UTF-8: {call_id}")
                continue
            model_output = ToolResult(
                call_id=receipt.call_id,
                tool_name=receipt.tool_name,
                arguments=receipt.arguments,
                output=output,
                output_sha256=receipt.fact.sha256,
                status=receipt.status,
                started_at="",
                ended_at="",
                duration_ms=0,
            ).model_output()
            encoded = model_output.encode("utf-8", errors="replace")
            prefix = encoded[:MAX_EXCERPT_BYTES].decode("utf-8", errors="ignore")
            items.extend(
                [
                    {
                        "type": "function_call",
                        "call_id": receipt.call_id,
                        "name": receipt.tool_name,
                        "arguments": _canonical_json(receipt.arguments),
                    },
                    {
                        "type": "function_call_output",
                        "call_id": receipt.call_id,
                        "output_sha256": hashlib.sha256(encoded).hexdigest(),
                        "output_first_2kb": prefix,
                        "output_bytes": len(encoded),
                    },
                ]
            )
        return items

    @staticmethod
    def _receipt_index_before(
        entries: list[dict[str, Any]],
        before_index: int,
    ) -> list[dict[str, Any]]:
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
        return [
            {key: payload.get(key) for key in keys}
            for index, entry in enumerate(entries)
            if index < before_index
            and entry.get("event_type") == "tool.completed"
            and isinstance((payload := entry.get("payload")), dict)
        ]

    def _verify_request_budget(
        self,
        entries: list[dict[str, Any]],
        request_index: int,
        budget: Any,
        previous_elapsed: float | None,
        *,
        label: str,
    ) -> float | None:
        if not isinstance(budget, dict) or set(budget) != set(_BUDGET_FIELDS):
            self.error(f"{label} budget does not match BudgetSnapshot")
            return previous_elapsed
        responses = [
            entry.get("payload")
            for index, entry in enumerate(entries)
            if index < request_index
            and entry.get("event_type") == "model.response"
            and isinstance(entry.get("payload"), dict)
        ]
        totals = {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "cache_write_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        running_cost = 0.0
        for response in responses:
            counts = response.get("token_counts")
            if not isinstance(counts, dict):
                continue
            for target, source in (
                ("input_tokens", "input_tokens"),
                ("cached_input_tokens", "cached_input_tokens"),
                ("cache_write_tokens", "cache_write_tokens"),
                ("output_tokens", "output_tokens"),
                ("total_tokens", "provider_total_tokens"),
            ):
                value = counts.get(source)
                if _is_int(value) and value >= 0:
                    totals[target] += value
            call_cost = response.get("call_cost_usd_estimate")
            if _is_finite_number(call_cost):
                running_cost += float(call_cost)
        tool_calls = len(self._receipt_index_before(entries, request_index))
        expected_integers = {"tool_calls": tool_calls, **totals}
        for field, expected in expected_integers.items():
            if budget.get(field) != expected:
                self.error(f"{label} budget {field} differs from prior audited activity")
        cost = budget.get("estimated_cost_usd")
        if not _is_finite_number(cost) or not math.isclose(
            float(cost),
            running_cost,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            self.error(f"{label} budget cost differs from prior model responses")
        if budget.get("fired") is not None:
            self.error(f"{label} budget records a fired cap")
        elapsed = budget.get("elapsed_seconds")
        if not _is_finite_number(elapsed) or float(elapsed) < 0:
            self.error(f"{label} budget elapsed_seconds is invalid")
            return previous_elapsed
        normalized_elapsed = float(elapsed)
        if previous_elapsed is not None and normalized_elapsed < previous_elapsed:
            self.error(f"{label} budget elapsed_seconds decreases between turns")
        caps = self._event_payload(entries, "caps.configured")
        max_wall = caps.get("max_wall_seconds") if isinstance(caps, dict) else None
        if _is_finite_number(max_wall) and normalized_elapsed >= float(max_wall):
            self.error(f"{label} budget elapsed_seconds reaches the wall cap")
        return normalized_elapsed

    @staticmethod
    def _response_id(entry: dict[str, Any]) -> Any:
        payload = entry.get("payload")
        return payload.get("response_id") if isinstance(payload, dict) else None

    @staticmethod
    def _string_list(value: Any) -> list[str] | None:
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            return None
        return list(value)

    def _model_user_packet(
        self,
        entry: dict[str, Any],
        *,
        label: str,
    ) -> dict[str, Any] | None:
        payload = entry.get("payload")
        input_items = payload.get("input") if isinstance(payload, dict) else None
        if not isinstance(input_items, list) or not input_items:
            self.error(f"{label} has no audited user packet")
            return None
        first = input_items[0]
        content = first.get("content") if isinstance(first, dict) else None
        if (
            not isinstance(first, dict)
            or first.get("role") != "user"
            or not isinstance(content, list)
            or len(content) != 1
        ):
            self.error(f"{label} user packet has an invalid message shape")
            return None
        item = content[0]
        text = item.get("text") if isinstance(item, dict) else None
        if (
            not isinstance(item, dict)
            or item.get("type") != "input_text"
            or not isinstance(text, str)
        ):
            self.error(f"{label} user packet has no canonical input_text")
            return None
        try:
            packet = _strict_json_loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            self.error(f"{label} user packet is not strict JSON: {exc}")
            return None
        if not isinstance(packet, dict) or _canonical_json(packet) != text:
            self.error(f"{label} user packet is not one canonical JSON object")
            return None
        return packet

    def _verify_finalizer_binding(
        self,
        entries: list[dict[str, Any]],
        response_record: tuple[int, dict[str, Any]],
        investigate_turns: int,
        expected_ledger: str,
    ) -> None:
        response_index, response = response_record
        calls = self._response_calls(response, require_valid=True)
        if len(calls) != 1 or (calls and calls[0].get("name") != "submit_investigation"):
            self.error("investigation-finalize must call submit_investigation exactly once")
            return
        call = calls[0]
        arguments = call.get("arguments")
        finished_index = self._event_index(entries, "investigator.finished")
        finished = self._event_payload(entries, "investigator.finished")
        if not isinstance(arguments, dict) or finished is None:
            return
        if finished_index is not None and response_index >= finished_index:
            self.error("investigator.finished does not follow submit_investigation")
        required = {
            "status",
            "case_notes",
            "findings",
            "limitations",
            "unresolved_questions",
        }
        if set(arguments) != required or arguments.get("status") != "DONE":
            self.error("submit_investigation arguments do not match the forced serializer schema")
            return
        if finished.get("turns") != investigate_turns:
            self.error("investigator.finished turns do not match investigate model turns")
        if finished.get("case_ledger") != expected_ledger:
            self.error("investigator.finished case_ledger differs from adaptive ledger updates")
        finalizer_requests = [
            entry
            for entry in entries
            if entry.get("event_type") == "model.request"
            and isinstance(entry.get("payload"), dict)
            and entry["payload"].get("phase") == "investigation-finalize"
        ]
        if len(finalizer_requests) != 1:
            self.error("investigation-finalize has no unique audited request")
        else:
            packet = self._model_user_packet(
                finalizer_requests[0],
                label="investigation-finalize request",
            )
            if packet is not None:
                if set(packet) != {
                    "controller_request",
                    "evidence_profile",
                    "case_notes_so_far",
                    "receipt_index",
                }:
                    self.error("investigation-finalize user packet has the wrong fields")
                if (
                    packet.get("controller_request")
                    != "Serialize the completed investigation only."
                ):
                    self.error("investigation-finalize controller request is not canonical")
                if packet.get("case_notes_so_far") != expected_ledger:
                    self.error(
                        "investigation-finalize request does not contain the adaptive ledger"
                    )
                if packet.get("evidence_profile") != self._profile_public:
                    self.error("investigation-finalize request uses a different evidence profile")
                if not isinstance(packet.get("receipt_index"), list):
                    self.error("investigation-finalize receipt_index is not an array")
        for source_key, event_key in (
            ("case_notes", "case_notes"),
            ("limitations", "limitations"),
            ("unresolved_questions", "unresolved_questions"),
        ):
            if arguments.get(source_key) != finished.get(event_key):
                self.error(f"investigator.finished {event_key} differs from serializer arguments")
        raw_findings = arguments.get("findings")
        event_findings = finished.get("findings")
        if not isinstance(raw_findings, list) or not isinstance(event_findings, list):
            self.error("serialized and recorded findings must both be arrays")
            return
        if len(raw_findings) != len(event_findings):
            self.error("investigator.finished finding count differs from serializer arguments")
            return
        for ordinal, (raw, recorded) in enumerate(
            zip(raw_findings, event_findings, strict=True),
            start=1,
        ):
            if not isinstance(raw, dict) or not isinstance(recorded, dict):
                self.error(f"serialized finding {ordinal} is malformed")
                continue
            self._verify_serialized_finding(raw, recorded, ordinal)

    def _verify_serialized_finding(
        self,
        raw: dict[str, Any],
        recorded: dict[str, Any],
        ordinal: int,
    ) -> None:
        required = {
            "finding_id",
            "title",
            "summary",
            "proposed_status",
            "severity",
            "tool_call_ids",
            "supporting_quotes",
            "iocs",
            "limitations",
        }
        if set(raw) != required:
            self.error(f"submit_investigation finding {ordinal} has the wrong fields")
            return
        normalized_status = (
            str(raw.get("proposed_status") or "NEEDS-REVIEW").upper().replace("_", "-")
        )
        expected = {
            "finding_id": str(raw.get("finding_id") or f"F{ordinal:03d}"),
            "title": str(raw.get("title") or "Untitled finding"),
            "summary": str(raw.get("summary") or ""),
            "proposed_status": (
                normalized_status if normalized_status in _FINDING_RANK else "NEEDS-REVIEW"
            ),
            "severity": str(raw.get("severity") or "UNKNOWN").upper(),
            "tool_call_ids": self._string_list(raw.get("tool_call_ids")),
            "iocs": self._string_list(raw.get("iocs")),
            "limitations": self._string_list(raw.get("limitations")),
        }
        for key, value in expected.items():
            if value is None or recorded.get(key) != value:
                self.error(f"investigator.finished finding {ordinal} field {key} is unbound")
        quotes = raw.get("supporting_quotes")
        spans = recorded.get("supporting_spans")
        if not isinstance(quotes, list) or not isinstance(spans, list) or len(quotes) != len(spans):
            self.error(
                f"investigator.finished finding {ordinal} spans differ from submitted quotes"
            )
            return
        for quote_index, (quote, span) in enumerate(zip(quotes, spans, strict=True)):
            if (
                not isinstance(quote, dict)
                or set(quote) != {"tool_call_id", "text"}
                or not isinstance(span, dict)
                or quote.get("tool_call_id") != span.get("tool_call_id")
                or quote.get("text") != span.get("text")
            ):
                self.error(
                    f"investigator.finished finding {ordinal} span {quote_index} "
                    "does not resolve its submitted quote"
                )

    def _verify_judge_binding(
        self,
        entries: list[dict[str, Any]],
        response_record: tuple[int, dict[str, Any]],
    ) -> None:
        response_index, response = response_record
        calls = self._response_calls(response, require_valid=True)
        if len(calls) != 1 or (calls and calls[0].get("name") != "submit_judgment"):
            self.error("judge phase must call submit_judgment exactly once")
            return
        arguments = calls[0].get("arguments")
        completed_index = self._event_index(entries, "judge.completed")
        completed = self._event_payload(entries, "judge.completed")
        investigator = self._event_payload(entries, "investigator.finished")
        if not isinstance(arguments, dict) or completed is None or investigator is None:
            return
        if set(arguments) != {"verdicts"}:
            self.error("submit_judgment arguments do not match the forced judge schema")
            return
        if completed_index is not None and response_index >= completed_index:
            self.error("judge.completed does not follow submit_judgment")
        raw_verdicts = arguments.get("verdicts")
        recorded_verdicts = completed.get("verdicts")
        findings = investigator.get("findings")
        if not all(
            isinstance(value, list) for value in (raw_verdicts, recorded_verdicts, findings)
        ):
            self.error("judge arguments, verdicts, and findings must be arrays")
            return
        raw_by_id: dict[str, dict[str, Any]] = {}
        for raw in raw_verdicts:
            if not isinstance(raw, dict):
                self.error("submit_judgment contains a malformed verdict")
                continue
            finding_id = raw.get("finding_id")
            if not isinstance(finding_id, str) or not finding_id or finding_id in raw_by_id:
                self.error("submit_judgment contains a missing or duplicate finding_id")
                continue
            raw_by_id[finding_id] = raw
        expected_ids = [
            finding.get("finding_id") for finding in findings if isinstance(finding, dict)
        ]
        recorded_ids = [
            verdict.get("finding_id") for verdict in recorded_verdicts if isinstance(verdict, dict)
        ]
        if set(raw_by_id) != set(expected_ids) or recorded_ids != expected_ids:
            self.error("submit_judgment/judge.completed finding order or set is unbound")
            return
        finding_by_id = {
            finding.get("finding_id"): finding for finding in findings if isinstance(finding, dict)
        }
        for recorded in recorded_verdicts:
            if not isinstance(recorded, dict):
                self.error("judge.completed contains a malformed verdict")
                continue
            finding_id = recorded.get("finding_id")
            raw = raw_by_id.get(finding_id)
            finding = finding_by_id.get(finding_id)
            if raw is None or not isinstance(finding, dict):
                continue
            self._verify_recorded_verdict(raw, recorded, finding)

    def _verify_recorded_verdict(
        self,
        raw: dict[str, Any],
        recorded: dict[str, Any],
        finding: dict[str, Any],
    ) -> None:
        finding_id = str(recorded.get("finding_id") or "")
        required = {
            "finding_id",
            "status",
            "rationale",
            "cited_tool_call_ids",
            "quoted_spans",
            "annotations",
        }
        if set(raw) != required:
            self.error(f"submit_judgment verdict {finding_id} has the wrong fields")
            return
        raw_status = str(raw.get("status") or "").upper().replace("_", "-")
        proposed = finding.get("proposed_status")
        expected_status = raw_status
        annotations = self._string_list(raw.get("annotations"))
        if annotations is None:
            self.error(f"submit_judgment verdict {finding_id} annotations are malformed")
            return
        if (
            raw_status in _FINDING_RANK
            and proposed in _FINDING_RANK
            and _FINDING_RANK[raw_status] > _FINDING_RANK[proposed]
        ):
            annotations.append(
                f"Judge upgrade to {raw_status} was not applied; retained "
                f"investigator status {proposed}."
            )
            expected_status = proposed
        expected = {
            "finding_id": raw.get("finding_id"),
            "status": expected_status,
            "rationale": str(raw.get("rationale") or "").strip(),
            "cited_tool_call_ids": self._string_list(raw.get("cited_tool_call_ids")),
            "quoted_spans": raw.get("quoted_spans"),
            "annotations": annotations,
        }
        if recorded != expected:
            self.error(f"judge.completed verdict {finding_id} differs from submit_judgment")

    def _verify_report_binding(
        self,
        entries: list[dict[str, Any]],
        response_record: tuple[int, dict[str, Any]],
    ) -> None:
        response_index, response = response_record
        calls = self._response_calls(response, require_valid=True)
        if len(calls) != 1 or (calls and calls[0].get("name") != "submit_report_draft"):
            self.error("report phase must call submit_report_draft exactly once")
            return
        arguments = calls[0].get("arguments")
        completed_index = self._event_index(entries, "report.completed")
        completed = self._event_payload(entries, "report.completed")
        if not isinstance(arguments, dict) or completed is None:
            return
        if completed_index is not None and response_index >= completed_index:
            self.error("report.completed does not follow submit_report_draft")
        required = {
            "executive_summary",
            "investigative_narrative",
            "ioc_commentary",
            "limitations_commentary",
            "referenced_finding_ids",
            "referenced_span_ids",
        }
        if set(arguments) != required:
            self.error("submit_report_draft arguments do not match the report schema")
            return
        for field in (
            "executive_summary",
            "investigative_narrative",
            "ioc_commentary",
            "limitations_commentary",
        ):
            value = arguments.get(field)
            if not isinstance(value, str) or not value.strip():
                self.error(f"submit_report_draft {field} must be nonempty text")
        finding_ids = self._string_list(arguments.get("referenced_finding_ids"))
        span_ids = self._string_list(arguments.get("referenced_span_ids"))
        if finding_ids is None or len(finding_ids) != len(set(finding_ids)):
            self.error("submit_report_draft finding references are malformed")
        if span_ids is None or len(span_ids) != len(set(span_ids)):
            self.error("submit_report_draft span references are malformed")
        if completed.get("finding_ids") != finding_ids:
            self.error("report.completed finding_ids differ from submit_report_draft")
        if completed.get("span_ids") != span_ids:
            self.error("report.completed span_ids differ from submit_report_draft")
        investigator = self._event_payload(entries, "investigator.finished") or {}
        judge = self._event_payload(entries, "judge.completed") or {}
        expected_findings = {
            finding.get("finding_id")
            for finding in investigator.get("findings", [])
            if isinstance(finding, dict)
        }
        expected_spans = {
            quote.get("span_id")
            for verdict in judge.get("verdicts", [])
            if isinstance(verdict, dict)
            for quote in verdict.get("quoted_spans", [])
            if isinstance(quote, dict)
        }
        if finding_ids is not None and set(finding_ids) != expected_findings:
            self.error("submit_report_draft finding references do not match adjudicated findings")
        if span_ids is not None and set(span_ids) != expected_spans:
            self.error("submit_report_draft span references do not match judged evidence")
        report_fact = self._artifact_facts.get("report.md")
        if report_fact is None:
            return
        content = self._read_verified_fact(report_fact, label="report.md")
        if content is None:
            return
        try:
            report = content.decode("utf-8")
        except UnicodeDecodeError:
            self.error("report.md is not valid UTF-8")
            return
        if completed.get("status") != "COMPLETE":
            self.error("report.completed status must equal COMPLETE")
        if completed.get("renderer") != REPORT_RENDERER_ID:
            self.error(f"report.completed renderer is not {REPORT_RENDERER_ID}")
        if completed.get("characters") != len(report):
            self.error("report.completed characters do not match report.md")
        if completed.get("report_bytes") != len(content):
            self.error("report.completed report_bytes do not match report.md")
        if completed.get("report_sha256") != hashlib.sha256(content).hexdigest():
            self.error("report.completed report_sha256 does not match report.md")
        expected_report = self._render_expected_report(entries, arguments)
        if expected_report is not None and report != expected_report:
            self.error("report.md is not the exact deterministic rendering of verified inputs")

    def _render_expected_report(
        self,
        entries: list[dict[str, Any]],
        draft_arguments: dict[str, Any],
    ) -> str | None:
        profile = self._profile
        investigator = self._event_payload(entries, "investigator.finished")
        judge = self._event_payload(entries, "judge.completed")
        if profile is None or investigator is None or judge is None:
            self.error("deterministic report inputs are incomplete")
            return None
        raw_findings = investigator.get("findings")
        raw_verdicts = judge.get("verdicts")
        case_notes = investigator.get("case_notes")
        limitations = investigator.get("limitations")
        unresolved = investigator.get("unresolved_questions")
        if (
            not isinstance(raw_findings, list)
            or not isinstance(raw_verdicts, list)
            or not isinstance(case_notes, str)
            or not isinstance(limitations, list)
            or any(not isinstance(value, str) for value in limitations)
            or not isinstance(unresolved, list)
            or any(not isinstance(value, str) for value in unresolved)
        ):
            self.error("investigator.finished cannot be reconstructed for deterministic reporting")
            return None
        try:
            findings: list[Finding] = []
            for raw in raw_findings:
                if not isinstance(raw, dict):
                    raise ValueError("finding is not an object")
                raw_spans = raw.get("supporting_spans")
                if not isinstance(raw_spans, list):
                    raise ValueError("finding supporting_spans is not an array")
                spans = tuple(
                    EvidenceSpan(
                        span_id=str(span["span_id"]),
                        tool_call_id=str(span["tool_call_id"]),
                        artifact_sha256=str(span["artifact_sha256"]),
                        byte_start=int(span["byte_start"]),
                        byte_end=int(span["byte_end"]),
                        text=str(span["text"]),
                        occurrence_count=int(span["occurrence_count"]),
                    )
                    for span in raw_spans
                    if isinstance(span, dict)
                )
                if len(spans) != len(raw_spans):
                    raise ValueError("finding contains a non-object evidence span")
                if [span.public_dict() for span in spans] != raw_spans:
                    raise ValueError("finding evidence spans are not canonical")
                tool_call_ids = raw.get("tool_call_ids")
                iocs = raw.get("iocs")
                finding_limitations = raw.get("limitations")
                if not all(
                    isinstance(value, list) for value in (tool_call_ids, iocs, finding_limitations)
                ):
                    raise ValueError("finding arrays are malformed")
                finding = Finding(
                    finding_id=str(raw["finding_id"]),
                    title=str(raw["title"]),
                    summary=str(raw["summary"]),
                    proposed_status=FindingStatus(str(raw["proposed_status"])),
                    severity=str(raw["severity"]),
                    tool_call_ids=tuple(str(value) for value in tool_call_ids),
                    supporting_spans=spans,
                    iocs=tuple(str(value) for value in iocs),
                    limitations=tuple(str(value) for value in finding_limitations),
                )
                if finding.public_dict() != raw:
                    raise ValueError("finding record is not canonical")
                findings.append(finding)
            verdicts: list[JudgeVerdict] = []
            for raw in raw_verdicts:
                if not isinstance(raw, dict):
                    raise ValueError("verdict is not an object")
                citations = raw.get("cited_tool_call_ids")
                quotes = raw.get("quoted_spans")
                annotations = raw.get("annotations")
                if not all(isinstance(value, list) for value in (citations, quotes, annotations)):
                    raise ValueError("verdict arrays are malformed")
                parsed_quotes = tuple(
                    EvidenceQuote(
                        span_id=str(quote["span_id"]),
                        tool_call_id=str(quote["tool_call_id"]),
                        text=str(quote["text"]),
                    )
                    for quote in quotes
                    if isinstance(quote, dict)
                )
                if len(parsed_quotes) != len(quotes):
                    raise ValueError("verdict contains a non-object quote")
                verdict = JudgeVerdict(
                    finding_id=str(raw["finding_id"]),
                    status=FindingStatus(str(raw["status"])),
                    rationale=str(raw["rationale"]),
                    cited_tool_call_ids=tuple(str(value) for value in citations),
                    quoted_spans=parsed_quotes,
                    annotations=tuple(str(value) for value in annotations),
                )
                if verdict.public_dict() != raw:
                    raise ValueError("judge verdict record is not canonical")
                verdicts.append(verdict)
            state = InvestigationState(
                case_notes=case_notes,
                findings=findings,
                limitations=list(limitations),
                unresolved_questions=list(unresolved),
                turns=int(investigator.get("turns") or 0),
            )
            draft = parse_report_draft(draft_arguments, tuple(findings), tuple(verdicts))
            return render_report_markdown(profile, state, tuple(verdicts), draft)
        except (KeyError, TypeError, ValueError, ReportProtocolError) as exc:
            self.error(f"deterministic report inputs are malformed: {exc}")
            return None

    @staticmethod
    def _uses_typed_done_protocol(request_events: list[dict[str, Any]]) -> bool:
        investigate_requests = [
            entry
            for entry in request_events
            if isinstance(entry.get("payload"), dict)
            and entry["payload"].get("phase") == "investigate"
        ]
        return bool(investigate_requests) and all(
            isinstance((tools := entry["payload"].get("tools")), list)
            and any(schema == investigation_finish_schema() for schema in tools)
            for entry in investigate_requests
        )

    def _model_phases(
        self,
        events: list[dict[str, Any]],
        event_type: str,
    ) -> tuple[str, ...]:
        phases: list[str] = []
        for entry in events:
            payload = entry.get("payload")
            phase = payload.get("phase") if isinstance(payload, dict) else None
            if not isinstance(phase, str) or not phase:
                self.error(f"{event_type} sequence {entry.get('sequence')} has no phase")
                phases.append("")
            else:
                phases.append(phase)
        return tuple(phases)

    def _verify_model_phase_sequence(self, phases: tuple[str, ...]) -> None:
        minimum = len(_MODEL_PHASE_PREFIX) + 1 + len(_MODEL_PHASE_SUFFIX)
        if len(phases) < minimum:
            self.error(
                "strict completion requires opening, one-or-more investigate, "
                "investigation-finalize, judge, and report model phases"
            )
            return
        if phases[: len(_MODEL_PHASE_PREFIX)] != _MODEL_PHASE_PREFIX:
            self.error("strict completion model lifecycle must begin with opening")
        if phases[-len(_MODEL_PHASE_SUFFIX) :] != _MODEL_PHASE_SUFFIX:
            self.error(
                "strict completion model lifecycle must end with "
                "investigation-finalize, judge, report"
            )
        investigate = phases[len(_MODEL_PHASE_PREFIX) : -len(_MODEL_PHASE_SUFFIX)]
        if not investigate or any(phase != "investigate" for phase in investigate):
            self.error("strict completion model lifecycle has an invalid investigate phase span")

    def _verify_live_gpt56(self, entries: list[dict[str, Any]]) -> None:
        responses = [entry for entry in entries if entry.get("event_type") == "model.response"]
        if not responses:
            self.error("strict live GPT-5.6 verification found no model.response events")
            return
        response_ids: set[str] = set()
        request_ids: set[str] = set()
        for entry in responses:
            sequence = entry.get("sequence")
            payload = entry.get("payload")
            label = f"model.response sequence {sequence}"
            if not isinstance(payload, dict):
                self.error(f"{label} payload must be an object")
                continue
            requested = payload.get("requested_model")
            if requested is None:
                requested = payload.get("model")
            provider = payload.get("provider_model")
            if not self._gpt56_sol_model(requested):
                self.error(f"{label} requested model is not GPT-5.6 Sol")
            if not self._gpt56_sol_model(provider):
                self.error(f"{label} provider_model is not an explicit GPT-5.6 Sol identifier")
            response_id = payload.get("response_id")
            request_id = payload.get("request_id")
            if not isinstance(response_id, str) or not response_id:
                self.error(f"{label} has no response_id")
            elif response_id in response_ids:
                self.error(f"{label} reuses response_id {response_id!r}")
            else:
                response_ids.add(response_id)
            if not isinstance(request_id, str) or not request_id:
                self.error(f"{label} has no request_id")
            elif request_id in request_ids:
                self.error(f"{label} reuses request_id {request_id!r}")
            else:
                request_ids.add(request_id)
            if payload.get("status") != "completed":
                self.error(f"{label} status is not completed")
            counts = payload.get("token_counts")
            if not isinstance(counts, dict):
                self.error(f"{label} token_counts must be an object")
            else:
                for field in _USAGE_FIELDS:
                    value = counts.get(field)
                    if not _is_int(value) or value < 0:
                        self.error(f"{label} {field} must be a nonnegative integer")
                provider_total = counts.get("provider_total_tokens")
                if not _is_int(provider_total) or provider_total <= 0:
                    self.error(f"{label} provider_total_tokens must be greater than zero")
            fake_flags = ("fake", "is_fake", "replay", "is_replay")
            if any(payload.get(field) is True for field in fake_flags):
                self.error(f"{label} is marked fake or replayed")
            for field in ("mode", "source", "provider"):
                marker = payload.get(field)
                if isinstance(marker, str) and marker.strip().lower() in {
                    "fake",
                    "mock",
                    "replay",
                    "stub",
                    "fixture",
                }:
                    self.error(f"{label} is marked as {marker!r}")
            for model_value in (requested, provider):
                if isinstance(model_value, str) and any(
                    marker in model_value.lower()
                    for marker in ("fake", "mock", "replay", "stub", "fixture")
                ):
                    self.error(f"{label} uses a fake or replay model identifier")


def verify_run(
    path: Path | str,
    require_complete: bool = False,
    require_live_gpt56: bool = False,
) -> VerificationResult:
    """Verify one finalized proof bundle without imports, network, or evidence access.

    Integrity failures are returned in ``VerificationResult.errors`` rather
    than raised.  This keeps the API useful for a future CLI while retaining a
    stable, serializable result for tests and static viewers.
    """

    run_directory = Path(path)
    verifier = _Verifier(
        run_directory,
        require_complete=require_complete,
        require_live_gpt56=require_live_gpt56,
    )
    try:
        verifier.run()
    except Exception as exc:  # noqa: BLE001 - malformed bundles must become a result
        verifier.error(f"verification stopped safely: {type(exc).__name__}: {exc}")
    return verifier.finish()


__all__ = ["RECORDED_CUSTODY_NOTICE", "VerificationResult", "verify_run"]
