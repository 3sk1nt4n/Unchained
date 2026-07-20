"""Offline tests for the frozen Qwen-versus-OpenAI comparison guard."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import scripts.benchmark_compare as benchmark_compare
from scripts.benchmark_compare import evaluate, render_markdown


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


# The candidate records below start at 2026-07-20T00:0X; the freeze tag must be
# dated strictly before them, and it must NOT float to the wall clock (otherwise
# the fixture "expires" the moment real time passes the candidate timestamps).
_FIXTURE_FREEZE_DATE = "2026-07-19T00:00:00+0000"


def _git(repo: Path, *args: str, committer_date: str | None = None) -> str:
    env = None
    if committer_date is not None:
        env = {
            **os.environ,
            "GIT_AUTHOR_DATE": committer_date,
            "GIT_COMMITTER_DATE": committer_date,
        }
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return result.stdout.strip()


def _source_contract() -> dict[str, Any]:
    repo = Path(__file__).resolve().parents[1]
    return json.loads((repo / "docs" / "QWEN-COMPARISON.v1.json").read_text(encoding="utf-8"))


def _ready_contract(tmp_path: Path) -> tuple[dict[str, Any], Path]:
    contract = copy.deepcopy(_source_contract())
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Unchained Test")
    _git(repo, "config", "user.email", "sentinel-test@example.invalid")
    _write_json(repo / "source.json", {"source": "frozen implementation"})
    _git(repo, "add", "source.json")
    _git(repo, "commit", "-m", "Freeze implementation source")
    source_commit = _git(repo, "rev-parse", "HEAD")

    lock = repo / "docs" / "BENCHMARK-FREEZE.lock.json"
    facts = repo / "experiment" / "reference-facts-v1.json"
    qwen_prices = repo / "docs" / "runs" / "qwen-price-contract-v1.json"
    qwen_build = repo / "docs" / "runs" / "qwen-build-provenance-v1.json"
    qwen_sbom = repo / "docs" / "runs" / "qwen-sbom-v1.json"
    host_receipt = repo / "docs" / "runs" / "comparison-host-resources-v1.json"
    source_lock = (
        Path(__file__).resolve().parents[1]
        / contract["systems"]["openai"]["runtime_contract"]["dependency_lock_path"]
    )
    target_lock = repo / contract["systems"]["openai"]["runtime_contract"]["dependency_lock_path"]
    target_lock.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_lock, target_lock)
    _write_json(lock, {"freeze": "fixture"})
    _write_json(
        facts,
        {"facts": [{"fact_id": f"DC01-F{index:03d}", "scored": True} for index in range(1, 6)]},
    )
    _write_json(qwen_prices, {"prices": "fixture"})
    _write_json(qwen_build, {"image": "fixture immutable build"})
    _write_json(qwen_sbom, {"packages": ["fixture"]})
    _write_json(host_receipt, {"host": "fixed fixture", "concurrent_workloads": False})

    contract["status"] = "READY"
    contract["freeze"].update(
        {
            "lock_sha256": _sha256(lock),
            "reference_fact_set_sha256": _sha256(facts),
        }
    )
    contract["repositories"]["openai"]["required_ancestor"] = source_commit
    contract["systems"]["openai"]["price_contract_sha256"] = _sha256(lock)
    contract["systems"]["qwen"]["price_contract_sha256"] = _sha256(qwen_prices)
    contract["systems"]["qwen"]["runtime_contract"].update(
        {
            "immutable_image_digest": "sha256:" + "d" * 64,
            "build_provenance_sha256": _sha256(qwen_build),
            "sbom_sha256": _sha256(qwen_sbom),
        }
    )
    contract["execution"]["measurement_regime"]["host_resource_receipt_sha256"] = _sha256(
        host_receipt
    )
    _write_json(repo / "docs" / "QWEN-COMPARISON.v1.json", contract)
    _git(repo, "add", ".")
    _git(
        repo,
        "commit",
        "-m",
        "Commit reachable freeze controller",
        committer_date=_FIXTURE_FREEZE_DATE,
    )
    _git(
        repo,
        "tag",
        "-a",
        "experiment-freeze-v1",
        "-m",
        "Freeze comparison v1",
        committer_date=_FIXTURE_FREEZE_DATE,
    )
    return contract, repo


def _repository_commits(contract: dict[str, Any], repo: Path) -> dict[str, str]:
    return {
        "openai": _git(repo, "rev-parse", "experiment-freeze-v1^{commit}"),
        "qwen": contract["repositories"]["qwen"]["required_commit"],
    }


def _rate(numerator: int, denominator: int) -> dict[str, object]:
    if denominator == 0:
        return {
            "status": "NOT_APPLICABLE",
            "numerator": 0,
            "denominator": 0,
            "value": None,
        }
    return {
        "status": "VALUE",
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator,
    }


def _metrics(seed: int) -> dict[str, object]:
    precision = _rate(seed + 1, seed + 2)
    confirmed_recall = _rate(seed, 5)
    precision_value = float(precision["value"])
    recall_value = float(confirmed_recall["value"])
    f1 = (
        0.0
        if precision_value + recall_value == 0
        else 2 * precision_value * recall_value / (precision_value + recall_value)
    )
    return {
        "wall_time_seconds": float(seed * 10),
        "time_to_first_observation_seconds": float(seed),
        "model_request_count": seed + 1,
        "tool_call_count": seed + 2,
        "input_tokens": seed * 100,
        "output_tokens": seed * 10,
        "total_tokens": seed * 110,
        "estimated_cost_usd": seed / 10,
        "final_confirmed_factual_precision": precision,
        "discovered_fact_recall": _rate(seed + 1, 5),
        "confirmed_fact_recall": confirmed_recall,
        "unsupported_finding_rate": _rate(1, seed + 2),
        "exact_citation_resolution_rate": _rate(seed + 1, seed + 2),
        "confirmed_f1": {"status": "VALUE", "value": f1},
        "custody_pass": True,
        "native_verifier_pass": True,
    }


def _source_receipt(artifact_id: str, *, scorer: bool = False) -> dict[str, object]:
    receipt: dict[str, object] = {
        "artifact_id": artifact_id,
        "artifact_sha256": "c" * 64,
        "verification": "HASH_REFERENCE_ONLY_SOURCE_NOT_REVERIFIED_BY_AGGREGATOR",
    }
    if scorer:
        receipt["method"] = "SHARED_FROZEN_SCORER_ITEM_LEVEL_V1"
    return receipt


def _extraction(
    contract: dict[str, Any], system: str, record: dict[str, object], seed: int
) -> dict[str, object]:
    metrics = _metrics(seed)
    return {
        "schema_version": 1,
        "comparison_id": contract["comparison_id"],
        "system": system,
        "run_id": record["run_id"],
        "policy": "LEDGER_BOUND_SANITIZED_EXTRACTION_V1",
        "source_receipt": _source_receipt(f"{system}-private-run-summary-{seed}"),
        "values": {
            "wall_time_seconds": metrics["wall_time_seconds"],
            "time_to_first_observation_seconds": metrics["time_to_first_observation_seconds"],
            "model_request_count": metrics["model_request_count"],
            "tool_call_count": metrics["tool_call_count"],
            "input_tokens": metrics["input_tokens"],
            "output_tokens": metrics["output_tokens"],
            "estimated_cost_usd": metrics["estimated_cost_usd"],
            "custody_pass": metrics["custody_pass"],
            "native_verifier_pass": metrics["native_verifier_pass"],
        },
    }


def _adjudication(
    contract: dict[str, Any], system: str, record: dict[str, object], seed: int
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "comparison_id": contract["comparison_id"],
        "system": system,
        "run_id": record["run_id"],
        "policy": "LEDGER_BOUND_ITEM_LEVEL_SHARED_SCORER_ADJUDICATION_V1",
        "scorer_version": contract["freeze"]["shared_scoring_version"],
        "reference_fact_set_sha256": contract["freeze"]["reference_fact_set_sha256"],
        "candidate_source_receipt": _source_receipt(f"{system}-candidate-report-{seed}"),
        "scorer_receipt": _source_receipt(f"shared-scorer-{system}-{seed}", scorer=True),
        "reference_facts": [
            {
                "fact_id": f"DC01-F{index:03d}",
                "surfaced_at_any_final_status": index <= seed + 1,
                "surfaced_final_confirmed": index <= seed,
            }
            for index in range(1, 6)
        ],
        "findings": [
            {
                "finding_id": f"F{index:03d}",
                "final_confirmed": True,
                "factual_label": "CORRECT" if index <= seed + 1 else "INCORRECT",
                "receipt_label": "UNSUPPORTED" if index == seed + 2 else "SUPPORTED",
                "has_citations": True,
                "all_citations_exactly_resolved": index <= seed + 1,
            }
            for index in range(1, seed + 3)
        ],
    }


def _record(
    contract: dict[str, Any],
    system: str,
    sequence: int,
    *,
    classification: str = "VALID",
    repository_commits: dict[str, str],
) -> dict[str, object]:
    valid = classification == "VALID"
    return {
        "schema_version": 1,
        "comparison_id": contract["comparison_id"],
        "system": system,
        "run_id": f"{system}-run-{sequence:03d}",
        "sequence": sequence,
        "started_at_utc": f"2026-07-20T00:0{sequence}:00Z",
        "post_freeze": True,
        "classification": classification,
        "eligible_for_aggregate": valid,
        "infrastructure_fault": (
            None
            if classification != "INFRASTRUCTURE_FAULT"
            else {
                "code": "PROVIDER_UNAVAILABLE_BEFORE_USABLE_RESPONSE",
                "rationale": "fixture provider failure before a usable response",
            }
        ),
        "terminal_status": (
            contract["systems"][system]["terminal_complete_value"] if valid else "PARTIAL"
        ),
        "repository_commit": repository_commits[system],
        "freeze_id": contract["freeze"]["freeze_id"],
        "reference_fact_set_sha256": contract["freeze"]["reference_fact_set_sha256"],
        "evidence": copy.deepcopy(contract["evidence"]),
        "model": {
            "requested": contract["systems"][system]["required_requested_models"],
            "provider_returned": (
                ["gpt-5.6-sol"] if system == "openai" else ["qwen3.7-max", "qwen-plus"]
            ),
            "response_count": 1 if system == "openai" else 2,
        },
        "tool_policy": contract["systems"][system]["tool_policy"],
        "runtime_contract": contract["systems"][system]["runtime_contract"],
        "cap_contract": contract["systems"][system]["cap_contract"],
        "measurement_regime": contract["execution"]["measurement_regime"],
        "metrics": _metrics(sequence) if valid else {},
    }


def _write_ledger(
    records_root: Path,
    contract: dict[str, Any],
    system: str,
    records: list[dict[str, object]],
) -> None:
    root = records_root / system
    entries = []
    for record in records:
        sequence = int(record["sequence"])
        name = f"candidate-{sequence:03d}.json"
        path = root / name
        _write_json(path, record)
        extraction_name: str | None = None
        extraction_sha256: str | None = None
        adjudication_name: str | None = None
        adjudication_sha256: str | None = None
        if record["classification"] == "VALID":
            extraction_name = f"candidate-{sequence:03d}.extraction.json"
            extraction_path = root / extraction_name
            _write_json(extraction_path, _extraction(contract, system, record, sequence))
            extraction_sha256 = _sha256(extraction_path)
            adjudication_name = f"candidate-{sequence:03d}.adjudication.json"
            adjudication_path = root / adjudication_name
            _write_json(adjudication_path, _adjudication(contract, system, record, sequence))
            adjudication_sha256 = _sha256(adjudication_path)
        entries.append(
            {
                "sequence": sequence,
                "path": name,
                "sha256": _sha256(path),
                "extraction_path": extraction_name,
                "extraction_sha256": extraction_sha256,
                "adjudication_path": adjudication_name,
                "adjudication_sha256": adjudication_sha256,
            }
        )
    _write_json(
        root / "ledger.json",
        {
            "schema_version": 1,
            "comparison_id": contract["comparison_id"],
            "system": system,
            "scope": "ALL_POST_FREEZE_CANDIDATE_ATTEMPTS",
            "records": entries,
        },
    )


def _complete_records(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    contract, repo = _ready_contract(tmp_path)
    repository_commits = _repository_commits(contract, repo)
    records_root = tmp_path / "records"
    for system in ("openai", "qwen"):
        records = [
            _record(
                contract,
                system,
                sequence,
                repository_commits=repository_commits,
            )
            for sequence in (1, 2, 3)
        ]
        _write_ledger(records_root, contract, system, records)
    return contract, repo, records_root


def test_committed_contract_is_pending_and_default_dry_run_accesses_nothing() -> None:
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_compare.py", "--json"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 2
    assert payload["status"] == "PENDING"
    assert payload["same_evidence"] is False
    assert payload["dimension_comparison_allowed"] is False
    assert payload["blanket_superiority_claim_allowed"] is False
    assert payload["provider_or_evidence_accessed"] is False
    assert any(item["code"] == "RUN_LEDGER_PENDING" for item in payload["pending"])


def test_execute_refuses_pending_contract_before_evidence_access(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    private_marker = "PRIVATE_EVIDENCE_PATH_MUST_NOT_APPEAR"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_compare.py",
            "--execute",
            "--system",
            "openai",
            "--json",
            "--evidence-dir",
            str(tmp_path / private_marker),
            "--private-run-root",
            str(tmp_path / "private-launches"),
            "--candidate-sequence",
            "1",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 2
    assert payload["status"] == "REFUSED"
    assert payload["provider_or_evidence_accessed"] is False
    assert private_marker not in result.stdout + result.stderr


def test_qwen_execute_fails_before_evidence_without_container_ownership(
    tmp_path: Path,
) -> None:
    repo = Path(__file__).resolve().parents[1]
    private_root = tmp_path / "private-launches"
    evidence_path = tmp_path / "private-evidence"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_compare.py",
            "--execute",
            "--system",
            "qwen",
            "--json",
            "--evidence-dir",
            str(evidence_path),
            "--private-run-root",
            str(private_root),
            "--candidate-sequence",
            "1",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "REFUSED"
    assert payload["provider_or_evidence_accessed"] is False
    assert any(item["code"] == "QWEN_CONTAINER_OWNERSHIP_UNAVAILABLE" for item in payload["errors"])
    assert not private_root.exists()
    assert not evidence_path.exists()


def test_complete_ledgers_aggregate_every_valid_run_with_median_and_spread(
    tmp_path: Path,
) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "COMPLETE"
    assert result["same_evidence"] is True
    assert result["comparison_qualification"] == "SAME_EVIDENCE"
    assert result["blanket_superiority_claim_allowed"] is False
    assert result["proof_backed_faster_or_cheaper_claim_allowed"] is False
    assert result["proof_backed_accuracy_superiority_claim_allowed"] is False
    for system in ("openai", "qwen"):
        summary = result["systems"][system]
        assert summary["valid_runs"] == 3
        assert summary["primary_run_id"] == f"{system}-run-001"
        assert summary["valid_run_ids"] == [
            f"{system}-run-001",
            f"{system}-run-002",
            f"{system}-run-003",
        ]
        wall = summary["metrics"]["wall_time_seconds"]
        assert wall == {
            "applicable_runs": 3,
            "not_available_runs": 0,
            "median": 20.0,
            "minimum": 10.0,
            "maximum": 30.0,
            "spread": 20.0,
        }


def test_infrastructure_attempt_is_retained_but_never_cherry_picked_into_metrics(
    tmp_path: Path,
) -> None:
    contract, repo = _ready_contract(tmp_path)
    repository_commits = _repository_commits(contract, repo)
    records_root = tmp_path / "records"
    for system in ("openai", "qwen"):
        records = [
            _record(
                contract,
                system,
                1,
                classification="INFRASTRUCTURE_FAULT",
                repository_commits=repository_commits,
            ),
            _record(contract, system, 2, repository_commits=repository_commits),
            _record(contract, system, 3, repository_commits=repository_commits),
            _record(contract, system, 4, repository_commits=repository_commits),
        ]
        _write_ledger(records_root, contract, system, records)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "COMPLETE"
    for system in ("openai", "qwen"):
        summary = result["systems"][system]
        assert summary["candidate_attempts"] == 4
        assert summary["valid_runs"] == 3
        assert summary["primary_run_id"] == f"{system}-run-002"
        assert summary["excluded_attempts"] == [
            {
                "run_id": f"{system}-run-001",
                "classification": "INFRASTRUCTURE_FAULT",
            }
        ]


def test_mismatched_evidence_refuses_same_evidence_qualification(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    record_path = records_root / "qwen" / "candidate-002.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["evidence"]["sha256"] = "d" * 64
    _write_json(record_path, record)
    ledger_path = records_root / "qwen" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["records"][1]["sha256"] = _sha256(record_path)
    _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert result["same_evidence"] is False
    assert result["comparison_qualification"] == "NOT_ESTABLISHED"
    assert any(item["code"] == "INCOMPARABLE_EVIDENCE" for item in result["errors"])


def test_unlisted_candidate_file_fails_complete_ledger_rule(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    _write_json(records_root / "openai" / "hidden-valid.json", {"hidden": True})

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "LEDGER_INCOMPLETE" for item in result["errors"])


def test_runner_command_is_closed_and_cannot_be_replaced(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    contract["systems"]["qwen"]["runner_argv"] = ["arbitrary-command"]

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "RUNNER_AUTHORITY" for item in result["errors"])


def test_provider_model_drift_invalidates_candidate(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    record_path = records_root / "openai" / "candidate-001.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["model"]["provider_returned"] = ["not-gpt-5.6-sol"]
    _write_json(record_path, record)
    ledger_path = records_root / "openai" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["records"][0]["sha256"] = _sha256(record_path)
    _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "RUN_MODEL" for item in result["errors"])


def test_runtime_and_cap_contract_drift_invalidates_candidate(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    record_path = records_root / "qwen" / "candidate-001.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["runtime_contract"] = "unfrozen-runtime"
    record["cap_contract"] = "unfrozen-caps"
    _write_json(record_path, record)
    ledger_path = records_root / "qwen" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["records"][0]["sha256"] = _sha256(record_path)
    _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    error_codes = {item["code"] for item in result["errors"]}
    assert {"RUN_RUNTIME_DRIFT", "RUN_CAP_DRIFT"} <= error_codes


def test_forged_metric_assertions_cannot_override_sidecar_recomputation(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    record_path = records_root / "openai" / "candidate-001.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["metrics"]["wall_time_seconds"] = 0.0001
    _write_json(record_path, record)
    ledger_path = records_root / "openai" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["records"][0]["sha256"] = _sha256(record_path)
    _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "RUN_METRIC_RECOMPUTATION" for item in result["errors"])


def test_adjudication_tamper_without_ledger_rehash_is_rejected(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    sidecar = records_root / "qwen" / "candidate-001.adjudication.json"
    adjudication = json.loads(sidecar.read_text(encoding="utf-8"))
    adjudication["findings"][0]["factual_label"] = "INCORRECT"
    _write_json(sidecar, adjudication)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "SIDECAR_DIGEST" for item in result["errors"])


def test_zero_denominators_remain_not_applicable_instead_of_perfect(tmp_path: Path) -> None:
    contract, repo = _ready_contract(tmp_path)
    repository_commits = _repository_commits(contract, repo)
    records_root = tmp_path / "records"
    for system in ("openai", "qwen"):
        records = []
        for sequence in (1, 2, 3):
            record = _record(
                contract,
                system,
                sequence,
                repository_commits=repository_commits,
            )
            record["metrics"]["final_confirmed_factual_precision"] = _rate(0, 0)
            record["metrics"]["exact_citation_resolution_rate"] = _rate(0, 0)
            record["metrics"]["confirmed_f1"] = {
                "status": "NOT_APPLICABLE",
                "value": None,
            }
            records.append(record)
        _write_ledger(records_root, contract, system, records)
        ledger_path = records_root / system / "ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        for entry in ledger["records"]:
            adjudication_path = records_root / system / entry["adjudication_path"]
            adjudication = json.loads(adjudication_path.read_text(encoding="utf-8"))
            for finding in adjudication["findings"]:
                finding["factual_label"] = "AMBIGUOUS"
                finding["has_citations"] = False
                finding["all_citations_exactly_resolved"] = None
            _write_json(adjudication_path, adjudication)
            entry["adjudication_sha256"] = _sha256(adjudication_path)
        _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "COMPLETE"
    for system in ("openai", "qwen"):
        precision = result["systems"][system]["metrics"]["final_confirmed_factual_precision"]
        assert precision["median"] is None
        assert precision["not_available_runs"] == 3


def test_pending_markdown_excludes_historical_memory_plus_disk_metrics() -> None:
    contract = _source_contract()
    repo = Path(__file__).resolve().parents[1]
    result = evaluate(
        contract,
        repo_root=repo,
        records_root=repo / "docs" / "runs" / "comparison-inputs",
    )
    markdown = render_markdown(contract, result)

    assert "Status: PENDING" in markdown
    assert "Historical Qwen memory-plus-disk metrics are explicitly excluded" in markdown
    assert "proof-backed faster, cheaper, or accuracy-superiority" in markdown


def test_contract_pins_current_public_qwen_master() -> None:
    contract = _source_contract()

    assert (
        contract["repositories"]["qwen"]["required_commit"]
        == "7118c6ef02b19f4d016723470bfaa5f8a94dbfe5"
    )


def test_runtime_lock_digest_is_canonical_across_crlf_and_fresh_clone_lf(
    tmp_path: Path,
) -> None:
    source = (
        Path(__file__).resolve().parents[1] / "requirements" / ("pylock.windows-amd64-cp311.toml")
    )
    lf = source.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    crlf_path = tmp_path / "lock.toml"
    crlf_path.write_bytes(lf.replace(b"\n", b"\r\n"))

    expected = "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7"
    assert benchmark_compare._sha256_canonical_lf_text_file(source) == expected
    assert benchmark_compare._sha256_canonical_lf_text_file(crlf_path) == expected


def test_qwen_immutable_image_and_host_receipts_remain_pending_until_bound() -> None:
    errors, pending = benchmark_compare.validate_contract(_source_contract())
    pending_codes = {issue.code for issue in pending}

    assert not any(
        issue.code in {"QWEN_IMAGE_DIGEST", "QWEN_RUNTIME_PROVENANCE"} for issue in errors
    )
    assert "QWEN_IMAGE_DIGEST_PENDING" in pending_codes
    assert "QWEN_RUNTIME_PROVENANCE_PENDING" in pending_codes
    assert "HOST_RESOURCE_RECEIPT_PENDING" in pending_codes


def test_reachable_two_commit_annotated_anchor_resolves_without_self_reference(
    tmp_path: Path,
) -> None:
    contract, repo = _ready_contract(tmp_path)

    anchor, errors, pending = benchmark_compare._resolve_freeze_anchor(contract, repo)

    assert _git(repo, "rev-list", "--count", "HEAD") == "2"
    assert errors == []
    assert pending == []
    assert anchor is not None
    assert anchor.commit == _git(repo, "rev-parse", "HEAD")
    assert len(anchor.commit) == 40


def test_missing_annotated_anchor_remains_pending(tmp_path: Path) -> None:
    contract, repo = _ready_contract(tmp_path)
    _git(repo, "tag", "-d", "experiment-freeze-v1")

    result = evaluate(contract, repo_root=repo, records_root=tmp_path / "records")

    assert result["status"] == "PENDING"
    assert any(item["code"] == "FREEZE_TAG_PENDING" for item in result["pending"])
    assert any(item["code"] == "RUN_LEDGER_PENDING" for item in result["pending"])


def test_lightweight_anchor_is_rejected(tmp_path: Path) -> None:
    contract, repo = _ready_contract(tmp_path)
    _git(repo, "tag", "-d", "experiment-freeze-v1")
    _git(repo, "tag", "experiment-freeze-v1")

    result = evaluate(contract, repo_root=repo, records_root=tmp_path / "records")

    assert result["status"] == "INVALID"
    assert any(item["code"] == "FREEZE_TAG_NOT_ANNOTATED" for item in result["errors"])


def test_aggregation_descendant_cannot_change_nonresult_files(tmp_path: Path) -> None:
    contract, repo = _ready_contract(tmp_path)
    _write_json(repo / "after-tag.json", {"must": "not move HEAD past anchor"})
    _git(repo, "add", "after-tag.json")
    _git(repo, "commit", "-m", "Move past frozen anchor")

    result = evaluate(contract, repo_root=repo, records_root=tmp_path / "records")

    assert result["status"] == "INVALID"
    assert any(item["code"] == "FREEZE_DESCENDANT_SCOPE" for item in result["errors"])


def test_results_only_descendant_can_aggregate_but_cannot_execute(tmp_path: Path) -> None:
    contract, repo = _ready_contract(tmp_path)
    repository_commits = _repository_commits(contract, repo)
    anchor_commit = repository_commits["openai"]
    records_root = repo / "docs" / "runs" / "comparison-inputs"
    for system in ("openai", "qwen"):
        records = [
            _record(
                contract,
                system,
                sequence,
                repository_commits=repository_commits,
            )
            for sequence in (1, 2, 3)
        ]
        _write_ledger(records_root, contract, system, records)
    _git(repo, "add", "docs/runs/comparison-inputs")
    _git(repo, "commit", "-m", "Publish comparison result ledgers")
    descendant_commit = _git(repo, "rev-parse", "HEAD")

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert descendant_commit != anchor_commit
    assert result["status"] == "COMPLETE"
    assert result["resolved_repository_commits"]["openai"] == anchor_commit
    qwen_repo = tmp_path / "qwen-repo"
    qwen_repo.mkdir()
    execution, exit_code = benchmark_compare.execute_external_runs(
        contract,
        openai_repo=repo,
        qwen_repo=qwen_repo,
        evidence_dir=tmp_path / "private-evidence",
        private_run_root=tmp_path / "private-launches",
        systems=("openai",),
        candidate_sequence=1,
    )
    assert exit_code == 1
    assert execution["status"] == "REFUSED"
    assert execution["provider_or_evidence_accessed"] is False
    assert any(item["code"] == "FREEZE_TAG_TARGET" for item in execution["errors"])


def test_child_environment_isolates_provider_and_agent_credentials() -> None:
    contract = _source_contract()
    source = {
        "PATH": "safe-path",
        "OPENAI_API_KEY": "raw-openai-must-be-removed",
        "OPENAI_API_KEY_FILE": "openai-key-file",
        "DASHSCOPE_API_KEY": "dashscope-key",
        "QWEN_API_KEY": "qwen-key",
        "ANTHROPIC_API_KEY": "anthropic-key",
        "GH_TOKEN": "github-token",
        "SERVICE_ACCESS_TOKEN": "other-agent-token",
        "AWS_SECRET_ACCESS_KEY": "aws-secret",
        "NPM_TOKEN": "npm-token",
        "TOKEN": "generic-token",
        "PASSWORD": "generic-password",
        "SECRET": "generic-secret",
        "VENDOR_CREDENTIAL": "unknown-vendor-secret",
        "HTTPS_PROXY": "https://proxy-user:proxy-password@example.invalid",
        "USERPROFILE": "private-profile",
        "HOME": "private-home",
    }

    openai = benchmark_compare._build_child_environment(contract, "openai", source=source)
    qwen = benchmark_compare._build_child_environment(contract, "qwen", source=source)

    assert openai["PATH"] == "safe-path"
    assert openai["OPENAI_API_KEY_FILE"] == "openai-key-file"
    assert "OPENAI_API_KEY" not in openai
    assert "DASHSCOPE_API_KEY" not in openai
    assert "QWEN_API_KEY" not in openai
    assert "ANTHROPIC_API_KEY" not in openai
    assert "GH_TOKEN" not in openai
    assert "SERVICE_ACCESS_TOKEN" not in openai
    assert "AWS_SECRET_ACCESS_KEY" not in openai
    assert "NPM_TOKEN" not in openai
    assert "TOKEN" not in openai
    assert "PASSWORD" not in openai
    assert "SECRET" not in openai
    assert "VENDOR_CREDENTIAL" not in openai
    assert "HTTPS_PROXY" not in openai
    assert "USERPROFILE" not in openai
    assert "HOME" not in openai
    assert openai["UNCHAINED_MODEL"] == "gpt-5.6"

    assert qwen["DASHSCOPE_API_KEY"] == "dashscope-key"
    assert qwen["QWEN_API_KEY"] == "qwen-key"
    assert "OPENAI_API_KEY" not in qwen
    assert "OPENAI_API_KEY_FILE" not in qwen
    assert "ANTHROPIC_API_KEY" not in qwen
    assert "GH_TOKEN" not in qwen
    assert "SERVICE_ACCESS_TOKEN" not in qwen
    assert "AWS_SECRET_ACCESS_KEY" not in qwen
    assert "NPM_TOKEN" not in qwen
    assert "TOKEN" not in qwen
    assert "PASSWORD" not in qwen
    assert "SECRET" not in qwen
    assert "VENDOR_CREDENTIAL" not in qwen
    assert "HTTPS_PROXY" not in qwen
    assert "USERPROFILE" not in qwen
    assert "HOME" not in qwen
    assert qwen["SIFT_NO_OPEN"] == "1"


def test_posix_timeout_kills_and_reaps_owned_process_group(monkeypatch: Any) -> None:
    class FakeProcess:
        pid = 4321

        def __init__(self) -> None:
            self.wait_calls = 0
            self.killed = False

        def wait(self, timeout: float) -> int:
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired(["child"], timeout)
            return -int(getattr(benchmark_compare.signal, "SIGKILL", 9))

        def kill(self) -> None:
            self.killed = True

    fake_process = FakeProcess()
    popen_options: dict[str, Any] = {}
    killed_groups: list[tuple[int, int]] = []

    def fake_popen(_argv: list[str], **kwargs: Any) -> FakeProcess:
        popen_options.update(kwargs)
        return fake_process

    monkeypatch.setattr(benchmark_compare.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        benchmark_compare.os,
        "killpg",
        lambda process_group, sent_signal: killed_groups.append((process_group, sent_signal)),
        raising=False,
    )

    result = benchmark_compare._run_owned_process_tree(
        ["child"],
        cwd=Path.cwd(),
        environment={"PATH": "safe"},
        stdout_handle=io.BytesIO(),
        stderr_handle=io.BytesIO(),
        timeout_seconds=1800,
        platform_name="posix",
    )

    assert result.timed_out is True
    assert result.returncode is None
    assert result.ownership == "POSIX_NEW_SESSION_PROCESS_GROUP"
    assert result.cleanup_succeeded is True
    assert popen_options["shell"] is False
    assert popen_options["start_new_session"] is True
    assert killed_groups == [(4321, int(getattr(benchmark_compare.signal, "SIGKILL", 9)))]
    assert fake_process.wait_calls == 2


def test_windows_job_is_terminated_and_closed_even_after_success(monkeypatch: Any) -> None:
    class FakeProcess:
        pid = 9876
        _handle = 1234

        def __init__(self) -> None:
            self.wait_calls = 0

        def wait(self, timeout: float) -> int:
            self.wait_calls += 1
            return 0

        def kill(self) -> None:
            raise AssertionError("direct kill must not replace owned Job cleanup")

    fake_process = FakeProcess()
    popen_options: dict[str, Any] = {}
    job_events: list[tuple[str, int]] = []

    def fake_popen(_argv: list[str], **kwargs: Any) -> FakeProcess:
        popen_options.update(kwargs)
        return fake_process

    monkeypatch.setattr(benchmark_compare.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(benchmark_compare, "_assign_windows_kill_job", lambda _process: 77)
    monkeypatch.setattr(
        benchmark_compare,
        "_terminate_windows_job",
        lambda job: job_events.append(("terminate", job)) or True,
    )
    monkeypatch.setattr(
        benchmark_compare,
        "_close_windows_job",
        lambda job: job_events.append(("close", job)) or True,
    )

    result = benchmark_compare._run_owned_process_tree(
        ["child"],
        cwd=Path.cwd(),
        environment={"PATH": "safe"},
        stdout_handle=io.BytesIO(),
        stderr_handle=io.BytesIO(),
        timeout_seconds=1800,
        platform_name="nt",
    )

    assert result.timed_out is False
    assert result.returncode == 0
    assert result.ownership == "WINDOWS_JOB_OBJECT_KILL_ON_CLOSE"
    assert result.cleanup_succeeded is True
    assert popen_options["shell"] is False
    assert "creationflags" in popen_options
    assert job_events == [("terminate", 77), ("close", 77)]
    assert fake_process.wait_calls == 2


def test_windows_job_assignment_failure_fails_closed(monkeypatch: Any) -> None:
    class FakeProcess:
        pid = 2468
        _handle = 5678

        def __init__(self) -> None:
            self.killed = False

        def wait(self, timeout: float) -> int:
            return 1

        def kill(self) -> None:
            self.killed = True

    fake_process = FakeProcess()
    monkeypatch.setattr(
        benchmark_compare.subprocess,
        "Popen",
        lambda _argv, **_kwargs: fake_process,
    )
    monkeypatch.setattr(
        benchmark_compare,
        "_assign_windows_kill_job",
        lambda _process: (_ for _ in ()).throw(OSError("job unavailable")),
    )

    with pytest.raises(benchmark_compare.ProcessTreeOwnershipError):
        benchmark_compare._run_owned_process_tree(
            ["child"],
            cwd=Path.cwd(),
            environment={"PATH": "safe"},
            stdout_handle=io.BytesIO(),
            stderr_handle=io.BytesIO(),
            timeout_seconds=1800,
            platform_name="nt",
        )

    assert fake_process.killed is True


def test_nested_or_unexpected_candidate_content_fails_closed_directory_rule(
    tmp_path: Path,
) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    nested = records_root / "qwen" / "omitted-attempt"
    _write_json(nested / "candidate-004.json", {"hidden": True})

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "LEDGER_INCOMPLETE" for item in result["errors"])


def test_candidate_timestamps_must_increase_with_sequence(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    record_path = records_root / "openai" / "candidate-002.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["started_at_utc"] = "2026-07-20T00:00:30Z"
    _write_json(record_path, record)
    ledger_path = records_root / "openai" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["records"][1]["sha256"] = _sha256(record_path)
    _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "LEDGER_CHRONOLOGY" for item in result["errors"])


def test_pending_report_withholds_even_valid_partial_metric_population(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    contract["status"] = "PENDING"
    result = evaluate(contract, repo_root=repo, records_root=records_root)

    markdown = render_markdown(contract, result)

    assert result["status"] == "PENDING"
    assert "WITHHELD UNTIL COMPLETE" in markdown
    assert "20 [10" not in markdown


def test_malformed_classification_is_invalid_instead_of_crashing(tmp_path: Path) -> None:
    contract, repo, records_root = _complete_records(tmp_path)
    record_path = records_root / "qwen" / "candidate-001.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["classification"] = ["VALID"]
    _write_json(record_path, record)
    ledger_path = records_root / "qwen" / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["records"][0]["sha256"] = _sha256(record_path)
    _write_json(ledger_path, ledger)

    result = evaluate(contract, repo_root=repo, records_root=records_root)

    assert result["status"] == "INVALID"
    assert any(item["code"] == "RUN_CLASSIFICATION" for item in result["errors"])


def test_openai_runtime_failure_refuses_before_evidence_or_provider_access(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    contract, openai_repo = _ready_contract(tmp_path)
    qwen_repo = tmp_path / "qwen-repo"
    qwen_repo.mkdir()
    key_file = tmp_path / "openai-key.txt"
    key_file.write_text("private-key-marker", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(key_file))
    monkeypatch.setattr(
        benchmark_compare,
        "_verify_openai_runtime",
        lambda _repo, _contract: [
            benchmark_compare.Issue(
                "OPENAI_RUNTIME_VERSION",
                "fixture wrong Python version",
            )
        ],
    )
    evidence_dir = tmp_path / "must-not-be-read"
    private_root = tmp_path / "must-not-be-created"

    result, exit_code = benchmark_compare.execute_external_runs(
        contract,
        openai_repo=openai_repo,
        qwen_repo=qwen_repo,
        evidence_dir=evidence_dir,
        private_run_root=private_root,
        systems=("openai",),
        candidate_sequence=1,
    )

    assert exit_code == 1
    assert result["status"] == "REFUSED"
    assert result["provider_or_evidence_accessed"] is False
    assert any(item["code"] == "OPENAI_RUNTIME_VERSION" for item in result["errors"])
    assert not evidence_dir.exists()
    assert not private_root.exists()


def test_execution_captures_logs_isolates_credentials_and_detects_repo_drift(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    contract, openai_repo = _ready_contract(tmp_path)
    qwen_repo = tmp_path / "qwen-repo"
    qwen_repo.mkdir()
    evidence_dir = tmp_path / "evidence"
    private_root = tmp_path / "private-launches"
    key_file = tmp_path / "openai-key.txt"
    key_file.write_text("private-key-marker", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(key_file))
    monkeypatch.setenv("DASHSCOPE_API_KEY", "cross-provider-marker")
    monkeypatch.setenv("GH_TOKEN", "agent-marker")

    repository_checks = 0

    def fake_verify_repository(
        _repo: Path,
        _system: str,
        _contract: dict[str, Any],
        *,
        expected_commit: str,
    ) -> list[benchmark_compare.Issue]:
        assert len(expected_commit) == 40
        nonlocal repository_checks
        repository_checks += 1
        if repository_checks == 1:
            return []
        return [benchmark_compare.Issue("REPOSITORY_DIRTY", "post-run drift fixture")]

    evidence_file = evidence_dir / "memory.mem"

    def fake_verify_evidence(
        _path: Path, _contract: dict[str, Any]
    ) -> tuple[Path, list[benchmark_compare.Issue]]:
        return evidence_file, []

    captured_environment: dict[str, str] = {}

    def fake_owned_run(
        _argv: list[str],
        *,
        cwd: Path,
        environment: dict[str, str],
        stdout_handle: Any,
        stderr_handle: Any,
        timeout_seconds: int,
    ) -> benchmark_compare.OwnedProcessResult:
        assert cwd == openai_repo.resolve()
        captured_environment.update(environment)
        stdout_handle.write(b"private-child-stdout-marker")
        stderr_handle.write(b"private-child-stderr-marker")
        assert timeout_seconds == 1800
        return benchmark_compare.OwnedProcessResult(
            returncode=0,
            timed_out=False,
            ownership="WINDOWS_JOB_OBJECT_KILL_ON_CLOSE",
            cleanup_succeeded=True,
        )

    monkeypatch.setattr(benchmark_compare, "_verify_repository", fake_verify_repository)
    resolved_commit = _repository_commits(contract, openai_repo)["openai"]
    monkeypatch.setattr(
        benchmark_compare,
        "_resolve_freeze_anchor",
        lambda _contract, _repo, **_kwargs: (
            benchmark_compare.ResolvedFreezeAnchor(
                commit=resolved_commit,
                tagger_timestamp=benchmark_compare.datetime.fromisoformat(
                    "2026-07-19T00:00:00+00:00"
                ),
                tagger_timestamp_text="2026-07-19T00:00:00Z",
            ),
            [],
            [],
        ),
    )
    monkeypatch.setattr(benchmark_compare, "_verify_evidence_directory", fake_verify_evidence)
    monkeypatch.setattr(benchmark_compare, "_verify_openai_runtime", lambda _repo, _contract: [])
    monkeypatch.setattr(benchmark_compare, "_run_owned_process_tree", fake_owned_run)

    result, exit_code = benchmark_compare.execute_external_runs(
        contract,
        openai_repo=openai_repo,
        qwen_repo=qwen_repo,
        evidence_dir=evidence_dir,
        private_run_root=private_root,
        systems=("openai",),
        candidate_sequence=1,
    )

    public_result = json.dumps(result)
    assert exit_code == 1
    assert result["status"] == "EXECUTION_REQUIRES_REVIEW"
    assert result["provider_or_evidence_accessed"] is True
    assert result["executions"][0]["post_run_repository_verified"] is False
    assert result["executions"][0]["process_tree_cleanup_succeeded"] is True
    assert result["executions"][0]["post_run_repository_issue_codes"] == ["REPOSITORY_DIRTY"]
    assert captured_environment["OPENAI_API_KEY_FILE"] == str(key_file)
    assert "DASHSCOPE_API_KEY" not in captured_environment
    assert "GH_TOKEN" not in captured_environment
    assert "private-child-stdout-marker" not in public_result
    assert "private-child-stderr-marker" not in public_result
    assert (private_root / "openai-001.stdout.log").read_bytes() == b"private-child-stdout-marker"
    assert (private_root / "openai-001.stderr.log").read_bytes() == b"private-child-stderr-marker"


def test_external_timeout_is_retained_as_launch_error(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    contract, openai_repo = _ready_contract(tmp_path)
    qwen_repo = tmp_path / "qwen-repo"
    qwen_repo.mkdir()
    evidence_dir = tmp_path / "evidence"
    private_root = tmp_path / "private-launches"
    key_file = tmp_path / "openai-key.txt"
    key_file.write_text("private-key-marker", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(key_file))

    monkeypatch.setattr(
        benchmark_compare,
        "_verify_repository",
        lambda _repo, _system, _contract, *, expected_commit: [],
    )
    resolved_commit = _repository_commits(contract, openai_repo)["openai"]
    monkeypatch.setattr(
        benchmark_compare,
        "_resolve_freeze_anchor",
        lambda _contract, _repo, **_kwargs: (
            benchmark_compare.ResolvedFreezeAnchor(
                commit=resolved_commit,
                tagger_timestamp=benchmark_compare.datetime.fromisoformat(
                    "2026-07-19T00:00:00+00:00"
                ),
                tagger_timestamp_text="2026-07-19T00:00:00Z",
            ),
            [],
            [],
        ),
    )
    evidence_file = evidence_dir / "memory.mem"
    monkeypatch.setattr(
        benchmark_compare,
        "_verify_evidence_directory",
        lambda _path, _contract: (evidence_file, []),
    )
    monkeypatch.setattr(benchmark_compare, "_verify_openai_runtime", lambda _repo, _contract: [])

    monkeypatch.setattr(
        benchmark_compare,
        "_run_owned_process_tree",
        lambda *_args, **_kwargs: benchmark_compare.OwnedProcessResult(
            returncode=None,
            timed_out=True,
            ownership="WINDOWS_JOB_OBJECT_KILL_ON_CLOSE",
            cleanup_succeeded=True,
        ),
    )

    result, exit_code = benchmark_compare.execute_external_runs(
        contract,
        openai_repo=openai_repo,
        qwen_repo=qwen_repo,
        evidence_dir=evidence_dir,
        private_run_root=private_root,
        systems=("openai",),
        candidate_sequence=1,
    )

    assert exit_code == 1
    assert result["status"] == "EXECUTION_REQUIRES_REVIEW"
    assert result["executions"][0]["status"] == "LAUNCH_ERROR_TIMEOUT"
    assert result["executions"][0]["process_tree_cleanup_succeeded"] is True
    assert result["executions"][0]["post_run_repository_verified"] is True
    receipt = json.loads((private_root / "openai-001-launch.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "LAUNCH_ERROR_TIMEOUT"
    assert receipt["exit_code"] is None
    assert receipt["process_tree_cleanup_succeeded"] is True


def test_execute_and_report_are_refused_together_before_any_access(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_compare.py",
            "--execute",
            "--write-report",
            str(tmp_path / "must-not-be-written.md"),
            "--json",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "REFUSED"
    assert payload["provider_or_evidence_accessed"] is False
    assert payload["errors"][0]["code"] == "REPORT_REFUSED_DURING_EXECUTION"
    assert not (tmp_path / "must-not-be-written.md").exists()


def test_execute_rejects_external_contract_authority_before_any_access(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    external_contract = tmp_path / "comparison.json"
    _write_json(external_contract, _source_contract())
    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_compare.py",
            "--execute",
            "--contract",
            str(external_contract),
            "--json",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "REFUSED"
    assert payload["provider_or_evidence_accessed"] is False
    assert payload["errors"][0]["code"] == "EXECUTION_CONTRACT_AUTHORITY"
