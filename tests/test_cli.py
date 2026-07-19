"""User-facing command dispatch and fail-fast preflight tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import unchained.cli as cli_module
import unchained.verify as verify_module
from unchained.cli import EXIT_COMPLETE, EXIT_FATAL, EXIT_INVALID, _view, main
from unchained.models import FunctionCall, ModelResponse, ModelUsage
from unchained.verify import VerificationResult


def test_root_help_lists_the_user_lifecycle(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == EXIT_COMPLETE

    output = capsys.readouterr().out
    for command in ("doctor", "profile", "smoke-openai", "run", "verify", "view"):
        assert command in output
    assert "evidence" not in output.lower()


def test_view_requires_strict_lifecycle_when_bundle_claims_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[bool] = []

    def fake_verify(
        path: Path,
        require_complete: bool = False,
        require_live_gpt56: bool = False,
    ) -> VerificationResult:
        del require_live_gpt56
        calls.append(require_complete)
        return VerificationResult(
            passed=not require_complete,
            run_directory=str(path),
            run_id="run-test",
            terminal_status="COMPLETE",
            exit_code=0,
            errors=() if not require_complete else ("strict lifecycle mismatch",),
            warnings=(),
            verified_artifacts=6,
            verified_audit_entries=44,
        )

    monkeypatch.setattr(verify_module, "verify_run", fake_verify)

    assert _view(tmp_path, no_open=True) == EXIT_FATAL
    assert calls == [False, True]
    assert "failed strict lifecycle verification" in capsys.readouterr().err


def test_profile_is_offline_and_returns_public_custody_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "system.log").write_text(
        "2026-01-01T00:00:00 systemd[1]: start\n"
        "2026-01-01T00:00:01 sshd[2]: login\n"
        "2026-01-01T00:00:02 kernel: audit\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("UNCHAINED_MODEL", raising=False)

    exit_code = main(["profile", str(evidence), "--json"])

    assert exit_code == EXIT_COMPLETE
    payload = json.loads(capsys.readouterr().out)
    assert payload["openai_called"] is False
    assert payload["profile"]["shape"] == "logs-only"
    assert set(payload["custody"]["hashes"]) == {"E001"}
    assert "system.log" not in json.dumps(payload["custody"])


def test_live_run_configuration_fails_before_evidence_or_output_io(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-5.6")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY_FILE", raising=False)

    exit_code = main(["run", str(tmp_path / "missing-evidence")])

    assert exit_code == EXIT_INVALID
    assert "OPENAI_API_KEY is required" in capsys.readouterr().err
    assert not (tmp_path / "unchained-runs").exists()


def test_doctor_never_prints_secret_value(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret = "sk-test-do-not-print"
    monkeypatch.setattr(cli_module.sys, "version_info", (3, 11, 9))
    monkeypatch.setattr(cli_module.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-5.6")
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    exit_code = main(["doctor", "--json"])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == EXIT_COMPLETE
    assert payload["ready_for_live_run"] is True
    assert payload["checks"]["openai_api_key_present"] is True
    assert payload["secrets_printed"] is False
    assert secret not in output


def test_doctor_accepts_bounded_secret_file_without_printing_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret = "sk-test-file-do-not-print"
    secret_path = tmp_path / "openai_api_key"
    secret_path.write_text(f"{secret}\n", encoding="utf-8")
    monkeypatch.setattr(cli_module.sys, "version_info", (3, 11, 9))
    monkeypatch.setattr(cli_module.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setenv("UNCHAINED_MODEL", "gpt-5.6")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(secret_path))

    assert main(["doctor", "--json"]) == EXIT_COMPLETE

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["openai_api_key_source"] == "file"
    assert payload["checks"]["openai_api_key_present"] is True
    assert payload["secrets_printed"] is False
    assert secret not in output
    assert str(secret_path) not in output


def test_luna_smoke_is_one_bounded_nonqualifying_typed_call(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class FakeSmokeModel:
        def __init__(self, *, model_id: str, connectivity_smoke: bool) -> None:
            captured["model_id"] = model_id
            captured["connectivity_smoke"] = connectivity_smoke

        def create(self, request: object) -> ModelResponse:
            captured["request"] = request
            return ModelResponse(
                response_id="resp_smoke",
                request_id="req_smoke",
                provider_model="gpt-5.6-luna-2026-07-14",
                function_calls=(
                    FunctionCall(
                        call_id="call_smoke",
                        name="sentinel_smoke_ok",
                        arguments={"token": "SENTINEL_SMOKE_OK"},
                    ),
                ),
                usage=ModelUsage(
                    input_tokens=42,
                    output_tokens=12,
                    reasoning_tokens=4,
                    provider_total_tokens=54,
                ),
            )

    monkeypatch.setattr(cli_module, "OpenAIResponsesModel", FakeSmokeModel)

    assert main(["smoke-openai", "--json"]) == EXIT_COMPLETE

    payload = json.loads(capsys.readouterr().out)
    request = captured["request"]
    assert captured == {
        "model_id": "gpt-5.6-luna",
        "connectivity_smoke": True,
        "request": request,
    }
    assert request.phase == "connectivity-smoke"
    assert request.store is False
    assert request.max_output_tokens == 128
    assert request.max_tool_calls == 1
    assert request.parallel_tool_calls is False
    assert request.reasoning_effort == "low"
    assert request.text_verbosity == "low"
    assert request.tools[0]["strict"] is True
    assert payload["ok"] is True
    assert payload["provider_requests"] == 1
    assert payload["typed_tool_call_valid"] is True
    assert payload["qualification"] == "NONQUALIFYING_CONNECTIVITY_SMOKE"
    assert payload["forensic_evidence_read"] is False
    assert payload["proof_bundle_created"] is False
    assert payload["secrets_printed"] is False


def test_luna_smoke_compose_service_cannot_mount_evidence_or_runs() -> None:
    repository = Path(__file__).resolve().parents[1]
    compose = (repository / "compose.yaml").read_text(encoding="utf-8")
    dockerfile = (repository / "Dockerfile").read_text(encoding="utf-8")
    shared_runtime, services = compose.split("\nservices:\n", 1)
    offline, live_smoke = services.split("\n  live-smoke:\n", 1)
    live_smoke, _top_level_volumes = live_smoke.split("\nvolumes:\n", 1)

    assert "\n  volumes:\n" not in shared_runtime
    assert "platform: linux/amd64" in shared_runtime
    assert (
        "python:3.11.9-slim-bookworm@sha256:"
        "8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317"
    ) in dockerfile
    assert "python -m unchained onboard --json >/dev/null" in dockerfile
    assert "/opt/sentinel/bin/sentinel onboard --json >/dev/null" in dockerfile
    assert "COPY docs ./docs" in dockerfile
    assert "COPY requirements ./requirements" in dockerfile
    assert "COPY scripts ./scripts" in dockerfile
    assert "git init" in dockerfile
    assert "target: /evidence" in offline
    assert "target: /workspace/unchained-runs" in offline
    assert 'command: ["onboard", "--json"]' in offline
    assert "volumes:" not in live_smoke
    assert "/evidence" not in live_smoke
    assert "unchained-runs" not in live_smoke
    assert "secrets:" in live_smoke
    assert "- openai_api_key" in live_smoke


def test_luna_smoke_rejects_non_luna_before_provider_construction(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden_model(**_kwargs: object) -> object:
        raise AssertionError("provider adapter must not be constructed")

    monkeypatch.setattr(cli_module, "OpenAIResponsesModel", forbidden_model)

    assert main(["smoke-openai", "--model", "gpt-5-mini"]) == EXIT_INVALID
    assert "must identify GPT-5.6 Luna" in capsys.readouterr().err


def test_luna_smoke_suppresses_provider_and_credential_text_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret = "sk-test-provider-must-not-print"

    class FailingSmokeModel:
        def __init__(self, *, model_id: str, connectivity_smoke: bool) -> None:
            assert model_id == "gpt-5.6-luna"
            assert connectivity_smoke is True

        def create(self, request: object) -> ModelResponse:
            del request
            raise RuntimeError(f"provider echoed forbidden text {secret}")

    monkeypatch.setattr(cli_module, "OpenAIResponsesModel", FailingSmokeModel)

    assert main(["smoke-openai"]) == EXIT_FATAL

    output = capsys.readouterr().err
    assert "RuntimeError" in output
    assert "suppressed" in output
    assert secret not in output
    assert "provider echoed" not in output
