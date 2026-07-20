"""The self-driving `sentinel` front door: welcome -> one question -> card ->
depth -> key -> explicit launch, in a single command with no flags or env
juggling. These tests pin that flow and its input guards."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.test_onboarding import install_fake_session, ready_profile

import unchained.cli as cli_module
from unchained.cli import EXIT_COMPLETE, EXIT_INVALID, EXIT_PARTIAL, main


def _script_input(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    """Feed a fixed script of answers to builtins.input; extra prompts read ''."""

    pending = list(answers)

    def fake_input(_prompt: str = "") -> str:
        return pending.pop(0) if pending else ""

    monkeypatch.setattr("builtins.input", fake_input)


def test_pasted_secret_is_detected_by_shape_not_by_vendor() -> None:
    # A long, high-entropy, separator-free token that mixes letters and digits.
    assert cli_module._looks_like_pasted_secret("sk0proj0AbCd1234EfGh5678IjKl") is True
    # Real paths carry separators; menu answers are short; prose has spaces.
    assert cli_module._looks_like_pasted_secret(r"C:\Evidence\CASE-A") is False
    assert cli_module._looks_like_pasted_secret("2") is False
    assert cli_module._looks_like_pasted_secret("my case folder") is False
    # All-letters or all-digits alone is not credential-shaped.
    assert cli_module._looks_like_pasted_secret("abcdefghijklmnopqrstuvwx") is False


def test_evidence_prompt_discards_a_pasted_key_then_honors_quit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _script_input(monkeypatch, ["sk0proj0AbCd1234EfGh5678IjKl", "q"])

    assert cli_module._prompt_evidence_path() is None

    out = capsys.readouterr().out
    assert "discarded" in out.lower()
    # The credential itself is never echoed back.
    assert "sk0proj0AbCd1234EfGh5678IjKl" not in out


def test_evidence_prompt_strips_quotes_and_returns_existing_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    case = tmp_path / "case"
    case.mkdir()
    _script_input(monkeypatch, [f'"{case}"'])

    assert cli_module._prompt_evidence_path() == case


def test_bare_sentinel_without_a_terminal_prints_the_command_overview(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: False)
    monkeypatch.setattr(
        cli_module,
        "EvidenceSession",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not read evidence")),
    )

    assert main([]) == EXIT_COMPLETE
    assert "onboard" in capsys.readouterr().out


def test_bare_sentinel_self_drives_one_command_to_the_live_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-5.6")  # skip the auto-default branch
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_prompt_evidence_path", lambda: Path("operator-case"))
    monkeypatch.setattr(cli_module, "_choose_analysis_depth", lambda _selected: "default")
    monkeypatch.setattr(cli_module, "_ensure_key_for_launch", lambda: True)
    monkeypatch.setattr(cli_module, "_confirm_paid_sol_launch", lambda *_a: True)
    captured: dict[str, object] = {}

    def fake_run(evidence, caps_profile, *, show_case_card, mount_evidence):
        captured.update(
            evidence=evidence,
            caps_profile=caps_profile,
            show_case_card=show_case_card,
            mount_evidence=mount_evidence,
        )
        return EXIT_PARTIAL

    monkeypatch.setattr(cli_module, "run_cli", fake_run)

    assert main([]) == EXIT_PARTIAL
    assert captured == {
        "evidence": Path("operator-case"),
        "caps_profile": "default",
        "show_case_card": False,
        "mount_evidence": False,
    }


def test_guided_defaults_the_model_so_no_env_juggling_is_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.delenv("UNCHAINED_MODEL", raising=False)
    monkeypatch.setattr(cli_module, "cheap_model_opt_in", lambda: False)
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_prompt_evidence_path", lambda: Path("operator-case"))
    monkeypatch.setattr(cli_module, "_choose_analysis_depth", lambda _selected: "strict")
    monkeypatch.setattr(cli_module, "_ensure_key_for_launch", lambda: True)
    seen: dict[str, object] = {}

    def fake_confirm(_profile, _caps):
        seen["model"] = cli_module.os.getenv("UNCHAINED_MODEL")
        return False  # cancel before any spend

    monkeypatch.setattr(cli_module, "_confirm_paid_sol_launch", fake_confirm)
    monkeypatch.setattr(
        cli_module,
        "run_cli",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not launch")),
    )

    assert main([]) == EXIT_COMPLETE
    assert seen["model"] == "gpt-5.6"


def test_guided_cancelled_launch_stays_offline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-5.6")
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_prompt_evidence_path", lambda: Path("operator-case"))
    monkeypatch.setattr(cli_module, "_choose_analysis_depth", lambda _selected: "strict")
    monkeypatch.setattr(cli_module, "_ensure_key_for_launch", lambda: True)
    monkeypatch.setattr(cli_module, "_confirm_paid_sol_launch", lambda *_a: False)
    monkeypatch.setattr(
        cli_module,
        "run_cli",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not launch")),
    )

    assert main([]) == EXIT_COMPLETE
    assert "Launch cancelled" in capsys.readouterr().out


def test_guided_not_ready_case_can_be_abandoned_without_launch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, ready_profile(memory_count=2))  # fails route-readiness
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_prompt_evidence_path", lambda: Path("operator-case"))
    _script_input(monkeypatch, ["q"])  # decline "try another case?"
    monkeypatch.setattr(
        cli_module,
        "_confirm_paid_sol_launch",
        lambda *_a: (_ for _ in ()).throw(AssertionError("must not offer launch")),
    )

    assert main([]) == EXIT_INVALID
    assert "ACTION NEEDED" in capsys.readouterr().out
