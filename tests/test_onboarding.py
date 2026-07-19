from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

import unchained.cli as cli_module
from unchained.caps import CapConfig
from unchained.cli import EXIT_COMPLETE, EXIT_INVALID, EXIT_PARTIAL, main
from unchained.models import EvidenceItem, EvidenceProfile
from unchained.onboarding import render_welcome


@pytest.fixture(autouse=True)
def clean_cap_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("MAX_TOOL_CALLS", "MAX_TOTAL_TOKENS", "MAX_WALL_SECONDS", "MAX_COST_USD"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(f"UNCHAINED_{name}", raising=False)


def ready_profile(*, memory_count: int = 1) -> EvidenceProfile:
    items = tuple(
        EvidenceItem(
            evidence_id=f"E{index:03d}",
            path=Path(f"C:/private/case/never-print-host-{index}.mem"),
            kind="memory",
            size=2_147_483_648,
            sha256=f"{index:064x}",
            os_hint="windows",
            health="ready",
            symbols="resolved",
            available=True,
        )
        for index in range(1, memory_count + 1)
    )
    return EvidenceProfile(
        root=Path("C:/private/case"),
        os="windows",
        shape="memory-only",
        filesystems=(),
        sizes={item.evidence_id: item.size for item in items},
        health={item.evidence_id: item.health for item in items},
        symbols={item.evidence_id: item.symbols for item in items},
        hashes={item.evidence_id: item.sha256 for item in items},
        available_tool_families=("volatility3.windows",),
        capability_label="Windows tested path - memory ready",
        items=items,
    )


def ready_disk_profile(*, mounted: bool) -> EvidenceProfile:
    item = EvidenceItem(
        evidence_id="E001",
        path=Path("C:/private/case/never-print-host-disk.E01"),
        kind="disk",
        size=8_589_934_592,
        sha256="d" * 64,
        filesystem="ntfs",
        os_hint="windows",
        health="mounted-read-only" if mounted else "raw-only-mount-unavailable",
        symbols="not-applicable",
        available=True,
    )
    return EvidenceProfile(
        root=Path("C:/private/case"),
        os="windows",
        shape="disk-only",
        filesystems=("ntfs",),
        sizes={"E001": item.size},
        health={"E001": item.health},
        symbols={"E001": item.symbols},
        hashes={"E001": item.sha256},
        available_tool_families=("sleuthkit",),
        capability_label=(
            "Windows tested path - disk mounted read-only"
            if mounted
            else "Windows tested path - disk raw-only"
        ),
        items=(item,),
        mount_path=Path("C:/private/mount/never-print-mount") if mounted else None,
    )


def install_fake_session(
    monkeypatch: pytest.MonkeyPatch,
    profile: EvidenceProfile,
    captured: dict[str, object] | None = None,
) -> None:
    class FakeSession:
        def __init__(
            self,
            evidence: Path,
            *,
            mount: bool,
            case_card_stream: object,
        ) -> None:
            if captured is not None:
                captured.update(
                    evidence=evidence,
                    mount=mount,
                    case_card_stream=case_card_stream,
                )

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def profile(self) -> EvidenceProfile:
            return profile

        def verify_custody(self) -> dict[str, str]:
            return dict(profile.hashes)

        def close(self) -> bool:
            return True

    monkeypatch.setattr(cli_module, "EvidenceSession", FakeSession)


def test_root_help_and_onboard_help_present_the_safe_first_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--help"]) == EXIT_COMPLETE
    assert "onboard" in capsys.readouterr().out

    output = cli_module.build_onboard_parser().format_help()
    assert "exact confirmation" in output
    assert "--launch" in output
    assert "--json" in output


def test_welcome_only_is_machine_readable_and_performs_no_evidence_or_provider_io(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("welcome must not touch evidence or start a live run")

    monkeypatch.setattr(cli_module, "EvidenceSession", forbidden)
    monkeypatch.setattr(cli_module, "run_cli", forbidden)

    assert main(["onboard", "--json"]) == EXIT_COMPLETE

    payload = json.loads(capsys.readouterr().out)
    assert payload["stage"] == "WELCOME"
    assert payload["evidence_profiled"] is False
    assert payload["openai_called"] is False
    assert payload["paid_run_started"] is False
    assert payload["input_handling"]["archives_unpacked"] is False
    assert payload["one_case_limit"] == {
        "ready_disk_images": 1,
        "ready_memory_images": 1,
    }
    assert payload["next_command"].startswith("sentinel onboard")
    assert payload["secrets_printed"] is False


def test_profile_json_is_path_free_offline_and_binds_custody_and_caps(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile = ready_profile()
    captured: dict[str, object] = {}
    install_fake_session(monkeypatch, profile, captured)
    monkeypatch.setattr(
        cli_module,
        "run_cli",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must stay offline")),
    )

    assert main(["onboard", "operator-supplied-case", "--json", "--mount"]) == EXIT_COMPLETE

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["stage"] == "PROFILE_COMPLETE"
    assert payload["profile_ready"] is True
    assert payload["openai_called"] is False
    assert payload["paid_run_started"] is False
    assert payload["original_evidence_sent_to_openai"] is False
    assert payload["custody"]["match"] is True
    assert payload["custody"]["hashes"] == profile.hashes
    assert payload["caps_profile"] == "strict"
    assert payload["hard_caps"]["max_cost_usd"] == 2.5
    assert payload["next_commands"]["optional_paid_connectivity_canary"] == (
        "sentinel smoke-openai"
    )
    assert payload["mount"] == {
        "released": True,
        "requested": True,
        "status": "not-applicable-no-ready-disk",
    }
    assert "never-print-host" not in output
    assert "C:/private" not in output
    assert captured == {
        "evidence": Path("operator-supplied-case"),
        "mount": True,
        "case_card_stream": None,
    }


def test_human_case_card_is_junior_friendly_and_does_not_echo_child_paths(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.setenv("NO_COLOR", "1")

    assert main(["onboard", "operator-case"]) == EXIT_COMPLETE

    output = capsys.readouterr().out
    # A specific case skips the teaching welcome and goes straight to the card.
    assert "UNCHAINED" in output
    assert "Point me at one case" not in output
    assert "PROFILE COMPLETE" in output
    assert "VERIFIED CASE CARD" in output
    assert "PROFILE READY" in output
    assert "OpenAI calls 0" in output
    assert "HARD CEILINGS (not a price quote)" in output
    assert "CHOOSE ANALYSIS DEPTH" in output
    assert "HEAVY" in output
    assert "LIGHT" in output
    assert "CAUTIOUS [SELECTED]" in output
    assert "FLAGSHIP" in output
    assert "promises of result quality" in output
    assert "LAUNCH GPT-5.6 SOL" in output
    assert "never-print-host" not in output
    assert "C:/private" not in output
    assert "\x1b[" not in output


@pytest.mark.parametrize(
    ("profile", "expected_status"),
    [
        (ready_disk_profile(mounted=False), "requested-but-unavailable-raw-only"),
        (ready_disk_profile(mounted=True), "verified-read-only-and-released"),
    ],
)
def test_mount_card_reports_verified_outcome_without_disclosing_mountpoint(
    profile: EvidenceProfile,
    expected_status: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, profile)

    assert main(["onboard", "operator-case", "--mount", "--json"]) == EXIT_COMPLETE

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["mount"] == {
        "released": True,
        "requested": True,
        "status": expected_status,
    }
    assert "never-print-mount" not in output
    assert "C:/private" not in output


def test_no_color_environment_wins_even_for_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    class TtyBuffer(StringIO):
        def isatty(self) -> bool:
            return True

    stream = TtyBuffer()
    monkeypatch.setenv("NO_COLOR", "")
    render_welcome(
        caps_profile="strict",
        caps=CapConfig.from_env("strict"),
        stream=stream,
        no_color=False,
    )
    assert "\x1b[" not in stream.getvalue()


def test_legacy_windows_console_gets_a_clean_ascii_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Cp1252Tty(StringIO):
        encoding = "cp1252"

        def isatty(self) -> bool:
            return True

    stream = Cp1252Tty()
    monkeypatch.delenv("NO_COLOR", raising=False)
    render_welcome(
        caps_profile="strict",
        caps=CapConfig.from_env("strict"),
        stream=stream,
        no_color=True,
    )
    output = stream.getvalue()
    assert "UNCHAINED" in output
    assert "+" in output
    assert "╔" not in output
    output.encode("cp1252")


def test_paid_sol_confirmation_accepts_only_the_exact_phrase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caps = CapConfig.from_env("strict")
    monkeypatch.setattr("builtins.input", lambda _prompt: "launch gpt-5.6 sol")
    assert cli_module._confirm_paid_sol_launch("strict", caps) is False

    monkeypatch.setattr("builtins.input", lambda _prompt: "LAUNCH GPT-5.6 SOL")
    assert cli_module._confirm_paid_sol_launch("strict", caps) is True

    # A stray leading/trailing space (e.g. from a paste) must still be accepted;
    # the exact phrase, spacing, and case are still required.
    monkeypatch.setattr("builtins.input", lambda _prompt: "  LAUNCH GPT-5.6 SOL \n")
    assert cli_module._confirm_paid_sol_launch("strict", caps) is True

    monkeypatch.setattr("builtins.input", lambda _prompt: "LAUNCH  GPT-5.6  SOL")
    assert cli_module._confirm_paid_sol_launch("strict", caps) is False


def test_launch_requires_interactive_terminal_before_evidence_is_read(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: False)
    monkeypatch.setattr(
        cli_module,
        "EvidenceSession",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not hash")),
    )

    assert main(["onboard", "operator-case", "--launch"]) == EXIT_INVALID

    error = capsys.readouterr().err
    assert "requires an interactive terminal" in error


def test_declined_exact_confirmation_keeps_profile_offline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_confirm_paid_sol_launch", lambda *_args: False)
    monkeypatch.setattr(
        cli_module,
        "run_cli",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not launch")),
    )

    assert main(["onboard", "operator-case", "--launch"]) == EXIT_COMPLETE
    assert "Launch cancelled" in capsys.readouterr().out


def test_confirmed_launch_calls_existing_lifecycle_with_hidden_child_case_card(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_confirm_paid_sol_launch", lambda *_args: True)
    captured: dict[str, object] = {}

    def fake_run(
        evidence: Path,
        caps_profile: str,
        *,
        show_case_card: bool,
        mount_evidence: bool,
    ) -> int:
        captured.update(
            evidence=evidence,
            caps_profile=caps_profile,
            show_case_card=show_case_card,
            mount_evidence=mount_evidence,
        )
        return EXIT_PARTIAL

    monkeypatch.setattr(cli_module, "run_cli", fake_run)

    assert main(["onboard", "operator-case", "--launch", "--caps", "default"]) == EXIT_PARTIAL
    assert captured == {
        "evidence": Path("operator-case"),
        "caps_profile": "default",
        "show_case_card": False,
        "mount_evidence": False,
    }


def test_multiple_ready_memory_images_fail_closed_before_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, ready_profile(memory_count=2))
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(
        cli_module,
        "_confirm_paid_sol_launch",
        lambda *_args: (_ for _ in ()).throw(AssertionError("must not offer launch")),
    )

    assert main(["onboard", "operator-case", "--launch"]) == EXIT_INVALID

    output = capsys.readouterr().out
    assert "ACTION NEEDED" in output
    assert "More than one ready memory image" in output
    assert "split them into separate cases" in output


def test_launch_and_json_are_rejected_before_evidence_io(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(
        cli_module,
        "EvidenceSession",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not hash")),
    )

    assert main(["onboard", "operator-case", "--launch", "--json"]) == EXIT_INVALID
    assert "cannot be combined" in capsys.readouterr().err
