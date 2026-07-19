"""Command-line lifecycle for one isolated Unchained run."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
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
    is_gpt56_luna_model,
    is_gpt56_sol_model,
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
_SMOKE_MODEL = "gpt-5.6-luna"
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
        choices=("onboard", "doctor", "profile", "smoke-openai", "run", "verify", "view"),
        help="lifecycle command; run 'sentinel <command> --help' for details",
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
            "Run one cheap, non-forensic GPT-5.6 Luna typed-tool protocol canary. "
            "This never creates a proof bundle."
        ),
    )
    parser.add_argument(
        "--model",
        default=os.getenv("SENTINEL_SMOKE_MODEL", _SMOKE_MODEL),
        help="allowlisted Luna alias or snapshot (default: gpt-5.6-luna)",
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


def _doctor(*, json_output: bool) -> int:
    configured_model = os.getenv("UNCHAINED_MODEL")
    key_present, key_source = openai_api_key_status()
    checks = {
        "python_3_11": sys.version_info[:2] == (3, 11),
        "openai_sdk": importlib.util.find_spec("openai") is not None,
        "volatility3": importlib.util.find_spec("volatility3") is not None,
        "qwen_tool_package": importlib.util.find_spec("sift_sentinel") is not None,
        "model_is_gpt56_sol": bool(configured_model and is_gpt56_sol_model(configured_model)),
        "openai_api_key_present": key_present,
    }
    ready = all(checks.values())
    payload = {
        "ready_for_live_run": ready,
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
                "Next: set UNCHAINED_MODEL=gpt-5.6 and OPENAI_API_KEY "
                "(or OPENAI_API_KEY_FILE), then rerun doctor."
            )
    return EXIT_COMPLETE if ready else EXIT_INVALID


def _smoke_openai(*, model_id: str, json_output: bool) -> int:
    """Exercise one bounded Luna Responses call without creating forensic authority."""

    if not is_gpt56_luna_model(model_id):
        raise ValueError("--model must identify GPT-5.6 Luna")
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
    if not response.provider_model or not is_gpt56_luna_model(response.provider_model):
        problems.append("provider-returned model was absent or not GPT-5.6 Luna")
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


def _confirm_paid_sol_launch(caps_profile: str, caps: CapConfig) -> bool:
    """Require a high-friction, exact phrase before crossing the cloud boundary."""

    print()
    print("+-- EXPLICIT PAID CLOUD LAUNCH --------------------------------------------+")
    print("| GPT-5.6 Sol may receive the bounded profile and typed-tool observations. |")
    print("| Original evidence bytes stay local. This is no longer the $0 preview.   |")
    print(
        f"| {caps_profile.upper()} hard ceiling: ${caps.max_cost_usd:.2f} estimated cost; "
        f"{caps.max_total_tokens:,} tokens.{' ' * 11}|"
    )
    print("+--------------------------------------------------------------------------+")
    try:
        answer = input("Type exactly LAUNCH GPT-5.6 SOL (anything else cancels): ")
    except EOFError:
        return False
    return answer == "LAUNCH GPT-5.6 SOL"


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
        render_welcome(
            caps_profile=caps_profile,
            caps=caps,
            stream=sys.stdout,
            no_color=no_color,
        )
        print()
        print("* Looking at the supplied case with bounded local probes...", flush=True)

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
        )

    if not assessment.profile_ready:
        return EXIT_INVALID
    if not launch:
        return EXIT_COMPLETE
    if not _confirm_paid_sol_launch(caps_profile, caps):
        print("Launch cancelled. The local profile remains valid; OpenAI calls: 0.")
        return EXIT_COMPLETE
    print("Confirmation accepted. Starting the bounded GPT-5.6 Sol lifecycle...")
    return run_cli(
        evidence,
        caps_profile,
        show_case_card=False,
        mount_evidence=mount,
    )


_RUN_CLOCK: list[float] = []


def _elapsed() -> str | None:
    if not _RUN_CLOCK:
        return None
    seconds = time.monotonic() - _RUN_CLOCK[0]
    return f"{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def _progress(message: str) -> None:
    console = Console(sys.stderr)
    if console.enabled:
        console.step(message, elapsed=_elapsed())
    else:
        print(f"[sentinel] {message}", file=sys.stderr, flush=True)


class _AuditNarrator:
    """Display-only proxy over :class:`AuditLog` for an interactive terminal.

    Every call is forwarded to the wrapped audit log unchanged before any
    narration happens, so the appended record — not the narration — remains the
    sole authority. A narration failure can never alter or abort the run.
    """

    _PHASE_LABELS = {
        "opening": "GPT-5.6 opening book",
        "investigation": "Adaptive investigation",
        "serialization": "Structured findings serialization",
        "judge": "Fresh downgrade-only review",
        "report": "Deterministic report draft",
    }

    def __init__(self, audit: AuditLog, console: Console) -> None:
        self._audit = audit
        self._console = console
        self._phase_seen: str | None = None

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
                self._console.ok("opening book executed; all typed calls accounted for")
            elif event_type == "judge.started":
                self._phase_header("judge")
            elif event_type == "report.started":
                self._phase_header("report")
            elif event_type == "cap.fired" and isinstance(payload, dict):
                self._console.warn(f"hard cap fired: {payload.get('kind')}")
            elif event_type.startswith("model.retry"):
                self._console.warn("transient provider error; bounded audited retry")

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
            tokens = getattr(usage, "total_tokens", 0)
            running = kwargs.get("running_cost_usd", 0.0)
            self._console.detail(
                f"↓ response received · {tokens:,} tokens · ${float(running):.4f} est. total"
            )

        self._narrate(render)

    def tool_started(self, call_id: str, name: str, arguments: object, **kwargs: object) -> None:
        self._audit.tool_started(call_id, name, arguments, **kwargs)  # type: ignore[arg-type]
        self._narrate(lambda: self._console.step(f"⚒ {name} executing", elapsed=_elapsed()))

    def tool_completed(self, result: object, **kwargs: object) -> None:
        self._audit.tool_completed(result, **kwargs)  # type: ignore[arg-type]

        def render() -> None:
            name = getattr(result, "tool_name", "tool")
            status = getattr(result, "status", "?")
            byte_count = len(getattr(result, "output", "").encode("utf-8", "replace"))
            duration = getattr(result, "duration_ms", 0)
            line = f"{name} · {status} · {byte_count:,} bytes retained · {duration:,} ms"
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
) -> int:
    """Execute, close, manifest, and immediately verify one isolated run."""

    _RUN_CLOCK.clear()
    _RUN_CLOCK.append(time.monotonic())
    stderr_console = Console(sys.stderr)
    if stderr_console.enabled:
        stderr_console.banner("U N C H A I N E D", "Unchained reasoning. Chained evidence.")
        stderr_console.detail("GPT-5.6 chooses where to look; code proves what happened.")
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
    stdout_console = Console(sys.stdout)
    if stdout_console.enabled:
        stdout_console.rule()
        stdout_console.line(
            f"  {stdout_console.badge(terminal_status.value)}"
            f"  run {run_id}  ·  wall {_elapsed() or '?'}"
        )
        stdout_console.kv("Proof bundle", str(run_directory))
        stdout_console.kv("Verification", "PASS — report, viewer, custody, and audit chain")
        stdout_console.kv("Verify again", f'sentinel verify "{run_directory}" --require-complete')
        stdout_console.kv("Open viewer", f'sentinel view "{run_directory}"')
        stdout_console.rule()
    else:
        print(f"Run status: {terminal_status.value}")
        print(f"Proof bundle: {run_directory}")
        print("Bundle verification: PASS")
        print(f'Verify again: sentinel verify "{run_directory}" --require-complete')
        print(f'Open viewer: sentinel view "{run_directory}"')
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and return a stable process exit code."""

    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    if not raw_arguments or raw_arguments[:1] in (["-h"], ["--help"]):
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
