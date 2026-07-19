"""Profile-first, privacy-conscious console onboarding for junior analysts."""

from __future__ import annotations

import os
import shutil
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TextIO, cast

from .caps import CapConfig
from .models import EvidenceItem, EvidenceProfile, JsonValue

_CARD_WIDTH = 82
_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_CYAN = "\x1b[96m"
_BLUE = "\x1b[38;5;45m"
_VIOLET = "\x1b[38;5;141m"
_GREEN = "\x1b[38;5;78m"
_AMBER = "\x1b[38;5;214m"
_RED = "\x1b[38;5;203m"
_DIM = "\x1b[38;5;245m"
_WHITE = "\x1b[38;5;255m"
_ASCII_FALLBACK = str.maketrans(
    {
        "·": "-",
        "—": "-",
        "…": "...",
        "─": "-",
        "│": "|",
        "┌": "+",
        "┐": "+",
        "└": "+",
        "┘": "+",
        "═": "=",
        "║": "|",
        "╔": "+",
        "╗": "+",
        "╚": "+",
        "╝": "+",
        "◆": "*",
        "○": "-",
        "✓": "OK",
    }
)


class _EncodingSafeStream:
    """Translate decorative glyphs when an older Windows code page cannot encode them."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self.encoding = getattr(stream, "encoding", None)

    def write(self, value: str) -> int:
        return self._stream.write(value.translate(_ASCII_FALLBACK))

    def flush(self) -> None:
        self._stream.flush()

    def isatty(self) -> bool:
        isatty = getattr(self._stream, "isatty", None)
        return bool(callable(isatty) and isatty())


def _encoding_safe_stream(stream: TextIO) -> TextIO:
    encoding = getattr(stream, "encoding", None)
    if not encoding:
        return stream
    try:
        "╔═╗║╚╝◆○✓·—…".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return cast(TextIO, _EncodingSafeStream(stream))
    return stream


@dataclass(frozen=True, slots=True)
class OnboardingAssessment:
    """Safe summary of whether a deterministic profile can proceed to run preflight."""

    profile_ready: bool
    blockers: tuple[str, ...]
    recognized_items: int
    set_aside_items: int
    ready_memory_images: int
    ready_disk_images: int


def _preset_caps(profile: str) -> CapConfig:
    """Return the code-owned preset before operator environment overrides."""

    if profile == "default":
        return CapConfig()
    if profile == "strict":
        return CapConfig(
            max_tool_calls=20,
            max_total_tokens=100_000,
            max_wall_seconds=600.0,
            max_cost_usd=2.5,
        )
    raise ValueError(f"unknown cap profile: {profile}")


def _compact_caps(caps: CapConfig) -> dict[str, JsonValue]:
    return {
        "max_tool_calls": caps.max_tool_calls,
        "max_total_tokens": caps.max_total_tokens,
        "max_wall_seconds": caps.max_wall_seconds,
        "max_estimated_cost_usd": caps.max_cost_usd,
    }


def _run_choices(selected: str, effective: CapConfig) -> dict[str, JsonValue]:
    return {
        "selected": selected,
        "profiles": {
            "strict": {
                "label": "CAUTIOUS",
                "default_hard_caps": _compact_caps(_preset_caps("strict")),
                "command": "sentinel onboard <same-evidence> --launch --caps strict",
            },
            "default": {
                "label": "FLAGSHIP",
                "default_hard_caps": _compact_caps(_preset_caps("default")),
                "command": "sentinel onboard <same-evidence> --launch --caps default",
            },
        },
        "effective_selected_hard_caps": _compact_caps(effective),
        "hard_ceilings_not_quotes": True,
        "changes_model": False,
        "promises_result_quality": False,
    }


def mount_status(profile: EvidenceProfile, *, requested: bool, released: bool) -> str:
    """Describe mount outcome without exposing the private mountpoint."""

    if not requested:
        return "not-requested"
    if profile.mount_path is not None:
        return "verified-read-only-and-released" if released else "release-not-verified"
    if not profile.disk_items:
        return "not-applicable-no-ready-disk"
    return "requested-but-unavailable-raw-only"


def assess_profile(profile: EvidenceProfile) -> OnboardingAssessment:
    """Apply the same one-memory/one-disk route limits used by the tool loader."""

    ready_memory = len(profile.memory_items)
    ready_disk = len(profile.disk_items)
    recognized = sum(item.kind != "unknown" for item in profile.items)
    blockers: list[str] = []
    if profile.shape == "unknown" or recognized == 0:
        blockers.append("No supported memory, disk, or standalone-log content was recognized.")
    if not any(item.available for item in profile.items):
        blockers.append("Every recognized evidence route is currently unavailable.")
    if ready_memory > 1:
        blockers.append(
            "More than one ready memory image was found; split them into separate cases."
        )
    if ready_disk > 1:
        blockers.append("More than one ready disk image was found; split them into separate cases.")
    if not profile.available_tool_families:
        blockers.append("No typed forensic tool family is ready for this profile.")
    return OnboardingAssessment(
        profile_ready=not blockers,
        blockers=tuple(blockers),
        recognized_items=recognized,
        set_aside_items=len(profile.items) - recognized,
        ready_memory_images=ready_memory,
        ready_disk_images=ready_disk,
    )


def _human_size(size: int) -> str:
    value = float(size)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def _safe_health(item: EvidenceItem) -> str:
    if item.kind == "unknown":
        return "SET ASIDE"
    if item.available:
        return item.health.upper().replace("-", " ")
    return "UNAVAILABLE"


def _supports_color(stream: TextIO, *, no_color: bool) -> bool:
    if no_color or "NO_COLOR" in os.environ:
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def _paint(value: str, code: str, enabled: bool) -> str:
    return f"{code}{value}{_RESET}" if enabled else value


def _boxed(
    title: str,
    lines: list[str],
    *,
    stream: TextIO,
    color: bool,
    accent: str = _CYAN,
) -> None:
    """Render a fixed-width card with wrapping and no evidence-derived paths."""

    inner = _CARD_WIDTH - 2
    normalized_title = f" {title} "
    remaining = max(0, inner - len(normalized_title))
    print(
        _paint(f"┌{normalized_title}{'─' * remaining}┐", accent + _BOLD, color),
        file=stream,
    )
    edge = _paint("│", accent, color)
    for line in lines:
        wrapped = textwrap.wrap(
            line,
            width=inner - 2,
            replace_whitespace=True,
            drop_whitespace=True,
        ) or [""]
        for part in wrapped:
            print(f"{edge} {part:<{inner - 2}} {edge}", file=stream)
    print(_paint(f"└{'─' * inner}┘", accent, color), file=stream)


def _budget_choice_lines(selected: str, effective: CapConfig) -> list[str]:
    strict = _preset_caps("strict")
    flagship = _preset_caps("default")

    def marker(profile: str) -> str:
        return "[SELECTED]" if selected == profile else ""

    return [
        (
            f"1) HEAVY — FLAGSHIP {marker('default')} · --caps default · "
            "deepest bounded investigation"
        ),
        (
            f"ceilings: {flagship.max_tool_calls} tools / "
            f"{flagship.max_total_tokens:,} tokens / "
            f"{flagship.max_wall_seconds / 60:g} min / ${flagship.max_cost_usd:.2f} "
            "estimated cost"
        ),
        (
            f"2) LIGHT — CAUTIOUS {marker('strict')} · --caps strict · "
            "same investigator, tighter stop ceilings"
        ),
        (
            f"ceilings: {strict.max_tool_calls} tools / "
            f"{strict.max_total_tokens:,} tokens / "
            f"{strict.max_wall_seconds / 60:g} min / ${strict.max_cost_usd:.2f} "
            "estimated cost"
        ),
        (
            f"Selected effective ceilings: {effective.max_tool_calls} tools / "
            f"{effective.max_total_tokens:,} tokens / "
            f"{effective.max_wall_seconds / 60:g} min / ${effective.max_cost_usd:.2f}"
        ),
        (
            "Both depths run the same GPT-5.6 Sol investigator. These are hard stop "
            "ceilings, not price quotes, reasoning modes, or promises of result quality. "
            "Environment overrides may change effective ceilings."
        ),
        (
            "Model invocations per completed case: 4 fixed (opening book, findings "
            "serialization, fresh review, report draft) + one per adaptive action — "
            "every one inside the ceilings above."
        ),
    ]


def welcome_payload(caps_profile: str, caps: CapConfig) -> dict[str, JsonValue]:
    """Return a stable no-evidence/no-provider onboarding description."""

    return {
        "schema": "sentinel-onboarding-v1",
        "stage": "WELCOME",
        "evidence_profiled": False,
        "openai_called": False,
        "paid_run_started": False,
        "one_case_limit": {"ready_memory_images": 1, "ready_disk_images": 1},
        "input_handling": {
            "classification": "bounded content probes plus deterministic metadata",
            "archives_unpacked": False,
            "unknown_files": "hashed and listed, then set aside from forensic analysis",
        },
        "cloud_boundary": {
            "sent_if_launched": [
                "bounded public evidence profile",
                "bounded typed-tool observations",
            ],
            "kept_local": ["original evidence bytes", "runner-local evidence paths"],
        },
        "caps_profile": caps_profile,
        "hard_caps": asdict(caps),
        "run_choices": _run_choices(caps_profile, caps),
        "next_command": "sentinel onboard <one-case-evidence-folder>",
        "secrets_printed": False,
    }


def profile_payload(
    profile: EvidenceProfile,
    assessment: OnboardingAssessment,
    *,
    caps_profile: str,
    caps: CapConfig,
    custody_match: bool,
    mount_requested: bool,
    mount_released: bool,
) -> dict[str, JsonValue]:
    """Return path-free onboarding JSON suitable for scripts and recorded demos."""

    items: list[JsonValue] = []
    for item in profile.items:
        items.append(
            {
                "evidence_id": item.evidence_id,
                "kind": item.kind,
                "size": item.size,
                "sha256": item.sha256,
                "available": item.available,
                "health": item.health,
                "symbols": item.symbols,
                "filesystem": item.filesystem,
            }
        )
    return {
        "schema": "sentinel-onboarding-v1",
        "stage": "PROFILE_COMPLETE",
        "profile_ready": assessment.profile_ready,
        "blockers": list(assessment.blockers),
        "case": {
            "os": profile.os,
            "shape": profile.shape,
            "filesystems": list(profile.filesystems),
            "capability_label": profile.capability_label,
            "recognized_items": assessment.recognized_items,
            "set_aside_items": assessment.set_aside_items,
            "ready_memory_images": assessment.ready_memory_images,
            "ready_disk_images": assessment.ready_disk_images,
            "available_tool_families": list(profile.available_tool_families),
            "warning_count": len(profile.warnings),
            "evidence": items,
        },
        "custody": {"match": custody_match, "hashes": dict(profile.hashes)},
        "mount": {
            "requested": mount_requested,
            "status": mount_status(profile, requested=mount_requested, released=mount_released),
            "released": mount_released,
        },
        "openai_called": False,
        "paid_run_started": False,
        "original_evidence_sent_to_openai": False,
        "caps_profile": caps_profile,
        "hard_caps": asdict(caps),
        "run_choices": _run_choices(caps_profile, caps),
        "next_commands": {
            "live_readiness": "sentinel doctor",
            "optional_paid_connectivity_canary": "sentinel smoke-openai",
            "technical_profile": "sentinel profile <same-evidence> --json",
            "interactive_launch": (
                f"sentinel onboard <same-evidence> --launch --caps {caps_profile}"
            ),
        },
        "secrets_printed": False,
    }


def render_welcome(
    *,
    caps_profile: str,
    caps: CapConfig,
    stream: TextIO,
    no_color: bool,
) -> None:
    """Render the zero-I/O first-launch walkthrough."""

    stream = _encoding_safe_stream(stream)
    color = _supports_color(stream, no_color=no_color)
    width = _CARD_WIDTH
    banner_styles = {
        "UNCHAINED": _WHITE + _BOLD,
        "Digital Forensics & Incident Response · OpenAI GPT-5.6 Sol": _VIOLET,
        '"Point me at one case. I will profile it before any model call."': _DIM,
    }
    print(_paint("╔" + "═" * (width - 2) + "╗", _BLUE + _BOLD, color), file=stream)
    for line, style in banner_styles.items():
        print(
            _paint("║", _BLUE + _BOLD, color)
            + _paint(f"{line:^{width - 2}}", style, color)
            + _paint("║", _BLUE + _BOLD, color),
            file=stream,
        )
    print(_paint("╚" + "═" * (width - 2) + "╝", _BLUE + _BOLD, color), file=stream)
    print(file=stream)

    def line(marker_color: str, label: str, detail: str) -> None:
        print(
            _paint("◆ ", marker_color + _BOLD, color)
            + _paint(f"{label:<9}", marker_color + _BOLD, color)
            + _paint(detail, _DIM, color),
            file=stream,
        )

    strict = _preset_caps("strict")
    flagship = _preset_caps("default")
    line(
        _BLUE,
        "ONE CASE",
        "memory and/or disk from one host; bounded probes decide the kind, not the name.",
    )
    line(
        _GREEN,
        "PREVIEW",
        "enumerate, classify, public IDs, SHA-256 every file — no mount, no OpenAI, no spend.",
    )
    line(
        _CYAN,
        "START",
        "sentinel onboard <folder>  ·  key: sentinel key  ·  canary: sentinel smoke-openai",
    )
    line(
        _VIOLET,
        "DEPTH",
        f"LIGHT {strict.max_tool_calls} tools/${strict.max_cost_usd:.2f}  ·  "
        f"HEAVY {flagship.max_tool_calls} tools/${flagship.max_cost_usd:.0f}  — "
        "same GPT-5.6 Sol, hard ceilings only.",
    )
    line(
        _AMBER,
        "BOUNDARY",
        "OpenAI calls 0 · paid run not started · launch needs the phrase LAUNCH GPT-5.6 SOL.",
    )


def render_profile(
    profile: EvidenceProfile,
    assessment: OnboardingAssessment,
    *,
    caps_profile: str,
    caps: CapConfig,
    custody_match: bool,
    mount_requested: bool,
    mount_released: bool,
    stream: TextIO,
    no_color: bool,
) -> None:
    """Render a concise case card without file names or local child paths."""

    stream = _encoding_safe_stream(stream)
    color = _supports_color(stream, no_color=no_color)
    try:
        free_gb = shutil.disk_usage(Path.cwd()).free / 1024**3
        runs_root = Path.cwd() / "unchained-runs"
        retained = sum(1 for p in runs_root.iterdir() if p.is_dir()) if runs_root.is_dir() else 0
        preflight = f"{free_gb:.1f} GB free · {retained} retained run bundle(s)"
        healthy = free_gb >= 5.0
    except OSError:
        preflight = "storage facts unavailable"
        healthy = True
    print(
        _paint("◆ STORAGE PREFLIGHT ", _BLUE + _BOLD, color)
        + _paint(preflight, _WHITE if healthy else _AMBER, color),
        file=stream,
    )
    if not healthy:
        print(
            _paint(
                "  ! Low free space for multi-GiB evidence and retained tool output.",
                _AMBER,
                color,
            ),
            file=stream,
        )
    print(
        _paint(
            "◆ PROFILE COMPLETE — deterministic, local, zero OpenAI calls",
            _GREEN + _BOLD,
            color,
        ),
        file=stream,
    )
    print(file=stream)
    print(
        _paint(
            "◆ Looking at what you gave me — classified by bounded content probes, "
            "never by file name:",
            _VIOLET + _BOLD,
            color,
        ),
        file=stream,
    )
    for item in profile.items:
        state = _safe_health(item)
        ready = item.kind != "unknown" and item.available
        marker = _paint("✓", _GREEN + _BOLD, color) if ready else _paint("○", _DIM, color)
        digest = f"{item.sha256[:12]}…{item.sha256[-12:]}"
        print(
            f"  {marker} {item.evidence_id}  {item.kind.upper():<7}  "
            f"{_human_size(item.size):>10}  {state}  " + _paint(f"SHA-256 {digest}", _DIM, color),
            file=stream,
        )
    if assessment.set_aside_items:
        print(
            _paint("  ○ ", _DIM, color)
            + f"{assessment.set_aside_items} unsupported item(s) set aside — "
            "hashed, not forensically analyzed",
            file=stream,
        )
    print(file=stream)

    status = "PROFILE READY" if assessment.profile_ready else "ACTION NEEDED"
    case_lines = [
        f"Status       {status}",
        f"OS           {profile.os.upper()}",
        f"Scope        {profile.shape}",
        f"Filesystems  {', '.join(profile.filesystems) or 'none resolved'}",
        f"Memory       {assessment.ready_memory_images} ready (maximum 1 per case)",
        f"Disk         {assessment.ready_disk_images} ready (maximum 1 per case)",
        f"Tools        {', '.join(profile.available_tool_families) or 'none ready'}",
        f"Capability   {profile.capability_label}",
        f"Custody      {'PASS' if custody_match else 'FAIL'} · full SHA-256 recheck",
        (
            "Disk mount   "
            + mount_status(profile, requested=mount_requested, released=mount_released)
        ),
    ]
    _boxed(
        "VERIFIED CASE CARD",
        case_lines,
        stream=stream,
        color=color,
        accent=_GREEN if assessment.profile_ready else _AMBER,
    )
    # Not launch-ready: show the blockers and one short next line, nothing else.
    if not assessment.profile_ready:
        if assessment.blockers:
            _boxed(
                "FIX BEFORE LAUNCH",
                [f"{index}. {blocker}" for index, blocker in enumerate(assessment.blockers, 1)],
                stream=stream,
                color=color,
                accent=_RED,
            )
        print(
            _paint(
                "◆ Resolve the blocker(s) above, then profile again. "
                "No paid Sol launch is offered.",
                _AMBER + _BOLD,
                color,
            ),
            file=stream,
        )
        return

    # Launch-ready: the depth pick plus three compact honest lines.
    _boxed(
        "CHOOSE ANALYSIS DEPTH — HEAVY OR LIGHT",
        _budget_choice_lines(caps_profile, caps),
        stream=stream,
        color=color,
        accent=_VIOLET,
    )
    print(
        _paint(
            "◆ THIS STEP: local profile + custody only · OpenAI calls 0 · paid run not started",
            _GREEN + _BOLD,
            color,
        ),
        file=stream,
    )
    print(
        _paint(
            f"◆ HARD CEILINGS (not a price quote): {caps.max_tool_calls} calls · "
            f"{caps.max_total_tokens:,} tokens · {caps.max_wall_seconds / 60:g} min · "
            f"${caps.max_cost_usd:.2f}",
            _AMBER,
            color,
        ),
        file=stream,
    )
    print(
        _paint(
            f"◆ LAUNCH: sentinel onboard <same-evidence> --launch --caps {caps_profile}  "
            "→ then type the exact confirmation phrase LAUNCH GPT-5.6 SOL",
            _CYAN + _BOLD,
            color,
        ),
        file=stream,
    )
