"""The self-driving `sentinel` front door: welcome -> one question -> card ->
ONE launch card (model + depth + confirm) -> final key step (hidden paste), in
a single command with no flags or env juggling. These tests pin that flow and
its input guards."""

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
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_prompt_evidence_path", lambda: Path("operator-case"))
    calls: list[str] = []
    monkeypatch.setattr(
        cli_module, "_launch_menu", lambda _profile: calls.append("menu") or "default"
    )
    monkeypatch.setattr(cli_module, "_final_key_gate", lambda: calls.append("gate") or True)
    captured: dict[str, object] = {}

    def fake_run(evidence, caps_profile, *, show_case_card, mount_evidence, show_banner):
        captured.update(
            evidence=evidence,
            caps_profile=caps_profile,
            show_case_card=show_case_card,
            mount_evidence=mount_evidence,
            show_banner=show_banner,
        )
        return EXIT_PARTIAL

    monkeypatch.setattr(cli_module, "run_cli", fake_run)

    assert main([]) == EXIT_PARTIAL
    # The key step is the ONE final gate: launch card first, key paste last.
    assert calls == ["menu", "gate"]
    assert captured == {
        "evidence": Path("operator-case"),
        "caps_profile": "default",
        "show_case_card": False,
        "mount_evidence": False,
        "show_banner": False,
    }


def test_launch_menu_defaults_to_the_cheap_rehearsal_and_owns_the_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A stale environment variable can never silently preselect the expensive
    # model: the card starts on the Terra rehearsal no matter what is inherited.
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-5.6")
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "0")
    _script_input(monkeypatch, ["1"])

    assert cli_module._launch_menu("strict") == "strict"
    assert cli_module.os.getenv("UNCHAINED_MODEL") == "gpt-5.6-terra"
    assert cli_module.os.getenv("UNCHAINED_ALLOW_TEST_MODEL") == "1"


def test_launch_menu_3_switches_to_the_official_sol_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UNCHAINED_MODEL", "stale-model")
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "0")
    _script_input(monkeypatch, ["3", "1"])

    assert cli_module._launch_menu("strict") == "strict"
    assert cli_module.os.getenv("UNCHAINED_MODEL") == "gpt-5.6"
    assert cli_module.os.getenv("UNCHAINED_ALLOW_TEST_MODEL") is None


def test_launch_menu_2_switches_the_depth_on_the_same_card(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("UNCHAINED_MODEL", "stale-model")
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "0")
    _script_input(monkeypatch, ["2", "1"])

    assert cli_module._launch_menu("strict") == "default"
    # The card was redrawn for the new depth - same menu, never a second question.
    assert capsys.readouterr().out.count("LAUNCH - EVERYTHING ON ONE CARD") == 2


def test_launch_menu_enter_never_launches_and_q_cancels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UNCHAINED_MODEL", "stale-model")
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "0")
    _script_input(monkeypatch, ["", "q"])

    assert cli_module._launch_menu("strict") is None


def test_final_key_gate_enter_uses_the_saved_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (True, "default-key-file"))
    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "")
    monkeypatch.setattr(
        cli_module,
        "_store_key_material",
        lambda *_a: (_ for _ in ()).throw(AssertionError("must not rewrite the key")),
    )

    assert cli_module._final_key_gate() is True
    # The card always offers the paste - never a silent "no paste needed" skip.
    out = capsys.readouterr().out
    assert "FINAL STEP - OPENAI API KEY" in out
    assert "Paste" in out


def test_final_key_gate_paste_replaces_the_key_and_wins_for_this_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Even an inherited environment key loses to the key pasted at the gate.
    monkeypatch.setenv("OPENAI_API_KEY", "stale-environment-key")
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (True, "environment"))
    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "sk0proj0AbCd1234EfGh5678IjKl")
    stored: list[str] = []
    monkeypatch.setattr(cli_module, "_store_key_material", stored.append)

    assert cli_module._final_key_gate() is True
    assert stored == ["sk0proj0AbCd1234EfGh5678IjKl"]
    assert cli_module.os.environ["OPENAI_API_KEY"] == "sk0proj0AbCd1234EfGh5678IjKl"


def test_final_key_gate_without_a_saved_key_requires_a_paste(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (False, None))
    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "")

    assert cli_module._final_key_gate() is False


def test_final_key_gate_q_cancels_and_a_malformed_paste_never_saves(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (True, "default-key-file"))
    monkeypatch.setattr(
        cli_module,
        "_store_key_material",
        lambda *_a: (_ for _ in ()).throw(AssertionError("must not save")),
    )

    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "q")
    assert cli_module._final_key_gate() is False

    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "a" * 600)
    assert cli_module._final_key_gate() is False
    assert "single-line" in capsys.readouterr().out


def test_final_key_gate_a_typed_refusal_is_never_stored_as_a_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The launch card just taught n = no; a hidden prompt must honor it too,
    # never truncating a good saved key down to the two bytes "no".
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (True, "default-key-file"))
    monkeypatch.setattr(
        cli_module,
        "_store_key_material",
        lambda *_a: (_ for _ in ()).throw(AssertionError("must not save")),
    )

    for refusal in ("n", "no", "N", "NO"):
        monkeypatch.setattr("getpass.getpass", lambda _prompt="", _r=refusal: _r)
        assert cli_module._final_key_gate() is False


def test_final_key_gate_normalizes_env_style_and_quoted_pastes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stored: list[str] = []
    monkeypatch.setenv("OPENAI_API_KEY", "restored-by-monkeypatch")
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (False, None))
    monkeypatch.setattr(cli_module, "_store_key_material", stored.append)

    monkeypatch.setattr("getpass.getpass", lambda _prompt="": '"sk0proj0AbCd1234EfGh5678IjKl"')
    assert cli_module._final_key_gate() is True
    monkeypatch.setattr(
        "getpass.getpass", lambda _prompt="": "OPENAI_API_KEY=sk0proj0AbCd1234EfGh5678IjKl"
    )
    assert cli_module._final_key_gate() is True

    assert stored == ["sk0proj0AbCd1234EfGh5678IjKl", "sk0proj0AbCd1234EfGh5678IjKl"]


def test_normalize_pasted_key_strips_env_prefix_and_quotes_only() -> None:
    normalize = cli_module._normalize_pasted_key
    assert normalize('  "sk0token0AbCd1234"  ') == "sk0token0AbCd1234"
    assert normalize("export OPENAI_API_KEY='sk0token0AbCd1234'") == "sk0token0AbCd1234"
    assert normalize("openai_api_key = sk0token0AbCd1234") == "sk0token0AbCd1234"
    # A bare key is untouched, even when it contains '=' later in the token.
    assert normalize("sk0token0AbCd1234==") == "sk0token0AbCd1234=="


def test_final_key_gate_reports_an_unwritable_key_file_and_cancels(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "openai_api_key_status", lambda: (False, None))
    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "sk0proj0AbCd1234EfGh5678IjKl")
    monkeypatch.setattr(
        cli_module,
        "_store_key_material",
        lambda *_a: (_ for _ in ()).throw(PermissionError(13, "denied")),
    )

    assert cli_module._final_key_gate() is False
    assert "Could not write the key file" in capsys.readouterr().out


def test_guided_cancelled_launch_stays_offline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_session(monkeypatch, ready_profile())
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(cli_module, "_prompt_evidence_path", lambda: Path("operator-case"))
    monkeypatch.setattr(cli_module, "_launch_menu", lambda _profile: None)
    # A cancelled launch card never reaches the key step or the lifecycle.
    monkeypatch.setattr(
        cli_module,
        "_final_key_gate",
        lambda: (_ for _ in ()).throw(AssertionError("must not reach the key gate")),
    )
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
        "_launch_menu",
        lambda *_a: (_ for _ in ()).throw(AssertionError("must not offer launch")),
    )

    assert main([]) == EXIT_INVALID
    assert "ACTION NEEDED" in capsys.readouterr().out


def _archive_profile(case: Path, zip_name: str = "memory.zip"):
    from unchained.models import EvidenceItem, EvidenceProfile

    item = EvidenceItem(
        evidence_id="E001",
        path=case / zip_name,
        kind="unknown",
        size=(case / zip_name).stat().st_size,
        sha256="a" * 64,
        os_hint="unknown",
        health="archive-not-unpacked",
        symbols="not-applicable",
        available=False,
    )
    return EvidenceProfile(
        root=case,
        os="unknown",
        shape="unknown",
        filesystems=(),
        sizes={"E001": item.size},
        health={"E001": item.health},
        symbols={"E001": item.symbols},
        hashes={"E001": item.sha256},
        available_tool_families=(),
        capability_label="undetermined",
        items=(item,),
    )


def test_safe_extract_zip_rejects_zip_slip_members(tmp_path: Path) -> None:
    import zipfile

    hostile = tmp_path / "hostile.zip"
    with zipfile.ZipFile(hostile, "w") as archive:
        archive.writestr("../evil.txt", "x")
    destination = tmp_path / "out"
    destination.mkdir()

    with pytest.raises(ValueError, match="unsafe archive member"):
        cli_module._safe_extract_zip(hostile, destination)
    assert not (tmp_path / "evil.txt").exists()


def test_safe_extract_zip_extracts_nested_members(tmp_path: Path) -> None:
    import zipfile

    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as archive:
        archive.writestr("case/memory.raw", "MEM")
        archive.writestr("readme.txt", "hello")
    destination = tmp_path / "out"
    destination.mkdir()

    assert cli_module._safe_extract_zip(good, destination) == 2
    assert (destination / "case" / "memory.raw").read_text() == "MEM"
    assert (destination / "readme.txt").read_text() == "hello"


def test_zip_extraction_offer_extracts_into_clean_sibling_folder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zipfile

    case = tmp_path / "dc pair"
    case.mkdir()
    with zipfile.ZipFile(case / "memory.zip", "w") as archive:
        archive.writestr("dc01-memory.raw", "MEM")
    _script_input(monkeypatch, [""])  # Enter = yes

    destination = cli_module._offer_zip_extraction(case, _archive_profile(case))

    assert destination == tmp_path / "dc pair-extracted"
    assert (destination / "dc01-memory.raw").read_text() == "MEM"


def test_zip_extraction_offer_respects_a_decline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zipfile

    case = tmp_path / "case"
    case.mkdir()
    with zipfile.ZipFile(case / "evidence.zip", "w") as archive:
        archive.writestr("memory.raw", "MEM")
    _script_input(monkeypatch, ["n"])

    assert cli_module._offer_zip_extraction(case, _archive_profile(case, "evidence.zip")) is None
    assert not (tmp_path / "case-extracted").exists()
