#!/usr/bin/env python3
"""Plan, guard, and aggregate the frozen Qwen-versus-Unchained comparison.

The default invocation is deliberately read-only.  It validates the committed
comparison contract and any sanitized run ledgers, then prints a public-safe
status.  Provider-backed execution is reachable only through ``--execute`` and
is refused until the freeze, repository, evidence, and credential-presence
checks all pass.

This script never treats the historical Qwen memory-plus-disk metrics as a
same-evidence baseline.  A comparison is qualified as SAME_EVIDENCE only when
every retained candidate record binds the exact same memory-only evidence
identity, frozen fact set, repository commits, and metric contract.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata as importlib_metadata
import json
import math
import os
import platform
import re
import signal
import stat
import statistics
import subprocess
import sys
import time
import tomllib
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "docs" / "QWEN-COMPARISON.v1.json"
DEFAULT_RECORDS_ROOT = REPO_ROOT / "docs" / "runs" / "comparison-inputs"
DEFAULT_REPORT = REPO_ROOT / "docs" / "runs" / "comparison.md"

MAX_JSON_BYTES = 2 * 1024 * 1024
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SAFE_RECORD_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*\.json$")
SYSTEMS = ("openai", "qwen")
EXPECTED_RUNNER_ARGV = {
    "openai": [
        "{python}",
        "-I",
        "-m",
        "unchained",
        "run",
        "{evidence_dir}",
        "--caps",
        "default",
    ],
    "qwen": [
        "docker",
        "run",
        "--rm",
        "--name",
        "{container_name}",
        "--cidfile",
        "{cidfile}",
        "--mount",
        "type=bind,src={evidence_dir},dst=/evidence,readonly",
        "--env",
        "DASHSCOPE_API_KEY",
        "--env",
        "QWEN_API_KEY",
        "{qwen_image_digest}",
        "/evidence",
    ],
}
EXPECTED_CREDENTIAL_ENV = {
    "openai": ["OPENAI_API_KEY_FILE"],
    "qwen": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
}
MINIMAL_CHILD_ENV_NAMES = frozenset(
    {
        "COMSPEC",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "PATHEXT",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
        "WINDIR",
    }
)
CHILD_ENVIRONMENT_POLICY = "MINIMAL_NONSECRET_ALLOWLIST_PLUS_SELECTED_PROVIDER_CREDENTIALS_V1"
PROCESS_TREE_POLICY = "WINDOWS_JOB_OBJECT_KILL_ON_CLOSE_OR_POSIX_NEW_SESSION_PROCESS_GROUP_V1"
AGGREGATION_HEAD_POLICY = "CLEAN_TAG_DESCENDANT_CHANGING_ONLY_COMPARISON_RESULTS_V1"
EXPECTED_WORKLOAD_OWNERSHIP = {
    "openai": "CONTROLLER_OWNED_LOCAL_PROCESS_TREE_V1",
    "qwen": "DOCKER_DAEMON_CONTAINER_OWNERSHIP_UNAVAILABLE_FAIL_CLOSED",
}
EXPECTED_RUNTIME_CONTRACT = {
    "openai": {
        "policy_id": "TAGGED_CPYTHON311_PACKAGE_LOCK_AND_PROVIDER_RECEIPTS_V1",
        "python_implementation": "CPython",
        "python_version": "3.11.9",
        "dependency_lock_path": "requirements/pylock.windows-amd64-cp311.toml",
        "dependency_lock_sha256": (
            "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7"
        ),
    },
    "qwen": {
        "policy_id": "PINNED_DOCKERFILE_IMAGE_BUILD_AND_PROVIDER_RECEIPTS_V1",
        "execution_surface": (
            "Prebuilt immutable Docker image by digest; build excluded from run timing"
        ),
        "dependency_authority": "Dockerfile and dependency files at repository_commit",
        "immutable_image_digest": None,
        "build_provenance_path": "docs/runs/qwen-build-provenance-v1.json",
        "build_provenance_sha256": None,
        "sbom_path": "docs/runs/qwen-sbom-v1.json",
        "sbom_sha256": None,
    },
}
EXPECTED_CAP_CONTRACT = {
    "openai": {
        "profile": "default",
        "max_tool_calls": 60,
        "max_total_tokens": 400000,
        "max_wall_seconds": 1800.0,
        "max_cost_usd": 10.0,
    },
    "qwen": {
        "policy_id": "NO_EQUIVALENT_GLOBAL_TOKEN_OR_COST_CAP_V1",
        "global_token_cap": None,
        "global_cost_cap_usd": None,
        "http_timeout_seconds": 600,
    },
}
EXPECTED_MEASUREMENT_REGIME = {
    "candidate_order": "PAIRED_OPENAI_THEN_QWEN_BY_SEQUENCE_V1",
    "timing_scope": "PREBUILT_RUNTIME_INVESTIGATION_ONLY_EXCLUDES_BUILD_AND_INSTALL_V1",
    "cache_policy": "WARM_DEPENDENCY_CACHE_COLD_CASE_OUTPUT_NO_PROVIDER_RESPONSE_REUSE_V1",
    "runtime_build_metrics": "SEPARATE_DISCLOSED_NOT_IN_INVESTIGATION_WALL_TIME_V1",
    "host_resource_receipt_path": "docs/runs/comparison-host-resources-v1.json",
    "host_resource_receipt_sha256": None,
}
EXTRACTION_POLICY = "LEDGER_BOUND_SANITIZED_EXTRACTION_V1"
EXTRACTION_SOURCE_VERIFICATION = "HASH_REFERENCE_ONLY_SOURCE_NOT_REVERIFIED_BY_AGGREGATOR"
ADJUDICATION_POLICY = "LEDGER_BOUND_ITEM_LEVEL_SHARED_SCORER_ADJUDICATION_V1"
FACTUAL_LABELS = frozenset({"CORRECT", "INCORRECT", "AMBIGUOUS", "OUT_OF_RUBRIC"})
RECEIPT_LABELS = frozenset({"SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED"})

SCALAR_METRICS = (
    "wall_time_seconds",
    "time_to_first_observation_seconds",
    "model_request_count",
    "tool_call_count",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost_usd",
)
RATE_METRICS = (
    "final_confirmed_factual_precision",
    "discovered_fact_recall",
    "confirmed_fact_recall",
    "unsupported_finding_rate",
    "exact_citation_resolution_rate",
)
SCORE_METRICS = ("confirmed_f1",)
BOOLEAN_METRICS = ("custody_pass", "native_verifier_pass")
ALL_METRICS = SCALAR_METRICS + RATE_METRICS + SCORE_METRICS + BOOLEAN_METRICS

VALID_CLASSIFICATIONS = frozenset(
    {"VALID", "INFRASTRUCTURE_FAULT", "PARTIAL_CAP", "PROTOCOL_INVALID"}
)


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class LoadedRecord:
    system: str
    sequence: int
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ResolvedFreezeAnchor:
    commit: str
    tagger_timestamp: datetime
    tagger_timestamp_text: str


@dataclass(frozen=True, slots=True)
class OwnedProcessResult:
    returncode: int | None
    timed_out: bool
    ownership: str
    cleanup_succeeded: bool


class ProcessTreeOwnershipError(RuntimeError):
    """Raised when an external child cannot enter a controller-owned process tree."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_canonical_lf_text_file(path: Path) -> str:
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return _sha256_bytes(normalized)


def _read_json(path: Path, *, label: str) -> tuple[dict[str, Any] | None, list[Issue]]:
    try:
        info = path.lstat()
    except OSError as exc:
        return None, [Issue("JSON_MISSING", f"{label} is unavailable: {type(exc).__name__}")]
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return None, [Issue("JSON_UNSAFE", f"{label} must be a regular non-symlink file")]
    if info.st_size > MAX_JSON_BYTES:
        return None, [Issue("JSON_TOO_LARGE", f"{label} exceeds {MAX_JSON_BYTES} bytes")]
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [Issue("JSON_INVALID", f"{label} is invalid JSON: {type(exc).__name__}")]
    if not isinstance(value, dict):
        return None, [Issue("JSON_SCHEMA", f"{label} must be a JSON object")]
    return value, []


def _closed_fields(
    value: dict[str, Any],
    expected: set[str],
    *,
    label: str,
) -> list[Issue]:
    actual = set(value)
    if actual == expected:
        return []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    return [
        Issue(
            "SCHEMA_FIELDS",
            f"{label} fields differ; missing={missing!r}, extra={extra!r}",
        )
    ]


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_contract(contract: dict[str, Any]) -> tuple[list[Issue], list[Issue]]:
    """Return hard errors and honest readiness blockers for a contract."""

    errors = _closed_fields(
        contract,
        {
            "schema_version",
            "comparison_id",
            "status",
            "qualification",
            "freeze",
            "evidence",
            "repositories",
            "systems",
            "execution",
            "metrics",
            "run_record_contract",
            "disclosed_differences",
            "claim_policy",
        },
        label="comparison contract",
    )
    pending: list[Issue] = []
    if errors:
        return errors, pending

    if contract["schema_version"] != 1:
        errors.append(Issue("CONTRACT_VERSION", "comparison contract schema_version must be 1"))
    if not isinstance(contract["comparison_id"], str) or not contract["comparison_id"]:
        errors.append(Issue("COMPARISON_ID", "comparison_id must be a nonempty string"))
    if not isinstance(contract["status"], str) or contract["status"] not in {
        "PENDING",
        "READY",
    }:
        errors.append(Issue("CONTRACT_STATUS", "contract status must be PENDING or READY"))
    if contract["qualification"] != "CONTROLLED_COMPARATIVE_CASE_STUDY_NOT_CAUSAL_ABLATION":
        errors.append(
            Issue(
                "QUALIFICATION",
                "contract must disclose that the comparison is not a causal ablation",
            )
        )

    freeze = contract["freeze"]
    if not isinstance(freeze, dict):
        errors.append(Issue("FREEZE_SCHEMA", "freeze must be an object"))
    else:
        errors.extend(
            _closed_fields(
                freeze,
                {
                    "freeze_id",
                    "tag",
                    "tag_policy",
                    "aggregation_head_policy",
                    "candidate_time_floor",
                    "external_server_timestamp_utc",
                    "lock_path",
                    "lock_sha256",
                    "reference_fact_set_path",
                    "reference_fact_set_sha256",
                    "shared_scoring_version",
                },
                label="freeze",
            )
        )
        if freeze.get("tag") != "experiment-freeze-v1":
            errors.append(Issue("FREEZE_TAG", "freeze tag name must be experiment-freeze-v1"))
        if freeze.get("tag_policy") != "ANNOTATED_TAG_MUST_RESOLVE_TO_CURRENT_CLEAN_HEAD":
            errors.append(
                Issue(
                    "FREEZE_TAG_POLICY",
                    "freeze tag must be annotated and resolve to the current clean HEAD",
                )
            )
        if freeze.get("aggregation_head_policy") != AGGREGATION_HEAD_POLICY:
            errors.append(
                Issue(
                    "AGGREGATION_HEAD_POLICY",
                    "aggregation descendant policy differs from the closed results-only rule",
                )
            )
        if freeze.get("candidate_time_floor") != "ANNOTATED_TAGGER_TIMESTAMP":
            errors.append(
                Issue(
                    "FREEZE_TIME_POLICY",
                    "candidate time floor must be the retained annotated-tag tagger timestamp",
                )
            )
        for field in ("lock_sha256", "reference_fact_set_sha256"):
            value = freeze.get(field)
            if value is None:
                pending.append(Issue("FREEZE_VALUE_PENDING", f"freeze.{field} is not frozen"))
            elif not isinstance(value, str) or HEX_SHA256.fullmatch(value) is None:
                errors.append(Issue("FREEZE_VALUE", f"freeze.{field} has an invalid digest"))
        timestamp_value = freeze.get("external_server_timestamp_utc")
        if timestamp_value is not None:
            try:
                timestamp = datetime.fromisoformat(str(timestamp_value).replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    raise ValueError
            except ValueError:
                errors.append(
                    Issue(
                        "FREEZE_TIMESTAMP",
                        "optional external server timestamp must be timezone-aware ISO 8601",
                    )
                )

    evidence = contract["evidence"]
    if not isinstance(evidence, dict):
        errors.append(Issue("EVIDENCE_SCHEMA", "evidence must be an object"))
    else:
        errors.extend(
            _closed_fields(
                evidence,
                {"case_id", "public_evidence_id", "route", "size_bytes", "sha256"},
                label="evidence",
            )
        )
        if evidence.get("route") != "windows-memory-only":
            errors.append(Issue("EVIDENCE_ROUTE", "comparison route must be windows-memory-only"))
        if not isinstance(evidence.get("size_bytes"), int) or isinstance(
            evidence.get("size_bytes"), bool
        ):
            errors.append(Issue("EVIDENCE_SIZE", "evidence size_bytes must be an integer"))
        if (
            not isinstance(evidence.get("sha256"), str)
            or HEX_SHA256.fullmatch(evidence.get("sha256", "")) is None
        ):
            errors.append(Issue("EVIDENCE_DIGEST", "evidence sha256 is invalid"))

    repositories = contract["repositories"]
    if not isinstance(repositories, dict) or set(repositories) != set(SYSTEMS):
        errors.append(Issue("REPOSITORY_SCHEMA", "repositories must contain openai and qwen"))
    else:
        for system in SYSTEMS:
            repository = repositories[system]
            if not isinstance(repository, dict):
                errors.append(Issue("REPOSITORY_SCHEMA", f"{system} repository must be an object"))
                continue
            expected_fields = (
                {"commit_policy", "required_ancestor", "public_repository"}
                if system == "openai"
                else {"required_commit", "required_ancestor", "public_repository"}
            )
            errors.extend(
                _closed_fields(
                    repository,
                    expected_fields,
                    label=f"repositories.{system}",
                )
            )
            if system == "openai" and repository.get("commit_policy") != (
                "RESOLVED_ANNOTATED_FREEZE_TAG_COMMIT"
            ):
                errors.append(
                    Issue(
                        "REPOSITORY_COMMIT_POLICY",
                        "OpenAI commit must be resolved from the annotated freeze tag",
                    )
                )
            if system == "qwen":
                commit = repository.get("required_commit")
                if not isinstance(commit, str) or HEX_GIT_SHA.fullmatch(commit) is None:
                    errors.append(
                        Issue(
                            "REPOSITORY_COMMIT",
                            "qwen required_commit must be a full Git SHA",
                        )
                    )
            ancestor = repository.get("required_ancestor")
            if ancestor is not None and (
                not isinstance(ancestor, str) or HEX_GIT_SHA.fullmatch(ancestor) is None
            ):
                errors.append(
                    Issue(
                        "REPOSITORY_ANCESTOR", f"{system} required_ancestor must be null or a SHA"
                    )
                )

    systems = contract["systems"]
    if not isinstance(systems, dict) or set(systems) != set(SYSTEMS):
        errors.append(Issue("SYSTEM_SCHEMA", "systems must contain openai and qwen"))
    else:
        for system in SYSTEMS:
            value = systems[system]
            if not isinstance(value, dict):
                errors.append(Issue("SYSTEM_SCHEMA", f"systems.{system} must be an object"))
                continue
            errors.extend(
                _closed_fields(
                    value,
                    {
                        "display_name",
                        "runner_argv",
                        "required_environment_any_of",
                        "required_environment_values",
                        "required_requested_models",
                        "accepted_provider_model_patterns",
                        "terminal_complete_value",
                        "tool_policy",
                        "model_policy",
                        "runtime_contract",
                        "cap_contract",
                        "workload_ownership_policy",
                        "cost_basis",
                        "price_contract_path",
                        "price_contract_sha256",
                        "native_verifier",
                    },
                    label=f"systems.{system}",
                )
            )
            argv = value.get("runner_argv")
            if (
                not isinstance(argv, list)
                or not argv
                or any(not isinstance(item, str) or not item for item in argv)
            ):
                errors.append(Issue("RUNNER_ARGV", f"{system} runner_argv must be string argv"))
            elif argv != EXPECTED_RUNNER_ARGV[system]:
                errors.append(
                    Issue(
                        "RUNNER_AUTHORITY",
                        f"{system} runner_argv differs from the fixed no-shell launcher",
                    )
                )
            required_env = value.get("required_environment_any_of")
            if (
                not isinstance(required_env, list)
                or not required_env
                or any(not isinstance(item, str) or not item for item in required_env)
            ):
                errors.append(
                    Issue(
                        "RUNNER_ENV",
                        f"{system} required_environment_any_of must be a nonempty list",
                    )
                )
            elif required_env != EXPECTED_CREDENTIAL_ENV[system]:
                errors.append(
                    Issue(
                        "RUNNER_CREDENTIAL_AUTHORITY",
                        f"{system} credential sources differ from the fixed allowlist",
                    )
                )
            environment_values = value.get("required_environment_values")
            if (
                not isinstance(environment_values, dict)
                or not environment_values
                or any(
                    not isinstance(name, str)
                    or not name
                    or not isinstance(configured, str)
                    or not configured
                    for name, configured in (
                        environment_values.items() if isinstance(environment_values, dict) else ()
                    )
                )
            ):
                errors.append(
                    Issue(
                        "RUNNER_ENV_VALUES",
                        f"{system} required_environment_values must be a nonempty string map",
                    )
                )
            requested_models = value.get("required_requested_models")
            if (
                not isinstance(requested_models, list)
                or not requested_models
                or any(not isinstance(item, str) or not item for item in requested_models)
                or len(requested_models) != len(set(requested_models))
            ):
                errors.append(
                    Issue(
                        "MODEL_POLICY",
                        f"{system} required requested-model set must be nonempty and unique",
                    )
                )
            provider_patterns = value.get("accepted_provider_model_patterns")
            if (
                not isinstance(provider_patterns, list)
                or not provider_patterns
                or any(not isinstance(item, str) or not item for item in provider_patterns)
            ):
                errors.append(
                    Issue(
                        "MODEL_POLICY",
                        f"{system} provider-model patterns must be nonempty",
                    )
                )
            else:
                for pattern in provider_patterns:
                    try:
                        re.compile(pattern)
                    except re.error:
                        errors.append(
                            Issue("MODEL_POLICY", f"{system} provider-model regex is invalid")
                        )
            runtime_contract = value.get("runtime_contract")
            if system == "openai":
                if runtime_contract != EXPECTED_RUNTIME_CONTRACT[system]:
                    errors.append(
                        Issue(
                            "RUNTIME_CONTRACT",
                            "openai runtime contract differs from the frozen policy",
                        )
                    )
            elif not isinstance(runtime_contract, dict) or set(runtime_contract) != set(
                EXPECTED_RUNTIME_CONTRACT[system]
            ):
                errors.append(
                    Issue(
                        "RUNTIME_CONTRACT",
                        "qwen runtime contract must be the closed immutable-image receipt",
                    )
                )
            else:
                for name in (
                    "policy_id",
                    "execution_surface",
                    "dependency_authority",
                    "build_provenance_path",
                    "sbom_path",
                ):
                    if runtime_contract.get(name) != EXPECTED_RUNTIME_CONTRACT[system][name]:
                        errors.append(
                            Issue(
                                "RUNTIME_CONTRACT",
                                f"qwen runtime {name} differs from the frozen policy",
                            )
                        )
                image_digest = runtime_contract.get("immutable_image_digest")
                if image_digest is None:
                    pending.append(
                        Issue(
                            "QWEN_IMAGE_DIGEST_PENDING",
                            "Qwen immutable prebuilt image digest is not frozen",
                        )
                    )
                elif (
                    not isinstance(image_digest, str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest) is None
                ):
                    errors.append(
                        Issue(
                            "QWEN_IMAGE_DIGEST",
                            "Qwen immutable image digest must be sha256:<64 lowercase hex>",
                        )
                    )
                for name in ("build_provenance_sha256", "sbom_sha256"):
                    digest = runtime_contract.get(name)
                    if digest is None:
                        pending.append(
                            Issue(
                                "QWEN_RUNTIME_PROVENANCE_PENDING",
                                f"Qwen {name} is not frozen",
                            )
                        )
                    elif not isinstance(digest, str) or HEX_SHA256.fullmatch(digest) is None:
                        errors.append(
                            Issue(
                                "QWEN_RUNTIME_PROVENANCE",
                                f"Qwen {name} is invalid",
                            )
                        )
            if value.get("cap_contract") != EXPECTED_CAP_CONTRACT[system]:
                errors.append(
                    Issue(
                        "CAP_CONTRACT",
                        f"{system} cap contract differs from the frozen policy",
                    )
                )
            if value.get("workload_ownership_policy") != EXPECTED_WORKLOAD_OWNERSHIP[system]:
                errors.append(
                    Issue(
                        "WORKLOAD_OWNERSHIP_POLICY",
                        f"{system} workload ownership policy differs from the frozen policy",
                    )
                )
            price_path = value.get("price_contract_path")
            price_digest = value.get("price_contract_sha256")
            if price_digest is None:
                pending.append(
                    Issue("PRICE_CONTRACT_PENDING", f"{system} price contract is not frozen")
                )
            elif not isinstance(price_digest, str) or HEX_SHA256.fullmatch(price_digest) is None:
                errors.append(
                    Issue("PRICE_CONTRACT", f"{system} price contract SHA-256 is invalid")
                )
            if not isinstance(price_path, str) or not price_path:
                errors.append(Issue("PRICE_CONTRACT", f"{system} price contract path is invalid"))

    execution = contract["execution"]
    if not isinstance(execution, dict):
        errors.append(Issue("EXECUTION_SCHEMA", "execution must be an object"))
    else:
        errors.extend(
            _closed_fields(
                execution,
                {
                    "default_mode",
                    "provider_execution_switch",
                    "order",
                    "external_child_timeout_seconds",
                    "child_environment_policy",
                    "process_tree_policy",
                    "measurement_regime",
                    "target_valid_runs_per_system",
                    "selection_rule",
                    "ledger_rule",
                    "private_launch_receipts",
                    "infrastructure_fault_codes",
                    "not_infrastructure_faults",
                },
                label="execution",
            )
        )
        if execution.get("default_mode") != "DRY_RUN_NO_PROVIDER_NO_EVIDENCE_READ":
            errors.append(Issue("DEFAULT_MODE", "default mode must be the no-access dry run"))
        if execution.get("provider_execution_switch") != "--execute":
            errors.append(Issue("EXECUTION_SWITCH", "provider execution switch must be --execute"))
        if execution.get("order") != list(SYSTEMS):
            errors.append(
                Issue("EXECUTION_ORDER", "execution order must explicitly list both systems")
            )
        child_timeout = execution.get("external_child_timeout_seconds")
        if (
            not isinstance(child_timeout, int)
            or isinstance(child_timeout, bool)
            or child_timeout != 1800
        ):
            errors.append(
                Issue(
                    "EXTERNAL_CHILD_TIMEOUT",
                    "the neutral per-child external wall timeout must be frozen at 1800 seconds",
                )
            )
        if execution.get("child_environment_policy") != CHILD_ENVIRONMENT_POLICY:
            errors.append(
                Issue(
                    "CHILD_ENVIRONMENT_POLICY",
                    "external child environment policy differs from the minimal allowlist",
                )
            )
        if execution.get("process_tree_policy") != PROCESS_TREE_POLICY:
            errors.append(
                Issue(
                    "PROCESS_TREE_POLICY",
                    "external process-tree ownership policy is not frozen",
                )
            )
        measurement_regime = execution.get("measurement_regime")
        if not isinstance(measurement_regime, dict) or set(measurement_regime) != set(
            EXPECTED_MEASUREMENT_REGIME
        ):
            errors.append(
                Issue(
                    "MEASUREMENT_REGIME",
                    "measurement regime must be the closed prebuilt paired-run policy",
                )
            )
        else:
            for name, expected in EXPECTED_MEASUREMENT_REGIME.items():
                if name == "host_resource_receipt_sha256":
                    continue
                if measurement_regime.get(name) != expected:
                    errors.append(
                        Issue(
                            "MEASUREMENT_REGIME",
                            f"measurement regime {name} differs from the frozen policy",
                        )
                    )
            host_digest = measurement_regime.get("host_resource_receipt_sha256")
            if host_digest is None:
                pending.append(
                    Issue(
                        "HOST_RESOURCE_RECEIPT_PENDING",
                        "shared host/resource receipt is not frozen",
                    )
                )
            elif not isinstance(host_digest, str) or HEX_SHA256.fullmatch(host_digest) is None:
                errors.append(
                    Issue(
                        "HOST_RESOURCE_RECEIPT",
                        "shared host/resource receipt digest is invalid",
                    )
                )
        target = execution.get("target_valid_runs_per_system")
        if not isinstance(target, int) or isinstance(target, bool) or target < 1:
            errors.append(Issue("RUN_TARGET", "target_valid_runs_per_system must be positive"))
        fault_codes = execution.get("infrastructure_fault_codes")
        if (
            not isinstance(fault_codes, list)
            or not fault_codes
            or any(not isinstance(item, str) or not item for item in fault_codes)
            or len(fault_codes) != len(set(fault_codes))
        ):
            errors.append(
                Issue("INFRASTRUCTURE_FAULTS", "infrastructure fault codes must be frozen")
            )
        nonfaults = execution.get("not_infrastructure_faults")
        if not isinstance(nonfaults, list) or len(nonfaults) < 3:
            errors.append(
                Issue("NON_INFRASTRUCTURE_FAILURES", "semantic/nonfatal failures must be frozen")
            )

    if contract["metrics"] != list(ALL_METRICS):
        errors.append(Issue("METRIC_SET", "metrics do not equal the frozen comparison metric set"))
    record_contract = contract["run_record_contract"]
    if not isinstance(record_contract, dict):
        errors.append(Issue("RUN_RECORD_CONTRACT", "run_record_contract must be an object"))
    else:
        errors.extend(
            _closed_fields(
                record_contract,
                {
                    "location",
                    "ledger",
                    "rates",
                    "sidecars",
                    "runtime_and_caps",
                    "classification",
                },
                label="run_record_contract",
            )
        )
        classifications = record_contract.get("classification")
        if (
            not isinstance(classifications, list)
            or any(not isinstance(item, str) for item in classifications)
            or set(classifications) != VALID_CLASSIFICATIONS
        ):
            errors.append(
                Issue("RUN_RECORD_CONTRACT", "candidate classification set is not frozen")
            )
    if (
        not isinstance(contract["disclosed_differences"], list)
        or len(contract["disclosed_differences"]) < 5
        or any(not isinstance(item, str) or not item for item in contract["disclosed_differences"])
    ):
        errors.append(
            Issue(
                "DIFFERENCE_DISCLOSURE", "at least five architecture differences must be disclosed"
            )
        )

    claim_policy = contract["claim_policy"]
    if not isinstance(claim_policy, dict):
        errors.append(Issue("CLAIM_POLICY", "claim_policy must be an object"))
    else:
        errors.extend(
            _closed_fields(
                claim_policy,
                {
                    "current_claim",
                    "same_evidence_requires",
                    "superiority_requires",
                    "historical_qwen_metrics",
                },
                label="claim_policy",
            )
        )
        if claim_policy.get("current_claim") != "PENDING_NO_SAME_EVIDENCE_RESULT":
            errors.append(Issue("CURRENT_CLAIM", "current claim must remain explicitly pending"))
        invariants = claim_policy.get("same_evidence_requires")
        required = {
            "case_id",
            "public_evidence_id",
            "route",
            "size_bytes",
            "sha256",
            "reference_fact_set_sha256",
            "repository_commits",
            "complete_candidate_ledgers",
        }
        if (
            not isinstance(invariants, list)
            or any(not isinstance(item, str) for item in invariants)
            or set(invariants) != required
        ):
            errors.append(Issue("SAME_EVIDENCE_POLICY", "same-evidence invariants are incomplete"))

    if contract["status"] == "READY" and pending:
        errors.append(Issue("READY_WITH_PENDING_VALUES", "READY contract contains unfrozen values"))
    return errors, pending


def validate_bound_files(
    contract: dict[str, Any],
    *,
    repo_root: Path,
) -> tuple[list[Issue], list[Issue]]:
    errors: list[Issue] = []
    pending: list[Issue] = []
    freeze = contract.get("freeze")
    if not isinstance(freeze, dict):
        return errors, pending
    for path_field, digest_field, label in (
        ("lock_path", "lock_sha256", "benchmark freeze lock"),
        ("reference_fact_set_path", "reference_fact_set_sha256", "reference fact set"),
    ):
        relative = freeze.get(path_field)
        expected = freeze.get(digest_field)
        if expected is None:
            pending.append(Issue("BOUND_FILE_PENDING", f"{label} digest is not frozen"))
            continue
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            errors.append(Issue("BOUND_FILE_PATH", f"{label} path is unsafe"))
            continue
        path = repo_root / relative
        try:
            if not _inside(path.resolve(), repo_root.resolve()):
                raise ValueError("path escapes repository")
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise ValueError("not a regular file")
            actual = _sha256_file(path)
        except (OSError, ValueError) as exc:
            errors.append(
                Issue("BOUND_FILE_MISSING", f"{label} is unavailable: {type(exc).__name__}")
            )
            continue
        if actual != expected:
            errors.append(Issue("BOUND_FILE_DRIFT", f"{label} SHA-256 does not match the contract"))
    systems = contract.get("systems")
    if isinstance(systems, dict):
        openai = systems.get("openai")
        if isinstance(openai, dict):
            runtime = openai.get("runtime_contract")
            if isinstance(runtime, dict):
                relative = runtime.get("dependency_lock_path")
                expected = runtime.get("dependency_lock_sha256")
                if (
                    not isinstance(relative, str)
                    or Path(relative).is_absolute()
                    or ".." in Path(relative).parts
                ):
                    errors.append(Issue("RUNTIME_LOCK_PATH", "OpenAI runtime lock path is unsafe"))
                elif not isinstance(expected, str) or HEX_SHA256.fullmatch(expected) is None:
                    errors.append(
                        Issue("RUNTIME_LOCK_DIGEST", "OpenAI runtime lock digest is invalid")
                    )
                else:
                    try:
                        lock_path = repo_root / relative
                        if not _inside(lock_path.resolve(), repo_root.resolve()):
                            raise ValueError("path escapes repository")
                        info = lock_path.lstat()
                        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                            raise ValueError("not a regular file")
                        actual = _sha256_canonical_lf_text_file(lock_path)
                    except (OSError, ValueError) as exc:
                        errors.append(
                            Issue(
                                "RUNTIME_LOCK_MISSING",
                                f"OpenAI runtime lock is unavailable: {type(exc).__name__}",
                            )
                        )
                    else:
                        if actual != expected:
                            errors.append(
                                Issue(
                                    "RUNTIME_LOCK_DRIFT",
                                    "OpenAI runtime lock SHA-256 differs",
                                )
                            )
        for system in SYSTEMS:
            value = systems.get(system)
            if not isinstance(value, dict):
                continue
            relative = value.get("price_contract_path")
            expected = value.get("price_contract_sha256")
            if expected is None:
                pending.append(
                    Issue("PRICE_CONTRACT_PENDING", f"{system} price contract is not frozen")
                )
                continue
            if (
                not isinstance(relative, str)
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                errors.append(
                    Issue("PRICE_CONTRACT_PATH", f"{system} price contract path is unsafe")
                )
                continue
            try:
                price_path = repo_root / relative
                if not _inside(price_path.resolve(), repo_root.resolve()):
                    raise ValueError("path escapes repository")
                info = price_path.lstat()
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                    raise ValueError("not a regular file")
                actual = _sha256_file(price_path)
            except (OSError, ValueError) as exc:
                errors.append(
                    Issue(
                        "PRICE_CONTRACT_MISSING",
                        f"{system} price contract is unavailable: {type(exc).__name__}",
                    )
                )
                continue
            if actual != expected:
                errors.append(
                    Issue("PRICE_CONTRACT_DRIFT", f"{system} price contract SHA-256 differs")
                )
        qwen = systems.get("qwen")
        if isinstance(qwen, dict) and isinstance(qwen.get("runtime_contract"), dict):
            runtime = qwen["runtime_contract"]
            for path_field, digest_field, label in (
                ("build_provenance_path", "build_provenance_sha256", "Qwen build provenance"),
                ("sbom_path", "sbom_sha256", "Qwen SBOM"),
            ):
                relative = runtime.get(path_field)
                expected = runtime.get(digest_field)
                if expected is None:
                    pending.append(Issue("QWEN_RUNTIME_FILE_PENDING", f"{label} is not frozen"))
                    continue
                if (
                    not isinstance(relative, str)
                    or Path(relative).is_absolute()
                    or ".." in Path(relative).parts
                ):
                    errors.append(Issue("QWEN_RUNTIME_FILE_PATH", f"{label} path is unsafe"))
                    continue
                try:
                    path = repo_root / relative
                    if not _inside(path.resolve(), repo_root.resolve()):
                        raise ValueError("path escapes repository")
                    info = path.lstat()
                    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                        raise ValueError("not a regular file")
                    actual = _sha256_file(path)
                except (OSError, ValueError) as exc:
                    errors.append(
                        Issue(
                            "QWEN_RUNTIME_FILE_MISSING",
                            f"{label} is unavailable: {type(exc).__name__}",
                        )
                    )
                    continue
                if actual != expected:
                    errors.append(Issue("QWEN_RUNTIME_FILE_DRIFT", f"{label} SHA-256 differs"))
    execution = contract.get("execution")
    if isinstance(execution, dict) and isinstance(execution.get("measurement_regime"), dict):
        regime = execution["measurement_regime"]
        relative = regime.get("host_resource_receipt_path")
        expected = regime.get("host_resource_receipt_sha256")
        if expected is None:
            pending.append(Issue("HOST_RESOURCE_RECEIPT_PENDING", "host receipt is not frozen"))
        elif (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            errors.append(Issue("HOST_RESOURCE_RECEIPT_PATH", "host receipt path is unsafe"))
        else:
            try:
                path = repo_root / relative
                if not _inside(path.resolve(), repo_root.resolve()):
                    raise ValueError("path escapes repository")
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                    raise ValueError("not a regular file")
                actual = _sha256_file(path)
            except (OSError, ValueError) as exc:
                errors.append(
                    Issue(
                        "HOST_RESOURCE_RECEIPT_MISSING",
                        f"host receipt is unavailable: {type(exc).__name__}",
                    )
                )
            else:
                if actual != expected:
                    errors.append(
                        Issue("HOST_RESOURCE_RECEIPT_DRIFT", "host receipt SHA-256 differs")
                    )
    return errors, pending


def _validate_rate(name: str, value: object) -> tuple[float | None, list[Issue]]:
    if not isinstance(value, dict):
        return None, [Issue("METRIC_SCHEMA", f"{name} must be an object")]
    issues = _closed_fields(
        value,
        {"status", "numerator", "denominator", "value"},
        label=f"metric {name}",
    )
    if issues:
        return None, issues
    status_value = value["status"]
    numerator = value["numerator"]
    denominator = value["denominator"]
    result = value["value"]
    if (
        not isinstance(numerator, int)
        or isinstance(numerator, bool)
        or numerator < 0
        or not isinstance(denominator, int)
        or isinstance(denominator, bool)
        or denominator < 0
        or numerator > denominator
    ):
        issues.append(Issue("METRIC_COUNTS", f"{name} has invalid numerator/denominator"))
        return None, issues
    if denominator == 0:
        if status_value != "NOT_APPLICABLE" or result is not None or numerator != 0:
            issues.append(
                Issue("ZERO_DENOMINATOR", f"{name} must be NOT_APPLICABLE at denominator zero")
            )
        return None, issues
    expected = numerator / denominator
    if (
        status_value != "VALUE"
        or not _is_number(result)
        or not math.isclose(float(result), expected, rel_tol=1e-12, abs_tol=1e-12)
    ):
        issues.append(Issue("METRIC_VALUE", f"{name} value does not match its counts"))
        return None, issues
    return expected, issues


def _validate_valid_metrics(metrics: object) -> list[Issue]:
    if not isinstance(metrics, dict):
        return [Issue("METRICS_SCHEMA", "valid run metrics must be an object")]
    issues = _closed_fields(metrics, set(ALL_METRICS), label="valid run metrics")
    if issues:
        return issues
    for name in SCALAR_METRICS:
        value = metrics[name]
        if value is None and name in {
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "estimated_cost_usd",
        }:
            continue
        if not _is_number(value) or float(value) < 0:
            issues.append(Issue("SCALAR_METRIC", f"{name} must be nonnegative or explicitly null"))
    for name in (
        "model_request_count",
        "tool_call_count",
        "input_tokens",
        "output_tokens",
        "total_tokens",
    ):
        value = metrics[name]
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            issues.append(Issue("INTEGER_METRIC", f"{name} must be an integer or null"))
    if (
        all(metrics[name] is not None for name in ("input_tokens", "output_tokens", "total_tokens"))
        and metrics["total_tokens"] != metrics["input_tokens"] + metrics["output_tokens"]
    ):
        issues.append(
            Issue("TOKEN_TOTAL", "total_tokens must equal input_tokens plus output_tokens")
        )
    for name in RATE_METRICS:
        _value, rate_issues = _validate_rate(name, metrics[name])
        issues.extend(rate_issues)
    f1 = metrics["confirmed_f1"]
    if not isinstance(f1, dict):
        issues.append(Issue("F1_SCHEMA", "confirmed_f1 must be an object"))
    else:
        issues.extend(
            _closed_fields(
                f1,
                {"status", "value"},
                label="metric confirmed_f1",
            )
        )
        precision, _ = _validate_rate(
            "final_confirmed_factual_precision", metrics["final_confirmed_factual_precision"]
        )
        recall, _ = _validate_rate("confirmed_fact_recall", metrics["confirmed_fact_recall"])
        if precision is None or recall is None:
            if f1.get("status") != "NOT_APPLICABLE" or f1.get("value") is not None:
                issues.append(Issue("F1_VALUE", "confirmed_f1 must be NOT_APPLICABLE"))
        else:
            expected = (
                0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
            )
            if (
                f1.get("status") != "VALUE"
                or not _is_number(f1.get("value"))
                or not math.isclose(float(f1["value"]), expected, rel_tol=1e-12, abs_tol=1e-12)
            ):
                issues.append(Issue("F1_VALUE", "confirmed_f1 does not match precision/recall"))
    for name in BOOLEAN_METRICS:
        if metrics[name] is not None and not isinstance(metrics[name], bool):
            issues.append(Issue("BOOLEAN_METRIC", f"{name} must be boolean or null"))
    return issues


def _rate_from_counts(numerator: int, denominator: int) -> dict[str, Any]:
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


def _validate_safe_source_reference(
    value: object,
    *,
    label: str,
    expected_method: str | None = None,
) -> list[Issue]:
    if not isinstance(value, dict):
        return [Issue("SIDECAR_SOURCE", f"{label} must be an object")]
    expected_fields = {"artifact_id", "artifact_sha256", "verification"}
    if expected_method is not None:
        expected_fields.add("method")
    issues = _closed_fields(value, expected_fields, label=label)
    if issues:
        return issues
    artifact_id = value["artifact_id"]
    digest = value["artifact_sha256"]
    if (
        not isinstance(artifact_id, str)
        or not artifact_id
        or any(token in artifact_id for token in ("/", "\\", ":"))
        or not isinstance(digest, str)
        or HEX_SHA256.fullmatch(digest) is None
        or value["verification"] != EXTRACTION_SOURCE_VERIFICATION
    ):
        issues.append(
            Issue("SIDECAR_SOURCE", f"{label} is invalid, path-bearing, or overclaims verification")
        )
    if expected_method is not None and value.get("method") != expected_method:
        issues.append(Issue("SIDECAR_SOURCE", f"{label} method differs from the frozen scorer"))
    return issues


def _validate_extraction_receipt(
    contract: dict[str, Any],
    system: str,
    record: dict[str, Any],
    receipt: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[Issue]]:
    issues = _closed_fields(
        receipt,
        {
            "schema_version",
            "comparison_id",
            "system",
            "run_id",
            "policy",
            "source_receipt",
            "values",
        },
        label=f"{system} extraction receipt",
    )
    if issues:
        return None, issues
    if (
        receipt["schema_version"] != 1
        or receipt["comparison_id"] != contract["comparison_id"]
        or receipt["system"] != system
        or receipt["run_id"] != record["run_id"]
        or receipt["policy"] != EXTRACTION_POLICY
    ):
        issues.append(Issue("EXTRACTION_IDENTITY", f"{system} extraction identity is invalid"))
    issues.extend(
        _validate_safe_source_reference(
            receipt["source_receipt"], label=f"{system} extraction source"
        )
    )
    values = receipt["values"]
    value_fields = {
        "wall_time_seconds",
        "time_to_first_observation_seconds",
        "model_request_count",
        "tool_call_count",
        "input_tokens",
        "output_tokens",
        "estimated_cost_usd",
        "custody_pass",
        "native_verifier_pass",
    }
    if not isinstance(values, dict):
        issues.append(Issue("EXTRACTION_VALUES", f"{system} extraction values must be an object"))
        return None, issues
    issues.extend(_closed_fields(values, value_fields, label=f"{system} extraction values"))
    if issues:
        return None, issues
    if record["classification"] != "VALID":
        if any(value is not None for value in values.values()):
            issues.append(
                Issue("EXTRACTION_VALUES", f"nonvalid {system} extraction values must be null")
            )
        return None, issues
    for name in ("wall_time_seconds", "time_to_first_observation_seconds"):
        if not _is_number(values[name]) or float(values[name]) < 0:
            issues.append(Issue("EXTRACTION_VALUES", f"{system} {name} is invalid"))
    for name in ("model_request_count", "tool_call_count"):
        if not isinstance(values[name], int) or isinstance(values[name], bool) or values[name] < 0:
            issues.append(Issue("EXTRACTION_VALUES", f"{system} {name} is invalid"))
    for name in ("input_tokens", "output_tokens"):
        if values[name] is not None and (
            not isinstance(values[name], int) or isinstance(values[name], bool) or values[name] < 0
        ):
            issues.append(Issue("EXTRACTION_VALUES", f"{system} {name} is invalid"))
    if values["estimated_cost_usd"] is not None and (
        not _is_number(values["estimated_cost_usd"]) or float(values["estimated_cost_usd"]) < 0
    ):
        issues.append(Issue("EXTRACTION_VALUES", f"{system} estimated cost is invalid"))
    for name in BOOLEAN_METRICS:
        if values[name] is not None and not isinstance(values[name], bool):
            issues.append(Issue("EXTRACTION_VALUES", f"{system} {name} is invalid"))
    if issues:
        return None, issues
    input_tokens = values["input_tokens"]
    output_tokens = values["output_tokens"]
    total_tokens = (
        input_tokens + output_tokens
        if isinstance(input_tokens, int) and isinstance(output_tokens, int)
        else None
    )
    return {
        **{name: values[name] for name in SCALAR_METRICS if name != "total_tokens"},
        "total_tokens": total_tokens,
        **{name: values[name] for name in BOOLEAN_METRICS},
    }, issues


def _validate_adjudication(
    contract: dict[str, Any],
    system: str,
    record: dict[str, Any],
    adjudication: dict[str, Any],
    *,
    scored_fact_ids: tuple[str, ...],
) -> tuple[dict[str, Any] | None, list[Issue]]:
    issues = _closed_fields(
        adjudication,
        {
            "schema_version",
            "comparison_id",
            "system",
            "run_id",
            "policy",
            "scorer_version",
            "reference_fact_set_sha256",
            "candidate_source_receipt",
            "scorer_receipt",
            "reference_facts",
            "findings",
        },
        label=f"{system} semantic adjudication",
    )
    if issues:
        return None, issues
    if (
        adjudication["schema_version"] != 1
        or adjudication["comparison_id"] != contract["comparison_id"]
        or adjudication["system"] != system
        or adjudication["run_id"] != record["run_id"]
        or adjudication["policy"] != ADJUDICATION_POLICY
        or adjudication["scorer_version"] != contract["freeze"]["shared_scoring_version"]
        or adjudication["reference_fact_set_sha256"]
        != contract["freeze"]["reference_fact_set_sha256"]
    ):
        issues.append(Issue("ADJUDICATION_IDENTITY", f"{system} adjudication identity is invalid"))
    issues.extend(
        _validate_safe_source_reference(
            adjudication["candidate_source_receipt"],
            label=f"{system} candidate source",
        )
    )
    issues.extend(
        _validate_safe_source_reference(
            adjudication["scorer_receipt"],
            label=f"{system} scorer receipt",
            expected_method="SHARED_FROZEN_SCORER_ITEM_LEVEL_V1",
        )
    )
    fact_rows = adjudication["reference_facts"]
    if not isinstance(fact_rows, list):
        issues.append(Issue("ADJUDICATION_FACTS", f"{system} reference facts must be an array"))
        return None, issues
    observed_fact_ids: list[str] = []
    discovered = 0
    confirmed = 0
    for row in fact_rows:
        if not isinstance(row, dict):
            issues.append(Issue("ADJUDICATION_FACTS", f"{system} fact row must be an object"))
            continue
        row_issues = _closed_fields(
            row,
            {"fact_id", "surfaced_at_any_final_status", "surfaced_final_confirmed"},
            label=f"{system} fact adjudication",
        )
        issues.extend(row_issues)
        if row_issues:
            continue
        fact_id = row["fact_id"]
        surfaced = row["surfaced_at_any_final_status"]
        final_confirmed = row["surfaced_final_confirmed"]
        if (
            not isinstance(fact_id, str)
            or not isinstance(surfaced, bool)
            or not isinstance(final_confirmed, bool)
        ):
            issues.append(Issue("ADJUDICATION_FACTS", f"{system} fact row values are invalid"))
            continue
        if final_confirmed and not surfaced:
            issues.append(
                Issue("ADJUDICATION_FACTS", f"{system} confirmed fact must also be discovered")
            )
        observed_fact_ids.append(fact_id)
        discovered += int(surfaced)
        confirmed += int(final_confirmed)
    if tuple(observed_fact_ids) != scored_fact_ids:
        issues.append(
            Issue(
                "ADJUDICATION_FACT_SET",
                f"{system} adjudication must enumerate every scored frozen fact exactly once",
            )
        )

    finding_rows = adjudication["findings"]
    if not isinstance(finding_rows, list):
        issues.append(Issue("ADJUDICATION_FINDINGS", f"{system} findings must be an array"))
        return None, issues
    finding_ids: set[str] = set()
    precision_denominator = 0
    precision_numerator = 0
    unsupported = 0
    cited_findings = 0
    resolved_cited_findings = 0
    for row in finding_rows:
        if not isinstance(row, dict):
            issues.append(Issue("ADJUDICATION_FINDINGS", f"{system} finding row must be an object"))
            continue
        row_issues = _closed_fields(
            row,
            {
                "finding_id",
                "final_confirmed",
                "factual_label",
                "receipt_label",
                "has_citations",
                "all_citations_exactly_resolved",
            },
            label=f"{system} finding adjudication",
        )
        issues.extend(row_issues)
        if row_issues:
            continue
        finding_id = row["finding_id"]
        final_confirmed = row["final_confirmed"]
        factual_label = row["factual_label"]
        receipt_label = row["receipt_label"]
        has_citations = row["has_citations"]
        citations_resolved = row["all_citations_exactly_resolved"]
        if (
            not isinstance(finding_id, str)
            or not finding_id
            or finding_id in finding_ids
            or not isinstance(final_confirmed, bool)
            or factual_label not in FACTUAL_LABELS
            or receipt_label not in RECEIPT_LABELS
            or not isinstance(has_citations, bool)
            or (
                has_citations
                and not isinstance(citations_resolved, bool)
                or not has_citations
                and citations_resolved is not None
            )
        ):
            issues.append(Issue("ADJUDICATION_FINDINGS", f"{system} finding row is invalid"))
            continue
        finding_ids.add(finding_id)
        if final_confirmed and factual_label in {"CORRECT", "INCORRECT"}:
            precision_denominator += 1
            precision_numerator += int(factual_label == "CORRECT")
        unsupported += int(receipt_label in {"UNSUPPORTED", "CONTRADICTED"})
        if has_citations:
            cited_findings += 1
            resolved_cited_findings += int(citations_resolved is True)
    if issues:
        return None, issues
    precision = _rate_from_counts(precision_numerator, precision_denominator)
    discovered_recall = _rate_from_counts(discovered, len(scored_fact_ids))
    confirmed_recall = _rate_from_counts(confirmed, len(scored_fact_ids))
    unsupported_rate = _rate_from_counts(unsupported, len(finding_rows))
    citation_rate = _rate_from_counts(resolved_cited_findings, cited_findings)
    if precision["value"] is None or confirmed_recall["value"] is None:
        f1 = {"status": "NOT_APPLICABLE", "value": None}
    else:
        precision_value = float(precision["value"])
        recall_value = float(confirmed_recall["value"])
        value = (
            0.0
            if precision_value + recall_value == 0
            else 2 * precision_value * recall_value / (precision_value + recall_value)
        )
        f1 = {"status": "VALUE", "value": value}
    return {
        "final_confirmed_factual_precision": precision,
        "discovered_fact_recall": discovered_recall,
        "confirmed_fact_recall": confirmed_recall,
        "unsupported_finding_rate": unsupported_rate,
        "exact_citation_resolution_rate": citation_rate,
        "confirmed_f1": f1,
    }, issues


def _scored_reference_fact_ids(
    contract: dict[str, Any], repo_root: Path
) -> tuple[tuple[str, ...] | None, list[Issue]]:
    relative = contract["freeze"]["reference_fact_set_path"]
    payload, issues = _read_json(repo_root / relative, label="frozen reference fact set")
    if payload is None:
        return None, issues
    facts = payload.get("facts")
    if not isinstance(facts, list):
        return None, [Issue("REFERENCE_FACT_SCHEMA", "reference facts must be an array")]
    identifiers: list[str] = []
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("scored"), bool):
            return None, [Issue("REFERENCE_FACT_SCHEMA", "reference fact entry is invalid")]
        if fact["scored"]:
            fact_id = fact.get("fact_id")
            if not isinstance(fact_id, str) or not fact_id:
                return None, [Issue("REFERENCE_FACT_SCHEMA", "scored fact ID is invalid")]
            identifiers.append(fact_id)
    if not identifiers or len(identifiers) != len(set(identifiers)):
        return None, [Issue("REFERENCE_FACT_SCHEMA", "scored fact IDs are empty or duplicated")]
    return tuple(identifiers), []


def validate_run_record(
    contract: dict[str, Any],
    system: str,
    record: dict[str, Any],
    *,
    repository_commits: dict[str, str],
    anchor_timestamp: datetime,
) -> list[Issue]:
    issues = _closed_fields(
        record,
        {
            "schema_version",
            "comparison_id",
            "system",
            "run_id",
            "sequence",
            "started_at_utc",
            "post_freeze",
            "classification",
            "eligible_for_aggregate",
            "infrastructure_fault",
            "terminal_status",
            "repository_commit",
            "freeze_id",
            "reference_fact_set_sha256",
            "evidence",
            "model",
            "tool_policy",
            "runtime_contract",
            "cap_contract",
            "measurement_regime",
            "metrics",
        },
        label=f"{system} run record",
    )
    if issues:
        return issues
    if record["schema_version"] != 1:
        issues.append(Issue("RUN_VERSION", f"{system} run schema_version must be 1"))
    if record["comparison_id"] != contract["comparison_id"] or record["system"] != system:
        issues.append(Issue("RUN_IDENTITY", f"{system} run identity does not match the contract"))
    if not isinstance(record["run_id"], str) or not record["run_id"]:
        issues.append(Issue("RUN_ID", f"{system} run_id must be nonempty"))
    sequence = record["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        issues.append(Issue("RUN_SEQUENCE", f"{system} sequence must be positive"))
    timestamp: datetime | None = None
    try:
        timestamp = datetime.fromisoformat(str(record["started_at_utc"]).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError
    except ValueError:
        issues.append(
            Issue("RUN_TIMESTAMP", f"{system} started_at_utc must be timezone-aware ISO 8601")
        )
    if record["post_freeze"] is not True:
        issues.append(
            Issue(
                "PRE_FREEZE_RECORD", f"{system} comparison ledger may contain only post-freeze runs"
            )
        )
    if timestamp is not None and timestamp <= anchor_timestamp:
        issues.append(
            Issue(
                "PRE_FREEZE_TIMESTAMP",
                f"{system} candidate did not start after the annotated tagger timestamp",
            )
        )

    classification = record["classification"]
    if not isinstance(classification, str) or classification not in VALID_CLASSIFICATIONS:
        issues.append(Issue("RUN_CLASSIFICATION", f"{system} classification is invalid"))
    expected_complete = contract["systems"][system]["terminal_complete_value"]
    if not isinstance(record["terminal_status"], str) or not record["terminal_status"]:
        issues.append(Issue("RUN_TERMINAL", f"{system} terminal status must be nonempty"))
    if classification == "VALID":
        if record["eligible_for_aggregate"] is not True:
            issues.append(
                Issue("RUN_ELIGIBILITY", f"valid {system} run must be aggregate-eligible")
            )
        if record["infrastructure_fault"] is not None:
            issues.append(
                Issue("RUN_FAULT", f"valid {system} run cannot have an infrastructure fault")
            )
        if record["terminal_status"] != expected_complete:
            issues.append(
                Issue("RUN_TERMINAL", f"valid {system} run has the wrong terminal status")
            )
        issues.extend(_validate_valid_metrics(record["metrics"]))
    else:
        if record["metrics"] != {}:
            issues.append(
                Issue("NONVALID_METRICS", f"nonvalid {system} run cannot publish metrics")
            )
        if record["eligible_for_aggregate"] is not False:
            issues.append(Issue("RUN_ELIGIBILITY", f"nonvalid {system} run cannot be aggregated"))
        if record["terminal_status"] == expected_complete:
            issues.append(
                Issue("RUN_TERMINAL", f"nonvalid {system} run cannot claim complete status")
            )
        if classification == "INFRASTRUCTURE_FAULT" and not isinstance(
            record["infrastructure_fault"], dict
        ):
            issues.append(
                Issue("RUN_FAULT", f"{system} infrastructure fault needs a retained reason")
            )
        elif classification == "INFRASTRUCTURE_FAULT":
            fault = record["infrastructure_fault"]
            if (
                set(fault) != {"code", "rationale"}
                or fault.get("code") not in contract["execution"]["infrastructure_fault_codes"]
            ):
                issues.append(
                    Issue(
                        "RUN_FAULT",
                        f"{system} infrastructure fault is not in the frozen allowlist",
                    )
                )
        elif record["infrastructure_fault"] is not None:
            issues.append(
                Issue(
                    "RUN_FAULT",
                    f"non-infrastructure {system} run cannot carry an infrastructure fault",
                )
            )

    if record["repository_commit"] != repository_commits[system]:
        issues.append(
            Issue("RUN_REPOSITORY_DRIFT", f"{system} run used a different repository commit")
        )
    freeze = contract["freeze"]
    if record["freeze_id"] != freeze["freeze_id"]:
        issues.append(Issue("RUN_FREEZE_DRIFT", f"{system} run used a different freeze"))
    if record["reference_fact_set_sha256"] != freeze["reference_fact_set_sha256"]:
        issues.append(Issue("RUN_FACT_DRIFT", f"{system} run used a different reference fact set"))
    if record["evidence"] != contract["evidence"]:
        issues.append(
            Issue(
                "INCOMPARABLE_EVIDENCE",
                f"{system} evidence identity differs; SAME_EVIDENCE is refused",
            )
        )
    if record["tool_policy"] != contract["systems"][system]["tool_policy"]:
        issues.append(
            Issue("RUN_TOOL_POLICY_DRIFT", f"{system} tool policy differs from the contract")
        )
    if record["runtime_contract"] != contract["systems"][system]["runtime_contract"]:
        issues.append(
            Issue("RUN_RUNTIME_DRIFT", f"{system} runtime contract differs from the freeze")
        )
    if record["cap_contract"] != contract["systems"][system]["cap_contract"]:
        issues.append(Issue("RUN_CAP_DRIFT", f"{system} cap contract differs from the freeze"))
    if record["measurement_regime"] != contract["execution"]["measurement_regime"]:
        issues.append(
            Issue(
                "RUN_MEASUREMENT_REGIME_DRIFT",
                f"{system} measurement regime differs from the freeze",
            )
        )
    model = record["model"]
    if not isinstance(model, dict) or set(model) != {
        "requested",
        "provider_returned",
        "response_count",
    }:
        issues.append(Issue("RUN_MODEL", f"{system} model metadata must be a closed receipt"))
    else:
        requested = model["requested"]
        returned = model["provider_returned"]
        response_count = model["response_count"]
        required_requested = contract["systems"][system]["required_requested_models"]
        patterns = contract["systems"][system]["accepted_provider_model_patterns"]
        if (
            not isinstance(requested, list)
            or any(not isinstance(item, str) or not item for item in requested)
            or sorted(set(requested)) != sorted(required_requested)
        ):
            issues.append(Issue("RUN_MODEL", f"{system} requested-model set differs from freeze"))
        if (
            not isinstance(returned, list)
            or not returned
            or any(
                not isinstance(item, str)
                or not item
                or not any(re.fullmatch(pattern, item) for pattern in patterns)
                for item in returned
            )
        ):
            issues.append(Issue("RUN_MODEL", f"{system} provider-returned identity is invalid"))
        if (
            not isinstance(response_count, int)
            or isinstance(response_count, bool)
            or response_count < 1
            or not isinstance(returned, list)
            or response_count != len(returned)
        ):
            issues.append(Issue("RUN_MODEL", f"{system} provider response count is invalid"))
        metrics = record["metrics"]
        if (
            classification == "VALID"
            and isinstance(metrics, dict)
            and isinstance(metrics.get("model_request_count"), int)
            and isinstance(response_count, int)
            and response_count > metrics["model_request_count"]
        ):
            issues.append(
                Issue("RUN_MODEL", f"{system} provider responses exceed recorded model requests")
            )
    return issues


def load_candidate_records(
    contract: dict[str, Any],
    records_root: Path,
    *,
    repository_commits: dict[str, str],
    anchor_timestamp: datetime,
    scored_fact_ids: tuple[str, ...],
) -> tuple[dict[str, list[LoadedRecord]], list[Issue], list[Issue]]:
    loaded = {system: [] for system in SYSTEMS}
    errors: list[Issue] = []
    pending: list[Issue] = []
    for system in SYSTEMS:
        system_root = records_root / system
        ledger_path = system_root / "ledger.json"
        try:
            system_info = system_root.lstat()
        except FileNotFoundError:
            pending.append(
                Issue("RUN_LEDGER_PENDING", f"{system} candidate ledger is not retained")
            )
            continue
        except OSError as exc:
            errors.append(
                Issue(
                    "LEDGER_DIRECTORY",
                    f"{system} ledger directory failed: {type(exc).__name__}",
                )
            )
            continue
        if stat.S_ISLNK(system_info.st_mode) or not stat.S_ISDIR(system_info.st_mode):
            errors.append(
                Issue(
                    "LEDGER_DIRECTORY",
                    f"{system} ledger location must be a non-symlink directory",
                )
            )
            continue
        try:
            ledger_path.lstat()
        except FileNotFoundError:
            pending.append(
                Issue("RUN_LEDGER_PENDING", f"{system} candidate ledger is not retained")
            )
            continue
        except OSError as exc:
            errors.append(
                Issue(
                    "LEDGER_DIRECTORY",
                    f"{system} ledger failed: {type(exc).__name__}",
                )
            )
            continue
        ledger, ledger_issues = _read_json(ledger_path, label=f"{system} candidate ledger")
        errors.extend(ledger_issues)
        if ledger is None:
            continue
        ledger_fields = _closed_fields(
            ledger,
            {"schema_version", "comparison_id", "system", "scope", "records"},
            label=f"{system} candidate ledger",
        )
        errors.extend(ledger_fields)
        if ledger_fields:
            continue
        if (
            ledger["schema_version"] != 1
            or ledger["comparison_id"] != contract["comparison_id"]
            or ledger["system"] != system
            or ledger["scope"] != "ALL_POST_FREEZE_CANDIDATE_ATTEMPTS"
        ):
            errors.append(
                Issue("LEDGER_IDENTITY", f"{system} candidate ledger identity is invalid")
            )
            continue
        entries = ledger["records"]
        if not isinstance(entries, list):
            errors.append(Issue("LEDGER_SCHEMA", f"{system} records must be a list"))
            continue
        expected_names: set[str] = set()
        expected_sequences: list[int] = []
        for entry in entries:
            entry_fields = {
                "sequence",
                "path",
                "sha256",
                "extraction_path",
                "extraction_sha256",
                "adjudication_path",
                "adjudication_sha256",
            }
            if not isinstance(entry, dict) or set(entry) != entry_fields:
                errors.append(Issue("LEDGER_ENTRY", f"{system} ledger entry is invalid"))
                continue
            name = entry["path"]
            sequence = entry["sequence"]
            digest = entry["sha256"]
            extraction_name = entry["extraction_path"]
            extraction_digest = entry["extraction_sha256"]
            adjudication_name = entry["adjudication_path"]
            adjudication_digest = entry["adjudication_sha256"]
            if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
                errors.append(Issue("LEDGER_SEQUENCE", f"{system} ledger sequence is invalid"))
                continue
            expected_sequences.append(sequence)
            exact_record_name = f"candidate-{sequence:03d}.json"
            if (
                not isinstance(name, str)
                or SAFE_RECORD_NAME.fullmatch(name) is None
                or name != exact_record_name
            ):
                errors.append(Issue("LEDGER_PATH", f"{system} ledger record path is unsafe"))
                continue
            if not isinstance(digest, str) or HEX_SHA256.fullmatch(digest) is None:
                errors.append(Issue("LEDGER_DIGEST", f"{system} ledger digest is invalid"))
                continue
            sidecar_values = (
                (extraction_name, extraction_digest, f"candidate-{sequence:03d}.extraction.json"),
                (
                    adjudication_name,
                    adjudication_digest,
                    f"candidate-{sequence:03d}.adjudication.json",
                ),
            )
            sidecars_well_formed = True
            for sidecar_name, sidecar_digest, exact_name in sidecar_values:
                if sidecar_name is None and sidecar_digest is None:
                    continue
                if (
                    not isinstance(sidecar_name, str)
                    or sidecar_name != exact_name
                    or SAFE_RECORD_NAME.fullmatch(sidecar_name) is None
                    or not isinstance(sidecar_digest, str)
                    or HEX_SHA256.fullmatch(sidecar_digest) is None
                ):
                    errors.append(Issue("LEDGER_SIDECAR", f"{system} sidecar binding is invalid"))
                    sidecars_well_formed = False
            if not sidecars_well_formed:
                continue
            bound_names = [name] + [
                sidecar_name
                for sidecar_name, _sidecar_digest, _exact_name in sidecar_values
                if isinstance(sidecar_name, str)
            ]
            if any(bound_name in expected_names for bound_name in bound_names):
                errors.append(Issue("LEDGER_DUPLICATE", f"{system} ledger repeats a bound path"))
                continue
            expected_names.update(bound_names)
            record_path = system_root / name
            record, record_issues = _read_json(record_path, label=f"{system} candidate record")
            errors.extend(record_issues)
            if record is None:
                continue
            try:
                actual_digest = _sha256_file(record_path)
            except OSError as exc:
                errors.append(
                    Issue(
                        "RUN_RECORD_UNREADABLE",
                        f"{system} candidate is unreadable: {type(exc).__name__}",
                    )
                )
                continue
            if actual_digest != digest:
                errors.append(
                    Issue("RUN_RECORD_DIGEST", f"{system} candidate digest does not match")
                )
                continue
            record_issues = validate_run_record(
                contract,
                system,
                record,
                repository_commits=repository_commits,
                anchor_timestamp=anchor_timestamp,
            )
            if record_issues:
                errors.extend(record_issues)
                continue
            if record["sequence"] != sequence:
                record_issues.append(
                    Issue("LEDGER_SEQUENCE", f"{system} ledger/record sequence differs")
                )
            if record["classification"] == "VALID":
                if any(
                    not isinstance(value, str)
                    for value in (
                        extraction_name,
                        extraction_digest,
                        adjudication_name,
                        adjudication_digest,
                    )
                ):
                    record_issues.append(
                        Issue(
                            "LEDGER_SIDECAR_REQUIRED",
                            f"valid {system} candidate requires both hash-bound sidecars",
                        )
                    )
                else:
                    extraction, extraction_issues = _read_json(
                        system_root / extraction_name,
                        label=f"{system} extraction receipt",
                    )
                    adjudication, adjudication_issues = _read_json(
                        system_root / adjudication_name,
                        label=f"{system} semantic adjudication",
                    )
                    record_issues.extend(extraction_issues)
                    record_issues.extend(adjudication_issues)
                    if extraction is not None:
                        try:
                            actual = _sha256_file(system_root / extraction_name)
                        except OSError as exc:
                            record_issues.append(
                                Issue(
                                    "SIDECAR_UNREADABLE",
                                    f"{system} extraction is unreadable: {type(exc).__name__}",
                                )
                            )
                        else:
                            if actual != extraction_digest:
                                record_issues.append(
                                    Issue(
                                        "SIDECAR_DIGEST",
                                        f"{system} extraction digest does not match",
                                    )
                                )
                    if adjudication is not None:
                        try:
                            actual = _sha256_file(system_root / adjudication_name)
                        except OSError as exc:
                            record_issues.append(
                                Issue(
                                    "SIDECAR_UNREADABLE",
                                    f"{system} adjudication is unreadable: {type(exc).__name__}",
                                )
                            )
                        else:
                            if actual != adjudication_digest:
                                record_issues.append(
                                    Issue(
                                        "SIDECAR_DIGEST",
                                        f"{system} adjudication digest does not match",
                                    )
                                )
                    operational: dict[str, Any] | None = None
                    semantic: dict[str, Any] | None = None
                    if extraction is not None:
                        operational, sidecar_issues = _validate_extraction_receipt(
                            contract, system, record, extraction
                        )
                        record_issues.extend(sidecar_issues)
                    if adjudication is not None:
                        semantic, sidecar_issues = _validate_adjudication(
                            contract,
                            system,
                            record,
                            adjudication,
                            scored_fact_ids=scored_fact_ids,
                        )
                        record_issues.extend(sidecar_issues)
                    if operational is not None and semantic is not None:
                        recomputed_metrics = {**operational, **semantic}
                        if record["metrics"] != recomputed_metrics:
                            record_issues.append(
                                Issue(
                                    "RUN_METRIC_RECOMPUTATION",
                                    f"{system} candidate metrics differ from sidecar recomputation",
                                )
                            )
            elif any(
                value is not None
                for value in (
                    extraction_name,
                    extraction_digest,
                    adjudication_name,
                    adjudication_digest,
                )
            ):
                record_issues.append(
                    Issue(
                        "LEDGER_SIDECAR_UNEXPECTED",
                        f"nonvalid {system} candidate cannot publish metric sidecars",
                    )
                )
            errors.extend(record_issues)
            if not record_issues:
                loaded[system].append(LoadedRecord(system, sequence, record))
        if expected_sequences != list(range(1, len(expected_sequences) + 1)):
            errors.append(
                Issue("LEDGER_SEQUENCE", f"{system} sequences must be contiguous and ordered")
            )
        try:
            directory_entries = list(system_root.iterdir())
        except OSError as exc:
            errors.append(
                Issue("LEDGER_DIRECTORY", f"{system} ledger directory failed: {type(exc).__name__}")
            )
            continue
        actual_names = {path.name for path in directory_entries}
        allowed_names = expected_names | {"ledger.json"}
        unsafe_entries = []
        for path in directory_entries:
            try:
                entry_info = path.lstat()
            except OSError:
                unsafe_entries.append(path.name)
                continue
            if stat.S_ISLNK(entry_info.st_mode) or not stat.S_ISREG(entry_info.st_mode):
                unsafe_entries.append(path.name)
        if actual_names != allowed_names or unsafe_entries:
            errors.append(
                Issue(
                    "LEDGER_INCOMPLETE",
                    f"{system} ledger directory is not the exact closed candidate file set",
                )
            )
        run_ids = [item.payload["run_id"] for item in loaded[system]]
        if len(run_ids) != len(set(run_ids)):
            errors.append(Issue("RUN_ID_DUPLICATE", f"{system} run IDs must be unique"))
        ordered_records = sorted(loaded[system], key=lambda item: item.sequence)
        timestamps = [
            datetime.fromisoformat(str(item.payload["started_at_utc"]).replace("Z", "+00:00"))
            for item in ordered_records
        ]
        if any(
            current <= previous
            for previous, current in zip(timestamps, timestamps[1:], strict=False)
        ):
            errors.append(
                Issue(
                    "LEDGER_CHRONOLOGY",
                    f"{system} candidate timestamps must increase with sequence",
                )
            )
        valid = [item for item in loaded[system] if item.payload["classification"] == "VALID"]
        if not valid:
            pending.append(
                Issue("VALID_RUN_PENDING", f"{system} has no valid post-freeze complete run")
            )
        target = contract["execution"]["target_valid_runs_per_system"]
        if len(valid) < target:
            pending.append(
                Issue(
                    "REPLICATE_TARGET_PENDING",
                    f"{system} has {len(valid)}/{target} retained valid runs for median/spread",
                )
            )
    return loaded, errors, pending


def _metric_value(metrics: dict[str, Any], name: str) -> float | None:
    if name in RATE_METRICS or name in SCORE_METRICS:
        value = metrics[name]["value"]
    else:
        value = metrics[name]
    if value is None:
        return None
    return float(value)


def aggregate_valid_runs(records: dict[str, list[LoadedRecord]]) -> dict[str, Any]:
    systems: dict[str, Any] = {}
    for system in SYSTEMS:
        candidates = sorted(records[system], key=lambda item: item.sequence)
        valid = [item for item in candidates if item.payload["classification"] == "VALID"]
        metric_summary: dict[str, Any] = {}
        for name in SCALAR_METRICS + RATE_METRICS + SCORE_METRICS:
            values = [
                value
                for item in valid
                if (value := _metric_value(item.payload["metrics"], name)) is not None
            ]
            metric_summary[name] = {
                "applicable_runs": len(values),
                "not_available_runs": len(valid) - len(values),
                "median": statistics.median(values) if values else None,
                "minimum": min(values) if values else None,
                "maximum": max(values) if values else None,
                "spread": max(values) - min(values) if values else None,
            }
        for name in BOOLEAN_METRICS:
            values = [
                item.payload["metrics"][name]
                for item in valid
                if item.payload["metrics"][name] is not None
            ]
            passed = sum(value is True for value in values)
            metric_summary[name] = {
                "applicable_runs": len(values),
                "not_available_runs": len(valid) - len(values),
                "passed": passed,
                "all_passed": bool(values) and passed == len(values),
            }
        systems[system] = {
            "candidate_attempts": len(candidates),
            "valid_runs": len(valid),
            "primary_run_id": valid[0].payload["run_id"] if valid else None,
            "valid_run_ids": [item.payload["run_id"] for item in valid],
            "excluded_attempts": [
                {
                    "run_id": item.payload["run_id"],
                    "classification": item.payload["classification"],
                }
                for item in candidates
                if item.payload["classification"] != "VALID"
            ],
            "metrics": metric_summary,
        }
    return systems


def evaluate(
    contract: dict[str, Any],
    *,
    repo_root: Path,
    records_root: Path,
) -> dict[str, Any]:
    errors, pending = validate_contract(contract)
    if not errors:
        bound_errors, bound_pending = validate_bound_files(contract, repo_root=repo_root)
        errors.extend(bound_errors)
        pending.extend(bound_pending)
    anchor: ResolvedFreezeAnchor | None = None
    repository_commits: dict[str, str] = {}
    repositories = contract.get("repositories")
    if isinstance(repositories, dict):
        qwen_repository = repositories.get("qwen")
        if isinstance(qwen_repository, dict) and isinstance(
            qwen_repository.get("required_commit"), str
        ):
            repository_commits["qwen"] = qwen_repository["required_commit"]
    if not errors:
        anchor, anchor_errors, anchor_pending = _resolve_freeze_anchor(contract, repo_root)
        errors.extend(anchor_errors)
        pending.extend(anchor_pending)
        if anchor is not None:
            repository_commits["openai"] = anchor.commit
    records = {system: [] for system in SYSTEMS}
    if not errors and anchor is not None and set(repository_commits) == set(SYSTEMS):
        scored_fact_ids, fact_issues = _scored_reference_fact_ids(contract, repo_root)
        errors.extend(fact_issues)
        if scored_fact_ids is not None and not fact_issues:
            records, record_errors, record_pending = load_candidate_records(
                contract,
                records_root,
                repository_commits=repository_commits,
                anchor_timestamp=anchor.tagger_timestamp,
                scored_fact_ids=scored_fact_ids,
            )
            errors.extend(record_errors)
            pending.extend(record_pending)
    elif not errors and anchor is None:
        for system in SYSTEMS:
            try:
                (records_root / system / "ledger.json").lstat()
            except FileNotFoundError:
                pending.append(
                    Issue("RUN_LEDGER_PENDING", f"{system} candidate ledger is not retained")
                )
            except OSError as exc:
                errors.append(
                    Issue(
                        "LEDGER_DIRECTORY",
                        f"{system} ledger metadata failed: {type(exc).__name__}",
                    )
                )

    incomparable = any(issue.code == "INCOMPARABLE_EVIDENCE" for issue in errors)
    ready = not errors and not pending and contract.get("status") == "READY" and anchor is not None
    if errors:
        status_value = "INVALID"
    elif ready:
        status_value = "COMPLETE"
    else:
        status_value = "PENDING"
    aggregate = aggregate_valid_runs(records)
    return {
        "schema_version": 1,
        "comparison_id": contract.get("comparison_id"),
        "status": status_value,
        "comparison_qualification": "SAME_EVIDENCE" if ready else "NOT_ESTABLISHED",
        "same_evidence": ready and not incomparable,
        "dimension_comparison_allowed": ready,
        "blanket_superiority_claim_allowed": False,
        "proof_backed_faster_or_cheaper_claim_allowed": False,
        "proof_backed_accuracy_superiority_claim_allowed": False,
        "metric_assurance": {
            "semantic": (
                "LEDGER_HASHED_ITEM_LEVEL_OPERATOR_ADJUDICATION_RECOMPUTED_SOURCE_NOT_AUTHENTICATED"
            ),
            "operational": (
                "LEDGER_HASHED_SANITIZED_EXTRACTION_SOURCE_NOT_REVERIFIED_BY_AGGREGATOR"
            ),
        },
        "provider_or_evidence_accessed": False,
        "resolved_repository_commits": {
            "openai": repository_commits.get("openai"),
            "qwen": repository_commits.get("qwen"),
        },
        "anchor_tagger_timestamp_utc": (
            anchor.tagger_timestamp_text if anchor is not None else None
        ),
        "selection": {
            "rule": "all valid post-freeze runs; first valid is primary",
            "cherry_picking_allowed": False,
        },
        "systems": aggregate,
        "errors": [asdict(issue) for issue in errors],
        "pending": [asdict(issue) for issue in _deduplicate_issues(pending)],
        "disclosed_differences": contract.get("disclosed_differences", []),
    }


def _deduplicate_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str]] = set()
    result: list[Issue] = []
    for issue in issues:
        key = (issue.code, issue.message)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def _format_number(name: str, summary: dict[str, Any]) -> str:
    median = summary["median"]
    if median is None:
        return "NOT AVAILABLE"
    minimum = summary["minimum"]
    maximum = summary["maximum"]
    count = summary["applicable_runs"]
    if name.endswith("_rate") or name in {
        "final_confirmed_factual_precision",
        "discovered_fact_recall",
        "confirmed_fact_recall",
        "confirmed_f1",
    }:
        return f"{median * 100:.1f}% [{minimum * 100:.1f}%–{maximum * 100:.1f}%], n={count}"
    if name == "estimated_cost_usd":
        return f"${median:.4f} [${minimum:.4f}–${maximum:.4f}], n={count}"
    if name.endswith("_seconds"):
        return f"{median:.3f}s [{minimum:.3f}–{maximum:.3f}s], n={count}"
    return f"{median:g} [{minimum:g}–{maximum:g}], n={count}"


def render_markdown(contract: dict[str, Any], result: dict[str, Any]) -> str:
    status_value = result["status"]
    if status_value == "COMPLETE":
        banner = (
            "**Status: COMPLETE SAME-EVIDENCE COMPARISON.** Values are medians with "
            "min–max spread across every valid post-freeze run retained in each ledger."
        )
    elif status_value == "INVALID":
        banner = (
            "**Status: INVALID / INCOMPARABLE.** The script refused a same-evidence claim "
            "because a contract, ledger, digest, or evidence invariant failed."
        )
    else:
        banner = (
            "**Status: PENDING.** No frozen same-evidence result is published. Historical "
            "Qwen memory-plus-disk metrics are explicitly excluded."
        )
    rows = (
        ("End-to-end wall", "wall_time_seconds"),
        ("Time to first accepted observation", "time_to_first_observation_seconds"),
        ("Model requests", "model_request_count"),
        ("Typed forensic tool calls", "tool_call_count"),
        ("Input tokens", "input_tokens"),
        ("Output tokens", "output_tokens"),
        ("Total tokens", "total_tokens"),
        ("Estimated cost", "estimated_cost_usd"),
        ("Final-confirmed factual precision", "final_confirmed_factual_precision"),
        ("Discovered-fact recall", "discovered_fact_recall"),
        ("Confirmed-fact recall", "confirmed_fact_recall"),
        ("Confirmed F1", "confirmed_f1"),
        ("Unsupported-finding rate", "unsupported_finding_rate"),
        ("Exact-citation-resolution rate", "exact_citation_resolution_rate"),
    )
    lines = [
        "# Frozen same-evidence Qwen versus OpenAI comparison",
        "",
        banner,
        "",
        "This is a controlled comparative case study, not a one-variable causal ablation. "
        "The model, provider, prompts, orchestration, tool policy, validation, and report "
        "contracts differ. The shared claims are limited to the frozen memory image and "
        "external fact/metric definitions.",
        "",
        "Semantic values are recomputed from ledger-hashed item-level adjudications, but the "
        "adjudication source receipts remain operator-retained hash references rather than "
        "independently authenticated source reopening. "
        "Operational values are recomputed from ledger-hashed sanitized extraction receipts, "
        "but this public aggregator does not reopen their private source bundles; therefore its "
        "machine output never authorizes a proof-backed faster, cheaper, or accuracy-superiority "
        "headline.",
        "",
        "| Metric | OpenAI-native Unchained | Qwen Ensemble |",
        "|---|---:|---:|",
    ]
    for label, name in rows:
        if status_value != "COMPLETE":
            values = ["WITHHELD UNTIL COMPLETE", "WITHHELD UNTIL COMPLETE"]
        else:
            values = []
            for system in SYSTEMS:
                summary = result["systems"][system]["metrics"][name]
                values.append(_format_number(name, summary))
        lines.append(f"| {label} | {values[0]} | {values[1]} |")
    for label, name in (
        ("Custody pass", "custody_pass"),
        ("Native verifier pass", "native_verifier_pass"),
    ):
        if status_value != "COMPLETE":
            values = ["WITHHELD UNTIL COMPLETE", "WITHHELD UNTIL COMPLETE"]
        else:
            values = []
            for system in SYSTEMS:
                summary = result["systems"][system]["metrics"][name]
                if summary["applicable_runs"] == 0:
                    values.append("NOT AVAILABLE")
                else:
                    values.append(f"{summary['passed']}/{summary['applicable_runs']}")
        lines.append(f"| {label} | {values[0]} | {values[1]} |")

    lines.extend(
        [
            "",
            "## Frozen invariants",
            "",
            f"- Evidence: `{contract['evidence']['public_evidence_id']}`, "
            f"`{contract['evidence']['route']}`, {contract['evidence']['size_bytes']:,} bytes, "
            f"SHA-256 `{contract['evidence']['sha256']}`.",
            f"- Shared fact/scoring freeze: `{contract['freeze']['freeze_id']}`; current "
            f"qualification `{result['comparison_qualification']}`.",
            f"- OpenAI annotated-tag commit: "
            f"`{result.get('resolved_repository_commits', {}).get('openai') or 'PENDING'}`; "
            f"tagger time `{result.get('anchor_tagger_timestamp_utc') or 'PENDING'}`.",
            f"- Qwen pinned commit: "
            f"`{result.get('resolved_repository_commits', {}).get('qwen') or 'PENDING'}`.",
            "- Selection: every valid post-freeze run is aggregated; the first valid run is "
            "the primary and later valid runs are disclosed replicates.",
            "- Spread means min–max across all applicable valid runs. A one-run spread is zero "
            "and remains labeled as a single-run result.",
            "",
            "## Candidate inclusion",
            "",
            "| System | All candidate attempts | Valid runs | Primary |",
            "|---|---:|---:|---|",
        ]
    )
    for system in SYSTEMS:
        data = result["systems"][system]
        lines.append(
            f"| {contract['systems'][system]['display_name']} | {data['candidate_attempts']} | "
            f"{data['valid_runs']} | {data['primary_run_id'] or 'PENDING'} |"
        )

    lines.extend(["", "## Disclosed differences", ""])
    lines.extend(f"- {value}" for value in contract["disclosed_differences"])
    if result["errors"]:
        lines.extend(["", "## Refusal reasons", ""])
        lines.extend(f"- `{item['code']}`: {item['message']}" for item in result["errors"])
    if result["pending"]:
        lines.extend(["", "## Remaining gates", ""])
        lines.extend(f"- `{item['code']}`: {item['message']}" for item in result["pending"])
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "No row by itself proves one architecture is generally faster, cheaper, or more "
            "accurate. Cross-provider token and cost accounting may differ, native verifier "
            "contracts are not equivalent, and one public case may have training contamination. "
            "Operational source artifacts are hash-referenced but not independently reopened by "
            "this public aggregator. The explicit machine claim flags remain false. Any bounded "
            "case-study statement must cite this table, its retained ledgers and sidecars, exact "
            "commits, and the frozen fact set.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_cli_markdown(contract: dict[str, Any], result: dict[str, Any]) -> str:
    try:
        return render_markdown(contract, result)
    except (KeyError, TypeError, ValueError):
        lines = [
            "# Frozen same-evidence Qwen versus OpenAI comparison",
            "",
            "**Status: INVALID.** The comparison contract cannot be rendered safely.",
            "",
        ]
        for item in result.get("errors", []):
            lines.append(
                f"- `{item.get('code', 'INVALID')}`: {item.get('message', 'invalid input')}"
            )
        lines.append("")
        return "\n".join(lines)


def _git_value(repo: Path, *args: str) -> tuple[str | None, Issue | None]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            shell=False,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, Issue("GIT_UNAVAILABLE", f"repository check failed: {type(exc).__name__}")
    if result.returncode != 0:
        return None, Issue("GIT_CHECK", "repository check returned nonzero")
    return result.stdout.strip(), None


def _git_changed_paths(
    repo: Path, older_commit: str, newer_commit: str
) -> tuple[list[str] | None, Issue | None]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "diff",
                "--name-only",
                "-z",
                older_commit,
                newer_commit,
                "--",
            ],
            check=False,
            capture_output=True,
            shell=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, Issue("GIT_UNAVAILABLE", f"repository diff failed: {type(exc).__name__}")
    if result.returncode != 0:
        return None, Issue("GIT_CHECK", "repository diff returned nonzero")
    try:
        paths = [value.decode("utf-8") for value in result.stdout.split(b"\0") if value]
    except UnicodeError:
        return None, Issue("GIT_CHECK", "repository diff contained a non-UTF-8 path")
    return paths, None


def _resolve_freeze_anchor(
    contract: dict[str, Any],
    repo: Path,
    *,
    require_current_head: bool = False,
) -> tuple[ResolvedFreezeAnchor | None, list[Issue], list[Issue]]:
    """Resolve the post-commit annotated anchor without embedding its future SHA."""

    errors: list[Issue] = []
    pending: list[Issue] = []
    tag = contract["freeze"]["tag"]
    tag_ref = f"refs/tags/{tag}"
    try:
        existence = subprocess.run(
            ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", tag_ref],
            check=False,
            capture_output=True,
            shell=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        errors.append(Issue("FREEZE_TAG_CHECK", f"freeze tag check failed: {type(exc).__name__}"))
        return None, errors, pending
    if existence.returncode == 1:
        pending.append(
            Issue(
                "FREEZE_TAG_PENDING",
                "annotated experiment-freeze-v1 tag is not present yet",
            )
        )
        return None, errors, pending
    if existence.returncode != 0:
        errors.append(Issue("FREEZE_TAG_CHECK", "freeze tag lookup returned nonzero"))
        return None, errors, pending

    object_type, issue = _git_value(repo, "cat-file", "-t", tag_ref)
    if issue:
        errors.append(Issue(issue.code, f"freeze tag type {issue.message}"))
        return None, errors, pending
    if object_type != "tag":
        errors.append(
            Issue(
                "FREEZE_TAG_NOT_ANNOTATED",
                "experiment-freeze-v1 must be an annotated tag, not a lightweight tag",
            )
        )
        return None, errors, pending

    commit, issue = _git_value(repo, "rev-parse", f"{tag_ref}^{{commit}}")
    if issue or commit is None or HEX_GIT_SHA.fullmatch(commit) is None:
        errors.append(Issue("FREEZE_TAG_COMMIT", "freeze tag does not peel to a full commit SHA"))
        return None, errors, pending
    head, issue = _git_value(repo, "rev-parse", "HEAD")
    if issue or head is None:
        errors.append(Issue("FREEZE_TAG_HEAD", "current repository HEAD cannot be resolved"))
        return None, errors, pending
    if require_current_head:
        if head != commit:
            errors.append(
                Issue(
                    "FREEZE_TAG_TARGET",
                    "provider execution requires the annotated tag at current HEAD",
                )
            )
            return None, errors, pending
    elif head != commit:
        try:
            tag_ancestry = subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, head],
                check=False,
                capture_output=True,
                shell=False,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(
                Issue(
                    "FREEZE_TAG_TARGET",
                    f"aggregation ancestry check failed: {type(exc).__name__}",
                )
            )
            return None, errors, pending
        if tag_ancestry.returncode != 0:
            errors.append(
                Issue(
                    "FREEZE_TAG_TARGET",
                    "aggregation HEAD is not a descendant of the annotated freeze tag",
                )
            )
            return None, errors, pending
        changed_paths, changed_issue = _git_changed_paths(repo, commit, head)
        if changed_issue or changed_paths is None:
            errors.append(
                changed_issue
                or Issue("FREEZE_DESCENDANT_SCOPE", "aggregation descendant cannot be inspected")
            )
            return None, errors, pending
        unexpected_paths = [
            path
            for path in changed_paths
            if path != "docs/runs/comparison.md"
            and not path.startswith("docs/runs/comparison-inputs/")
        ]
        if unexpected_paths:
            errors.append(
                Issue(
                    "FREEZE_DESCENDANT_SCOPE",
                    "aggregation descendant changes files outside the closed "
                    "comparison-results paths",
                )
            )
            return None, errors, pending
    ancestor = contract["repositories"]["openai"]["required_ancestor"]
    if ancestor:
        try:
            ancestry = subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, commit],
                check=False,
                capture_output=True,
                shell=False,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(
                Issue(
                    "FREEZE_TAG_ANCESTRY",
                    f"freeze tag ancestry check failed: {type(exc).__name__}",
                )
            )
            return None, errors, pending
        if ancestry.returncode != 0:
            errors.append(
                Issue(
                    "FREEZE_TAG_ANCESTRY",
                    "annotated freeze tag is missing the required OpenAI ancestor",
                )
            )
            return None, errors, pending
    status_value, issue = _git_value(repo, "status", "--porcelain")
    if issue:
        errors.append(Issue(issue.code, f"freeze worktree {issue.message}"))
        return None, errors, pending
    if status_value:
        errors.append(
            Issue(
                "FREEZE_WORKTREE_DIRTY",
                "annotated freeze tag checkout is not a clean worktree",
            )
        )
        return None, errors, pending

    tagger_value, issue = _git_value(
        repo,
        "for-each-ref",
        "--format=%(taggerdate:iso-strict)",
        tag_ref,
    )
    if issue or not tagger_value:
        errors.append(
            Issue("FREEZE_TAG_TIMESTAMP", "annotated freeze tagger timestamp is unavailable")
        )
        return None, errors, pending
    try:
        tagger_timestamp = datetime.fromisoformat(tagger_value.replace("Z", "+00:00"))
        if tagger_timestamp.tzinfo is None:
            raise ValueError
    except ValueError:
        errors.append(
            Issue("FREEZE_TAG_TIMESTAMP", "annotated tagger timestamp is not timezone-aware")
        )
        return None, errors, pending
    canonical_timestamp = tagger_timestamp.astimezone(UTC)
    return (
        ResolvedFreezeAnchor(
            commit=commit,
            tagger_timestamp=canonical_timestamp,
            tagger_timestamp_text=canonical_timestamp.isoformat().replace("+00:00", "Z"),
        ),
        errors,
        pending,
    )


def _verify_repository(
    repo: Path,
    system: str,
    contract: dict[str, Any],
    *,
    expected_commit: str,
) -> list[Issue]:
    issues: list[Issue] = []
    head, issue = _git_value(repo, "rev-parse", "HEAD")
    if issue:
        return [Issue(issue.code, f"{system} {issue.message}")]
    if head != expected_commit:
        issues.append(Issue("REPOSITORY_DRIFT", f"{system} HEAD is not the exact frozen commit"))
    status_value, issue = _git_value(repo, "status", "--porcelain")
    if issue:
        issues.append(Issue(issue.code, f"{system} {issue.message}"))
    elif status_value:
        issues.append(Issue("REPOSITORY_DIRTY", f"{system} worktree is not clean"))
    ancestor = contract["repositories"][system]["required_ancestor"]
    if ancestor:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, "HEAD"],
                check=False,
                capture_output=True,
                shell=False,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            issues.append(
                Issue(
                    "REPOSITORY_ANCESTOR", f"{system} ancestry check failed: {type(exc).__name__}"
                )
            )
        else:
            if result.returncode != 0:
                issues.append(
                    Issue("REPOSITORY_ANCESTOR", f"{system} is missing the required ancestor")
                )
    return issues


def _verify_openai_runtime(repo: Path, contract: dict[str, Any]) -> list[Issue]:
    """Fail closed unless this process is the exact frozen OpenAI runtime."""

    issues: list[Issue] = []
    runtime = contract["systems"]["openai"]["runtime_contract"]
    observed_implementation = platform.python_implementation()
    observed_version = platform.python_version()
    if observed_implementation != runtime["python_implementation"]:
        issues.append(
            Issue(
                "OPENAI_RUNTIME_IMPLEMENTATION",
                "OpenAI execution requires the frozen Python implementation",
            )
        )
    if observed_version != runtime["python_version"]:
        issues.append(
            Issue(
                "OPENAI_RUNTIME_VERSION",
                "OpenAI execution requires the exact frozen Python version",
            )
        )

    executable = _absolute_without_resolving(Path(sys.executable))
    try:
        executable_info = executable.lstat()
    except OSError as exc:
        issues.append(
            Issue(
                "OPENAI_RUNTIME_EXECUTABLE",
                f"Python executable metadata check failed: {type(exc).__name__}",
            )
        )
    else:
        if stat.S_ISLNK(executable_info.st_mode) or not stat.S_ISREG(executable_info.st_mode):
            issues.append(
                Issue(
                    "OPENAI_RUNTIME_EXECUTABLE",
                    "Python executable must be a regular non-symlink file",
                )
            )

    relative = runtime["dependency_lock_path"]
    expected = runtime["dependency_lock_sha256"]
    lock_path = repo / relative
    lock_payload: dict[str, Any] | None = None
    try:
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("unsafe relative path")
        if not _inside(lock_path.resolve(), repo.resolve()):
            raise ValueError("path escapes repository")
        lock_info = lock_path.lstat()
        if stat.S_ISLNK(lock_info.st_mode) or not stat.S_ISREG(lock_info.st_mode):
            raise ValueError("not a regular file")
        actual = _sha256_canonical_lf_text_file(lock_path)
        lock_payload = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        issues.append(
            Issue(
                "OPENAI_RUNTIME_LOCK",
                f"Frozen Python dependency lock is unavailable: {type(exc).__name__}",
            )
        )
    else:
        if actual != expected:
            issues.append(
                Issue(
                    "OPENAI_RUNTIME_LOCK",
                    "Frozen Python dependency lock SHA-256 differs",
                )
            )

    if lock_payload is not None:
        locked_versions: dict[str, str] = {}
        packages = lock_payload.get("packages")
        if not isinstance(packages, list):
            issues.append(
                Issue("OPENAI_RUNTIME_PACKAGES", "dependency lock package list is invalid")
            )
        else:
            for package in packages:
                if not isinstance(package, dict):
                    issues.append(
                        Issue("OPENAI_RUNTIME_PACKAGES", "dependency lock package entry is invalid")
                    )
                    continue
                name = package.get("name")
                version = package.get("version")
                if isinstance(name, str) and isinstance(version, str):
                    normalized = re.sub(r"[-_.]+", "-", name).lower()
                    locked_versions[normalized] = version
            installed_versions = {
                re.sub(r"[-_.]+", "-", str(distribution.metadata.get("Name", ""))).lower(): (
                    distribution.version
                )
                for distribution in importlib_metadata.distributions()
                if distribution.metadata.get("Name")
            }
            mismatches = [
                name
                for name, version in locked_versions.items()
                if installed_versions.get(name) != version
            ]
            if mismatches:
                issues.append(
                    Issue(
                        "OPENAI_RUNTIME_PACKAGES",
                        "installed distributions do not match the frozen dependency lock",
                    )
                )

    repo_resolved = repo.resolve()
    try:
        unchained = __import__("unchained")
        module_file = Path(unchained.__file__).resolve()
    except (AttributeError, ImportError, OSError, TypeError) as exc:
        issues.append(
            Issue(
                "OPENAI_RUNTIME_MODULE_IDENTITY",
                f"unchained module identity failed: {type(exc).__name__}",
            )
        )
    else:
        if not _inside(module_file, repo_resolved):
            issues.append(
                Issue(
                    "OPENAI_RUNTIME_MODULE_IDENTITY",
                    "unchained does not resolve inside the frozen repository",
                )
            )
    try:
        distribution = importlib_metadata.distribution("sentinel-unchained")
        direct_url_raw = distribution.read_text("direct_url.json")
        if direct_url_raw is None:
            raise ValueError("direct_url.json missing")
        direct_url = json.loads(direct_url_raw)
        parsed = urllib.parse.urlparse(direct_url.get("url", ""))
        if parsed.scheme != "file" or direct_url.get("dir_info", {}).get("editable") is not True:
            raise ValueError("distribution is not an editable local checkout")
        local_text = urllib.request.url2pathname(urllib.parse.unquote(parsed.path))
        if parsed.netloc:
            local_text = f"//{parsed.netloc}{local_text}"
        distribution_root = Path(local_text).resolve()
        if distribution_root != repo_resolved:
            raise ValueError("distribution checkout differs")
    except (
        AttributeError,
        importlib_metadata.PackageNotFoundError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        issues.append(
            Issue(
                "OPENAI_RUNTIME_DISTRIBUTION_IDENTITY",
                f"installed distribution identity failed: {type(exc).__name__}",
            )
        )

    if lock_payload is not None:
        try:
            sift_entry = next(
                package
                for package in lock_payload["packages"]
                if isinstance(package, dict) and package.get("name") == "sift-sentinel"
            )
            locked_vcs = sift_entry["vcs"]
            direct_url_raw = importlib_metadata.distribution("sift-sentinel").read_text(
                "direct_url.json"
            )
            if direct_url_raw is None:
                raise ValueError("direct_url.json missing")
            direct_url = json.loads(direct_url_raw)
            vcs_info = direct_url.get("vcs_info")
            if (
                not isinstance(locked_vcs, dict)
                or not isinstance(vcs_info, dict)
                or direct_url.get("url") != locked_vcs.get("url")
                or vcs_info.get("vcs") != locked_vcs.get("type")
                or vcs_info.get("commit_id") != locked_vcs.get("commit-id")
                or vcs_info.get("requested_revision") != locked_vcs.get("requested-revision")
            ):
                raise ValueError("VCS identity differs from lock")
        except (
            AttributeError,
            importlib_metadata.PackageNotFoundError,
            json.JSONDecodeError,
            KeyError,
            OSError,
            StopIteration,
            TypeError,
            ValueError,
        ) as exc:
            issues.append(
                Issue(
                    "OPENAI_RUNTIME_DIRECT_DEPENDENCY_IDENTITY",
                    f"sift-sentinel direct dependency identity failed: {type(exc).__name__}",
                )
            )

    try:
        cap_module = __import__("unchained.caps", fromlist=["CapConfig"])
        cap_config = cap_module.CapConfig()
    except (AttributeError, ImportError, TypeError, ValueError) as exc:
        issues.append(
            Issue(
                "OPENAI_CAP_RUNTIME",
                f"runtime cap inspection failed: {type(exc).__name__}",
            )
        )
    else:
        cap_contract = contract["systems"]["openai"]["cap_contract"]
        observed_caps = {
            "profile": "default",
            "max_tool_calls": cap_config.max_tool_calls,
            "max_total_tokens": cap_config.max_total_tokens,
            "max_wall_seconds": cap_config.max_wall_seconds,
            "max_cost_usd": cap_config.max_cost_usd,
        }
        if observed_caps != cap_contract:
            issues.append(
                Issue("OPENAI_CAP_RUNTIME", "runtime default caps differ from the frozen contract")
            )
    return issues


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _absolute_without_resolving(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _build_child_environment(
    contract: dict[str, Any],
    system: str,
    *,
    source: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return a child environment containing only this system's provider credentials."""

    inherited = dict(os.environ if source is None else source)
    child = {
        name: value for name, value in inherited.items() if name.upper() in MINIMAL_CHILD_ENV_NAMES
    }
    by_upper = {name.upper(): value for name, value in inherited.items()}
    for credential_name in EXPECTED_CREDENTIAL_ENV[system]:
        value = by_upper.get(credential_name)
        if value:
            child[credential_name] = value
    child.update(contract["systems"][system]["required_environment_values"])
    return child


def _assign_windows_kill_job(process: subprocess.Popen[bytes]) -> int:
    """Put a launched process and its descendants in a kill-on-close Job Object."""

    import ctypes
    from ctypes import wintypes

    class JobBasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JobBasicLimits),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    information = ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
    if not kernel32.SetInformationJobObject(
        job,
        9,  # JobObjectExtendedLimitInformation
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        error = ctypes.WinError(ctypes.get_last_error())
        kernel32.CloseHandle(job)
        raise error
    process_handle = wintypes.HANDLE(int(process._handle))  # type: ignore[attr-defined]
    if not kernel32.AssignProcessToJobObject(job, process_handle):
        error = ctypes.WinError(ctypes.get_last_error())
        kernel32.CloseHandle(job)
        raise error
    return int(job)


def _terminate_windows_job(job: int) -> bool:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    return bool(kernel32.TerminateJobObject(wintypes.HANDLE(job), 1))


def _close_windows_job(job: int) -> bool:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return bool(kernel32.CloseHandle(wintypes.HANDLE(job)))


def _terminate_owned_process_tree(
    process: subprocess.Popen[bytes],
    windows_job: int | None,
    *,
    platform_name: str | None = None,
) -> bool:
    """Terminate the complete owned tree and reap the direct child."""

    cleanup_succeeded = True
    platform = os.name if platform_name is None else platform_name
    if platform == "nt":
        if windows_job is None:
            cleanup_succeeded = False
            with contextlib.suppress(OSError):
                process.kill()
        else:
            if not _terminate_windows_job(windows_job):
                cleanup_succeeded = False
            if not _close_windows_job(windows_job):
                cleanup_succeeded = False
    else:
        try:
            os.killpg(process.pid, getattr(signal, "SIGKILL", 9))
        except ProcessLookupError:
            pass
        except OSError:
            cleanup_succeeded = False
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        cleanup_succeeded = False
        with contextlib.suppress(OSError):
            process.kill()
        try:
            process.wait(timeout=5.0)
        except (OSError, subprocess.TimeoutExpired):
            cleanup_succeeded = False
    except OSError:
        cleanup_succeeded = False
    return cleanup_succeeded


def _run_owned_process_tree(
    argv: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout_handle: Any,
    stderr_handle: Any,
    timeout_seconds: int,
    platform_name: str | None = None,
) -> OwnedProcessResult:
    """Run one no-shell child in an owned process tree and always clean descendants."""

    popen_options: dict[str, Any] = {
        "cwd": cwd,
        "env": environment,
        "shell": False,
        "stdin": subprocess.DEVNULL,
        "stdout": stdout_handle,
        "stderr": stderr_handle,
    }
    platform = os.name if platform_name is None else platform_name
    if platform == "nt":
        popen_options["creationflags"] = getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        ) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        ownership = "WINDOWS_JOB_OBJECT_KILL_ON_CLOSE"
    else:
        popen_options["start_new_session"] = True
        ownership = "POSIX_NEW_SESSION_PROCESS_GROUP"

    process = subprocess.Popen(argv, **popen_options)
    windows_job: int | None = None
    if platform == "nt":
        try:
            windows_job = _assign_windows_kill_job(process)
        except OSError as exc:
            _terminate_owned_process_tree(process, None, platform_name=platform)
            raise ProcessTreeOwnershipError(
                f"Windows Job Object assignment failed: {type(exc).__name__}"
            ) from exc

    timed_out = False
    returncode: int | None = None
    try:
        try:
            returncode = process.wait(timeout=float(timeout_seconds))
        except subprocess.TimeoutExpired:
            timed_out = True
    finally:
        cleanup_succeeded = _terminate_owned_process_tree(
            process, windows_job, platform_name=platform
        )
    return OwnedProcessResult(
        returncode=None if timed_out else returncode,
        timed_out=timed_out,
        ownership=ownership,
        cleanup_succeeded=cleanup_succeeded,
    )


def _verify_evidence_directory(
    path: Path, contract: dict[str, Any]
) -> tuple[Path | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        directory_info = path.lstat()
    except OSError as exc:
        return None, [
            Issue("EVIDENCE_DIRECTORY", f"evidence directory failed: {type(exc).__name__}")
        ]
    if stat.S_ISLNK(directory_info.st_mode) or not stat.S_ISDIR(directory_info.st_mode):
        return None, [Issue("EVIDENCE_DIRECTORY", "evidence input must be a non-symlink directory")]
    try:
        entries = list(path.iterdir())
    except OSError as exc:
        return None, [
            Issue("EVIDENCE_DIRECTORY", f"evidence inventory failed: {type(exc).__name__}")
        ]
    if len(entries) != 1:
        return None, [
            Issue(
                "EVIDENCE_SHAPE",
                "comparison evidence folder must contain exactly one memory file and no disk image",
            )
        ]
    evidence_file = entries[0]
    try:
        info = evidence_file.lstat()
    except OSError as exc:
        return None, [Issue("EVIDENCE_FILE", f"evidence file failed: {type(exc).__name__}")]
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return None, [Issue("EVIDENCE_FILE", "evidence must be a regular non-symlink file")]
    expected = contract["evidence"]
    if info.st_size != expected["size_bytes"]:
        issues.append(
            Issue("EVIDENCE_SIZE_MISMATCH", "evidence size differs from the frozen value")
        )
    try:
        digest = _sha256_file(evidence_file)
    except OSError as exc:
        issues.append(Issue("EVIDENCE_HASH", f"evidence hashing failed: {type(exc).__name__}"))
    else:
        if digest != expected["sha256"]:
            issues.append(
                Issue("EVIDENCE_HASH_MISMATCH", "evidence SHA-256 differs from the freeze")
            )
    return evidence_file, issues


def _expand_runner_argv(
    template: list[str],
    *,
    repo: Path,
    evidence_dir: Path,
) -> list[str]:
    replacements = {
        "{python}": sys.executable,
        "{repo}": str(repo.resolve()),
        "{evidence_dir}": str(evidence_dir.resolve()),
    }
    expanded: list[str] = []
    for value in template:
        for marker, replacement in replacements.items():
            value = value.replace(marker, replacement)
        expanded.append(value)
    return expanded


def _write_json_atomic(path: Path, value: object) -> None:
    raw = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(raw, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _path_exists_without_following(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def execute_external_runs(
    contract: dict[str, Any],
    *,
    openai_repo: Path,
    qwen_repo: Path,
    evidence_dir: Path | None,
    private_run_root: Path | None,
    systems: tuple[str, ...],
    candidate_sequence: int | None,
) -> tuple[dict[str, Any], int]:
    errors, pending = validate_contract(contract)
    if not errors:
        bound_errors, bound_pending = validate_bound_files(contract, repo_root=openai_repo)
        errors.extend(bound_errors)
        pending.extend(bound_pending)
    if "qwen" in systems:
        errors.append(
            Issue(
                "QWEN_CONTAINER_OWNERSHIP_UNAVAILABLE",
                "Qwen execution is disabled until its pinned Docker runner provides a "
                "deterministic container ID and forced daemon-side cleanup",
            )
        )
    anchor: ResolvedFreezeAnchor | None = None
    repository_commits: dict[str, str] = {}
    repositories = contract.get("repositories")
    if isinstance(repositories, dict):
        qwen_repository = repositories.get("qwen")
        if isinstance(qwen_repository, dict) and isinstance(
            qwen_repository.get("required_commit"), str
        ):
            repository_commits["qwen"] = qwen_repository["required_commit"]
    if not errors:
        anchor, anchor_errors, anchor_pending = _resolve_freeze_anchor(
            contract, openai_repo, require_current_head=True
        )
        errors.extend(anchor_errors)
        pending.extend(anchor_pending)
        if anchor is not None:
            repository_commits["openai"] = anchor.commit
    if contract.get("status") != "READY":
        pending.append(Issue("CONTRACT_NOT_READY", "comparison contract is not READY"))
    if evidence_dir is None:
        errors.append(Issue("EVIDENCE_ARGUMENT", "--evidence-dir is required with --execute"))
    if private_run_root is None:
        errors.append(
            Issue("PRIVATE_ROOT_ARGUMENT", "--private-run-root is required with --execute")
        )
    if candidate_sequence is None or candidate_sequence < 1:
        errors.append(
            Issue("CANDIDATE_SEQUENCE", "positive --candidate-sequence is required with --execute")
        )
    repos = {"openai": openai_repo.resolve(), "qwen": qwen_repo.resolve()}
    if repos["openai"] == repos["qwen"] or any(
        _inside(repos[first], repos[second])
        for first, second in (("openai", "qwen"), ("qwen", "openai"))
    ):
        errors.append(
            Issue("REPOSITORY_LOCATION", "comparison repositories must be separate trees")
        )
    evidence_absolute = (
        _absolute_without_resolving(evidence_dir) if evidence_dir is not None else None
    )
    private_absolute = (
        _absolute_without_resolving(private_run_root) if private_run_root is not None else None
    )
    if private_run_root is not None:
        assert private_absolute is not None
        if any(
            _inside(private_absolute, repo) or _inside(repo, private_absolute)
            for repo in repos.values()
        ):
            errors.append(
                Issue(
                    "PRIVATE_ROOT_LOCATION",
                    "private launch receipts must use a tree separate from both repositories",
                )
            )
        if evidence_absolute is not None and (
            _inside(private_absolute, evidence_absolute)
            or _inside(evidence_absolute, private_absolute)
        ):
            errors.append(
                Issue(
                    "PRIVATE_ROOT_LOCATION",
                    "private launch receipts and evidence must be in separate directory trees",
                )
            )
        try:
            private_info = private_absolute.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            errors.append(
                Issue(
                    "PRIVATE_ROOT_LOCATION",
                    f"private launch root metadata failed: {type(exc).__name__}",
                )
            )
        else:
            if stat.S_ISLNK(private_info.st_mode) or not stat.S_ISDIR(private_info.st_mode):
                errors.append(
                    Issue(
                        "PRIVATE_ROOT_LOCATION",
                        "private launch root must be a non-symlink directory",
                    )
                )
    if evidence_absolute is not None and any(
        _inside(evidence_absolute, repo) or _inside(repo, evidence_absolute)
        for repo in repos.values()
    ):
        errors.append(
            Issue(
                "EVIDENCE_LOCATION",
                "evidence must use a tree separate from both repositories",
            )
        )
    if not errors and not pending:
        for system in systems:
            expected_commit = repository_commits.get(system)
            if not isinstance(expected_commit, str):
                errors.append(
                    Issue(
                        "REPOSITORY_COMMIT_UNRESOLVED",
                        f"{system} repository commit authority is unresolved",
                    )
                )
                continue
            errors.extend(
                _verify_repository(
                    repos[system],
                    system,
                    contract,
                    expected_commit=expected_commit,
                )
            )
            if system == "openai":
                errors.extend(_verify_openai_runtime(repos[system], contract))
            required = contract["systems"][system]["required_environment_any_of"]
            if not any(os.environ.get(name) for name in required):
                errors.append(
                    Issue(
                        "CREDENTIAL_SOURCE_MISSING",
                        f"{system} requires one configured credential source; "
                        "no value was read or printed",
                    )
                )
            elif system == "openai":
                key_file_value = os.environ.get("OPENAI_API_KEY_FILE", "")
                key_path = _absolute_without_resolving(Path(key_file_value))
                try:
                    key_info = key_path.lstat()
                except OSError as exc:
                    errors.append(
                        Issue(
                            "CREDENTIAL_SOURCE_INVALID",
                            f"OpenAI key file metadata check failed: {type(exc).__name__}",
                        )
                    )
                else:
                    if stat.S_ISLNK(key_info.st_mode) or not stat.S_ISREG(key_info.st_mode):
                        errors.append(
                            Issue(
                                "CREDENTIAL_SOURCE_INVALID",
                                "OpenAI key file must be a regular non-symlink file",
                            )
                        )
                    if any(_inside(key_path.resolve(), repo) for repo in repos.values()):
                        errors.append(
                            Issue(
                                "CREDENTIAL_SOURCE_LOCATION",
                                "OpenAI key file must remain outside both repositories",
                            )
                        )
    if (
        not errors
        and not pending
        and evidence_absolute is not None
        and private_absolute is not None
    ):
        evidence_resolved = evidence_absolute.resolve()
        private_resolved = private_absolute.resolve()
        if any(
            _inside(evidence_resolved, repo) or _inside(repo, evidence_resolved)
            for repo in repos.values()
        ):
            errors.append(
                Issue(
                    "EVIDENCE_LOCATION",
                    "resolved evidence tree overlaps a comparison repository",
                )
            )
        if any(
            _inside(private_resolved, repo) or _inside(repo, private_resolved)
            for repo in repos.values()
        ):
            errors.append(
                Issue(
                    "PRIVATE_ROOT_LOCATION",
                    "resolved private launch tree overlaps a comparison repository",
                )
            )
        if _inside(private_resolved, evidence_resolved) or _inside(
            evidence_resolved, private_resolved
        ):
            errors.append(
                Issue(
                    "PRIVATE_ROOT_LOCATION",
                    "resolved private launch and evidence trees overlap",
                )
            )
    evidence_file: Path | None = None
    evidence_accessed = False
    if not errors and not pending and evidence_absolute is not None:
        evidence_accessed = True
        evidence_file, evidence_issues = _verify_evidence_directory(evidence_absolute, contract)
        errors.extend(evidence_issues)
    if errors or pending:
        return (
            {
                "schema_version": 1,
                "status": "REFUSED",
                "provider_or_evidence_accessed": evidence_accessed,
                "errors": [asdict(issue) for issue in _deduplicate_issues(errors)],
                "pending": [asdict(issue) for issue in _deduplicate_issues(pending)],
            },
            1 if errors else 2,
        )

    assert evidence_dir is not None
    assert private_run_root is not None
    assert evidence_absolute is not None
    assert private_absolute is not None
    assert anchor is not None
    assert candidate_sequence is not None
    private_absolute.mkdir(parents=True, exist_ok=True)
    executions: list[dict[str, Any]] = []
    for system in systems:
        credential_names = contract["systems"][system]["required_environment_any_of"]
        if not any(os.environ.get(name) for name in credential_names):
            executions.append({"system": system, "status": "REFUSED_CREDENTIAL_MISSING"})
            continue
        receipt_path = private_absolute / f"{system}-{candidate_sequence:03d}-launch.json"
        stdout_path = private_absolute / f"{system}-{candidate_sequence:03d}.stdout.log"
        stderr_path = private_absolute / f"{system}-{candidate_sequence:03d}.stderr.log"
        if any(
            _path_exists_without_following(path)
            for path in (receipt_path, stdout_path, stderr_path)
        ):
            executions.append({"system": system, "status": "REFUSED_DUPLICATE_SEQUENCE"})
            continue
        started = datetime.now(UTC)
        receipt = {
            "schema_version": 1,
            "qualification": "PRIVATE_EXTERNAL_LAUNCH_NOT_A_SCORED_RESULT",
            "comparison_id": contract["comparison_id"],
            "system": system,
            "candidate_sequence": candidate_sequence,
            "repository_commit": repository_commits[system],
            "freeze_id": contract["freeze"]["freeze_id"],
            "evidence": contract["evidence"],
            "runtime_contract": contract["systems"][system]["runtime_contract"],
            "cap_contract": contract["systems"][system]["cap_contract"],
            "measurement_regime": contract["execution"]["measurement_regime"],
            "runtime_observed": (
                {
                    "python_implementation": platform.python_implementation(),
                    "python_version": platform.python_version(),
                    "dependency_lock_sha256": contract["systems"][system]["runtime_contract"][
                        "dependency_lock_sha256"
                    ],
                }
                if system == "openai"
                else None
            ),
            "started_at_utc": started.isoformat().replace("+00:00", "Z"),
            "finished_at_utc": None,
            "wall_time_seconds": None,
            "exit_code": None,
            "state": "STARTED",
            "local_paths_recorded": False,
            "private_logs_retained": True,
            "process_tree_policy": contract["execution"]["process_tree_policy"],
            "process_tree_ownership": None,
            "process_tree_cleanup_succeeded": None,
            "post_run_repository_verified": None,
            "post_run_repository_issue_codes": [],
        }
        _write_json_atomic(receipt_path, receipt)
        argv = _expand_runner_argv(
            contract["systems"][system]["runner_argv"],
            repo=repos[system],
            evidence_dir=evidence_absolute,
        )
        child_environment = _build_child_environment(contract, system)
        start_clock = time.monotonic()
        process_tree_ownership: str | None = None
        process_tree_cleanup_succeeded = False
        try:
            with stdout_path.open("xb") as stdout_handle, stderr_path.open("xb") as stderr_handle:
                owned_result = _run_owned_process_tree(
                    argv,
                    cwd=repos[system],
                    environment=child_environment,
                    stdout_handle=stdout_handle,
                    stderr_handle=stderr_handle,
                    timeout_seconds=contract["execution"]["external_child_timeout_seconds"],
                )
            process_tree_ownership = owned_result.ownership
            process_tree_cleanup_succeeded = owned_result.cleanup_succeeded
            exit_code = owned_result.returncode
            if owned_result.timed_out:
                state = (
                    "LAUNCH_ERROR_TIMEOUT"
                    if owned_result.cleanup_succeeded
                    else "LAUNCH_ERROR_TIMEOUT_TREE_CLEANUP"
                )
            elif not owned_result.cleanup_succeeded:
                state = "LAUNCH_ERROR_TREE_CLEANUP"
            else:
                state = "FINISHED_UNINGESTED"
        except (OSError, subprocess.SubprocessError, ProcessTreeOwnershipError) as exc:
            exit_code = None
            state = f"LAUNCH_ERROR_{type(exc).__name__}"
        post_repository_issues = _verify_repository(
            repos[system],
            system,
            contract,
            expected_commit=repository_commits[system],
        )
        post_repository_verified = not post_repository_issues
        finished = datetime.now(UTC)
        receipt.update(
            {
                "finished_at_utc": finished.isoformat().replace("+00:00", "Z"),
                "wall_time_seconds": round(time.monotonic() - start_clock, 6),
                "exit_code": exit_code,
                "state": state,
                "process_tree_ownership": process_tree_ownership,
                "process_tree_cleanup_succeeded": process_tree_cleanup_succeeded,
                "post_run_repository_verified": post_repository_verified,
                "post_run_repository_issue_codes": [issue.code for issue in post_repository_issues],
            }
        )
        _write_json_atomic(receipt_path, receipt)
        executions.append(
            {
                "system": system,
                "status": state,
                "exit_code": exit_code,
                "qualification": "UNINGESTED_DO_NOT_COMPARE",
                "process_tree_ownership": process_tree_ownership,
                "process_tree_cleanup_succeeded": process_tree_cleanup_succeeded,
                "post_run_repository_verified": post_repository_verified,
                "post_run_repository_issue_codes": [issue.code for issue in post_repository_issues],
            }
        )

    assert evidence_file is not None
    final_file, final_evidence_issues = _verify_evidence_directory(evidence_absolute, contract)
    final_match = not final_evidence_issues and final_file == evidence_file
    if not final_match:
        executions.append({"system": "custody", "status": "POST_RUN_DIGEST_MISMATCH"})
    failed = (
        any(
            item.get("exit_code") not in {0, None}
            or item["status"].startswith(("REFUSED", "LAUNCH_ERROR"))
            or item.get("post_run_repository_verified") is False
            for item in executions
        )
        or not final_match
    )
    return (
        {
            "schema_version": 1,
            "status": "EXECUTED_UNINGESTED" if not failed else "EXECUTION_REQUIRES_REVIEW",
            "comparison_qualification": "NOT_ESTABLISHED",
            "same_evidence": False,
            "provider_or_evidence_accessed": True,
            "resolved_repository_commits": repository_commits,
            "anchor_tagger_timestamp_utc": anchor.tagger_timestamp_text,
            "executions": executions,
            "post_run_custody_match": final_match,
            "instruction": (
                "Retain every attempt, create sanitized candidate records and complete ledgers, "
                "then rerun without --execute. Launch receipts are not benchmark results."
            ),
        },
        1 if failed else 2,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guard and aggregate the frozen same-evidence Qwen/OpenAI benchmark."
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--records-root", type=Path, default=DEFAULT_RECORDS_ROOT)
    parser.add_argument("--openai-repo", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--qwen-repo", type=Path, default=REPO_ROOT.parent / "Sentinel-Ensemble-Qwen"
    )
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--private-run-root", type=Path)
    parser.add_argument("--candidate-sequence", type=int)
    parser.add_argument("--system", choices=("both",) + SYSTEMS, default="both")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Explicitly permit external provider-backed runner commands after every gate passes.",
    )
    parser.add_argument("--write-report", type=Path, nargs="?", const=DEFAULT_REPORT)
    parser.add_argument(
        "--json", action="store_true", help="Print sanitized machine-readable JSON."
    )
    return parser


def _execution_preflight_issue(args: argparse.Namespace) -> Issue | None:
    if args.write_report:
        return Issue(
            "REPORT_REFUSED_DURING_EXECUTION",
            "--execute and --write-report are mutually exclusive before any access",
        )
    expected_contract = args.openai_repo.resolve() / "docs" / "QWEN-COMPARISON.v1.json"
    if args.contract.resolve() != expected_contract.resolve():
        return Issue(
            "EXECUTION_CONTRACT_AUTHORITY",
            "execution requires the comparison contract inside the exact OpenAI repository",
        )
    return None


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    contract, issues = _read_json(args.contract, label="comparison contract")
    if contract is None:
        result = {
            "schema_version": 1,
            "status": "INVALID",
            "provider_or_evidence_accessed": False,
            "errors": [asdict(issue) for issue in issues],
            "pending": [],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    if args.execute:
        preflight_issue = _execution_preflight_issue(args)
        if preflight_issue is not None:
            result = {
                "schema_version": 1,
                "status": "REFUSED",
                "provider_or_evidence_accessed": False,
                "errors": [asdict(preflight_issue)],
                "pending": [],
            }
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
            return 1
        systems = SYSTEMS if args.system == "both" else (args.system,)
        result, exit_code = execute_external_runs(
            contract,
            openai_repo=args.openai_repo,
            qwen_repo=args.qwen_repo,
            evidence_dir=args.evidence_dir,
            private_run_root=args.private_run_root,
            systems=systems,
            candidate_sequence=args.candidate_sequence,
        )
    else:
        result = evaluate(
            contract,
            repo_root=args.openai_repo,
            records_root=args.records_root,
        )
        exit_code = (
            1 if result["status"] == "INVALID" else 0 if result["status"] == "COMPLETE" else 2
        )

    if args.write_report:
        report_path = args.write_report.resolve()
        if not _inside(report_path, args.openai_repo.resolve()):
            result.setdefault("errors", []).append(
                {
                    "code": "REPORT_PATH",
                    "message": "comparison report must stay inside the OpenAI repository",
                }
            )
            result["status"] = "INVALID"
            exit_code = 1
        else:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                _render_cli_markdown(contract, result), encoding="utf-8", newline="\n"
            )

    if args.json or args.execute:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(_render_cli_markdown(contract, result), end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
