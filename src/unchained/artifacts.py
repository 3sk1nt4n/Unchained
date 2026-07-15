"""Atomic, allowlisted construction of one inspectable run proof bundle.

This module deliberately knows nothing about OpenAI, evidence mounting, or
forensic parsers.  It writes only artifacts explicitly supplied by the
runner; it never walks the working tree looking for files to publish.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import site
import stat
import subprocess
import sys
import tomllib
import uuid
from collections import Counter
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .audit import GENESIS_HASH, canonical_json
from .models import EvidenceProfile, JsonValue
from .prompts import HOSTILE_DATA_RULE, INVESTIGATOR_PROMPT

MANIFEST_EXCLUSIONS = ("manifest.json", "manifest.sha256", "verifier-output.txt")
_PACKAGE_ALLOWLIST = (
    "openai",
    "python-registry",
    "tiktoken",
    "volatility3",
    "sift-sentinel",
    "sentinel-unchained",
)


class ArtifactError(RuntimeError):
    """Raised when a proof artifact cannot be written or verified safely."""


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """One exact file that can be placed in the core manifest."""

    role: str
    path: str
    sha256: str
    bytes: int
    media_type: str
    encoding: str | None
    required: bool = True

    def public_dict(self) -> dict[str, JsonValue]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def safe_relative_path(value: str) -> str:
    """Return a normalized POSIX bundle path or reject unsafe syntax."""

    if not value or "\\" in value or ":" in value or "\x00" in value:
        raise ArtifactError(f"unsafe artifact path: {value!r}")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ArtifactError(f"unsafe artifact path: {value!r}")
    normalized = candidate.as_posix()
    if normalized != value:
        raise ArtifactError(f"artifact path is not normalized POSIX: {value!r}")
    return normalized


def hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def hash_file(path: Path) -> tuple[str, int]:
    """Hash one regular non-symlink file without trusting its filename."""

    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ArtifactError(f"artifact is not a regular non-symlink file: {path.name}")
    digest = hashlib.sha256()
    size = 0
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            raise ArtifactError(f"artifact changed type during hashing: {path.name}")
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest(), size


def _write_all(fd: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        written = os.write(fd, content[offset:])
        if written <= 0:
            raise OSError(f"short artifact write: {offset}/{len(content)} bytes")
        offset += written


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


class ArtifactStore:
    """Atomically write explicitly named files beneath one run directory."""

    def __init__(self, run_directory: Path, *, fsync: bool = True) -> None:
        self.run_directory = run_directory.resolve()
        self._fsync = fsync
        info = self.run_directory.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ArtifactError("run directory is not a real directory")

    def _target(self, relative_path: str) -> Path:
        normalized = safe_relative_path(relative_path)
        target = self.run_directory.joinpath(*PurePosixPath(normalized).parts)
        resolved_parent = target.parent.resolve()
        if resolved_parent != self.run_directory and not resolved_parent.is_relative_to(
            self.run_directory
        ):
            raise ArtifactError(f"artifact escapes run directory: {relative_path!r}")
        return target

    def write_bytes(
        self,
        relative_path: str,
        content: bytes,
        *,
        role: str,
        media_type: str,
        encoding: str | None,
        required: bool = True,
    ) -> ArtifactRef:
        """Atomically replace one explicitly named artifact with exact bytes."""

        target = self._target(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        parent_info = target.parent.lstat()
        if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
            raise ArtifactError(f"artifact parent is not a real directory: {relative_path!r}")
        if target.exists() or target.is_symlink():
            info = target.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise ArtifactError(f"artifact target is not a regular file: {relative_path!r}")

        temporary = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        fd = os.open(temporary, flags, 0o600)
        try:
            _write_all(fd, content)
            if self._fsync:
                os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.replace(temporary, target)
            with suppress(NotImplementedError, OSError):
                target.chmod(0o600, follow_symlinks=False)
            if self._fsync:
                _fsync_directory(target.parent)
        finally:
            temporary.unlink(missing_ok=True)

        digest, byte_count = hash_file(target)
        expected = hash_bytes(content)
        if digest != expected or byte_count != len(content):
            raise ArtifactError(f"artifact failed post-write verification: {relative_path!r}")
        return ArtifactRef(
            role=role,
            path=safe_relative_path(relative_path),
            sha256=digest,
            bytes=byte_count,
            media_type=media_type,
            encoding=encoding,
            required=required,
        )

    def write_text(
        self,
        relative_path: str,
        value: str,
        *,
        role: str,
        media_type: str,
        required: bool = True,
    ) -> ArtifactRef:
        return self.write_bytes(
            relative_path,
            value.encode("utf-8"),
            role=role,
            media_type=media_type,
            encoding="utf-8",
            required=required,
        )

    def write_json(
        self,
        relative_path: str,
        value: Any,
        *,
        role: str,
        required: bool = True,
    ) -> ArtifactRef:
        try:
            rendered = (
                json.dumps(
                    value,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                    allow_nan=False,
                )
                + "\n"
            )
        except (TypeError, ValueError) as exc:
            raise ArtifactError(f"artifact is not strict JSON: {relative_path!r}") from exc
        return self.write_text(
            relative_path,
            rendered,
            role=role,
            media_type="application/json",
            required=required,
        )


def artifact_ref_from_existing(
    run_directory: Path,
    relative_path: str,
    *,
    role: str,
    media_type: str,
    encoding: str | None = "utf-8",
    required: bool = True,
) -> ArtifactRef:
    normalized = safe_relative_path(relative_path)
    target = run_directory.joinpath(*PurePosixPath(normalized).parts)
    digest, byte_count = hash_file(target)
    return ArtifactRef(role, normalized, digest, byte_count, media_type, encoding, required)


def _package_versions() -> dict[str, JsonValue]:
    versions: dict[str, JsonValue] = {}
    for name in _PACKAGE_ALLOWLIST:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _installed_versions_match_lock(lock_path: Path) -> bool | None:
    """Compare every versioned pylock package with installed metadata."""

    try:
        parsed = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeError):
        return None
    packages = parsed.get("packages")
    if not isinstance(packages, list):
        return None
    compared = 0
    for package in packages:
        if not isinstance(package, dict):
            return False
        name = package.get("name")
        version = package.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            continue
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return False
        if installed != version:
            return False
        compared += 1
    return compared > 0


def _runtime_binary_available(name: str) -> bool:
    """Find console scripts beside this interpreter as well as on PATH."""

    runtime_scripts = str(Path(sys.executable).resolve().parent)
    inherited_path = os.environ.get("PATH", "")
    search_path = os.pathsep.join(value for value in (runtime_scripts, inherited_path) if value)
    return shutil.which(name, path=search_path) is not None


def _git_state(project_directory: Path) -> tuple[str | None, bool | None]:
    """Capture only commit/dirty state; never serialize the repository path."""

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_directory,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_directory,
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
        )
    except (OSError, subprocess.SubprocessError):
        return None, None
    return commit or None, dirty


def capture_environment(
    *,
    run_id: str,
    project_directory: Path,
    requested_model: str | None,
    caps_profile: str,
    caps: dict[str, JsonValue],
    tool_schemas: tuple[dict[str, JsonValue], ...] = (),
) -> dict[str, JsonValue]:
    """Build a privacy-preserving allowlisted execution environment record."""

    commit, dirty = _git_state(project_directory)
    lock_relative_path = "requirements/pylock.windows-amd64-cp311.toml"
    lock_path = project_directory / "requirements" / "pylock.windows-amd64-cp311.toml"
    lock_sha256: str | None = None
    lock_matches_environment: bool | None = None
    if lock_path.is_file() and not lock_path.is_symlink():
        lock_sha256, _lock_bytes = hash_file(lock_path)
        lock_matches_environment = _installed_versions_match_lock(lock_path)
    catalog_json = canonical_json(list(tool_schemas))
    prompt_bundle = canonical_json(
        {
            "investigator": INVESTIGATOR_PROMPT,
            "hostile_data_rule": HOSTILE_DATA_RULE,
        }
    )
    return {
        "schema_version": 1,
        "run_id": run_id,
        "captured_at_utc": utc_now(),
        "project": {
            "name": "sentinel-unchained",
            "version": _package_versions().get("sentinel-unchained"),
            "git_commit": commit,
            "git_dirty": dirty,
        },
        "runtime": {
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "target_python": "3.11",
            "target_python_satisfied": sys.version_info[:2] == (3, 11),
            "user_site_enabled": bool(site.ENABLE_USER_SITE),
        },
        "dependencies": _package_versions(),
        "dependency_lock": {
            "path": lock_relative_path if lock_sha256 is not None else None,
            "sha256": lock_sha256,
            "target": "windows-amd64-cp311",
            "installed_versions_match": lock_matches_environment,
        },
        "native_tools": {
            name: {"available": _runtime_binary_available(name)}
            for name in ("vol", "fsstat", "mmls", "img_stat", "ewfmount", "ntfs-3g")
        },
        "model_configuration": {
            "requested_model": requested_model,
            "store": False,
        },
        "tool_catalog": {
            "count": len(tool_schemas),
            "sha256": hash_bytes(catalog_json.encode("utf-8")),
        },
        "prompt_bundle": {
            "sha256": hash_bytes(prompt_bundle.encode("utf-8")),
        },
        "caps": {"profile": caps_profile, **caps},
        "privacy": {
            "environment_allowlist_only": True,
            "secrets_recorded": False,
            "absolute_evidence_path_recorded": False,
            "username_recorded": False,
            "hostname_recorded": False,
        },
    }


def _payload(entry: dict[str, JsonValue]) -> dict[str, JsonValue]:
    value = entry.get("payload")
    return value if isinstance(value, dict) else {}


def build_summary(
    *,
    run_id: str,
    entries: list[dict[str, JsonValue]],
    status: str,
    exit_code: int,
    profile: EvidenceProfile | None,
    cap: str | None,
    reason: str | None,
    mount_released: bool,
) -> dict[str, JsonValue]:
    """Derive public counters from the audit rather than parallel mutable state."""

    model_entries = [entry for entry in entries if entry.get("event_type") == "model.response"]
    tool_entries = [entry for entry in entries if entry.get("event_type") == "tool.completed"]
    tool_started = [entry for entry in entries if entry.get("event_type") == "tool.started"]
    status_counts = Counter(str(_payload(entry).get("status")) for entry in tool_entries)
    requested_models = sorted(
        {
            str(value)
            for entry in model_entries
            if (value := _payload(entry).get("requested_model") or _payload(entry).get("model"))
        }
    )
    provider_models = sorted(
        {str(value) for entry in model_entries if (value := _payload(entry).get("provider_model"))}
    )
    usage_fields = (
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "provider_total_tokens",
    )
    usage = {field: 0 for field in usage_fields}
    for entry in model_entries:
        counts = _payload(entry).get("token_counts")
        if isinstance(counts, dict):
            for field in usage_fields:
                value = counts.get(field)
                if isinstance(value, int) and not isinstance(value, bool):
                    usage[field] += value
    estimated_cost = sum(
        float(value)
        for entry in model_entries
        if isinstance((value := _payload(entry).get("call_cost_usd_estimate")), (int, float))
        and not isinstance(value, bool)
    )
    findings: list[dict[str, JsonValue]] = []
    verdicts: list[dict[str, JsonValue]] = []
    turns = 0
    for entry in entries:
        if entry.get("event_type") == "investigator.finished":
            payload = _payload(entry)
            raw_findings = payload.get("findings")
            findings = raw_findings if isinstance(raw_findings, list) else []
            raw_turns = payload.get("turns")
            turns = raw_turns if isinstance(raw_turns, int) else 0
        if entry.get("event_type") == "judge.completed":
            raw_verdicts = _payload(entry).get("verdicts")
            verdicts = raw_verdicts if isinstance(raw_verdicts, list) else []
    initial = next(
        (entry for entry in entries if entry.get("event_type") == "custody.initial.completed"),
        None,
    )
    final = next(
        (
            entry
            for entry in reversed(entries)
            if entry.get("event_type") == "custody.final.completed"
        ),
        None,
    )
    return {
        "schema_version": 1,
        "run_id": run_id,
        "terminal": {
            "status": status,
            "exit_code": exit_code,
            "cap": cap,
            "reason": reason,
        },
        "time": {
            "started_at_utc": entries[0].get("timestamp_utc") if entries else None,
            "ended_at_utc": entries[-1].get("timestamp_utc") if entries else None,
            "wall_ms": entries[-1].get("elapsed_ms") if entries else None,
        },
        "model": {
            "requested_models": requested_models,
            "provider_models": provider_models,
            "responses": len(model_entries),
            "response_ids_present": sum(
                bool(_payload(entry).get("response_id")) for entry in model_entries
            ),
            "request_ids_present": sum(
                bool(_payload(entry).get("request_id")) for entry in model_entries
            ),
        },
        "usage": {
            **usage,
            "estimated_cost_usd": round(estimated_cost, 10),
            "provider_billed_cost_usd": None,
        },
        "tools": {
            "started": len(tool_started),
            "completed": len(tool_entries),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "investigation": {
            "turns": turns,
            "finding_count": len(findings),
            "verdict_count": len(verdicts),
        },
        "profile": (
            None
            if profile is None
            else {
                "os": profile.os,
                "shape": profile.shape,
                "capability_label": profile.capability_label,
                "evidence_items": len(profile.items),
            }
        ),
        "custody": {
            "baseline_established": initial is not None,
            "final_check_performed": final is not None,
            "match": _payload(final).get("match") if final is not None else None,
            "mount_released": mount_released,
        },
    }


def build_manifest(
    *,
    run_id: str,
    status: str,
    exit_code: int,
    audit_ref: ArtifactRef,
    audit_entries: list[dict[str, JsonValue]],
    artifacts: list[ArtifactRef],
) -> dict[str, JsonValue]:
    """Build a non-self-referential core manifest from an explicit allowlist."""

    if not audit_entries:
        raise ArtifactError("cannot manifest an empty audit")
    paths = [artifact.path for artifact in artifacts]
    if len(paths) != len(set(paths)):
        raise ArtifactError("manifest artifact paths are not unique")
    if any(path in MANIFEST_EXCLUSIONS for path in paths):
        raise ArtifactError("self-referential or detached file cannot be manifested")
    terminal = audit_entries[-1]
    if terminal.get("event_type") != "run.completed":
        raise ArtifactError("run.completed must be the final audit event")
    custody_initial = next(
        (
            _payload(entry)
            for entry in audit_entries
            if entry.get("event_type") == "custody.initial.completed"
        ),
        None,
    )
    custody_final = next(
        (
            _payload(entry)
            for entry in reversed(audit_entries)
            if entry.get("event_type") == "custody.final.completed"
        ),
        None,
    )
    all_artifacts = sorted([audit_ref, *artifacts], key=lambda item: item.path)
    return {
        "schema_version": 1,
        "layout_version": 1,
        "run_id": run_id,
        "created_at_utc": utc_now(),
        "terminal": {"status": status, "exit_code": exit_code},
        "audit": {
            "path": audit_ref.path,
            "sha256": audit_ref.sha256,
            "bytes": audit_ref.bytes,
            "schema_version": 1,
            "entry_count": len(audit_entries),
            "genesis_hash": GENESIS_HASH,
            "final_entry_hash": audit_entries[-1].get("entry_hash"),
            "terminal_sequence": audit_entries[-1].get("sequence"),
        },
        "custody": {
            "baseline_established": custody_initial is not None,
            "final_check_performed": custody_final is not None,
            "match": custody_final.get("match") if custody_final is not None else None,
            "mount_released": (
                custody_final.get("mount_released") if custody_final is not None else None
            ),
            "original_evidence_included": False,
        },
        "artifacts": [artifact.public_dict() for artifact in all_artifacts],
        "excluded_from_self_manifest": list(MANIFEST_EXCLUSIONS),
    }


def write_manifest_pair(
    store: ArtifactStore,
    manifest: dict[str, JsonValue],
) -> tuple[ArtifactRef, ArtifactRef]:
    """Atomically write a manifest and its intentionally detached checksum."""

    manifest_ref = store.write_json("manifest.json", manifest, role="manifest")
    checksum = f"{manifest_ref.sha256}  manifest.json\n"
    checksum_ref = store.write_text(
        "manifest.sha256",
        checksum,
        role="manifest-checksum",
        media_type="text/plain",
    )
    return manifest_ref, checksum_ref
