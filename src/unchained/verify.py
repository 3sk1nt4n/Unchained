"""Standard-library, offline verification for Sentinel Unchained proof bundles.

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
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

GENESIS_HASH = "0" * 64
SCHEMA_VERSION = 1
LAYOUT_VERSION = 1
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_QUOTE_BYTES = 1024
MAX_EXCERPT_BYTES = 2048
TOOL_OUTPUT_DIRECTORY = "tool-outputs"
RECORDED_CUSTODY_NOTICE = (
    "Verification is limited to recorded custody receipts; the original evidence was not rehashed."
)

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
    status: str
    artifact_path: str
    excerpt: str
    fact: _FileFact


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


def _is_lower_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


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
        if self.require_complete and self.terminal_status != "COMPLETE":
            self.error("strict completion requires terminal status COMPLETE")
        if self.require_live_gpt56:
            if self.terminal_status != "COMPLETE":
                self.error("strict live GPT-5.6 verification requires a COMPLETE run")
            self._verify_live_gpt56(entries)
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
        return _FileFact(target, digest.hexdigest(), byte_count, bytes(prefix), utf8_valid)

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
        started: dict[str, tuple[int, str, Any]] = {}
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
                    started[call_id] = (index, name if isinstance(name, str) else "", arguments)
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
            start_index, start_name, start_arguments = start
            completion_index, payload = completion
            if start_index >= completion_index:
                self.error(f"tool completion does not follow its start: {call_id}")
            if payload.get("tool_name") != start_name:
                self.error(f"tool name changed between start and completion: {call_id}")
            if payload.get("arguments") != start_arguments:
                self.error(f"tool arguments changed between start and completion: {call_id}")

        receipts: dict[str, _ToolReceipt] = {}
        referenced_paths: set[str] = set()
        for call_id, (_index, payload) in completed.items():
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
            excerpt = self._receipt_excerpt(payload, call_id)
            expected_excerpt = self._largest_utf8_prefix(fact.prefix) if fact.valid_utf8 else None
            if expected_excerpt is None:
                self.error(f"tool output has no valid UTF-8 prefix: {call_id}")
                continue
            if excerpt != expected_excerpt:
                self.error(f"tool receipt excerpt is not the exact <=2048-byte prefix: {call_id}")
            if excerpt is None:
                continue
            receipts[call_id] = _ToolReceipt(
                call_id=call_id,
                status=status_value,
                artifact_path=artifact_path,
                excerpt=excerpt,
                fact=fact,
            )
        self._verify_tool_output_inventory(referenced_paths)
        return receipts

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
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            fd = os.open(fact.path, flags)
            try:
                previous = b""
                overlap = max(0, len(needle) - 1)
                while True:
                    chunk = os.read(fd, 1024 * 1024)
                    if not chunk:
                        return needle in previous
                    combined = previous + chunk
                    if needle in combined:
                        return True
                    previous = combined[-overlap:] if overlap else b""
            finally:
                os.close(fd)
        except OSError as exc:
            self.error(f"tool output could not be searched ({fact.path.name}): {exc}")
            return False

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
            if "quoted_spans" in verdict:
                self._verify_quotes(finding_id, verdict.get("quoted_spans"), cited, receipts)

    def _verify_quotes(
        self,
        finding_id: str,
        raw_quotes: Any,
        cited: list[str],
        receipts: dict[str, _ToolReceipt],
    ) -> None:
        if not isinstance(raw_quotes, list):
            self.error(f"judge verdict {finding_id} quoted_spans must be an array")
            return
        quoted_calls: set[str] = set()
        seen: set[tuple[str, str]] = set()
        for index, raw in enumerate(raw_quotes):
            if not isinstance(raw, dict):
                self.error(f"judge quote {finding_id}/{index} must be an object")
                continue
            call_id = raw.get("tool_call_id")
            text = raw.get("text")
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
            pair = (call_id, text)
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
            if text not in receipt.excerpt:
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

    @staticmethod
    def _gpt56_model(value: Any) -> bool:
        return isinstance(value, str) and (value == "gpt-5.6" or value.startswith("gpt-5.6-"))

    def _verify_live_gpt56(self, entries: list[dict[str, Any]]) -> None:
        responses = [entry for entry in entries if entry.get("event_type") == "model.response"]
        if not responses:
            self.error("strict live GPT-5.6 verification found no model.response events")
            return
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
            if not self._gpt56_model(requested):
                self.error(f"{label} requested model is not GPT-5.6")
            if not self._gpt56_model(provider):
                self.error(f"{label} provider_model is not an explicit GPT-5.6 identifier")
            if not isinstance(payload.get("response_id"), str) or not payload.get("response_id"):
                self.error(f"{label} has no response_id")
            if not isinstance(payload.get("request_id"), str) or not payload.get("request_id"):
                self.error(f"{label} has no request_id")
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
