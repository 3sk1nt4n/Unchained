"""One-hidden-paste key setup: canonical file fallback and the `sentinel key` command."""

from __future__ import annotations

from pathlib import Path

import pytest

import unchained.cli as cli_module
import unchained.model as model_module
from unchained.cli import EXIT_COMPLETE, EXIT_INVALID, main


@pytest.fixture()
def isolated_key_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    key_file = tmp_path / "conf" / "openai_api_key"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY_FILE", raising=False)
    monkeypatch.setattr(model_module, "default_api_key_file", lambda: key_file)
    return key_file


def test_default_key_file_fallback_reports_safe_source(isolated_key_file: Path) -> None:
    assert model_module.openai_api_key_status() == (False, None)
    isolated_key_file.parent.mkdir(parents=True)
    isolated_key_file.write_text("sk-test-abc\n", encoding="utf-8")
    assert model_module.openai_api_key_status() == (True, "default-key-file")


def test_environment_still_overrides_the_saved_key_file(
    isolated_key_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated_key_file.parent.mkdir(parents=True)
    isolated_key_file.write_text("sk-from-file\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    assert model_module.openai_api_key_status() == (True, "environment")


def test_env_file_still_overrides_the_saved_key_file(
    isolated_key_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    isolated_key_file.parent.mkdir(parents=True)
    isolated_key_file.write_text("sk-from-default\n", encoding="utf-8")
    mounted = tmp_path / "mounted-secret"
    mounted.write_text("sk-from-mounted\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(mounted))
    assert model_module.openai_api_key_status() == (True, "file")


def test_malformed_saved_key_file_fails_closed(isolated_key_file: Path) -> None:
    isolated_key_file.parent.mkdir(parents=True)
    isolated_key_file.write_text("two\nlines\n", encoding="utf-8")
    assert model_module.openai_api_key_status() == (False, None)


def test_key_status_never_prints_the_credential(
    isolated_key_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    isolated_key_file.parent.mkdir(parents=True)
    isolated_key_file.write_text("sk-super-secret\n", encoding="utf-8")
    assert main(["key", "--status"]) == EXIT_COMPLETE
    output = capsys.readouterr().out
    assert "sk-super-secret" not in output
    assert "Secrets printed: never." in output


def test_key_paste_requires_an_interactive_terminal(
    isolated_key_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli_module, "_interactive_terminal", lambda: False)
    assert main(["key"]) == EXIT_INVALID
    assert not isolated_key_file.exists()


def test_key_remove_deletes_only_the_saved_file(
    isolated_key_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    isolated_key_file.parent.mkdir(parents=True)
    isolated_key_file.write_text("sk-x\n", encoding="utf-8")
    assert main(["key", "--remove"]) == EXIT_COMPLETE
    assert not isolated_key_file.exists()
    assert main(["key", "--remove"]) == EXIT_COMPLETE
    assert "No saved key file" in capsys.readouterr().out
