"""Cheap test-model runs: allowed live, honestly labeled, never Sol-qualifying."""

from __future__ import annotations

import pytest

from unchained.model import (
    _is_gpt56_model,
    cheap_model_opt_in,
    is_gpt5_family,
    is_gpt56_sol_model,
)


def test_gpt5_family_predicate() -> None:
    assert is_gpt5_family("gpt-5.6-luna")
    assert is_gpt5_family("gpt-5.4-nano")
    assert is_gpt5_family("gpt-5.6-sol")
    assert not is_gpt5_family("gpt-4.1-nano")
    assert not is_gpt5_family("gpt-oss-20b")


def test_opt_in_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UNCHAINED_ALLOW_TEST_MODEL", raising=False)
    assert cheap_model_opt_in() is False
    for truthy in ("1", "true", "YES", "on"):
        monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", truthy)
        assert cheap_model_opt_in() is True
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "0")
    assert cheap_model_opt_in() is False


def test_default_rejects_non_sol_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UNCHAINED_ALLOW_TEST_MODEL", raising=False)
    assert _is_gpt56_model("gpt-5.6-sol") is True
    assert _is_gpt56_model("gpt-5.6-luna") is False
    assert _is_gpt56_model("gpt-5.4-nano") is False


def test_opt_in_accepts_gpt5_response_but_not_foreign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "1")
    assert _is_gpt56_model("gpt-5.6-luna") is True
    assert _is_gpt56_model("gpt-5.4-nano") is True
    assert _is_gpt56_model("gpt-5.6-sol") is True
    assert _is_gpt56_model("gpt-4.1-nano") is False


def test_test_model_run_is_never_sol_qualifying(monkeypatch: pytest.MonkeyPatch) -> None:
    # The cheap test model is a real GPT-5 run but never counts as a Sol bundle:
    # is_gpt56_sol_model stays False for it, so --require-live-gpt56 must fail.
    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "1")
    assert is_gpt56_sol_model("gpt-5.6-luna") is False
    assert is_gpt56_sol_model("gpt-5.4-nano") is False


def test_model_construction_rejects_non_gpt5_in_test_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unchained.model import OpenAIResponsesModel

    monkeypatch.setenv("UNCHAINED_ALLOW_TEST_MODEL", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used")
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-4.1-nano")
    with pytest.raises(ValueError, match="GPT-5"):
        OpenAIResponsesModel()
