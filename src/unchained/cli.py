"""Command-line lifecycle for one isolated Unchained run."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import re
import sys
import time
import uuid
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .agent import AgentRun, UnchainedAgent, defang_untrusted_inline
from .artifacts import (
    ArtifactError,
    ArtifactRef,
    ArtifactStore,
    artifact_ref_from_existing,
    build_manifest,
    build_summary,
    capture_environment,
    write_manifest_pair,
)
from .audit import AuditLog
from .caps import CapConfig, CapExceeded, RunBudget
from .console import Console
from .evidence import CustodyError, EvidenceDiscoveryError, EvidenceError, EvidenceSession
from .model import (
    ModelProviderError,
    ModelRequest,
    OpenAIResponsesModel,
    cheap_model_opt_in,
    is_gpt5_family,
    is_gpt56_sol_model,
    is_gpt56_terra_model,
    openai_api_key_status,
)
from .models import EvidenceProfile, RunStatus
from .onboarding import (
    assess_profile,
    profile_payload,
    render_profile,
    render_welcome,
    welcome_payload,
)
from .tools import ToolRegistry
from .viewer import render_viewer_html

EXIT_COMPLETE = 0
EXIT_FATAL = 1
EXIT_INVALID = 2
EXIT_PARTIAL = 3
_SMOKE_MODEL = "gpt-5.6-terra"
_SMOKE_TOKEN = "SENTINEL_SMOKE_OK"
_SMOKE_MAX_OUTPUT_TOKENS = 128


def build_parser() -> argparse.ArgumentParser:
    """Create the user-facing run command and legacy no-subcommand parser."""

    parser = argparse.ArgumentParser(
        prog="sentinel run",
        description=(
            "Run a bounded GPT-5.6-driven Digital Forensics & Incident Response "
            "(DFIR) investigation."
        ),
    )
    parser.add_argument("evidence", type=Path, help="file or folder containing captured evidence")
    parser.add_argument(
        "--caps",
        choices=("default", "strict"),
        default="default",
        help="hard-limit profile (environment overrides still apply)",
    )
    return parser


def build_root_parser() -> argparse.ArgumentParser:
    """Create the compact command overview shown before any evidence I/O."""

    parser = argparse.ArgumentParser(
        prog="sentinel",
        description=(
            "Profile, investigate, verify, and view a bounded GPT-5.6 "
            "Digital Forensics & Incident Response (DFIR) case."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("onboard", "key", "doctor", "profile", "smoke-openai", "run", "verify", "view"),
        help="lifecycle command; run 'sentinel <command> --help' for details",
    )
    return parser


def build_key_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel key",
        description=(
            "One-time hidden OpenAI key setup: paste once with masked input; every "
            "later command finds it automatically. The key is never echoed or printed."
        ),
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="report whether a key is configured and from which source; never the key",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="delete the saved sentinel key file",
    )
    return parser


def build_onboard_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel onboard",
        description=(
            "Walk through one case, profile it locally, and require an exact confirmation "
            "before any paid GPT-5.6 Sol run."
        ),
    )
    parser.add_argument(
        "evidence",
        nargs="?",
        type=Path,
        help="one case's evidence file or folder; omit it for the welcome walkthrough",
    )
    parser.add_argument(
        "--mount",
        action="store_true",
        help="attempt a read-only disk mount during the local profile",
    )
    parser.add_argument(
        "--caps",
        choices=("default", "strict"),
        default="strict",
        help="hard ceilings shown now and applied if launch is explicitly confirmed",
    )
    parser.add_argument(
        "--launch",
        action="store_true",
        help="after a ready profile, offer an interactive paid-run confirmation gate",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI color; NO_COLOR is also honored",
    )
    return parser


def build_verify_parser() -> argparse.ArgumentParser:
    """Create the dependency-free completed-bundle verification command."""

    parser = argparse.ArgumentParser(
        prog="sentinel verify",
        description="Verify a retained Unchained proof bundle without rebuilding it.",
    )
    parser.add_argument("run_directory", type=Path, help="completed proof-bundle directory")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--require-live-gpt56", action="store_true")
    return parser


def build_doctor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel doctor",
        description="Check local runtime and live-run configuration without reading evidence.",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def build_smoke_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel smoke-openai",
        description=(
            "Run one cheap, non-forensic GPT-5.6 Terra typed-tool protocol canary. "
            "This never creates a proof bundle."
        ),
    )
    parser.add_argument(
        "--model",
        default=os.getenv("SENTINEL_SMOKE_MODEL", _SMOKE_MODEL),
        help="allowlisted Terra alias or snapshot (default: gpt-5.6-terra)",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def build_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel profile",
        description="Inventory, classify, route, and hash evidence without an OpenAI call.",
    )
    parser.add_argument("evidence", type=Path)
    parser.add_argument(
        "--mount",
        action="store_true",
        help="attempt a read-only disk mount while computing capabilities",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def build_view_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel view",
        description="Verify and open the retained offline proof viewer.",
    )
    parser.add_argument("run_directory", type=Path)
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="verify and print the viewer path without launching a browser",
    )
    return parser


_KEY_SOURCE_LABELS = {
    "environment": "OPENAI_API_KEY environment variable",
    "file": "OPENAI_API_KEY_FILE secret file",
    "default-key-file": "saved sentinel key file (one-time 'sentinel key' setup)",
}


def _store_key_material(entered: str) -> Path:
    """Write the key to the canonical owner-only file and return its path."""

    from .model import default_api_key_file

    key_path = default_api_key_file()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(descriptor, (entered + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)
    if os.name == "nt":
        import subprocess

        with contextlib.suppress(Exception):
            subprocess.run(
                [
                    "icacls",
                    str(key_path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{os.environ.get('USERNAME', 'SYSTEM')}:(R,W)",
                ],
                capture_output=True,
                check=False,
                timeout=15,
            )
    return key_path


def _key_command(*, status: bool, remove: bool) -> int:
    """Manage the canonical hidden-input key file; never print the credential."""

    from .model import default_api_key_file, openai_api_key_status

    console = Console(sys.stdout)
    key_path = default_api_key_file()

    if status:
        present, source = openai_api_key_status()
        if present:
            label = _KEY_SOURCE_LABELS.get(source or "", source or "unknown source")
            message = f"Key configured via the {label}."
            console.ok(message) if console.enabled else print(message)
        else:
            message = "No key configured. Run 'sentinel key' for one-time hidden setup."
            console.warn(message) if console.enabled else print(message)
        print(f"Saved-key location: {key_path}")
        print("Secrets printed: never.")
        return EXIT_COMPLETE

    if remove:
        if key_path.is_file():
            key_path.unlink()
            print(f"Removed the saved key file: {key_path}")
        else:
            print("No saved key file to remove.")
        return EXIT_COMPLETE

    if not _interactive_terminal():
        print(
            "sentinel key needs an interactive terminal for hidden input; "
            "set OPENAI_API_KEY or OPENAI_API_KEY_FILE for automation.",
            file=sys.stderr,
        )
        return EXIT_INVALID

    if console.enabled:
        console.phase("ONE-TIME KEY SETUP")
        console.detail("Paste once with hidden input. Saved to a private per-user file.")
        console.detail("Every sentinel command then finds it automatically - no")
        console.detail("environment variables needed. Env configuration still overrides.")
    import getpass

    entered = getpass.getpass("Paste your OpenAI API key (input stays hidden): ").strip()
    if not entered:
        print("Cancelled; nothing was saved.")
        return EXIT_INVALID
    if "\n" in entered or "\r" in entered or len(entered.encode("utf-8")) > 512:
        print("That does not look like one single-line API key; nothing was saved.")
        return EXIT_INVALID

    _store_key_material(entered)
    entered = ""

    success = "Key saved. Every sentinel command now finds it automatically."
    if console.enabled:
        console.ok(success)
    else:
        print(success)
    print(f"Location: {key_path} (owner-only access)")
    print("Check any time: sentinel key --status - remove: sentinel key --remove")
    print("Tip: if UNCHAINED_MODEL is unset, set it to gpt-5.6 before a paid run.")
    return EXIT_COMPLETE


def _doctor(*, json_output: bool) -> int:
    configured_model = os.getenv("UNCHAINED_MODEL")
    key_present, key_source = openai_api_key_status()
    test_mode = cheap_model_opt_in()
    if test_mode:
        model_ok = bool(configured_model and is_gpt5_family(configured_model))
        model_check_name = "model_is_gpt5_test"
    else:
        model_ok = bool(configured_model and is_gpt56_sol_model(configured_model))
        model_check_name = "model_is_gpt56_sol"
    checks = {
        "python_3_11": sys.version_info[:2] == (3, 11),
        "openai_sdk": importlib.util.find_spec("openai") is not None,
        "volatility3": importlib.util.find_spec("volatility3") is not None,
        "qwen_tool_package": importlib.util.find_spec("sift_sentinel") is not None,
        model_check_name: model_ok,
        "openai_api_key_present": key_present,
    }
    ready = all(checks.values())
    payload = {
        "ready_for_live_run": ready,
        "test_model_mode": test_mode,
        "checks": checks,
        "configured_model": configured_model,
        "openai_api_key_source": key_source,
        "python": sys.version.split()[0],
        "secrets_printed": False,
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("READY" if ready else "NOT READY")
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL':<4}  {name}")
        if not ready:
            print(
                "Next: run 'sentinel key' for one-time hidden key setup, set "
                "UNCHAINED_MODEL=gpt-5.6, then rerun doctor. (Automation can set "
                "OPENAI_API_KEY or OPENAI_API_KEY_FILE instead.)"
            )
    return EXIT_COMPLETE if ready else EXIT_INVALID


def _smoke_openai(*, model_id: str, json_output: bool) -> int:
    """Exercise one bounded Terra Responses call without creating forensic authority."""

    if not is_gpt56_terra_model(model_id):
        raise ValueError("--model must identify GPT-5.6 Terra")
    model = OpenAIResponsesModel(model_id=model_id, connectivity_smoke=True)
    tool = {
        "type": "function",
        "name": "sentinel_smoke_ok",
        "description": "Confirm the bounded Unchained OpenAI protocol canary.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "enum": [_SMOKE_TOKEN],
                    "description": "The exact fixed canary token.",
                }
            },
            "required": ["token"],
            "additionalProperties": False,
        },
    }
    response = model.create(
        ModelRequest(
            phase="connectivity-smoke",
            instructions=(
                "This is a non-forensic connectivity test. Call sentinel_smoke_ok exactly once "
                f"with token {_SMOKE_TOKEN}. Do not return narrative text."
            ),
            input_items="Perform the fixed typed-tool connectivity canary now.",
            tools=(tool,),
            parallel_tool_calls=False,
            tool_choice={"type": "function", "name": "sentinel_smoke_ok"},
            max_output_tokens=_SMOKE_MAX_OUTPUT_TOKENS,
            timeout_seconds=30.0,
            store=False,
            reasoning_effort="low",
            text_verbosity="low",
            max_tool_calls=1,
        )
    )
    problems: list[str] = []
    if response.status != "completed":
        problems.append(f"response status was {response.status!r}")
    if not response.response_id:
        problems.append("response ID was absent")
    if not response.request_id:
        problems.append("request ID was absent")
    if not response.provider_model or not is_gpt56_terra_model(response.provider_model):
        problems.append("provider-returned model was absent or not GPT-5.6 Terra")
    if response.usage_error:
        problems.append(f"usage accounting was invalid: {response.usage_error}")
    if response.usage.output_tokens > _SMOKE_MAX_OUTPUT_TOKENS:
        problems.append("reported output tokens exceeded the request ceiling")
    if response.text.strip():
        problems.append("model returned narrative text instead of only the forced tool call")
    if len(response.function_calls) != 1:
        problems.append("model did not return exactly one typed tool call")
    else:
        call = response.function_calls[0]
        if not call.arguments_valid:
            problems.append(f"tool arguments were invalid: {call.parse_error}")
        if call.name != "sentinel_smoke_ok" or call.arguments != {"token": _SMOKE_TOKEN}:
            problems.append("typed tool name or fixed arguments did not match")
    if problems:
        raise ModelProviderError("; ".join(problems))

    payload = {
        "ok": True,
        "qualification": "NONQUALIFYING_CONNECTIVITY_SMOKE",
        "forensic_evidence_read": False,
        "proof_bundle_created": False,
        "provider_requests": 1,
        "requested_model": model_id,
        "provider_model": response.provider_model,
        "response_id": response.response_id,
        "request_id": response.request_id,
        "status": response.status,
        "typed_tool_call_valid": True,
        "store": False,
        "max_output_tokens": _SMOKE_MAX_OUTPUT_TOKENS,
        "usage": asdict(response.usage),
        "secrets_printed": False,
        "does_not_prove": [
            "a completed forensic lifecycle",
            "semantic forensic accuracy",
            "Windows/DC01 native-tool parity",
            "eligibility for --require-live-gpt56",
        ],
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("OPENAI SMOKE: PASS")
        print("Qualification: NONQUALIFYING_CONNECTIVITY_SMOKE")
        print(f"Requested model: {model_id}")
        print(f"Provider model: {response.provider_model}")
        print("Responses calls: 1")
        print("Typed tool call: PASS")
        print("Proof bundle: not created")
        print("Forensic evidence: not read")
    return EXIT_COMPLETE


def _profile(evidence: Path, *, mount: bool, json_output: bool) -> int:
    stream = None if json_output else sys.stdout
    with EvidenceSession(evidence, mount=mount, case_card_stream=stream) as session:
        profile = session.profile()
        final_hashes = session.verify_custody()
    if final_hashes != profile.hashes:
        raise CustodyError("profile custody receipts changed namespace or content")
    if json_output:
        print(
            json.dumps(
                {
                    "profile": profile.public_dict(),
                    "custody": {"match": True, "hashes": final_hashes},
                    "openai_called": False,
                    "mount_requested": mount,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("Custody recheck: PASS")
        print("OpenAI calls: 0")
        if not mount and profile.disk_items:
            print("Tip: rerun with --mount to include read-only mounted-disk capabilities.")
    return EXIT_COMPLETE


def _interactive_terminal() -> bool:
    """Return whether an operator can see and answer the paid-launch gate."""

    stdin_isatty = getattr(sys.stdin, "isatty", None)
    stdout_isatty = getattr(sys.stdout, "isatty", None)
    return bool(
        callable(stdin_isatty) and stdin_isatty() and callable(stdout_isatty) and stdout_isatty()
    )


def _set_run_model(rehearsal: bool) -> None:
    """Point THIS process at the chosen model, explicitly and unambiguously.

    The launch card is the only model authority for interactive runs, so a
    stale environment variable from an older bootstrap can never silently pick
    the expensive model. Process scope only - nothing is persisted.
    """

    if rehearsal:
        os.environ["UNCHAINED_ALLOW_TEST_MODEL"] = "1"
        os.environ["UNCHAINED_MODEL"] = "gpt-5.6-terra"
    else:
        os.environ.pop("UNCHAINED_ALLOW_TEST_MODEL", None)
        os.environ["UNCHAINED_MODEL"] = "gpt-5.6"


def _launch_menu(caps_profile: str) -> str | None:
    """THE one pre-spend menu: model, depth, ceilings, and confirmation on a
    single card. 1 = LAUNCH, 2 = switch depth, 3 = switch model, Q = quit -
    no question is ever asked twice, and each switch redraws the same card.

    Starts on the cheaper Terra rehearsal (recommended first run); 3 flips to the
    official Sol run. Returns the final caps profile on launch, or None on
    cancel. Enter alone re-asks - an accidental keypress can never start a
    paid run.
    """

    from .onboarding import render_launch_gate

    rehearsal = True
    while True:
        _set_run_model(rehearsal)
        caps = CapConfig.from_env(caps_profile)
        print()
        render_launch_gate(caps_profile, caps, stream=sys.stdout)
        try:
            answer = input("  > Pick 1, 2, 3, or Q: ").strip().lower()
        except (EOFError, OSError):
            return None
        if answer in ("1", "launch", "l", "go", "y", "yes"):
            return caps_profile
        if answer == "2":
            caps_profile = "default" if caps_profile == "strict" else "strict"
            continue
        if answer == "3":
            rehearsal = not rehearsal
            continue
        if answer in ("q", "quit", "cancel", "n", "no"):
            return None
        print("     (1 = LAUNCH - 2 = switch depth - 3 = switch model - Q = quit)")


def _onboard(
    evidence: Path | None,
    *,
    mount: bool,
    caps_profile: str,
    launch: bool,
    json_output: bool,
    no_color: bool,
) -> int:
    """Run the local profile-first onboarding and optional explicit launch gate."""

    caps = CapConfig.from_env(caps_profile)
    if launch and evidence is None:
        raise ValueError("--launch requires one evidence file or folder")
    if launch and json_output:
        raise ValueError("--launch cannot be combined with --json")
    if launch and not _interactive_terminal():
        raise ValueError(
            "--launch requires an interactive terminal; use 'sentinel run' only when "
            "automation has separately authorized a paid run"
        )

    if evidence is None:
        # On a real terminal, the welcome is just the FIRST screen of one
        # self-driving flow: welcome -> ask the case -> card -> depth -> launch.
        # Non-interactive callers (JSON, pipes, CI) still get the static welcome.
        if not json_output and _interactive_terminal():
            return _guided(mount=mount, caps_profile=caps_profile, no_color=no_color)
        if json_output:
            print(json.dumps(welcome_payload(caps_profile, caps), indent=2, sort_keys=True))
        else:
            render_welcome(
                caps_profile=caps_profile,
                caps=caps,
                stream=sys.stdout,
                no_color=no_color,
            )
        return EXIT_COMPLETE

    if not json_output:
        # A specific case skips the teaching welcome (that's for bare `onboard`).
        # One compact line, then straight to the verified card.
        console = Console(sys.stdout)
        if console.enabled:
            console.banner("U N C H A I N E D", "One case, profiled locally before any model call.")
            console.step("bounded local probes - SHA-256 custody - zero OpenAI calls")
        else:
            print("UNCHAINED - profiling one case locally (zero OpenAI calls)...", flush=True)

    session = EvidenceSession(evidence, mount=mount, case_card_stream=None)
    with session:
        profile = session.profile()
        final_hashes = session.verify_custody()
    mount_released = session.close()
    if not mount_released:
        raise CustodyError("read-only mount release could not be positively verified")
    if final_hashes != profile.hashes:
        raise CustodyError("profile custody receipts changed namespace or content")
    assessment = assess_profile(profile)

    if json_output:
        print(
            json.dumps(
                profile_payload(
                    profile,
                    assessment,
                    caps_profile=caps_profile,
                    caps=caps,
                    custody_match=True,
                    mount_requested=mount,
                    mount_released=mount_released,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        # When a launch is happening, the one launch card and the final key
        # step come next in THIS same command, so use the guided footer instead
        # of printing a separate "sentinel onboard ... --launch" command that
        # would read as a redundant, contradictory extra step.
        render_profile(
            profile,
            assessment,
            caps_profile=caps_profile,
            caps=caps,
            custody_match=True,
            mount_requested=mount,
            mount_released=mount_released,
            stream=sys.stdout,
            no_color=no_color,
            guided=launch,
        )

    if not assessment.profile_ready:
        return EXIT_INVALID
    if not launch:
        return EXIT_COMPLETE
    chosen_profile = _launch_menu(caps_profile)
    if chosen_profile is None:
        print("Launch cancelled. The local profile remains valid; OpenAI calls: 0.")
        return EXIT_COMPLETE
    # The ONE final step before any money is spent: the key card with the
    # hidden paste always offered - never a silent "no paste needed" skip.
    if not _final_key_gate():
        print("Launch cancelled at the key step. Nothing was sent; OpenAI calls: 0.")
        return EXIT_COMPLETE
    print("Confirmation accepted. Starting the bounded GPT-5.6 lifecycle...")
    return run_cli(
        evidence,
        chosen_profile,
        show_case_card=False,
        mount_evidence=mount,
        show_banner=False,
    )


_SECRET_LIKE = re.compile(r"^[A-Za-z0-9_\-]{20,}$")


def _looks_like_pasted_secret(text: str) -> bool:
    """True when a long, high-entropy, separator-free token is pasted where a
    path or menu answer is expected - almost certainly an API key. Shape-based
    and vendor-agnostic; real paths carry separators and menu answers are short.
    """

    token = (text or "").strip()
    if len(token) < 20 or not _SECRET_LIKE.match(token):
        return False
    return any(char.isalpha() for char in token) and any(char.isdigit() for char in token)


def _prompt_evidence_path() -> Path | None:
    """Ask the one question a run needs - where the evidence is - and return a
    resolved path, or None to quit. Re-asks on a bad path; a pasted key is
    discarded, never used, so a fat-fingered credential can't leak into a path.
    """

    print()
    print("  -- YOUR CASE " + "-" * 52)
    print("     Paste the path to ONE case's evidence: a folder holding a")
    print("     memory image and/or a disk image from one host (a memory+disk")
    print("     PAIR is welcome). ZIP archives are fine - I can extract them")
    print("     for you. Unchained never downloads evidence itself; for the")
    print("     public DC01 practice case, the installer walks you to it.")
    print("     Example: C:\\Evidence\\CASE-A" + " " * 18 + "q = quit")
    print("  " + "-" * 65)
    while True:
        try:
            raw = input("  > Paste the evidence path (folder or file): ")
        except (EOFError, OSError):
            return None
        answer = (raw or "").strip().strip('"').strip("'").strip()
        if answer.lower() in ("q", "quit", "exit"):
            return None
        if not answer:
            print("  Type the path to one case folder (or q to quit).")
            continue
        if _looks_like_pasted_secret(answer):
            print(
                "  That looked like an API key pasted at the path prompt - discarded "
                "(never used, stored, or logged). Paste keys only at the hidden key "
                "step, and revoke it if it was real."
            )
            continue
        candidate = Path(answer).expanduser()
        if not candidate.exists():
            print(f"  Not found: {answer}. Check the path and try again (or q to quit).")
            continue
        return candidate


def _safe_extract_zip(zip_path: Path, destination: Path) -> int:
    """Extract one ZIP into ``destination`` with zip-slip protection.

    Every member path is validated (no absolute paths, no ``..``, no drive
    prefix) before a byte is written, and the total uncompressed size must fit
    the free space with 1 GiB headroom. Returns the number of files extracted.
    """

    import shutil
    import zipfile
    from pathlib import PurePosixPath

    extracted = 0
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.infolist()
        total_bytes = sum(m.file_size for m in members if not m.is_dir())
        free = shutil.disk_usage(destination).free
        if total_bytes > max(0, free - 1_073_741_824):
            raise ValueError(
                f"not enough free space to extract {zip_path.name} ({total_bytes:,} bytes needed)"
            )
        for member in members:
            if member.is_dir():
                continue
            name = member.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if (
                not pure.parts
                or pure.is_absolute()
                or any(part == ".." for part in pure.parts)
                or ":" in pure.parts[0]
            ):
                raise ValueError(f"unsafe archive member path: {member.filename!r}")
            target = destination.joinpath(*pure.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, open(target, "wb") as sink:
                shutil.copyfileobj(source, sink, 16 * 1024 * 1024)
            extracted += 1
    return extracted


def _offer_zip_extraction(evidence: Path, profile: EvidenceProfile) -> Path | None:
    """When a not-ready case contains ZIP archives, offer to extract them into a
    clean sibling case folder and return that folder for re-profiling.

    Local and free; nothing leaves the machine and the original archives are
    untouched. Returns None when there is nothing to extract, the user
    declines, or extraction fails.
    """

    import zipfile

    zips = [
        item.path
        for item in profile.items
        if item.health == "archive-not-unpacked" and item.path.suffix.casefold() == ".zip"
    ]
    if not zips:
        return None
    print()
    print(f"  I found {len(zips)} ZIP archive(s) in this case. Archives are never")
    print("  analyzed in place, but I can extract them into a clean case folder")
    print("  right here - local and free; nothing leaves this machine.")
    try:
        answer = input("  Extract now and re-profile? [Enter = yes - n = no]: ")
    except (EOFError, OSError):
        return None
    if answer.strip().lower() in ("n", "no", "q", "quit"):
        return None
    root = evidence if evidence.is_dir() else evidence.parent
    destination = root.parent / f"{root.name}-extracted"
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"  Could not create the extraction folder: {exc}")
        return None
    total_files = 0
    for zip_path in zips:
        packed_gib = zip_path.stat().st_size / 1024**3
        print(
            f"  Extracting {zip_path.name} ({packed_gib:.2f} GiB packed) - "
            "large images take a few minutes..."
        )
        try:
            total_files += _safe_extract_zip(zip_path, destination)
        except (ValueError, OSError, zipfile.BadZipFile) as exc:
            print(f"  Could not extract {zip_path.name}: {exc}")
            return None
    print(f"  Extracted {total_files} file(s) into: {destination}")
    print("  Re-profiling the extracted case...")
    return destination


def _final_key_gate() -> bool:
    """The ONE final step between the launch card and the pipeline: the key
    card with the hidden paste always offered. Enter keeps a saved key, a paste
    (never echoed) replaces it for this and future runs, and q cancels. The
    pasted key also overrides any inherited OPENAI_API_KEY for this process, so
    the key just pasted is always the key the run uses."""

    from .onboarding import render_key_card

    present, source = openai_api_key_status()
    label = _KEY_SOURCE_LABELS.get(source or "", source or "a configured source")
    render_key_card(present, label if present else None, stream=sys.stdout)
    import getpass

    prompt = (
        "  > Enter = use saved key - or paste a new key (input stays hidden): "
        if present
        else "  > Paste your OpenAI API key (input stays hidden) - Enter/q cancels: "
    )
    try:
        entered = getpass.getpass(prompt).strip()
    except (EOFError, OSError):
        return False
    if not entered:
        return present
    if entered.lower() in ("q", "quit", "exit"):
        return False
    if "\n" in entered or "\r" in entered or len(entered.encode("utf-8")) > 512:
        print("  That does not look like one single-line API key; launch cancelled.")
        return False
    _store_key_material(entered)
    os.environ["OPENAI_API_KEY"] = entered
    entered = ""
    print("  Key saved with hidden input - using it for this run.")
    return True


def _guided(*, mount: bool = False, caps_profile: str = "strict", no_color: bool = False) -> int:
    """The self-driving front door: one command from welcome to a live, verified
    run. Welcome -> ask the case (one question) -> local $0 card -> ONE launch
    card -> final key step (hidden paste) -> live lifecycle -> verify/view.

    No flags, no environment juggling: the launch card owns model AND depth on
    a single menu, and the key card is the ONE final step before the pipeline
    starts - Enter keeps a saved key, a hidden paste replaces a stale one right
    there. No question is ever asked twice, and nothing is spent before both
    the explicit 1 = LAUNCH confirmation and the key step pass.
    """

    caps = CapConfig.from_env(caps_profile)
    if not _interactive_terminal():
        render_welcome(caps_profile=caps_profile, caps=caps, stream=sys.stdout, no_color=no_color)
        return EXIT_COMPLETE

    render_welcome(caps_profile=caps_profile, caps=caps, stream=sys.stdout, no_color=no_color)

    # Step 1-2: one question, then the local verified case card (no key, $0).
    # ``pending`` carries a path produced inside the loop (e.g. a freshly
    # extracted case folder) so it is profiled next without re-asking.
    pending: Path | None = None
    while True:
        evidence = pending or _prompt_evidence_path()
        pending = None
        if evidence is None:
            print("No case selected. Nothing was read; OpenAI calls: 0.")
            return EXIT_COMPLETE

        console = Console(sys.stdout)
        if console.enabled:
            console.phase("LOCAL PROFILE")
            console.step("bounded content probes - SHA-256 custody - zero OpenAI calls")
        else:
            print("Profiling this case locally (zero OpenAI calls)...", flush=True)

        try:
            session = EvidenceSession(evidence, mount=mount, case_card_stream=None)
            with session:
                profile = session.profile()
                final_hashes = session.verify_custody()
            mount_released = session.close()
        except (EvidenceError, OSError, ValueError) as exc:
            print(f"  Could not profile that case: {type(exc).__name__}. Pick another path.")
            continue
        if not mount_released:
            raise CustodyError("read-only mount release could not be positively verified")
        if final_hashes != profile.hashes:
            raise CustodyError("profile custody receipts changed namespace or content")

        assessment = assess_profile(profile)
        render_profile(
            profile,
            assessment,
            caps_profile=caps_profile,
            caps=caps,
            custody_match=True,
            mount_requested=mount,
            mount_released=mount_released,
            stream=sys.stdout,
            no_color=no_color,
            guided=True,
        )
        if assessment.profile_ready:
            break
        # A folder of ZIP archives is the most common first-run stumble; offer
        # to extract them into a clean sibling case folder and re-profile.
        pending = _offer_zip_extraction(evidence, profile)
        if pending is not None:
            continue
        print("  This case is not route-ready yet - fix the blockers above, or pick another.")
        try:
            again = input("  Try another case? [Enter = yes - q = quit]: ").strip().lower()
        except (EOFError, OSError):
            return EXIT_INVALID
        if again in ("q", "quit", "exit", "n", "no"):
            return EXIT_INVALID

    # Step 3: ONE launch card - model, depth, ceilings, and confirmation on the
    # same menu (1 = LAUNCH, 2 = depth, 3 = model, Q = quit). The card owns the
    # model choice, so no earlier step ever asks the same question.
    chosen_profile = _launch_menu(caps_profile)
    if chosen_profile is None:
        print("Launch cancelled. The local profile remains valid; OpenAI calls: 0.")
        return EXIT_COMPLETE

    # Step 4: the ONE final step before money is spent - the key card with the
    # hidden paste always offered. Enter keeps a saved key, a paste replaces a
    # stale or exhausted one right here, q cancels. Never a silent skip.
    if not _final_key_gate():
        print("Launch cancelled at the key step. Nothing was sent; OpenAI calls: 0.")
        return EXIT_COMPLETE
    print("Confirmation accepted. Starting the bounded GPT-5.6 lifecycle...")
    return run_cli(
        evidence, chosen_profile, show_case_card=False, mount_evidence=mount, show_banner=False
    )


_RUN_CLOCK: list[float] = []


def _elapsed() -> str | None:
    if not _RUN_CLOCK:
        return None
    seconds = time.monotonic() - _RUN_CLOCK[0]
    return f"{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def _partial_next_step(reason: str) -> str:
    """Honest next action for a PARTIAL run, keyed off the full failure text.

    The panel's Why line truncates to 160 characters, which can cut the reason
    before the provider's machine code appears, so this decision reads the
    untruncated text.
    """

    if "insufficient_quota" in reason:
        return (
            "the OpenAI account behind this key has no API credit - billing, "
            "not code; add credit or switch keys, then re-run"
        )
    return "re-run when the reported condition is resolved"


def _progress(message: str) -> None:
    console = Console(sys.stderr)
    if console.enabled:
        console.step(message, elapsed=_elapsed())
    else:
        print(f"[sentinel] {message}", file=sys.stderr, flush=True)


def _stage(label: str) -> None:
    """Announce one numbered architecture stage as a banner on the live screen."""

    console = Console(sys.stderr)
    if console.enabled:
        console.phase(label)
    else:
        print(f"[sentinel] == {label} ==", file=sys.stderr, flush=True)


class _AuditNarrator:
    """Display-only proxy over :class:`AuditLog` for an interactive terminal.

    Every call is forwarded to the wrapped audit log unchanged before any
    narration happens, so the appended record - not the narration - remains the
    sole authority. A narration failure can never alter or abort the run.
    """

    # Numbered to the architecture flow so the live screen reads step-by-step.
    # Keys are the exact model-request phase strings emitted by the agent.
    _PHASE_LABELS = {
        "opening": "STEP 2  OPENING BOOK - GPT-5.6 selects up to 12 typed tools",
        "investigate": "STEP 5  ADAPTIVE LOOP - PLAN -> ACT -> OBSERVE -> UPDATE (GPT-5.6)",
        "investigation-finalize": "STEP 6  FORCED SERIALIZATION - strict findings, no tools",
        "judge": "STEP 8  FRESH JUDGE - preserve or downgrade, never promote",
        "report": "STEP 9  STRUCTURED REPORT DRAFT - GPT-5.6 narrative",
    }

    def __init__(self, audit: AuditLog, console: Console) -> None:
        self._audit = audit
        self._console = console
        self._phase_seen: str | None = None
        self._execution_announced = False
        self._proposed: dict[str, dict[str, object]] = {}

    def __getattr__(self, name: str) -> object:
        return getattr(self._audit, name)

    def _narrate(self, render: object) -> None:
        if not self._console.enabled:
            return
        with contextlib.suppress(Exception):
            render()  # type: ignore[operator]

    def _phase_header(self, phase: str) -> None:
        if phase == self._phase_seen:
            return
        self._phase_seen = phase
        label = self._PHASE_LABELS.get(phase, phase.replace("_", " ").title())
        self._console.phase(label)

    def append(self, event_type: str, payload: object, *, actor: str = "runner") -> object:
        record = self._audit.append(event_type, payload, actor=actor)

        def render() -> None:
            if event_type == "custody.initial.completed" and isinstance(payload, dict):
                count = payload.get("file_count")
                self._console.ok(f"initial SHA-256 custody sealed over {count} file(s)")
            elif event_type == "custody.final.completed":
                self._console.ok("final custody re-hash matched the baseline")
            elif event_type == "opening.completed" and isinstance(payload, dict):
                selected = payload.get("selected")
                executed = payload.get("executed")
                rejected = payload.get("rejected")
                self._console.ok(
                    f"opening book: {selected} selected - {executed} executed - "
                    f"{rejected} rejected - all-or-none validated"
                )
                self._console.phase(
                    "STEP 4  CASE LEDGER - receipts + bounded typed observations "
                    "become the case packet"
                )
            elif event_type == "investigator.notes.updated" and isinstance(payload, dict):
                turn = payload.get("turn")
                update = str(payload.get("case_ledger_update", "")).strip().replace("\n", " ")
                if update:
                    self._console.detail(f"turn {turn} reasoning: {update[:120]}")
            elif event_type == "investigator.action" and isinstance(payload, dict):
                turn = payload.get("turn")
                self._console.step(f"turn {turn}: one typed action", elapsed=_elapsed())
            elif event_type == "investigator.finished" and isinstance(payload, dict):
                findings = [f for f in payload.get("findings") or [] if isinstance(f, dict)]
                self._proposed = {str(f.get("finding_id")): f for f in findings}
                self._console.ok(
                    f"typed DONE accepted - {len(findings)} structured finding(s) proposed"
                )
                for finding in findings:
                    self._console.detail(
                        f"● {finding.get('finding_id')} - {finding.get('proposed_status')} - "
                        f"{finding.get('severity')} - {str(finding.get('title', ''))[:56]}"
                    )
                self._console.phase(
                    "STEP 7  EXACT SPAN RESOLUTION - quote -> artifact SHA-256 + byte range"
                )
            elif event_type == "judge.completed" and isinstance(payload, dict):
                for verdict in payload.get("verdicts") or []:
                    if not isinstance(verdict, dict):
                        continue
                    fid = str(verdict.get("finding_id"))
                    status = str(verdict.get("status"))
                    proposed = str(self._proposed.get(fid, {}).get("proposed_status", "?"))
                    rationale = str(verdict.get("rationale", ""))[:48]
                    if status == proposed:
                        self._console.ok(f"{fid} - {proposed} → preserved - {rationale}")
                    else:
                        self._console.warn(
                            f"{fid} - {proposed} → downgraded to {status} - {rationale}"
                        )
            elif event_type == "report.completed" and isinstance(payload, dict):
                report_bytes = payload.get("report_bytes")
                digest = str(payload.get("report_sha256", ""))[:12]
                self._console.phase(
                    "STEP 10  DETERMINISTIC RENDERER - authoritative rows, verdicts, citations"
                )
                self._console.ok(
                    f"deterministic report sealed - {report_bytes:,} bytes - sha256 {digest}…"
                )
            elif event_type == "judge.started":
                self._phase_header("judge")
            elif event_type == "report.started":
                self._phase_header("report")
            elif event_type == "cap.fired" and isinstance(payload, dict):
                self._console.warn(f"hard cap fired: {payload.get('kind')}")
            elif event_type.startswith("model.retry"):
                self._console.warn("transient provider error; bounded audited retry")
            elif event_type == "model.attempt.error" and isinstance(payload, dict):
                if not payload.get("retryable") and "insufficient_quota" in str(
                    payload.get("error", "")
                ):
                    self._console.warn(
                        "OpenAI account has no API credit (insufficient_quota) - "
                        "terminal billing stop, no retry"
                    )

        self._narrate(render)
        return record

    def model_request(self, **kwargs: object) -> None:
        self._audit.model_request(**kwargs)  # type: ignore[arg-type]

        def render() -> None:
            phase = str(kwargs.get("phase", ""))
            self._phase_header(phase)
            model = kwargs.get("requested_model", "GPT-5.6")
            self._console.step(f"↑ dispatching bounded {model} request", elapsed=_elapsed())

        self._narrate(render)

    def model_response(self, **kwargs: object) -> None:
        self._audit.model_response(**kwargs)  # type: ignore[arg-type]

        def render() -> None:
            response = kwargs.get("response")
            usage = getattr(response, "usage", None)
            tokens_in = getattr(usage, "input_tokens", 0)
            tokens_out = getattr(usage, "output_tokens", 0)
            provider = getattr(response, "provider_model", None) or "response"
            running = kwargs.get("running_cost_usd", 0.0)
            self._console.detail(
                f"↓ {provider} - in {tokens_in:,} / out {tokens_out:,} tokens - "
                f"${float(running):.4f} est. total"
            )

        self._narrate(render)

    def tool_started(self, call_id: str, name: str, arguments: object, **kwargs: object) -> None:
        self._audit.tool_started(call_id, name, arguments, **kwargs)  # type: ignore[arg-type]

        def render() -> None:
            if not self._execution_announced:
                self._execution_announced = True
                self._console.phase(
                    "STEP 3  PARALLEL TYPED EXECUTION - atomic caps, owned paths, "
                    "receipts bound to evidence ID + digest"
                )
            self._console.step(f"⚒ {name} executing", elapsed=_elapsed())

        self._narrate(render)

    def tool_completed(self, result: object, **kwargs: object) -> None:
        self._audit.tool_completed(result, **kwargs)  # type: ignore[arg-type]

        def render() -> None:
            name = getattr(result, "tool_name", "tool")
            status = getattr(result, "status", "?")
            byte_count = len(getattr(result, "output", "").encode("utf-8", "replace"))
            duration = getattr(result, "duration_ms", 0)
            line = f"{name} - {status} - {byte_count:,} bytes retained - {duration:,} ms"
            if status == "success":
                self._console.ok(line)
            else:
                self._console.warn(line)

        self._narrate(render)


def _view(run_directory: Path, *, no_open: bool) -> int:
    from .verify import verify_run

    result = verify_run(run_directory)
    if not result.passed:
        print("Viewer refused: proof-bundle verification failed.", file=sys.stderr)
        for error in result.errors:
            print(f"- {error}", file=sys.stderr)
        return EXIT_FATAL
    if result.terminal_status == RunStatus.COMPLETE.value:
        result = verify_run(run_directory, require_complete=True)
        if not result.passed:
            print(
                "Viewer refused: COMPLETE bundle failed strict lifecycle verification.",
                file=sys.stderr,
            )
            for error in result.errors:
                print(f"- {error}", file=sys.stderr)
            return EXIT_FATAL
    viewer = run_directory.expanduser().resolve(strict=True) / "viewer.html"
    if not viewer.is_file() or viewer.is_symlink():
        print("Viewer refused: verified bundle has no regular viewer.html.", file=sys.stderr)
        return EXIT_INVALID
    print(f"Verified viewer: {viewer}")
    if not no_open:
        import webbrowser

        if not webbrowser.open(viewer.as_uri()):
            print("The browser did not accept the viewer URL; open the printed path manually.")
    return EXIT_COMPLETE


def _run_directory(evidence: Path) -> tuple[str, Path]:
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    base = Path.cwd().resolve()
    resolved = evidence.expanduser().resolve(strict=False)
    evidence_directory = resolved if resolved.is_dir() else resolved.parent
    if base == evidence_directory or base.is_relative_to(evidence_directory):
        base = evidence_directory.parent
    directory = base / "unchained-runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o700)
    return run_id, directory


def _fatal_report(reason: str, profile: EvidenceProfile | None = None) -> str:
    route = defang_untrusted_inline(
        "not established" if profile is None else f"{profile.os} / {profile.shape}"
    )
    safe_reason = defang_untrusted_inline(reason)
    return f"""# Unchained DFIR Report - FATAL

The run aborted because a deterministic safety or runtime invariant failed.

- Evidence route: `{route}`
- Failure: {safe_reason}

## Limitations

No complete investigative result is asserted. This system has no deterministic
validator by design. Consult `audit.jsonl` and independently re-establish
evidence custody before relying on any preserved observations.
"""


def _invalid_report(reason: str) -> str:
    safe_reason = defang_untrusted_inline(reason)
    return f"""# Unchained DFIR Report - INVALID

The input or configuration did not pass preflight: {safe_reason}

No investigation was claimed and no forensic finding was produced.
"""


def _cap_report(error: CapExceeded, profile: EvidenceProfile | None) -> str:
    route = defang_untrusted_inline(
        "not established" if profile is None else f"{profile.os} / {profile.shape}"
    )
    detail = defang_untrusted_inline(error.detail)
    return f"""# Unchained DFIR Report - PARTIAL

The hard cap `{error.kind.value}` fired and the run stopped gracefully.

- Evidence route: `{route}`
- Stop detail: {detail}

## Limitations

Required investigation, judge, or report phases may not have run. This system
has no deterministic validator by design. Review `audit.jsonl` before relying
on any preserved result.
"""


def _terminal_exit(run: AgentRun) -> int:
    return EXIT_COMPLETE if run.status is RunStatus.COMPLETE else EXIT_PARTIAL


def _tool_output_artifacts(
    run_directory: Path,
    entries: list[dict[str, object]],
) -> list[ArtifactRef]:
    """Collect only blobs explicitly referenced by audited tool completions."""

    by_path: dict[str, ArtifactRef] = {}
    for entry in entries:
        if entry.get("event_type") != "tool.completed":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            raise ArtifactError("tool.completed payload is not an object")
        receipt = payload.get("output_artifact")
        if not isinstance(receipt, dict):
            raise ArtifactError("tool.completed omitted output_artifact")
        path = str(receipt.get("path") or "")
        media_type = str(receipt.get("media_type") or "application/octet-stream")
        encoding = receipt.get("encoding")
        if encoding is not None and not isinstance(encoding, str):
            raise ArtifactError("tool-output encoding is not a string or null")
        actual = artifact_ref_from_existing(
            run_directory,
            path,
            role="tool-output",
            media_type=media_type,
            encoding=encoding,
        )
        claimed_hash = receipt.get("sha256") or payload.get("output_sha256")
        claimed_bytes = receipt.get("bytes") or payload.get("output_bytes")
        if actual.sha256 != claimed_hash or actual.bytes != claimed_bytes:
            raise ArtifactError(f"audited tool artifact does not match retained bytes: {path}")
        existing = by_path.get(path)
        if existing is not None and existing != actual:
            raise ArtifactError(f"conflicting duplicate tool artifact receipt: {path}")
        by_path[path] = actual
    return [by_path[path] for path in sorted(by_path)]


def run_cli(
    evidence_path: Path,
    caps_profile: str,
    *,
    show_case_card: bool = True,
    mount_evidence: bool = True,
    show_banner: bool = True,
) -> int:
    """Execute, close, manifest, and immediately verify one isolated run.

    ``show_banner=False`` is passed by the guided/onboard flows, which already
    printed the UNCHAINED banner - so one screen never shows it twice.
    """

    _RUN_CLOCK.clear()
    _RUN_CLOCK.append(time.monotonic())
    stderr_console = Console(sys.stderr)
    if show_banner and stderr_console.enabled:
        stderr_console.banner("U N C H A I N E D", "Unchained reasoning. Chained evidence.")
        stderr_console.detail("GPT-5.6 chooses where to look; code proves what happened.")
    if cheap_model_opt_in():
        configured = os.getenv("UNCHAINED_MODEL", "a non-Sol GPT-5.6 model")
        stderr_console.warn(
            f"TEST MODEL MODE: running on {configured}, not Sol. This validates the "
            "pipeline live and cheaply; the bundle is NONQUALIFYING and cannot pass "
            "--require-live-gpt56. Cost is Sol-priced (an upper bound)."
        )
    _progress("checking GPT-5.6 configuration before evidence I/O")
    model = OpenAIResponsesModel()
    run_id, run_directory = _run_directory(evidence_path)
    audit_path = run_directory / "audit.jsonl"
    store = ArtifactStore(run_directory)
    session: EvidenceSession | None = None
    profile: EvidenceProfile | None = None
    investigation: AgentRun | None = None
    registry: ToolRegistry | None = None
    cap_config: CapConfig | None = None
    terminal_status = RunStatus.FATAL
    exit_code = EXIT_FATAL
    report = _fatal_report("run did not start")
    terminal_reason: str | None = "run did not start"
    custody_required = False
    mount_released = True
    budget: RunBudget | None = None
    root_artifacts: list[ArtifactRef] = []

    with AuditLog(audit_path, run_id) as audit_log:
        audit = _AuditNarrator(audit_log, stderr_console)
        audit.append(
            "run.created",
            {
                "run_directory": ".",
                "evidence_input_label": "CASE-A",
                "evidence_input_kind": "directory" if evidence_path.is_dir() else "file",
                "caps_profile": caps_profile,
                "absolute_paths_recorded": False,
            },
        )
        try:
            cap_config = CapConfig.from_env(caps_profile)
            budget = RunBudget(cap_config)
            _stage("STEP 1  PROFILE + ROUTE - classify, hash (EID-keyed SHA-256), capability truth")
            _progress("profiling and hashing the evidence set")
            audit.append("caps.configured", asdict(cap_config))
            session = EvidenceSession(
                evidence_path,
                budget=budget,
                mount=mount_evidence,
                case_card_stream=sys.stdout if show_case_card else None,
            )
            audit.append("custody.initial.started", {})
            profile = session.profile()
            custody_required = True
            audit.append(
                "custody.initial.completed",
                {
                    "hashes": profile.hashes,
                    "sizes": profile.sizes,
                    "file_count": len(profile.items),
                },
            )
            audit.append("profile.completed", profile.public_dict())
            _progress(
                f"route ready: {profile.os}/{profile.shape}; {len(profile.items)} evidence item(s)"
            )

            if profile.shape == "unknown":
                raise EvidenceDiscoveryError(
                    "no supported memory, disk, or log content was recognized"
                )
            if not any(item.available for item in profile.items):
                raise EvidenceDiscoveryError("all recognized evidence routes are unavailable")

            budget.check()
            _progress("loading route-valid typed forensic tools")
            try:
                registry = ToolRegistry.from_reference(profile, audit, budget)
            except RuntimeError as exc:
                raise ValueError(f"forensic tool readiness failed: {exc}") from exc
            agent = UnchainedAgent(model=model, tools=registry, audit=audit, budget=budget)
            _progress(
                "starting GPT-5.6 opening book; bounded profile and observations may be sent "
                "to OpenAI, original evidence bytes stay local"
            )
            investigation = agent.run(profile)
            _progress(f"model pipeline finished with status {investigation.status.value}")
            terminal_status = investigation.status
            exit_code = _terminal_exit(investigation)
            report = investigation.report_markdown
            terminal_reason = investigation.partial_reason
        except CapExceeded as exc:
            terminal_status = RunStatus.PARTIAL
            exit_code = EXIT_PARTIAL
            report = _cap_report(exc, profile)
            terminal_reason = str(exc)
            audit.append(
                "cap.fired",
                {
                    "kind": exc.kind.value,
                    "detail": exc.detail,
                    "budget": exc.snapshot.public_dict(),
                },
            )
        except CustodyError as exc:
            terminal_status = RunStatus.FATAL
            exit_code = EXIT_FATAL
            report = _fatal_report(str(exc), profile)
            terminal_reason = str(exc)
            audit.append(
                "custody.mismatch",
                {"match": False, "error": str(exc), "status": RunStatus.FATAL.value},
            )
        except (EvidenceDiscoveryError, ValueError) as exc:
            terminal_status = RunStatus.INVALID
            exit_code = EXIT_INVALID
            report = _invalid_report(str(exc))
            terminal_reason = f"{type(exc).__name__}: {exc}"
            audit.append(
                "run.preflight_failed",
                {"status": terminal_status.value, "error": terminal_reason},
            )
        except EvidenceError as exc:
            terminal_status = RunStatus.FATAL
            exit_code = EXIT_FATAL
            report = _fatal_report(str(exc), profile)
            terminal_reason = f"{type(exc).__name__}: {exc}"
            audit.append(
                "run.failed",
                {"status": terminal_status.value, "error": terminal_reason},
            )
        except KeyboardInterrupt:
            terminal_status = RunStatus.FATAL
            exit_code = EXIT_FATAL
            terminal_reason = "KeyboardInterrupt: run interrupted by operator"
            report = _fatal_report(terminal_reason, profile)
            audit.append(
                "run.interrupted",
                {"status": terminal_status.value, "error": terminal_reason},
            )
        except Exception as exc:  # noqa: BLE001 - preserve an auditable failed run
            terminal_status = RunStatus.FATAL
            exit_code = EXIT_FATAL
            terminal_reason = f"{type(exc).__name__}: {exc}"
            report = _fatal_report(terminal_reason, profile)
            audit.append(
                "run.failed",
                {"status": terminal_status.value, "error": terminal_reason},
            )
        finally:
            if session is not None:
                mount_released = session.close()

        if not mount_released:
            terminal_status = RunStatus.FATAL
            exit_code = EXIT_FATAL
            terminal_reason = "read-only evidence mount could not be released"
            report = _fatal_report(terminal_reason, profile)
            audit.append(
                "mount.release_failed",
                {"status": RunStatus.FATAL.value, "mount_released": False},
            )

        if custody_required and session is not None:
            _stage("STEP 11  CLOSE TOOLS/MOUNTS -> FINAL FULL SHA-256 CUSTODY CHECK")
            _progress("performing final full SHA-256 custody verification")
            audit.append("custody.final.started", {})
            try:
                final_hashes = session.verify_custody()
                audit.append(
                    "custody.final.completed",
                    {
                        "hashes": final_hashes,
                        "match": True,
                        "mount_released": mount_released,
                    },
                )
            except CustodyError as exc:
                terminal_status = RunStatus.FATAL
                exit_code = EXIT_FATAL
                terminal_reason = str(exc)
                report = _fatal_report(terminal_reason, profile)
                audit.append(
                    "custody.mismatch",
                    {"match": False, "error": str(exc), "status": RunStatus.FATAL.value},
                )

        cap_name = (
            investigation.cap.kind.value
            if investigation is not None and investigation.cap is not None
            else None
        )
        _stage("STEP 12  SEAL REPORT + STATIC VIEWER + CONTENT-ADDRESSED PROOF BUNDLE")
        try:
            report = report.rstrip() + "\n"
            report_ref = store.write_text(
                "report.md",
                report,
                role="report",
                media_type="text/markdown",
            )
            root_artifacts.append(report_ref)
            if profile is not None:
                root_artifacts.append(
                    store.write_json(
                        "profile.json",
                        profile.public_dict(),
                        role="evidence-profile",
                    )
                )
            caps_payload = asdict(cap_config) if cap_config is not None else {}
            environment = capture_environment(
                run_id=run_id,
                project_directory=Path(__file__).resolve().parents[2],
                requested_model=(
                    model.model_id if model is not None else os.getenv("UNCHAINED_MODEL")
                ),
                caps_profile=caps_profile,
                caps=caps_payload,
                tool_schemas=registry.schemas() if registry is not None else (),
            )
            root_artifacts.append(
                store.write_json("environment.json", environment, role="environment")
            )
            preterminal_entries = AuditLog.verify(audit_path)
            summary = build_summary(
                run_id=run_id,
                entries=preterminal_entries,
                status=terminal_status.value,
                exit_code=exit_code,
                profile=profile,
                cap=cap_name,
                reason=terminal_reason,
                mount_released=mount_released,
            )
            root_artifacts.append(store.write_json("summary.json", summary, role="summary"))
            viewer = render_viewer_html(
                run_id=run_id,
                status=terminal_status.value,
                profile=profile,
                summary=summary,
                report_markdown=report,
                audit_entries=preterminal_entries,
            )
            root_artifacts.append(
                store.write_text(
                    "viewer.html",
                    viewer,
                    role="proof-viewer",
                    media_type="text/html",
                )
            )
            for artifact in root_artifacts:
                audit.append("artifact.written", artifact.public_dict())
            audit.append(
                "run.completed",
                {
                    "status": terminal_status.value,
                    "exit_code": exit_code,
                    "report": "report.md",
                    "audit": "audit.jsonl",
                    "profile": "profile.json" if profile is not None else None,
                    "environment": "environment.json",
                    "summary": "summary.json",
                    "cap": cap_name,
                    "reason": terminal_reason,
                    "custody_baseline_established": custody_required,
                    "custody_final_check_performed": custody_required,
                    "mount_released": mount_released,
                },
            )
            AuditLog.verify(audit_path)
        except Exception as exc:
            audit.append(
                "bundle.finalization_failed",
                {"error_type": type(exc).__name__, "error": str(exc)[:2_000]},
            )
            raise

    entries = AuditLog.verify(audit_path)
    audit_ref = artifact_ref_from_existing(
        run_directory,
        "audit.jsonl",
        role="audit",
        media_type="application/x-ndjson",
    )
    tool_artifacts = _tool_output_artifacts(run_directory, entries)
    manifest = build_manifest(
        run_id=run_id,
        status=terminal_status.value,
        exit_code=exit_code,
        audit_ref=audit_ref,
        audit_entries=entries,
        artifacts=[*root_artifacts, *tool_artifacts],
    )
    write_manifest_pair(store, manifest)

    from .verify import verify_run

    _stage("STEP 13  OFFLINE LIFECYCLE, HASH, RECEIPT, AND SPAN VERIFICATION")
    verification = verify_run(
        run_directory,
        require_complete=terminal_status is RunStatus.COMPLETE,
        require_live_gpt56=terminal_status is RunStatus.COMPLETE,
    )
    if not verification.passed:
        print("Proof-bundle verification failed:", file=sys.stderr)
        for error in verification.errors:
            print(f"- {error}", file=sys.stderr)
        return EXIT_FATAL

    _progress("content-addressed proof bundle verified")
    # The closing panel answers the three questions every run ends on: what was
    # found, where the report is, and what to do next. On PARTIAL it explains
    # WHY honestly and never suggests a --require-complete verify that would
    # fail against this very bundle.
    complete = terminal_status is RunStatus.COMPLETE
    findings_list = list(investigation.findings) if investigation is not None else []
    verdict_list = list(investigation.verdicts) if investigation is not None else []
    verdict_counts: dict[str, int] = {}
    for verdict in verdict_list:
        status_label = str(verdict.public_dict().get("status", "?"))
        verdict_counts[status_label] = verdict_counts.get(status_label, 0) + 1
    findings_line = f"{len(findings_list)} structured finding(s)"
    if verdict_counts:
        findings_line += " -> judge: " + " / ".join(
            f"{count} {status}" for status, count in sorted(verdict_counts.items())
        )
    why_partial = ""
    next_step = ""
    if not complete:
        if investigation is not None and investigation.cap is not None:
            why_partial = (
                f"hard cap {investigation.cap.kind.value} fired - ceilings are hard "
                "stops, so the remaining phases were skipped"
            )
            next_step = (
                "press 2 on the launch card next run (HEAVY ceilings) for the full "
                "lifecycle, or raise MAX_TOTAL_TOKENS deliberately"
            )
        else:
            reason = investigation.partial_reason if investigation is not None else None
            raw_reason = reason or terminal_reason or "the run stopped early"
            why_partial = raw_reason[:160]
            next_step = _partial_next_step(raw_reason)
    verify_hint = (
        f'sentinel verify "{run_directory}" --require-complete'
        if complete
        else f'sentinel verify "{run_directory}"'
    )
    stdout_console = Console(sys.stdout)
    if stdout_console.enabled:
        stdout_console.rule()
        stdout_console.line(
            f"  {stdout_console.badge(terminal_status.value)}"
            f"  run {run_id}  -  wall {_elapsed() or '?'}"
        )
        stdout_console.kv("Findings", findings_line)
        stdout_console.kv("Report", str(run_directory / "report.md"))
        stdout_console.kv("Proof bundle", str(run_directory))
        stdout_console.kv("Verification", "PASS - report, viewer, custody, and audit chain")
        stdout_console.kv(
            "Strict gates",
            "packets - receipts - spans - usage - cost - report bytes - viewer bytes",
        )
        if why_partial:
            stdout_console.kv("Why PARTIAL", why_partial)
            stdout_console.kv("Next", next_step)
        stdout_console.kv("Verify again", verify_hint)
        stdout_console.kv("Open viewer", f'sentinel view "{run_directory}"')
        stdout_console.rule()
    else:
        print(f"Run status: {terminal_status.value}")
        print(f"Findings: {findings_line}")
        print(f"Report: {run_directory / 'report.md'}")
        print(f"Proof bundle: {run_directory}")
        print("Bundle verification: PASS")
        if why_partial:
            print(f"Why PARTIAL: {why_partial}")
            print(f"Next: {next_step}")
        print(f"Verify again: {verify_hint}")
        print(f'Open viewer: sentinel view "{run_directory}"')
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and return a stable process exit code."""

    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    if raw_arguments[:1] in (["-h"], ["--help"]):
        build_root_parser().print_help()
        return EXIT_COMPLETE
    if not raw_arguments:
        # Bare `sentinel` on a real terminal self-drives the whole case, start to
        # finish. Non-interactive shells (pipes, CI) get the command overview.
        if _interactive_terminal():
            try:
                return _guided()
            except KeyboardInterrupt:
                print("Unchained onboarding interrupted; nothing launched.", file=sys.stderr)
                return EXIT_FATAL
        build_root_parser().print_help()
        return EXIT_COMPLETE
    if raw_arguments[:1] in (["verify-run"], ["verify"]):
        arguments = build_verify_parser().parse_args(raw_arguments[1:])
        from .verify import verify_run

        result = verify_run(
            arguments.run_directory,
            require_complete=arguments.require_complete,
            require_live_gpt56=arguments.require_live_gpt56,
        )
        if arguments.json_output:
            print(json.dumps(result.public_dict(), indent=2, sort_keys=True))
        else:
            console = Console(sys.stdout)
            if console.enabled:
                console.rule()
                verdict = "VALID" if result.passed else "INVALID"
                console.line(f"  {console.badge(verdict)}  independent offline verification")
                console.kv("Run", result.run_id or "unknown")
                console.kv("Terminal status", result.terminal_status or "unknown")
                console.kv("Artifacts", f"{result.verified_artifacts} verified")
                console.kv("Audit chain", f"{result.verified_audit_entries} entries verified")
                console.rule()
                for warning in result.warnings:
                    console.warn(warning)
            else:
                print("VALID" if result.passed else "INVALID")
                print(f"Run: {result.run_id or 'unknown'}")
                print(f"Status: {result.terminal_status or 'unknown'}")
                print(f"Artifacts verified: {result.verified_artifacts}")
                print(f"Audit entries verified: {result.verified_audit_entries}")
                for warning in result.warnings:
                    print(f"Warning: {warning}")
            for error in result.errors:
                print(f"Error: {error}", file=sys.stderr)
        return EXIT_COMPLETE if result.passed else EXIT_FATAL

    if raw_arguments[:1] == ["onboard"]:
        arguments = build_onboard_parser().parse_args(raw_arguments[1:])
        try:
            return _onboard(
                arguments.evidence,
                mount=arguments.mount,
                caps_profile=arguments.caps,
                launch=arguments.launch,
                json_output=arguments.json_output,
                no_color=arguments.no_color,
            )
        except KeyboardInterrupt:
            print(
                "Unchained onboarding interrupted; no launch confirmation accepted.",
                file=sys.stderr,
            )
            return EXIT_FATAL
        except ValueError as exc:
            print(f"Unchained onboarding configuration invalid: {exc}", file=sys.stderr)
            return EXIT_INVALID
        except (EvidenceError, OSError) as exc:
            print(
                f"Unchained onboarding could not profile the supplied source: "
                f"{type(exc).__name__}; child paths and probe details suppressed",
                file=sys.stderr,
            )
            return EXIT_INVALID

    if raw_arguments[:1] == ["key"]:
        arguments = build_key_parser().parse_args(raw_arguments[1:])
        return _key_command(status=arguments.status, remove=arguments.remove)

    if raw_arguments[:1] == ["doctor"]:
        arguments = build_doctor_parser().parse_args(raw_arguments[1:])
        return _doctor(json_output=arguments.json_output)

    if raw_arguments[:1] == ["smoke-openai"]:
        arguments = build_smoke_parser().parse_args(raw_arguments[1:])
        try:
            return _smoke_openai(model_id=arguments.model, json_output=arguments.json_output)
        except ValueError as exc:
            print(f"Unchained OpenAI smoke configuration invalid: {exc}", file=sys.stderr)
            return EXIT_INVALID
        except Exception as exc:  # noqa: BLE001 - never print provider text or credentials
            print(
                f"Unchained OpenAI smoke failed: {type(exc).__name__}; "
                "credential and provider-response text suppressed",
                file=sys.stderr,
            )
            return EXIT_FATAL

    if raw_arguments[:1] == ["profile"]:
        arguments = build_profile_parser().parse_args(raw_arguments[1:])
        try:
            return _profile(
                arguments.evidence,
                mount=arguments.mount,
                json_output=arguments.json_output,
            )
        except (EvidenceError, OSError, ValueError) as exc:
            print(f"Unchained profile failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return EXIT_INVALID

    if raw_arguments[:1] == ["view"]:
        arguments = build_view_parser().parse_args(raw_arguments[1:])
        try:
            return _view(arguments.run_directory, no_open=arguments.no_open)
        except (OSError, ValueError) as exc:
            print(f"Unchained viewer failed: {exc}", file=sys.stderr)
            return EXIT_INVALID

    if raw_arguments[:1] == ["run"]:
        raw_arguments = raw_arguments[1:]

    arguments = build_parser().parse_args(raw_arguments)
    try:
        return run_cli(arguments.evidence, arguments.caps)
    except KeyboardInterrupt:
        print("Unchained interrupted.", file=sys.stderr)
        return EXIT_FATAL
    except ValueError as exc:
        print(f"Unchained configuration invalid: {exc}", file=sys.stderr)
        return EXIT_INVALID
    except Exception as exc:  # noqa: BLE001 - stable CLI code even if finalization fails
        print(f"Unchained fatal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_FATAL
