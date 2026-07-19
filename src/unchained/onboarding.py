"""Profile-first, privacy-conscious console onboarding for junior analysts."""

from __future__ import annotations

import os
import textwrap
from dataclasses import asdict, dataclass
from typing import TextIO, cast

from .caps import CapConfig
from .models import EvidenceItem, EvidenceProfile, JsonValue

_CARD_WIDTH = 82
_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_CYAN = "\x1b[96m"
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


def _boxed(title: str, lines: list[str], *, stream: TextIO, color: bool) -> None:
    """Render a fixed-width card with wrapping and no evidence-derived paths."""

    inner = _CARD_WIDTH - 2
    normalized_title = f" {title} "
    remaining = max(0, inner - len(normalized_title))
    print(
        _paint(f"┌{normalized_title}{'─' * remaining}┐", _CYAN, color),
        file=stream,
    )
    for line in lines:
        wrapped = textwrap.wrap(
            line,
            width=inner - 2,
            replace_whitespace=True,
            drop_whitespace=True,
        ) or [""]
        for part in wrapped:
            print(f"│ {part:<{inner - 2}} │", file=stream)
    print(_paint(f"└{'─' * inner}┘", _CYAN, color), file=stream)


def _guardrail_lines(caps_profile: str, caps: CapConfig) -> list[str]:
    return [
        "THIS STEP: local profile + custody only · OpenAI calls 0 · paid run not started",
        (
            "IF YOU LAUNCH: OpenAI receives the bounded public profile and bounded typed-tool "
            "observations; original evidence bytes and runner-local paths stay local."
        ),
        (
            f"{caps_profile.upper()} HARD CEILINGS (not a price quote): "
            f"{caps.max_tool_calls} forensic calls · {caps.max_total_tokens:,} tokens · "
            f"{caps.max_wall_seconds / 60:g} min · ${caps.max_cost_usd:.2f} estimated cost"
        ),
        "Every mount attempt is read-only. Without --mount, disks remain raw-only.",
    ]


def _budget_choice_lines(selected: str, effective: CapConfig) -> list[str]:
    strict = _preset_caps("strict")
    flagship = _preset_caps("default")
    return [
        (
            f"CAUTIOUS {'[SELECTED]' if selected == 'strict' else ''} · --caps strict · "
            f"defaults: {strict.max_tool_calls} tools / {strict.max_total_tokens:,} tokens / "
            f"{strict.max_wall_seconds / 60:g} min / ${strict.max_cost_usd:.2f}"
        ),
        (
            f"FLAGSHIP {'[SELECTED]' if selected == 'default' else ''} · --caps default · "
            f"defaults: {flagship.max_tool_calls} tools / "
            f"{flagship.max_total_tokens:,} tokens / "
            f"{flagship.max_wall_seconds / 60:g} min / ${flagship.max_cost_usd:.2f}"
        ),
        (
            f"Selected effective ceilings: {effective.max_tool_calls} tools / "
            f"{effective.max_total_tokens:,} tokens / "
            f"{effective.max_wall_seconds / 60:g} min / ${effective.max_cost_usd:.2f}"
        ),
        (
            "Both use GPT-5.6 Sol. These are stop ceilings, not price quotes, depth modes, "
            "or promises of result quality. Environment overrides may change effective ceilings."
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
    print(_paint("╔" + "═" * (width - 2) + "╗", _CYAN, color), file=stream)
    for line in (
        "UNCHAINED",
        "Bounded autonomous DFIR · OpenAI GPT-5.6 Sol",
        '"Point me at one case. I will profile it before any model call."',
    ):
        print(
            _paint(f"║{line:^{width - 2}}║", _BOLD if line == "UNCHAINED" else _CYAN, color),
            file=stream,
        )
    print(_paint("╚" + "═" * (width - 2) + "╝", _CYAN, color), file=stream)
    print(file=stream)
    _boxed(
        "1 · PREPARE ONE CASE",
        [
            "Best fit: one ready memory image + one ready disk image from the same host.",
            (
                "Common memory containers include .raw, .img, .mem, .vmem, and .dmp; "
                "common disk containers include .E01, .dd, .raw, and .img."
            ),
            "Names and extensions are hints only; bounded probes decide the evidence kind.",
            "Memory-only or disk-only is supported when a typed forensic route is ready.",
            (
                "Multiple ready memory images or multiple ready disk images fail closed: "
                "split them into separate cases."
            ),
        ],
        stream=stream,
        color=color,
    )
    _boxed(
        "2 · WHAT THE SAFE PREVIEW DOES",
        [
            (
                "Enumerates regular files, probes bounded content and forensic metadata, "
                "assigns public evidence IDs, and hashes every input with SHA-256."
            ),
            (
                "Archives are not unpacked. Unknown documents and other unsupported files "
                "are hashed and listed, then set aside from forensic analysis."
            ),
            (
                "The default onboarding command does not mount disks, contact OpenAI, "
                "create a run bundle, or spend API credits."
            ),
        ],
        stream=stream,
        color=color,
    )
    _boxed(
        "3 · START HERE",
        [
            "sentinel onboard <one-case-evidence-folder>",
            "Optional read-only disk capabilities: add --mount",
            "Machine-readable, noninteractive preview: add --json",
            (
                "Optional paid Luna connectivity canary (no evidence; not proof): "
                "sentinel smoke-openai"
            ),
        ],
        stream=stream,
        color=color,
    )
    _boxed(
        "4 · CHOOSE A RUN BUDGET",
        _budget_choice_lines(caps_profile, caps),
        stream=stream,
        color=color,
    )
    _boxed(
        "CLOUD + COST BOUNDARY",
        _guardrail_lines(caps_profile, caps),
        stream=stream,
        color=color,
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
    print(
        _paint("◆ PROFILE COMPLETE — deterministic, local, zero OpenAI calls", _BOLD, color),
        file=stream,
    )
    print(file=stream)
    for item in profile.items:
        state = _safe_health(item)
        marker = "✓" if item.kind != "unknown" and item.available else "○"
        digest = f"{item.sha256[:12]}…{item.sha256[-12:]}"
        print(
            f"  {marker} {item.evidence_id}  {item.kind.upper():<7}  "
            f"{_human_size(item.size):>10}  {state}  SHA-256 {digest}",
            file=stream,
        )
    if assessment.set_aside_items:
        print(
            f"  ○ {assessment.set_aside_items} unsupported item(s) set aside — "
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
    _boxed("VERIFIED CASE CARD", case_lines, stream=stream, color=color)
    if assessment.blockers:
        _boxed(
            "FIX BEFORE LAUNCH",
            [f"{index}. {blocker}" for index, blocker in enumerate(assessment.blockers, 1)],
            stream=stream,
            color=color,
        )
    _boxed(
        "CHOOSE A RUN BUDGET",
        _budget_choice_lines(caps_profile, caps),
        stream=stream,
        color=color,
    )
    _boxed(
        "CLOUD + COST BOUNDARY",
        _guardrail_lines(caps_profile, caps),
        stream=stream,
        color=color,
    )
    next_lines = [
        "1. Check live dependencies and key presence: sentinel doctor",
        "2. Optional paid Luna canary (no evidence; not proof): sentinel smoke-openai",
        "3. Optional technical record: sentinel profile <same-evidence> --json",
    ]
    if assessment.profile_ready:
        next_lines.append(
            "4. Explicit paid Sol launch: sentinel onboard <same-evidence> "
            f"--launch --caps {caps_profile}"
        )
        next_lines.append("   You will still have to type an exact confirmation phrase.")
    else:
        next_lines.append(
            "4. Resolve the case-card blockers, then profile again. No paid Sol launch is offered."
        )
    _boxed("NEXT — NO GUESSWORK", next_lines, stream=stream, color=color)
    print(
        "Local profile and custody are complete. Live model readiness is not asserted "
        "until sentinel doctor passes.",
        file=stream,
    )
