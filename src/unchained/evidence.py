"""Deterministic evidence discovery, routing, mounting, and custody checks.

This module is deliberately model-free.  It opens original evidence only for
reading, classifies it from bytes and forensic probes (never a filename
extension), and owns the pre/post full-file SHA-256 custody boundary.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import queue
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout, suppress
from dataclasses import dataclass, replace
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Literal, TextIO

from .caps import CapExceeded, RunBudget
from .models import (
    EvidenceItem,
    EvidenceProfile,
    OsFamily,
    derive_evidence_shape,
    derive_filesystems,
    reconcile_evidence_os,
)

_HASH_CHUNK_BYTES = 16 * 1024 * 1024
_SAMPLE_CHUNK_BYTES = 2 * 1024 * 1024
_MIN_PROBABLE_MEMORY_BYTES = 16 * 1024 * 1024
_COMMAND_TIMEOUT_SECONDS = 120
_MOUNT_WORKER_ARGUMENT = "--internal-reference-mount-worker"
_REFERENCE_MOUNT_METHODS = frozenset({"raw@0", "ntfs_offsets", "dmpad"})
_MOUNT_WORKER_CLEANUP_SECONDS = 15.0
_MOUNT_WORKER_TERMINATE_SECONDS = 3.0
_MOUNT_WORKER_MAX_REPLY_BYTES = 64 * 1024


class EvidenceError(RuntimeError):
    """Base class for deterministic evidence-boundary failures."""


class EvidenceDiscoveryError(EvidenceError):
    """Raised when an evidence input cannot be enumerated safely."""


class CustodyError(EvidenceError):
    """Raised when the evidence set or an evidence file changes."""


class MountContainmentError(EvidenceError):
    """Raised when a mount attempt's owned resources cannot be proven released."""


@dataclass(frozen=True, slots=True)
class _FileSnapshot:
    """A run-private identity and digest snapshot for one original file."""

    path: Path
    relative_path: str
    size: int
    mtime_ns: int
    device: int
    inode: int
    sha256: str


@dataclass(frozen=True, slots=True)
class _Classification:
    """Bounded byte-probe result before readiness and mount checks."""

    kind: Literal["memory", "disk", "log", "unknown"]
    filesystem: str | None
    os_hint: OsFamily
    health: str
    banner: str | None = None
    partition_offsets: tuple[int, ...] = ()
    filesystem_offset: int | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _CommandResult:
    """Normalized result of a fixed-argument local forensic probe."""

    returncode: int
    output: str


def _identity(file_stat: os.stat_result) -> tuple[int, int]:
    """Return the strongest portable file identity exposed by ``stat``."""

    return int(file_stat.st_dev), int(file_stat.st_ino)


def _open_read_only(path: Path) -> BinaryIO:
    """Open a regular file read-only and reject a final-component symlink."""

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise EvidenceDiscoveryError(f"Evidence is not a regular file: {path}")
        return os.fdopen(descriptor, "rb", closefd=True)
    except Exception:
        os.close(descriptor)
        raise


def _sha256_snapshot(
    path: Path,
    relative_path: str,
    budget_check: Callable[[], None] | None = None,
) -> _FileSnapshot:
    """Hash every byte and reject a file that changes during the read."""

    digest = hashlib.sha256()
    if budget_check is not None:
        budget_check()
    try:
        with _open_read_only(path) as handle:
            before = os.fstat(handle.fileno())
            if hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_SEQUENTIAL"):
                with suppress(OSError):
                    os.posix_fadvise(handle.fileno(), 0, 0, os.POSIX_FADV_SEQUENTIAL)
            for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
                digest.update(chunk)
                if budget_check is not None:
                    budget_check()
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise EvidenceDiscoveryError(f"Cannot hash evidence file {path}: {exc}") from exc

    if (
        _identity(before) != _identity(after)
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise CustodyError(f"Evidence changed while it was being hashed: {path}")
    return _FileSnapshot(
        path=path,
        relative_path=relative_path,
        size=int(after.st_size),
        mtime_ns=int(after.st_mtime_ns),
        device=int(after.st_dev),
        inode=int(after.st_ino),
        sha256=digest.hexdigest(),
    )


def sha256_file(path: str | Path) -> str:
    """Return a full streaming SHA-256 digest for one regular file."""

    candidate = Path(path).expanduser().resolve(strict=True)
    return _sha256_snapshot(candidate, candidate.name).sha256


def _enumerate_files(
    root: Path,
    budget_check: Callable[[], None] | None = None,
) -> tuple[tuple[Path, str], ...]:
    """Enumerate the exact regular-file set without following symlinks."""

    if budget_check is not None:
        budget_check()
    if root.is_symlink():
        raise EvidenceDiscoveryError(f"Evidence input may not be a symlink: {root}")
    if root.is_file():
        if budget_check is not None:
            budget_check()
        return ((root, root.name),)
    if not root.is_dir():
        raise EvidenceDiscoveryError(f"Evidence input is not a file or directory: {root}")

    def reject_walk_error(error: OSError) -> None:
        raise EvidenceDiscoveryError(
            f"Cannot enumerate evidence directory {error.filename or root}: {error}"
        ) from error

    discovered: list[tuple[Path, str]] = []
    for current, directory_names, file_names in os.walk(
        root,
        followlinks=False,
        onerror=reject_walk_error,
    ):
        if budget_check is not None:
            budget_check()
        current_path = Path(current)
        retained_directories: list[str] = []
        for name in sorted(directory_names):
            if budget_check is not None:
                budget_check()
            candidate = current_path / name
            try:
                directory_stat = candidate.lstat()
            except OSError as exc:
                raise EvidenceDiscoveryError(
                    f"Cannot stat evidence directory {candidate}: {exc}"
                ) from exc
            if stat.S_ISLNK(directory_stat.st_mode):
                raise EvidenceDiscoveryError(
                    f"Symlinks are not accepted inside the evidence set: {candidate}"
                )
            if not stat.S_ISDIR(directory_stat.st_mode):
                raise EvidenceDiscoveryError(
                    f"Non-directory traversal entry is not accepted: {candidate}"
                )
            retained_directories.append(name)
        directory_names[:] = retained_directories
        for name in sorted(file_names):
            if budget_check is not None:
                budget_check()
            candidate = current_path / name
            try:
                file_stat = candidate.lstat()
            except OSError as exc:
                raise EvidenceDiscoveryError(
                    f"Cannot stat evidence file {candidate}: {exc}"
                ) from exc
            if stat.S_ISLNK(file_stat.st_mode):
                raise EvidenceDiscoveryError(
                    f"Symlinks are not accepted inside the evidence set: {candidate}"
                )
            if not stat.S_ISREG(file_stat.st_mode):
                raise EvidenceDiscoveryError(
                    f"Non-regular entries are not accepted as evidence: {candidate}"
                )
            discovered.append(
                (candidate.resolve(strict=True), candidate.relative_to(root).as_posix())
            )
            if budget_check is not None:
                budget_check()
    if not discovered:
        raise EvidenceDiscoveryError(f"No regular evidence files found under {root}")
    discovered.sort(key=lambda item: item[1].casefold())
    return tuple(discovered)


def _read_at(path: Path, offset: int, length: int) -> bytes:
    """Read a bounded byte range without changing the original file."""

    if offset < 0 or length <= 0:
        return b""
    try:
        with _open_read_only(path) as handle:
            handle.seek(offset)
            return handle.read(length)
    except (OSError, EvidenceDiscoveryError):
        return b""


def _sample_content(path: Path, size: int) -> bytes:
    """Read deterministic sparse samples suitable for banner detection."""

    if size <= _SAMPLE_CHUNK_BYTES:
        return _read_at(path, 0, size)
    maximum_start = max(0, size - _SAMPLE_CHUNK_BYTES)
    starts = {
        0,
        min(maximum_start, size // 4),
        min(maximum_start, size // 2),
        min(maximum_start, (size * 3) // 4),
        maximum_start,
    }
    return b"\n".join(_read_at(path, start, _SAMPLE_CHUNK_BYTES) for start in sorted(starts))


def _partition_offsets(path: Path, head: bytes, size: int) -> tuple[int, ...]:
    """Extract plausible partition byte offsets from MBR or GPT structures."""

    starts: set[int] = set()
    if len(head) >= 512 and head[510:512] == b"\x55\xaa":
        for index in range(4):
            entry = head[446 + (index * 16) : 462 + (index * 16)]
            if len(entry) != 16 or entry[4] == 0:
                continue
            sector = struct.unpack_from("<I", entry, 8)[0]
            if 0 < sector < size // 512:
                starts.add(sector * 512)

    gpt_header = _read_at(path, 512, 512)
    if gpt_header.startswith(b"EFI PART") and len(gpt_header) >= 92:
        entries_lba = struct.unpack_from("<Q", gpt_header, 72)[0]
        entry_count = min(struct.unpack_from("<I", gpt_header, 80)[0], 128)
        entry_size = struct.unpack_from("<I", gpt_header, 84)[0]
        if 128 <= entry_size <= 4096 and entries_lba < size // 512:
            table_length = min(entry_count * entry_size, 512 * 1024)
            table = _read_at(path, entries_lba * 512, table_length)
            for index in range(entry_count):
                entry = table[index * entry_size : (index + 1) * entry_size]
                if len(entry) < 40 or entry[:16] == bytes(16):
                    continue
                sector = struct.unpack_from("<Q", entry, 32)[0]
                if 0 < sector < size // 512:
                    starts.add(sector * 512)
    return tuple(sorted(starts))


def _filesystem_at(path: Path, offset: int) -> str | None:
    """Recognize common filesystems from their on-disk structures."""

    block = _read_at(path, offset, 4096)
    if len(block) >= 11 and block[3:11] == b"NTFS    ":
        return "ntfs"
    if block.startswith(b"XFSB"):
        return "xfs"
    if len(block) >= 36 and block[32:36] == b"NXSB":
        return "apfs"
    if len(block) >= 1082 and block[1080:1082] == b"\x53\xef":
        return "ext4"
    if len(block) >= 1026 and block[1024:1026] in {b"H+", b"HX"}:
        return "hfs+"
    return None


def _os_for_filesystem(filesystem: str | None) -> OsFamily:
    if filesystem == "ntfs":
        return "windows"
    if filesystem in {"ext4", "xfs"}:
        return "linux"
    if filesystem in {"apfs", "hfs+"}:
        return "macos"
    return "unknown"


def _run_fixed_command(
    arguments: list[str],
    timeout: float = _COMMAND_TIMEOUT_SECONDS,
    budget: RunBudget | None = None,
) -> _CommandResult:
    """Run a code-owned argv vector; evidence/model text never becomes a command."""

    if budget is not None:
        budget.check()
        timeout = min(timeout, budget.remaining_wall_seconds())
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            close_fds=True,
            env=_fixed_command_environment(),
            start_new_session=os.name != "nt",
            creationflags=creation_flags,
        )
    except OSError as exc:
        if budget is not None:
            budget.check()
        return _CommandResult(returncode=127, output=f"{type(exc).__name__}: {exc}")
    try:
        output, _ = process.communicate(timeout=max(0.001, timeout))
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        tail, _ = process.communicate()
        prior = exc.output if isinstance(exc.output, str) else ""
        output = prior + (tail or "")
        result = _CommandResult(
            returncode=124,
            output=f"TimeoutExpired after {timeout:.3f}s\n{output}",
        )
    else:
        result = _CommandResult(returncode=process.returncode, output=output)
    if budget is not None:
        budget.check()
    return result


def _fixed_command_environment() -> dict[str, str]:
    """Preserve runtime settings while withholding unrelated host credentials."""

    environment = os.environ.copy()
    exact_sensitive = {
        "ALL_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "SSH_AUTH_SOCK",
        "GPG_AGENT_INFO",
    }
    sensitive_prefixes = (
        "OPENAI_",
        "ANTHROPIC_",
        "AWS_",
        "AZURE_",
        "GOOGLE_",
        "GCP_",
        "GITHUB_",
        "GITLAB_",
        "DOCKER_",
        "KUBE",
    )
    sensitive_terms = ("API_KEY", "PASSWORD", "PRIVATE_KEY", "SECRET", "TOKEN", "CREDENTIAL")
    for key in tuple(environment):
        normalized = key.upper()
        if (
            normalized in exact_sensitive
            or normalized.startswith(sensitive_prefixes)
            or any(term in normalized for term in sensitive_terms)
        ):
            environment.pop(key, None)
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONSAFEPATH"] = "1"
    interpreter_directory = str(Path(sys.executable).resolve().parent)
    inherited_path = environment.get("PATH", "")
    path_parts = [
        part
        for part in inherited_path.split(os.pathsep)
        if part and os.path.normcase(part) != os.path.normcase(interpreter_directory)
    ]
    environment["PATH"] = os.pathsep.join((interpreter_directory, *path_parts))
    return environment


def _filesystem_from_text(output: str) -> str | None:
    """Normalize filesystem names emitted by trusted local forensic probes."""

    for line in output.splitlines():
        match = re.match(r"^\s*File System Type:\s*([^\s]+)", line, flags=re.IGNORECASE)
        if match is None:
            continue
        value = match.group(1).casefold()
        if value.startswith("ntfs"):
            return "ntfs"
        if value.startswith("apfs"):
            return "apfs"
        if value.startswith(("hfs+", "hfsx", "hfsplus")):
            return "hfs+"
        if value.startswith(("ext2", "ext3", "ext4")):
            return "ext4"
        if value.startswith("xfs"):
            return "xfs"
    return None


def _probe_filesystem_with_tsk(
    path: Path,
    budget: RunBudget | None = None,
) -> tuple[str | None, tuple[int, ...], int | None]:
    """Ask Sleuth Kit for opaque/EWF filesystem facts using fixed arguments."""

    fsstat = shutil.which("fsstat")
    if fsstat is None:
        return None, (), None
    direct = _run_fixed_command([fsstat, str(path)], timeout=60, budget=budget)
    filesystem = _filesystem_from_text(direct.output) if direct.returncode == 0 else None
    if filesystem is not None:
        return filesystem, (), 0

    mmls = shutil.which("mmls")
    if mmls is None:
        return None, (), None
    partitions = _run_fixed_command([mmls, str(path)], timeout=60, budget=budget)
    sector_offsets: list[int] = []
    for line in partitions.output.splitlines():
        match = re.match(r"\s*\d+:\s+\S+\s+(\d+)\s+\d+\s+\d+\s+", line)
        if match:
            sector = int(match.group(1))
            if sector > 0:
                sector_offsets.append(sector)
    for sector in sorted(set(sector_offsets)):
        result = _run_fixed_command(
            [fsstat, "-o", str(sector), str(path)],
            timeout=60,
            budget=budget,
        )
        filesystem = _filesystem_from_text(result.output) if result.returncode == 0 else None
        if filesystem is not None:
            offsets = tuple(value * 512 for value in sorted(set(sector_offsets)))
            return filesystem, offsets, sector * 512
    return None, tuple(value * 512 for value in sorted(set(sector_offsets))), None


def _volatility_base_command() -> list[str] | None:
    """Find a Volatility 3 launcher without importing the former pipeline."""

    interpreter_directory = Path(sys.executable).resolve().parent
    launcher_names = ("vol.exe", "vol", "vol.py") if os.name == "nt" else ("vol", "vol.py")
    for executable_name in launcher_names:
        adjacent = interpreter_directory / executable_name
        if adjacent.is_file():
            return [str(adjacent)]
    for executable_name in launcher_names:
        executable = shutil.which(executable_name)
        if executable:
            return [executable]
    return None


def _memory_os_from_bytes(sample: bytes) -> tuple[OsFamily, str | None]:
    """Return an OS hint and a bounded banner excerpt from sampled bytes."""

    markers: tuple[tuple[OsFamily, bytes], ...] = (
        ("linux", b"Linux version "),
        ("macos", b"Darwin Kernel Version"),
        ("windows", b"NtBuildLab"),
        ("windows", b"KUSER_SHARED_DATA"),
        ("windows", b"\\SystemRoot\\System32"),
        ("windows", b"ntoskrnl.exe"),
    )
    for os_family, marker in markers:
        index = sample.find(marker)
        if index >= 0:
            excerpt = sample[index : index + 512].split(b"\x00", 1)[0]
            return os_family, excerpt.decode("utf-8", errors="replace")
    return "unknown", None


def _probe_memory_with_volatility(
    path: Path,
    budget: RunBudget | None = None,
) -> tuple[OsFamily, str | None]:
    """Use OS-agnostic banners, then Windows info, solely as content probes."""

    base = _volatility_base_command()
    if base is None:
        return "unknown", None
    banners = _run_fixed_command(
        [*base, "-f", str(path), "banners.Banners"],
        timeout=90,
        budget=budget,
    )
    if banners.returncode == 0:
        os_hint, banner = _memory_os_from_bytes(banners.output.encode("utf-8", errors="replace"))
        if os_hint != "unknown":
            return os_hint, banner
    windows_info = _run_fixed_command(
        [*base, "-f", str(path), "windows.info.Info"],
        timeout=_COMMAND_TIMEOUT_SECONDS,
        budget=budget,
    )
    lowered = windows_info.output.casefold()
    if windows_info.returncode == 0 and (
        "ntmajorversion" in lowered or "kernel base" in lowered or "is64bit" in lowered
    ):
        return "windows", "Volatility windows.info resolved the NT kernel"
    return "unknown", None


def _looks_like_text_log(head: bytes) -> tuple[bool, OsFamily]:
    """Recognize high-signal log content without consulting the filename."""

    if head.startswith(b"ElfFile\x00"):
        return True, "windows"
    if head.startswith(b"regf"):
        return True, "windows"
    if head[:4] in {
        b"\xa1\xb2\xc3\xd4",
        b"\xd4\xc3\xb2\xa1",
        b"\xa1\xb2\x3c\x4d",
        b"\x4d\x3c\xb2\xa1",
        b"\x0a\x0d\x0d\x0a",
    }:
        return True, "unknown"
    text_sample = head[: 256 * 1024]
    if text_sample.count(0) / max(1, len(text_sample)) >= 0.01:
        return False, "unknown"
    decoded = text_sample.decode("utf-8", errors="ignore")
    if not decoded or "\n" not in decoded:
        return False, "unknown"
    if "Linux version " in decoded:
        return True, "linux"
    windows_signals = ("Microsoft-Windows-", "EventID", "Provider Name=", "LogonType")
    linux_signals = (" systemd[", " sshd[", " kernel:", " audit(", " CRON[")
    mac_signals = (" launchd[", "com.apple.", "kernel[0]:")
    if sum(signal in decoded for signal in windows_signals) >= 2:
        return True, "windows"
    if sum(signal in decoded for signal in linux_signals) >= 2:
        return True, "linux"
    if sum(signal in decoded for signal in mac_signals) >= 2:
        return True, "macos"
    dated_lines = len(re.findall(r"(?m)^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", decoded))
    return (dated_lines >= 3, "unknown") if dated_lines >= 3 else (False, "unknown")


def _classify(
    snapshot: _FileSnapshot,
    budget: RunBudget | None = None,
) -> _Classification:
    """Classify one file from structures, magic bytes, and bounded probes."""

    path = snapshot.path
    if budget is not None:
        budget.check()
    head = _read_at(path, 0, min(snapshot.size, 2 * 1024 * 1024))
    if not head and snapshot.size:
        return _Classification(
            kind="unknown",
            filesystem=None,
            os_hint="unknown",
            health="unreadable",
            warnings=("Content probe could not read this file.",),
        )

    offsets = _partition_offsets(path, head, snapshot.size)
    filesystem: str | None = None
    filesystem_offset = 0
    for offset in (0, *offsets):
        filesystem = _filesystem_at(path, offset)
        if filesystem is not None:
            filesystem_offset = offset
            break
    if filesystem is not None:
        warnings = (
            ()
            if filesystem_offset == 0
            else (f"Filesystem begins at deterministic byte offset {filesystem_offset}.",)
        )
        return _Classification(
            kind="disk",
            filesystem=filesystem,
            os_hint=_os_for_filesystem(filesystem),
            health="filesystem-recognized",
            partition_offsets=offsets,
            filesystem_offset=filesystem_offset,
            warnings=warnings,
        )

    is_ewf = head.startswith((b"EVF\x09\r\n\xff\x00", b"EVF2\r\n\x81\x00", b"LVF\x09\r\n\xff\x00"))
    has_partition_table = bool(offsets) or _read_at(path, 512, 8) == b"EFI PART"
    if is_ewf or has_partition_table:
        probed_filesystem, probed_offsets, probed_filesystem_offset = _probe_filesystem_with_tsk(
            path, budget
        )
        filesystem = probed_filesystem
        warnings: tuple[str, ...] = ()
        if filesystem is None:
            warnings = (
                "Disk container recognized, but its filesystem could not be resolved before mount.",
            )
        return _Classification(
            kind="disk",
            filesystem=filesystem,
            os_hint=_os_for_filesystem(filesystem),
            health="disk-container-recognized",
            partition_offsets=offsets or probed_offsets,
            filesystem_offset=probed_filesystem_offset,
            warnings=warnings,
        )

    if head.startswith((b"PAGEDUMP", b"PAGEDU64")):
        return _Classification(
            kind="memory",
            filesystem=None,
            os_hint="windows",
            health="memory-signature-recognized",
            banner="Windows crash-dump signature",
        )
    if head.startswith((b"EMiL", b"LiME")):
        return _Classification(
            kind="memory",
            filesystem=None,
            os_hint="linux",
            health="memory-signature-recognized",
            banner="Linux LiME signature",
        )

    is_log, log_os = _looks_like_text_log(head)
    if is_log:
        return _Classification(
            kind="log",
            filesystem=None,
            os_hint=log_os,
            health="standalone-log-recognized",
        )

    sample = _sample_content(path, snapshot.size)
    os_hint, banner = _memory_os_from_bytes(sample)
    if os_hint != "unknown":
        return _Classification(
            kind="memory",
            filesystem=None,
            os_hint=os_hint,
            health="memory-banner-recognized",
            banner=banner,
        )

    known_non_evidence = head.startswith(
        (
            b"PK\x03\x04",
            b"7z\xbc\xaf'\x1c",
            b"Rar!\x1a\x07",
            b"%PDF-",
            b"\x89PNG",
            b"SQLite format 3",
        )
    )
    nul_ratio = sample.count(0) / max(1, len(sample))
    if snapshot.size >= _MIN_PROBABLE_MEMORY_BYTES and not known_non_evidence and nul_ratio >= 0.01:
        probed_os, probed_banner = _probe_memory_with_volatility(path, budget)
        return _Classification(
            kind="memory",
            filesystem=None,
            os_hint=probed_os,
            health=(
                "probable-memory-content" if probed_os == "unknown" else "memory-profile-resolved"
            ),
            banner=probed_banner,
            warnings=(
                "Binary content resembles memory, but its operating system was not resolved.",
            )
            if probed_os == "unknown"
            else (),
        )

    return _Classification(
        kind="unknown",
        filesystem=None,
        os_hint="unknown",
        health="unrecognized-content",
        warnings=("File content did not match a supported evidence structure.",),
    )


def _symbol_search_roots() -> tuple[Path, ...]:
    """Return configured and conventional Volatility symbol roots."""

    roots: list[Path] = []
    for variable in (
        "UNCHAINED_VOLATILITY_SYMBOLS",
        "VOLATILITY_SYMBOL_DIRS",
        "VOLATILITY_SYMBOLS",
    ):
        value = os.environ.get(variable)
        if value:
            roots.extend(Path(part).expanduser() for part in value.split(os.pathsep) if part)
    roots.extend(
        (
            Path.home() / ".cache" / "volatility3" / "symbols",
            Path.home() / ".volatility3" / "symbols",
        )
    )
    specification = importlib.util.find_spec("volatility3")
    if specification and specification.submodule_search_locations:
        roots.extend(
            Path(location) / "symbols" for location in specification.submodule_search_locations
        )
    unique: dict[str, Path] = {}
    for root in roots:
        unique[str(root.resolve(strict=False))] = root
    return tuple(unique.values())


def _has_symbol_table(os_family: OsFamily, budget: RunBudget | None = None) -> bool:
    """Conservatively detect a Linux/macOS Volatility symbol table."""

    family_terms = ("linux",) if os_family == "linux" else ("mac", "darwin", "macos")
    for root in _symbol_search_roots():
        if budget is not None:
            budget.check()
        if root.is_file():
            lowered = root.name.casefold()
            if any(term in lowered for term in family_terms):
                return True
            continue
        if not root.is_dir():
            continue
        visited = 0
        for current, directory_names, file_names in os.walk(root):
            if budget is not None:
                budget.check()
            directory_names.sort()
            for file_name in sorted(file_names):
                visited += 1
                lowered = (Path(current) / file_name).as_posix().casefold()
                if any(term in lowered for term in family_terms) and file_name.casefold().endswith(
                    (".json", ".json.gz", ".json.xz", ".zip")
                ):
                    return True
                if visited >= 20_000:
                    break
            if visited >= 20_000:
                break
    return False


def _probe_symbol_readiness(
    path: Path,
    os_family: OsFamily,
    budget: RunBudget | None = None,
) -> tuple[str, bool, str]:
    """Return symbol posture, memory availability, and health text."""

    base = _volatility_base_command()
    if os_family == "windows":
        if base is None:
            return "runtime-missing", False, "unavailable-volatility-runtime-missing"
        result = _run_fixed_command(
            [*base, "-f", str(path), "windows.info.Info"],
            timeout=_COMMAND_TIMEOUT_SECONDS,
            budget=budget,
        )
        lowered = result.output.casefold()
        if result.returncode == 0 and (
            "ntmajorversion" in lowered or "kernel base" in lowered or "is64bit" in lowered
        ):
            return "ready", True, "ready"
        return "auto-download-pending", True, "degraded-windows-symbol-probe"

    if os_family not in {"linux", "macos"}:
        return "undetermined", False, "unavailable-os-undetermined"

    if base is None:
        if _has_symbol_table(os_family, budget):
            return "configured-unverified", False, "unavailable-volatility-runtime-missing"
        return "missing", False, "unavailable-symbol-table-and-runtime-missing"

    plugin = "linux.pslist.PsList" if os_family == "linux" else "mac.pslist.PsList"
    result = _run_fixed_command(
        [*base, "-f", str(path), plugin],
        timeout=180,
        budget=budget,
    )
    lowered = result.output.casefold()
    failure_signals = (
        "unsatisfied requirement",
        "symbol table",
        "unable to validate",
        "no suitable kernels",
        "automagic exception",
    )
    if result.returncode == 0 and not any(signal in lowered for signal in failure_signals):
        return "ready", True, "ready"
    if _has_symbol_table(os_family, budget):
        return (
            "configured-unverified",
            False,
            "unavailable-evidence-symbol-resolution-unverified",
        )
    return "missing", False, "unavailable-symbol-table-missing"


def _memory_readiness(
    path: Path,
    readiness_os: OsFamily,
    base_warnings: tuple[str, ...],
    budget: RunBudget | None,
) -> tuple[str, bool, str, tuple[str, ...]]:
    """Probe one memory item and derive its deterministic readiness warning."""

    symbols, available, health = _probe_symbol_readiness(path, readiness_os, budget)
    warnings = list(base_warnings)
    if not available and readiness_os in {"linux", "macos"}:
        if "runtime-missing" in health:
            reason = "the Volatility runtime is absent"
        elif "resolution-unverified" in health:
            reason = "the configured symbols did not resolve this evidence's process-list plugin"
        else:
            reason = "its symbol table is absent"
        warnings.append(
            f"{readiness_os} memory is UNAVAILABLE because {reason}; disk analysis may continue."
        )
    elif health == "degraded-windows-symbol-probe":
        warnings.append(
            "Windows memory remains routable for Volatility auto-download, but "
            "the evidence-specific info probe did not resolve during readiness."
        )
    return symbols, available, health, tuple(warnings)


def _privileged_prefix() -> list[str] | None:
    """Return a non-interactive privilege prefix when one is required."""

    if os.name == "nt":
        return None
    getuid = getattr(os, "geteuid", None)
    if getuid is not None and getuid() == 0:
        return []
    sudo = shutil.which("sudo")
    return [sudo, "-n"] if sudo else None


def _mount_is_read_only(path: Path) -> bool:
    """Verify Linux mount options without attempting a write to evidence."""

    mountinfo = Path("/proc/self/mountinfo")
    if not mountinfo.is_file():
        statvfs = getattr(os, "statvfs", None)
        read_only_flag = getattr(os, "ST_RDONLY", None)
        if statvfs is None or read_only_flag is None:
            return False
        try:
            return bool(statvfs(path).f_flag & read_only_flag)
        except OSError:
            return False
    try:
        lines = mountinfo.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    target = str(path.resolve(strict=False)).replace(" ", "\\040")
    for line in reversed(lines):
        fields = line.split()
        if len(fields) >= 6 and fields[4] == target:
            return "ro" in fields[5].split(",")
    return False


def _mount_is_active(path: Path) -> bool:
    """Return whether the path is still an active mount point."""

    mountinfo = Path("/proc/self/mountinfo")
    if mountinfo.is_file():
        try:
            lines = mountinfo.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return True
        target = str(path.resolve(strict=False)).replace(" ", "\\040")
        return any(len(fields := line.split()) >= 5 and fields[4] == target for line in lines)
    try:
        return path.is_mount()
    except OSError:
        return True


def _decode_mountinfo_path(value: str) -> Path:
    """Decode the octal escapes used in Linux ``mountinfo`` path fields."""

    decoded = re.sub(
        r"\\([0-7]{3})",
        lambda match: chr(int(match.group(1), 8)),
        value,
    )
    return Path(decoded)


def _active_mounts_under(roots: tuple[Path, ...]) -> tuple[Path, ...] | None:
    """List active Linux mounts below owned roots, or ``None`` if unknowable."""

    mountinfo = Path("/proc/self/mountinfo")
    if not mountinfo.is_file():
        return None
    try:
        lines = mountinfo.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    normalized = tuple(root.resolve(strict=False) for root in roots)
    active: set[Path] = set()
    for line in lines:
        fields = line.split()
        if len(fields) < 5:
            continue
        candidate = _decode_mountinfo_path(fields[4]).resolve(strict=False)
        for root in normalized:
            if candidate == root or root in candidate.parents:
                active.add(candidate)
                break
    return tuple(sorted(active, key=lambda path: len(path.parts), reverse=True))


def _release_owned_mountpoint(path: Path) -> bool:
    """Unmount one run-created mountpoint and positively verify its release."""

    if not _mount_is_active(path):
        return True
    prefix = _privileged_prefix()
    umount = shutil.which("umount")
    if prefix is None or umount is None:
        return False
    _run_fixed_command([*prefix, umount, str(path)], timeout=10)
    return not _mount_is_active(path)


def _loop_inventory(budget: RunBudget | None = None) -> dict[str, Path] | None:
    """Return loop backing paths, ``{}`` if absent, or ``None`` if unknowable."""

    losetup = shutil.which("losetup")
    if losetup is None:
        return {}
    result = _run_fixed_command(
        [losetup, "--json", "--output", "NAME,BACK-FILE"],
        timeout=10,
        budget=budget,
    )
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.output)
    except (json.JSONDecodeError, TypeError):
        return None
    devices = payload.get("loopdevices") if isinstance(payload, dict) else None
    if not isinstance(devices, list):
        return None
    inventory: dict[str, Path] = {}
    for item in devices:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        backing = item.get("back-file")
        if (
            isinstance(name, str)
            and re.fullmatch(r"/dev/loop\d+", name)
            and isinstance(backing, str)
            and backing
        ):
            inventory[name] = Path(backing).resolve(strict=False)
    return inventory


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Stop a fixed worker and its descendants, with a bounded grace period."""

    if process.poll() is not None:
        return
    if os.name != "nt":
        with suppress(OSError, ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
    else:
        with suppress(OSError):
            process.terminate()
    try:
        process.wait(timeout=_MOUNT_WORKER_TERMINATE_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name != "nt":
        with suppress(OSError, ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    else:
        with suppress(OSError):
            process.kill()
    with suppress(OSError, subprocess.TimeoutExpired):
        process.wait(timeout=_MOUNT_WORKER_TERMINATE_SECONDS)


def _mount_worker_environment(scratch: Path) -> dict[str, str]:
    """Build a minimal environment with no host credentials or import overrides."""

    environment = {
        "HOME": str(scratch),
        "LC_ALL": "C",
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONSAFEPATH": "1",
        "TEMP": str(scratch),
        "TMP": str(scratch),
        "TMPDIR": str(scratch),
        "XDG_CACHE_HOME": str(scratch),
    }
    if os.name == "nt":
        for key in ("COMSPEC", "PATHEXT", "SYSTEMROOT", "WINDIR"):
            value = os.environ.get(key)
            if value:
                environment[key] = value
    return environment


class _ReferenceMountWorker:
    """Own one allowlisted pinned-backend process and all of its resources."""

    def __init__(
        self,
        disk: Path,
        mountpoint: Path,
        budget: RunBudget | None = None,
    ) -> None:
        if budget is not None:
            budget.check()
        self.disk = disk.resolve(strict=True)
        self.mountpoint = mountpoint.resolve(strict=True)
        self.scratch = Path(tempfile.mkdtemp(prefix="unchained-mount-worker-"))
        try:
            if budget is not None:
                budget.check()
            loop_inventory = _loop_inventory(budget)
            if budget is not None:
                budget.check()
        except Exception:
            with suppress(OSError):
                shutil.rmtree(self.scratch)
            raise
        self._baseline_loops = frozenset(loop_inventory) if loop_inventory is not None else None
        self._dm_name = f"sift_onboard_{self.mountpoint.name}"
        self._dm_preexisting = (Path("/dev/mapper") / self._dm_name).exists()
        self._process: subprocess.Popen[str] | None = None
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._method: str | None = None
        self._mounted = False
        self._closed = False
        self._released = False

    def _start(self) -> None:
        creation_flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        )
        try:
            process = subprocess.Popen(
                [sys.executable, "-P", "-m", "unchained.evidence", _MOUNT_WORKER_ARGUMENT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                close_fds=True,
                cwd=self.scratch,
                env=_mount_worker_environment(self.scratch),
                shell=False,
                start_new_session=os.name != "nt",
                creationflags=creation_flags,
            )
        except OSError as exc:
            self._cleanup_owned_resources()
            raise EvidenceDiscoveryError(
                f"Could not start the pinned read-only mount worker: {exc}"
            ) from exc
        self._process = process
        assert process.stdout is not None

        def read_protocol() -> None:
            try:
                while line := process.stdout.readline():
                    self._lines.put(line)
            finally:
                self._lines.put(None)

        threading.Thread(
            target=read_protocol,
            name="unchained-mount-protocol",
            daemon=True,
        ).start()

    def _send(self, payload: dict[str, object]) -> None:
        process = self._process
        if process is None or process.stdin is None or process.poll() is not None:
            raise EvidenceDiscoveryError("Pinned mount worker exited before its request")
        try:
            process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise EvidenceDiscoveryError("Pinned mount worker protocol closed early") from exc

    def _reply(self, timeout: float) -> dict[str, object]:
        try:
            line = self._lines.get(timeout=max(0.001, timeout))
        except queue.Empty as exc:
            raise TimeoutError("Pinned mount worker exceeded its deadline") from exc
        if line is None:
            raise EvidenceDiscoveryError("Pinned mount worker exited without a reply")
        if len(line.encode("utf-8", errors="replace")) > _MOUNT_WORKER_MAX_REPLY_BYTES:
            raise EvidenceDiscoveryError("Pinned mount worker reply exceeded its fixed bound")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvidenceDiscoveryError("Pinned mount worker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise EvidenceDiscoveryError("Pinned mount worker returned a non-object reply")
        return payload

    def mount(self, method: str, budget: RunBudget | None) -> tuple[bool, str]:
        """Execute exactly one allowlisted method within the remaining wall time."""

        if method not in _REFERENCE_MOUNT_METHODS:
            raise EvidenceDiscoveryError(f"Pinned mount method is not allowlisted: {method}")
        if method == "dmpad" and (
            self._baseline_loops is None
            or shutil.which("losetup") is None
            or shutil.which("dmsetup") is None
        ):
            self._released = self._cleanup_owned_resources()
            self._closed = True
            raise EvidenceDiscoveryError(
                "dmpad was skipped because loop/device-mapper state cannot be contained"
            )
        if budget is not None:
            budget.check()
        self._method = method
        self._start()
        self._send(
            {
                "action": "mount",
                "disk": str(self.disk),
                "method": method,
                "mountpoint": str(self.mountpoint),
                "scratch": str(self.scratch.resolve(strict=True)),
            }
        )
        timeout = (
            min(_COMMAND_TIMEOUT_SECONDS, budget.remaining_wall_seconds())
            if budget is not None
            else _COMMAND_TIMEOUT_SECONDS
        )
        try:
            reply = self._reply(timeout)
        except (EvidenceDiscoveryError, TimeoutError):
            self._contain_and_verify()
            if budget is not None:
                budget.check()
            raise
        if budget is not None:
            try:
                budget.check()
            except Exception:
                self._contain_and_verify()
                raise
        if reply.get("ok") is not True or not isinstance(reply.get("mounted"), bool):
            self._contain_and_verify()
            detail = str(reply.get("error") or "malformed reply")
            raise EvidenceDiscoveryError(f"Pinned mount worker failed: {detail}")
        mounted = bool(reply["mounted"])
        message = str(reply.get("message") or "")
        self._mounted = mounted
        if not mounted:
            self._finish_failed_attempt()
        return mounted, message

    def _finish_failed_attempt(self) -> None:
        process = self._process
        if process is not None:
            try:
                process.wait(timeout=_MOUNT_WORKER_CLEANUP_SECONDS)
            except subprocess.TimeoutExpired:
                _terminate_process_group(process)
        self._released = self._cleanup_owned_resources()
        self._closed = True
        if not self._released:
            raise MountContainmentError(
                "Pinned mount attempt ended, but owned resources could not be released"
            )

    def _contain_and_verify(self) -> None:
        process = self._process
        if process is not None:
            _terminate_process_group(process)
        self._released = self._cleanup_owned_resources()
        self._closed = True
        if not self._released:
            raise MountContainmentError(
                "Timed-out pinned mount worker left run-owned resources active; "
                "the mount is rejected and its paths are preserved for recovery"
            )

    def _cleanup_owned_resources(self) -> bool:
        roots = (self.mountpoint, self.scratch)
        active = _active_mounts_under(roots)
        prefix = _privileged_prefix()
        umount = shutil.which("umount")
        if active and prefix is not None and umount is not None:
            for mounted_path in active:
                _run_fixed_command([*prefix, umount, str(mounted_path)], timeout=10)

        dm_path = Path("/dev/mapper") / self._dm_name
        if not self._dm_preexisting and dm_path.exists():
            dmsetup = shutil.which("dmsetup")
            if prefix is not None and dmsetup is not None:
                _run_fixed_command([*prefix, dmsetup, "remove", self._dm_name], timeout=10)

        inventory = _loop_inventory()
        losetup = shutil.which("losetup")
        owned_roots = (
            self.disk,
            self.scratch.resolve(strict=False),
        )
        if inventory is not None and losetup is not None and prefix is not None:
            for device, backing in inventory.items():
                if self._baseline_loops is not None and device in self._baseline_loops:
                    continue
                if any(backing == root or root in backing.parents for root in owned_roots):
                    _run_fixed_command([*prefix, losetup, "-d", device], timeout=10)

        active_after = _active_mounts_under(roots)
        loops_after = _loop_inventory()
        loop_state_known = self._baseline_loops is not None and loops_after is not None
        owned_loops_after = (
            {
                device
                for device, backing in loops_after.items()
                if device not in self._baseline_loops
                and any(backing == root or root in backing.parents for root in owned_roots)
            }
            if loop_state_known and loops_after is not None and self._baseline_loops is not None
            else set()
        )
        dm_released = self._dm_preexisting or not dm_path.exists()
        loop_released = self._method != "dmpad" or (loop_state_known and not owned_loops_after)
        released = active_after == () and loop_released and dm_released
        if released:
            with suppress(OSError):
                shutil.rmtree(self.scratch)
        return released

    def close(self) -> bool:
        """Ask the live owner to clean up, then independently verify resources."""

        if self._closed:
            return self._released
        process = self._process
        if process is not None and process.poll() is None:
            with suppress(EvidenceDiscoveryError):
                self._send({"action": "cleanup"})
            try:
                reply = self._reply(_MOUNT_WORKER_CLEANUP_SECONDS)
                if reply.get("ok") is not True or reply.get("cleaned") is not True:
                    _terminate_process_group(process)
            except (EvidenceDiscoveryError, TimeoutError):
                _terminate_process_group(process)
        if process is not None and process.poll() is None:
            _terminate_process_group(process)
        self._released = self._cleanup_owned_resources()
        self._closed = True
        return self._released


class _ReadOnlyMount:
    """Run-local mount owner with idempotent teardown."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self._reference_worker: _ReferenceMountWorker | None = None
        self._direct_mount = False
        self._closed = False
        self._released = True

    def mount(
        self,
        disk: Path,
        filesystem: str | None,
        os_family: OsFamily,
        filesystem_offset: int | None,
        budget: RunBudget | None = None,
    ) -> tuple[Path | None, tuple[str, ...]]:
        """Mount a supported filesystem with read-only flags, or report why not."""

        if filesystem_offset is not None and filesystem_offset < 0:
            raise EvidenceDiscoveryError("Filesystem offset cannot be negative")

        mountpoint = Path(tempfile.mkdtemp(prefix="unchained-evidence-ro-"))
        self.path = mountpoint
        self._released = False
        warnings: list[str] = []
        if budget is not None:
            budget.check()

        reference_allowed = (
            os.name != "nt"
            and getattr(os, "geteuid", lambda: -1)() == 0
            and Path("/proc/self/mountinfo").is_file()
            and filesystem in {"ntfs", None}
            and os_family in {"windows", "unknown"}
        )
        if reference_allowed:
            for method in ("raw@0", "ntfs_offsets", "dmpad"):
                if budget is not None:
                    budget.check()
                worker = _ReferenceMountWorker(disk, mountpoint, budget)
                self._reference_worker = worker
                try:
                    mounted, message = worker.mount(method, budget)
                except MountContainmentError:
                    raise
                except (EvidenceDiscoveryError, OSError, TimeoutError) as exc:
                    warnings.append(f"Reference read-only mount method {method} failed: {exc}")
                    if not worker.close():
                        raise MountContainmentError(
                            "Pinned mount failure could not be released safely"
                        ) from exc
                    self._reference_worker = None
                    continue
                if mounted:
                    if _mount_is_read_only(mountpoint):
                        return mountpoint, tuple(warnings)
                    warnings.append(
                        f"Mount method {method} did not verify as read-only; it was rejected."
                    )
                    if not worker.close():
                        raise MountContainmentError("Unverified mount could not be released safely")
                    self._reference_worker = None
                    break
                self._reference_worker = None
                if message:
                    warnings.append(f"Reference mount method {method}: {message}")
        elif filesystem in {"ntfs", None} and os_family in {"windows", "unknown"}:
            warnings.append(
                "Pinned NTFS mount backend requires root and Linux mountinfo for containment."
            )

        target_offset = filesystem_offset or 0
        prefix = _privileged_prefix()
        mount_binary = shutil.which("mount")
        arguments: list[str] | None = None
        if (
            prefix is not None
            and mount_binary is not None
            and filesystem in {"ext4", "xfs", "hfs+"}
        ):
            filesystem_type = {"ext4": "ext4", "xfs": "xfs", "hfs+": "hfsplus"}[filesystem]
            option_parts = {
                "ext4": ["ro", "noload", "loop"],
                "xfs": ["ro", "norecovery", "loop"],
                "hfs+": ["ro", "loop"],
            }[filesystem]
            if target_offset:
                option_parts.append(f"offset={target_offset}")
            arguments = [
                *prefix,
                mount_binary,
                "-t",
                filesystem_type,
                "-o",
                ",".join(option_parts),
                str(disk),
                str(mountpoint),
            ]
        elif filesystem == "apfs":
            if target_offset:
                warnings.append(
                    "APFS mount was withheld because the available backend cannot receive "
                    f"the classified byte offset {target_offset}."
                )
            else:
                apfs_fuse = shutil.which("apfs-fuse")
                if apfs_fuse:
                    arguments = [apfs_fuse, "-o", "ro", str(disk), str(mountpoint)]

        if arguments is not None:
            try:
                result = _run_fixed_command(
                    arguments,
                    timeout=_COMMAND_TIMEOUT_SECONDS,
                    budget=budget,
                )
            except CapExceeded as exc:
                if not _release_owned_mountpoint(mountpoint):
                    raise MountContainmentError(
                        "Wall deadline fired while mounting and release could not be verified"
                    ) from exc
                raise
            if result.returncode == 0 and _mount_is_read_only(mountpoint):
                self._direct_mount = True
                return mountpoint, tuple(warnings)
            if _mount_is_active(mountpoint) and not _release_owned_mountpoint(mountpoint):
                raise MountContainmentError(
                    "Rejected direct mount could not be positively released"
                )
            warnings.append(
                "Best-effort read-only mount failed or could not be verified read-only: "
                + result.output[:512].strip()
            )
        elif filesystem not in {"ntfs", None} or os_family not in {"windows", "unknown"}:
            warnings.append(
                f"No safe read-only mount backend is available for {filesystem or 'unknown fs'}."
            )

        if _mount_is_active(mountpoint):
            raise MountContainmentError(
                "Mount cleanup could not be verified; its owned mountpoint was preserved"
            )
        with suppress(OSError):
            mountpoint.rmdir()
        self.path = None
        self._released = True
        return None, tuple(warnings)

    def close(self) -> bool:
        """Release mounts safely and return whether teardown was verified."""

        if self._closed:
            return self._released
        self._closed = True
        owner_released = True
        if self._reference_worker is not None:
            owner_released = self._reference_worker.close()
        elif self._direct_mount and self.path is not None:
            prefix = _privileged_prefix()
            umount = shutil.which("umount")
            if prefix is not None and umount is not None:
                _run_fixed_command([*prefix, umount, str(self.path)], timeout=60)
        if self.path is not None:
            self._released = owner_released and not _mount_is_active(self.path)
            if self._released:
                with suppress(OSError):
                    self.path.rmdir()
        else:
            self._released = True
        return self._released


def _tool_families(
    os_family: OsFamily,
    items: tuple[EvidenceItem, ...],
    mounted: bool,
) -> tuple[str, ...]:
    """Describe only routes that the deterministic readiness gate permits."""

    families: list[str] = []
    memory_ready = any(item.kind == "memory" and item.available for item in items)
    volatility_ready = _volatility_base_command() is not None
    reference_ready = importlib.util.find_spec("sift_sentinel") is not None
    if memory_ready and volatility_ready and reference_ready:
        if os_family == "windows":
            families.append("volatility3.windows")
        elif os_family == "linux":
            families.append("volatility3.linux.experimental")
        elif os_family == "macos":
            families.append("volatility3.macos.best-effort")
    if any(item.kind == "disk" and item.available for item in items):
        if any(shutil.which(binary) for binary in ("fsstat", "mmls", "img_stat")):
            families.append("sleuthkit")
        if os_family == "windows" and mounted and reference_ready:
            families.append("sift-sentinel.windows-disk")
    return tuple(dict.fromkeys(families))


def _capability_label(
    os_family: OsFamily,
    items: tuple[EvidenceItem, ...],
    mounted: bool,
    conflict: bool,
    tool_families: tuple[str, ...],
) -> str:
    """Return a concise, deliberately non-inflated capability statement."""

    memory_items = tuple(item for item in items if item.kind == "memory")
    memory_present = bool(memory_items)
    memory_ready = any(item.available for item in memory_items)
    disk_present = any(item.kind == "disk" for item in items)
    disk_route = disk_present and (mounted or any(item.kind == "disk" for item in items))
    if conflict:
        label = "OS conflict - generic disk/log inspection only; OS-specific analysis disabled"
        return label if tool_families else f"{label}; no ready forensic tool family"
    tier = {
        "windows": "Windows tested path",
        "linux": "Linux experimental path",
        "macos": "macOS best-effort path",
        "unknown": "Undetermined OS - limited generic capability",
    }[os_family]
    states: list[str] = []
    if memory_present:
        if memory_ready and all(item.health == "ready" for item in memory_items):
            states.append("memory ready")
        elif memory_ready and any(
            item.health == "degraded-windows-symbol-probe" for item in memory_items
        ):
            states.append("memory routable; Windows symbol auto-download/probe pending")
        elif memory_ready:
            states.append("memory partially ready")
        else:
            states.append("memory unavailable")
    if disk_present:
        states.append("disk mounted read-only" if mounted else "disk raw-only")
    if not states and any(item.kind == "log" for item in items):
        states.append("standalone logs only")
    if disk_present and not disk_route:
        states.append("disk unavailable")
    label = f"{tier} - {', '.join(states) if states else 'no supported evidence route'}"
    if not tool_families:
        label += "; no ready forensic tool family"
    return label


def _human_size(size: int) -> str:
    value = float(size)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def _terminal_text(value: object) -> str:
    """Escape control characters in evidence-derived console text."""

    encoded = json.dumps(str(value), ensure_ascii=False)
    return encoded[1:-1]


def print_case_card(profile: EvidenceProfile, stream: TextIO = sys.stdout) -> None:
    """Print the human-readable deterministic profile and full custody hashes."""

    print("UNCHAINED - CASE CARD", file=stream)
    print(f"OS: {profile.os}", file=stream)
    print(f"Shape: {profile.shape}", file=stream)
    print(f"Filesystems: {', '.join(profile.filesystems) or 'none resolved'}", file=stream)
    print(f"Capability: {profile.capability_label}", file=stream)
    print(f"Read-only mount: {profile.mount_path or 'unavailable / not required'}", file=stream)
    print("Evidence:", file=stream)
    for item in profile.items:
        print(
            f"  {item.evidence_id}  {item.kind:<7} {_human_size(item.size):>11}  "
            f"health={item.health} symbols={item.symbols}",
            file=stream,
        )
        print(f"    path: {_terminal_text(item.path)}", file=stream)
        print(f"    SHA-256: {item.sha256}", file=stream)
    if profile.warnings:
        print("Warnings:", file=stream)
        for warning in profile.warnings:
            print(f"  - {_terminal_text(warning)}", file=stream)


class EvidenceSession:
    """Own one evidence profile, read-only mount, and custody lifecycle.

    ``profile`` is idempotent.  ``verify_custody`` always performs a fresh,
    full SHA-256 pass over the newly enumerated set and raises ``CustodyError``
    for missing, extra, resized, replaced, timestamp-changed, or rehashed files.
    ``close`` is also idempotent and may be called before final verification.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        mount: bool = True,
        case_card_stream: TextIO | None = sys.stdout,
        budget: RunBudget | None = None,
    ) -> None:
        requested = Path(root).expanduser()
        try:
            requested_stat = requested.lstat()
        except OSError as exc:
            raise EvidenceDiscoveryError(f"Evidence input does not exist: {requested}") from exc
        if stat.S_ISLNK(requested_stat.st_mode):
            raise EvidenceDiscoveryError(f"Evidence input may not be a symlink: {requested}")
        try:
            self.root = requested.resolve(strict=True)
        except OSError as exc:
            raise EvidenceDiscoveryError(f"Evidence input does not exist: {requested}") from exc
        self._mount_requested = mount
        self._case_card_stream = case_card_stream
        self._budget = budget
        self._profile: EvidenceProfile | None = None
        self._snapshots: dict[str, _FileSnapshot] = {}
        self._evidence_ids_by_relative_path: dict[str, str] = {}
        self._mount = _ReadOnlyMount()
        self._closed = False
        self._verified = False
        self._mount_released = True
        self._lock = threading.RLock()

    def __enter__(self) -> EvidenceSession:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.close()

    def profile(self) -> EvidenceProfile:
        """Discover, hash, classify, route, and optionally mount this evidence."""

        with self._lock:
            if self._profile is not None:
                return self._profile
            if self._closed:
                raise EvidenceError("Cannot profile a closed evidence session")

            if self._budget is not None:
                self._budget.check()
            enumerated = _enumerate_files(
                self.root,
                self._budget.check if self._budget is not None else None,
            )
            snapshots = tuple(
                _sha256_snapshot(
                    path,
                    relative,
                    self._budget.check if self._budget is not None else None,
                )
                for path, relative in enumerated
            )
            self._snapshots = {snapshot.relative_path: snapshot for snapshot in snapshots}
            classifications = tuple(_classify(snapshot, self._budget) for snapshot in snapshots)
            os_family, route_warnings = reconcile_evidence_os(classifications)
            shape = derive_evidence_shape(classifications)

            items: list[EvidenceItem] = []
            mount_messages: list[str] = []
            for index, (snapshot, classification) in enumerate(
                zip(snapshots, classifications, strict=True),
                start=1,
            ):
                item_os = classification.os_hint
                symbols = "not-applicable"
                available = classification.kind != "unknown"
                health = classification.health
                item_warnings = list(classification.warnings)
                if classification.kind == "memory":
                    readiness_os = item_os if item_os != "unknown" else os_family
                    symbols, available, health, derived_warnings = _memory_readiness(
                        snapshot.path,
                        readiness_os,
                        classification.warnings,
                        self._budget,
                    )
                    item_warnings = list(derived_warnings)
                items.append(
                    EvidenceItem(
                        evidence_id=f"E{index:03d}",
                        path=snapshot.path,
                        kind=classification.kind,
                        size=snapshot.size,
                        sha256=snapshot.sha256,
                        filesystem=classification.filesystem,
                        filesystem_offset=classification.filesystem_offset,
                        os_hint=item_os,
                        health=health,
                        symbols=symbols,
                        available=available,
                        warnings=tuple(item_warnings),
                    )
                )

            mount_path: Path | None = None
            if self._mount_requested:
                disk_index = next(
                    (
                        index
                        for index, item in enumerate(items)
                        if item.kind == "disk" and item.available
                    ),
                    None,
                )
                if disk_index is not None:
                    classification = classifications[disk_index]
                    mount_path, mount_warnings = self._mount.mount(
                        items[disk_index].path,
                        items[disk_index].filesystem,
                        os_family,
                        classification.filesystem_offset,
                        self._budget,
                    )
                    mount_messages.extend(mount_warnings)
                    if mount_path is not None and items[disk_index].filesystem is None:
                        items[disk_index] = replace(
                            items[disk_index],
                            filesystem="ntfs",
                            os_hint="windows",
                        )
                    mounted_health = (
                        "mounted-read-only" if mount_path else "raw-only-mount-unavailable"
                    )
                    items[disk_index] = replace(items[disk_index], health=mounted_health)

            final_os_family, final_route_warnings = reconcile_evidence_os(items)
            if final_os_family != os_family and final_os_family != "unknown":
                for memory_index, (snapshot, classification, memory_item) in enumerate(
                    zip(snapshots, classifications, items, strict=True)
                ):
                    if memory_item.kind != "memory" or memory_item.os_hint != "unknown":
                        continue
                    symbols, available, memory_health, memory_warnings = _memory_readiness(
                        snapshot.path,
                        final_os_family,
                        classification.warnings,
                        self._budget,
                    )
                    items[memory_index] = replace(
                        memory_item,
                        os_hint=final_os_family,
                        symbols=symbols,
                        available=available,
                        health=memory_health,
                        warnings=memory_warnings,
                    )
                final_os_family, final_route_warnings = reconcile_evidence_os(items)
            os_family = final_os_family
            route_warnings = final_route_warnings
            immutable_items = tuple(items)
            warnings = list(route_warnings)
            for item in immutable_items:
                warnings.extend(f"{item.evidence_id}: {warning}" for warning in item.warnings)
            warnings.extend(mount_messages)
            self._evidence_ids_by_relative_path = {
                snapshot.relative_path: item.evidence_id
                for snapshot, item in zip(snapshots, immutable_items, strict=True)
            }
            conflict = any(warning.startswith("OS CONFLICT:") for warning in route_warnings)
            filesystems = derive_filesystems(immutable_items)
            available_tool_families = _tool_families(
                os_family,
                immutable_items,
                mount_path is not None,
            )
            profile = EvidenceProfile(
                root=self.root,
                os=os_family,
                shape=shape,
                filesystems=filesystems,
                sizes={item.evidence_id: item.size for item in immutable_items},
                health={item.evidence_id: item.health for item in immutable_items},
                symbols={item.evidence_id: item.symbols for item in immutable_items},
                hashes={item.evidence_id: item.sha256 for item in immutable_items},
                available_tool_families=available_tool_families,
                capability_label=_capability_label(
                    os_family,
                    immutable_items,
                    mount_path is not None,
                    conflict,
                    available_tool_families,
                ),
                items=immutable_items,
                mount_path=mount_path,
                warnings=tuple(dict.fromkeys(warnings)),
            )
            self._profile = profile
            if self._case_card_stream is not None:
                print_case_card(profile, self._case_card_stream)
            return profile

    def verify_custody(self) -> dict[str, str]:
        """Freshly hash the post-run set and prove identity/content equality."""

        with self._lock:
            if self._profile is None:
                raise EvidenceError("profile() must complete before verify_custody()")
            try:
                enumerated = _enumerate_files(self.root)
            except EvidenceDiscoveryError as exc:
                raise CustodyError(f"Evidence custody verification failed: {exc}") from exc
            current_paths = {relative: path for path, relative in enumerated}
            original_names = set(self._snapshots)
            current_names = set(current_paths)
            missing = sorted(original_names - current_names)
            extra = sorted(current_names - original_names)

            current_snapshots: dict[str, _FileSnapshot] = {}
            hash_errors: list[str] = []
            for relative in sorted(current_names):
                try:
                    current_snapshots[relative] = _sha256_snapshot(
                        current_paths[relative],
                        relative,
                    )
                except EvidenceError as exc:
                    hash_errors.append(str(exc))

            mismatches: list[str] = []
            if missing:
                mismatches.append("missing files: " + ", ".join(missing))
            if extra:
                mismatches.append("extra files: " + ", ".join(extra))
            mismatches.extend(hash_errors)
            for relative in sorted(original_names & current_names):
                original = self._snapshots[relative]
                current = current_snapshots.get(relative)
                if current is None:
                    continue
                if (original.device, original.inode) != (current.device, current.inode):
                    mismatches.append(f"file identity changed: {relative}")
                if original.size != current.size:
                    mismatches.append(
                        f"file size changed: {relative} ({original.size} -> {current.size})"
                    )
                if original.mtime_ns != current.mtime_ns:
                    mismatches.append(f"file modification timestamp changed: {relative}")
                if original.sha256 != current.sha256:
                    mismatches.append(f"SHA-256 mismatch: {relative}")
            if mismatches:
                raise CustodyError("Evidence custody verification failed: " + "; ".join(mismatches))
            self._verified = True
            if set(self._evidence_ids_by_relative_path) != original_names:
                raise CustodyError(
                    "Evidence custody verification failed: sealed evidence-id map is incomplete"
                )
            return {
                self._evidence_ids_by_relative_path[relative]: current_snapshots[relative].sha256
                for relative in sorted(original_names)
            }

    def close(self) -> bool:
        """Unmount evidence and return whether release was positively verified."""

        with self._lock:
            if self._closed:
                return self._mount_released
            self._closed = True
            self._mount_released = self._mount.close()
            return self._mount_released


def verify_custody(profile: EvidenceProfile) -> dict[str, str]:
    """Rehash a profile's original files when no ``EvidenceSession`` is retained.

    This compatibility helper verifies size and digest.  Prefer the session
    method, which additionally verifies the originally enumerated set and file
    identities.
    """

    verified: dict[str, str] = {}
    mismatches: list[str] = []
    for item in profile.items:
        try:
            snapshot = _sha256_snapshot(item.path, item.evidence_id)
        except (EvidenceError, OSError) as exc:
            mismatches.append(f"{item.evidence_id}: {exc}")
            continue
        verified[item.evidence_id] = snapshot.sha256
        if snapshot.size != item.size:
            mismatches.append(f"{item.evidence_id}: size changed")
        if snapshot.sha256 != item.sha256:
            mismatches.append(f"{item.evidence_id}: SHA-256 mismatch")
    if mismatches:
        raise CustodyError("Evidence custody verification failed: " + "; ".join(mismatches))
    return verified


class _MountWorkerCancelled(Exception):
    """Private signal used only inside the fixed reference-mount worker."""


def _reference_mount_worker_main() -> int:
    """Run one allowlisted pinned mount operation and retain its cleanup owner."""

    protocol = sys.stdout

    def emit(payload: dict[str, object]) -> None:
        protocol.write(json.dumps(payload, separators=(",", ":")) + "\n")
        protocol.flush()

    try:
        line = sys.stdin.readline(_MOUNT_WORKER_MAX_REPLY_BYTES + 1)
        if not line or len(line.encode("utf-8", errors="replace")) > _MOUNT_WORKER_MAX_REPLY_BYTES:
            emit({"ok": False, "error": "missing or oversized worker request"})
            return 2
        request = json.loads(line)
        if not isinstance(request, dict) or request.get("action") != "mount":
            raise ValueError("worker action must be mount")
        method = request.get("method")
        if not isinstance(method, str) or method not in _REFERENCE_MOUNT_METHODS:
            raise ValueError("worker method is not allowlisted")
        disk_value = request.get("disk")
        mountpoint_value = request.get("mountpoint")
        scratch_value = request.get("scratch")
        if not all(
            isinstance(value, str) for value in (disk_value, mountpoint_value, scratch_value)
        ):
            raise ValueError("worker paths must be strings")
        disk = Path(str(disk_value)).resolve(strict=True)
        mountpoint = Path(str(mountpoint_value)).resolve(strict=True)
        scratch = Path(str(scratch_value)).resolve(strict=True)
        if disk.is_symlink() or not disk.is_file():
            raise ValueError("worker disk must be a regular non-symlink file")
        if mountpoint.is_symlink() or not mountpoint.is_dir():
            raise ValueError("worker mountpoint must be a non-symlink directory")
        if scratch.is_symlink() or not scratch.is_dir():
            raise ValueError("worker scratch must be a non-symlink directory")
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        emit({"ok": False, "error": f"invalid worker request: {exc}"})
        return 2

    os.environ["TMPDIR"] = str(scratch)
    os.environ["TMP"] = str(scratch)
    os.environ["TEMP"] = str(scratch)
    tempfile.tempdir = str(scratch)
    sink = sys.stderr
    backend: object | None = None
    cleaned = False

    def cancel(_signum: int, _frame: object) -> None:
        raise _MountWorkerCancelled

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cancel)

    def cleanup() -> None:
        nonlocal cleaned
        if cleaned:
            return
        cleaned = True
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if backend is not None:
            cleanup_method = getattr(backend, "cleanup", None)
            if callable(cleanup_method):
                with suppress(Exception), redirect_stdout(sink), redirect_stderr(sink):
                    cleanup_method()

    try:
        with redirect_stdout(sink), redirect_stderr(sink):
            from sift_sentinel.onboard.engine import RealProbes

            backend = RealProbes()
            mounted, message = backend.mount(str(disk), method, str(mountpoint))
        if not mounted:
            cleanup()
            emit({"ok": True, "mounted": False, "message": str(message)[:4096]})
            return 0

        emit({"ok": True, "mounted": True, "message": str(message)[:4096]})
        command_line = sys.stdin.readline(_MOUNT_WORKER_MAX_REPLY_BYTES + 1)
        if command_line:
            try:
                command = json.loads(command_line)
            except json.JSONDecodeError:
                command = None
            if not isinstance(command, dict) or command.get("action") != "cleanup":
                cleanup()
                emit({"ok": False, "cleaned": True, "error": "cleanup command required"})
                return 2
        cleanup()
        emit({"ok": True, "cleaned": True})
        return 0
    except _MountWorkerCancelled:
        cleanup()
        return 143
    except Exception as exc:
        cleanup()
        emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"[:4096]})
        return 1
    finally:
        cleanup()


if __name__ == "__main__":
    if sys.argv[1:] != [_MOUNT_WORKER_ARGUMENT]:
        raise SystemExit(2)
    raise SystemExit(_reference_mount_worker_main())
