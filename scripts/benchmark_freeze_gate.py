#!/usr/bin/env python3
"""Verify the Unchained DC01 benchmark preregistration without third-party packages.

The freeze deliberately has two layers:

1. ``docs/BENCHMARK-FREEZE.md`` binds the protocol foundation and every
   currently known experiment input.
2. A generated ``docs/BENCHMARK-FREEZE.lock.json`` binds the freeze document,
   this gate, the reference facts, and every protocol file without asking a
   file to contain its own Git commit or digest.

The lock is not generated until the reference fact set is populated and
declared ready.  The normal gate therefore fails closed while the evaluator is
unfinished.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import runpy
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

FREEZE_DOCUMENT = "docs/BENCHMARK-FREEZE.md"
FREEZE_GATE = "scripts/benchmark_freeze_gate.py"
MANIFEST_BEGIN = "<!-- BENCHMARK_FREEZE_MANIFEST_V1_BEGIN -->"
MANIFEST_END = "<!-- BENCHMARK_FREEZE_MANIFEST_V1_END -->"
FOUNDATION_COMMIT = "51662cfb809212af3b58a680c0d9265d91692302"
LOCK_SCHEMA_VERSION = 1
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
CANONICAL_ORIGIN_URL = "https://github.com/3sk1nt4n/sentinel-unchained.git"
REMOTE_VISIBILITY_CLAIM = (
    "public remote tag visibility is chronology evidence only; it does not authenticate "
    "server time, provide a signed timestamp, or establish cryptographic provenance"
)
EXPECTED_DEPENDENCY_LOCK = {
    "path": "requirements/pylock.windows-amd64-cp311.toml",
    "sha256": "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7",
    "target": "windows-amd64-cp311",
    "installed_versions_match": True,
}
EXPECTED_BEHAVIOR_CATEGORIES = [
    "process",
    "network",
    "service_persistence",
    "memory_injection",
    "identity_privilege",
    "execution",
    "environment_registry",
]
MINIMUM_SCORED_FACTS = 10
MINIMUM_SCORED_BEHAVIOR_CATEGORIES = 4

EXPECTED_BOUND_FILES = frozenset(
    {
        ".gitattributes",
        "docs/QWEN-COMPARISON-PROTOCOL.md",
        "docs/QWEN-COMPARISON.v1.json",
        "pyproject.toml",
        "requirements/bootstrap.txt",
        "requirements/constraints.windows-amd64-cp311.txt",
        "requirements/pylock.windows-amd64-cp311.toml",
        "scripts/benchmark_compare.py",
        "scripts/run_flagship.ps1",
        "src/unchained/__init__.py",
        "src/unchained/__main__.py",
        "src/unchained/_tool_worker.py",
        "src/unchained/agent.py",
        "src/unchained/artifacts.py",
        "src/unchained/audit.py",
        "src/unchained/caps.py",
        "src/unchained/cli.py",
        "src/unchained/evidence.py",
        "src/unchained/model.py",
        "src/unchained/models.py",
        "src/unchained/onboarding.py",
        "src/unchained/prompts.py",
        "src/unchained/reporting.py",
        "src/unchained/tools.py",
        "src/unchained/verify.py",
        "src/unchained/viewer.py",
        "src/unchained/viewer_policy.py",
    }
)

EXPECTED_TOOL_NAMES = (
    "vol_cmdline",
    "vol_dlllist",
    "vol_envars",
    "vol_filescan",
    "vol_getsids",
    "vol_handles",
    "vol_malfind",
    "vol_mftscan",
    "vol_netscan",
    "vol_privileges",
    "vol_psscan",
    "vol_pstree",
    "vol_reg_hivelist",
    "vol_svcscan",
)

EXPECTED_HARD_LIMITS = {
    "max_tool_calls": 60,
    "max_total_tokens": 400_000,
    "max_wall_seconds": 1_800.0,
    "max_cost_usd": 10.0,
}

EXPECTED_PRICE_TABLE = {
    "version": "openai-gpt-5.6-sol-2026-07-18",
    "currency": "USD",
    "unit": "per_1m_tokens",
    "input": 5.0,
    "cached_input": 0.5,
    "cache_write": 6.25,
    "output": 30.0,
    "long_context_threshold_input_tokens": 272_000,
    "long_context_input_multiplier": 2.0,
    "long_context_output_multiplier": 1.5,
    "purpose": "deterministic local cap estimate, not provider billing",
}

EXPECTED_RETRY_POLICY = {
    "sdk_max_retries": 0,
    "controller_max_transient_retries": 2,
    "base_delay_seconds": 0.25,
    "backoff": "base_delay_seconds * 2 ** zero_based_retry_index",
    "retryable_http_statuses": [408, 409, 429, "5xx"],
    "retryable_transport_classes": [
        "APIConnectionError",
        "APITimeoutError",
        "ConnectionError",
        "TimeoutError",
    ],
    "response_or_protocol_error_retryable": False,
    "forensic_tool_action_retried": False,
}

EXPECTED_PROTOCOL_CONTRACT = {
    "worker_max_response_bytes": 16_000_000,
    "model_tool_output_max_bytes": 65_536,
    "model_view_selection": "native-order UTF-8 prefix with explicit completeness receipt",
    "case_ledger_update_max_bytes": 8_192,
    "opening_min_tools": 1,
    "opening_max_tools": 6,
    "opening_execution": "all-or-none validation then parallel typed execution",
    "adaptive_max_tools_per_turn": 1,
    "terminal_protocol": "typed-DONE-v2",
    "terminal_action": "finish_investigation",
    "terminal_arguments": {"status": "DONE"},
    "terminal_match": "one canonical strict typed action; closed schema and exact enum",
    "legacy_literal_done": "verifier-readable historical v1 only; not a current runtime policy",
    "provider_store": False,
    "prompt_cache_mode": "implicit",
    "phase_policy": {
        "opening": {
            "reasoning": "low",
            "verbosity": "low",
            "max_output_tokens": 2_048,
            "minimum_output_tokens": 1,
            "max_tools": 6,
        },
        "adaptive": {
            "reasoning": "medium",
            "verbosity": "low",
            "max_output_tokens": 4_096,
            "minimum_output_tokens": 4_096,
            "max_tools": 1,
            "tool_choice": "required",
        },
        "serialization": {
            "reasoning": "medium",
            "verbosity": "low",
            "max_output_tokens": 12_288,
            "minimum_output_tokens": 4_096,
            "max_tools": 1,
        },
        "fresh_judge": {
            "reasoning": "high",
            "verbosity": "low",
            "max_output_tokens": 12_288,
            "minimum_output_tokens": 4_096,
            "max_tools": 1,
        },
        "report": {
            "reasoning": "low",
            "verbosity": "medium",
            "max_output_tokens": 8_192,
            "minimum_output_tokens": 1,
            "max_tools": 1,
        },
    },
    "public_path_sanitization": (
        "recursive case-insensitive Windows-slash-variant replacement on success and failure"
    ),
}

EXPECTED_SCORING = {
    "version": "dc01-scoring-v1",
    "zero_denominator": "NOT_APPLICABLE",
    "factual_labels": ["CORRECT", "INCORRECT", "AMBIGUOUS", "OUT_OF_RUBRIC"],
    "receipt_labels": [
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "UNSUPPORTED",
        "CONTRADICTED",
    ],
    "metrics": {
        "final_confirmed_factual_precision": {
            "numerator": "in-rubric final CONFIRMED findings labeled CORRECT",
            "denominator": "factually adjudicable in-rubric final CONFIRMED findings",
        },
        "discovered_fact_recall": {
            "numerator": "scored reference facts correctly surfaced at any final status",
            "denominator": "all scored observable reference facts",
        },
        "confirmed_fact_recall": {
            "numerator": "scored reference facts correctly surfaced and finally CONFIRMED",
            "denominator": "all scored observable reference facts",
        },
        "confirmed_f1": {
            "formula": (
                "2 * final_confirmed_factual_precision * confirmed_fact_recall / "
                "(final_confirmed_factual_precision + confirmed_fact_recall)"
            ),
            "not_applicable_when": "either component rate is NOT_APPLICABLE",
            "zero_when": "both component rates apply and their sum is zero",
        },
        "unsupported_finding_rate": {
            "numerator": (
                "final findings labeled UNSUPPORTED or CONTRADICTED on receipt sufficiency"
            ),
            "denominator": "all final findings",
        },
        "exact_citation_resolution_rate": {
            "numerator": (
                "findings for which every cited artifact hash and exact byte span verifies"
            ),
            "denominator": "all findings containing one or more citations",
        },
        "custody_pass": {
            "type": "boolean",
            "true_when": (
                "initial and final evidence ID sets, sizes, and SHA-256 values match "
                "and mounts release"
            ),
        },
        "strict_verifier_pass": {
            "type": "boolean",
            "true_when": ("sentinel verify exits 0 with --require-complete --require-live-gpt56"),
        },
    },
}

EXPECTED_RUN_SELECTION = {
    "rule_id": "first-eligible-post-freeze-complete-v1",
    "primary": (
        "the first post-freeze authentic run that reaches COMPLETE without a predeclared "
        "infrastructure fault"
    ),
    "semantic_failure_replacement_allowed": False,
    "later_valid_runs": "disclosed replicates only",
    "partial_or_cap_stopped_runs": "disclose; not primary; do not relabel as infrastructure",
    "pre_freeze_runs": "disclose and exclude from scored denominators",
    "chronology_source": (
        "local audit timestamps plus public remote tag visibility; neither authenticates "
        "server time"
    ),
    "infrastructure_faults": [
        "provider unavailable before a usable response",
        "evidence read failure or pre-run digest mismatch",
        "required symbol resolution unavailable before opening",
        "host process or storage failure that prevents protocol execution",
        "a verifier defect shown to invalidate all structurally equivalent bundles",
    ],
    "not_infrastructure_faults": [
        "weak or empty findings",
        "missed reference facts",
        "unsupported claims or reviewer escapes",
        "unattractive latency or cost within frozen caps",
        "model-selected tools",
        "a frozen cap firing",
        "low precision, recall, or F1",
    ],
}

EXPECTED_PRIOR_EXPOSURE = {
    "occurred": True,
    "date_utc": "2026-07-19",
    "classification": "PRE_FREEZE_PARTIAL_REHEARSAL_EXCLUDED_FROM_SCORING",
    "attempt_count": 5,
    "terminal_status": "PARTIAL in all five attempts",
    "successful_forensic_executions": 39,
    "successful_executions_by_attempt": [6, 8, 8, 11, 6],
    "unique_tool_names": [
        "vol_cmdline",
        "vol_dlllist",
        "vol_envars",
        "vol_getsids",
        "vol_handles",
        "vol_malfind",
        "vol_netscan",
        "vol_privileges",
        "vol_psscan",
        "vol_pstree",
        "vol_svcscan",
    ],
    "later_adaptive_successes_by_attempt": [
        ["vol_dlllist", "vol_dlllist"],
        ["vol_dlllist", "vol_handles"],
        ["vol_dlllist", "vol_handles", "vol_privileges", "vol_getsids", "vol_envars"],
        [],
    ],
    "later_terminal_no_call_message_characters": [1750, 1124, 1112, 395],
    "aggregate_local_cost_estimate_usd": 2.74536475,
    "cost_basis": "code-owned summary estimates; not provider invoices",
    "scope": (
        "GPT-5.6 Sol saw the DC01 profile and repeated opening/adaptive observations "
        "across 39 successful forensic executions; no findings, judge, or report completed"
    ),
    "effect": (
        "future primary means first eligible post-freeze COMPLETE run, "
        "not first-ever model exposure"
    ),
}

EXPECTED_LOCK_CONFIG = {
    "schema_version": 1,
    "path": "docs/BENCHMARK-FREEZE.lock.json",
    "required_for_scored_run": True,
}

EXPECTED_PUBLIC_ANCHOR = {
    "tag": "experiment-freeze-v1",
    "canonical_origin_url": CANONICAL_ORIGIN_URL,
    "remote_annotated_tag_required_for_scored_run": True,
    "remote_visibility_claim": REMOTE_VISIBILITY_CLAIM,
    "history_rewrite_allowed": False,
}

EXPECTED_DIGEST_SEMANTICS = (
    "SHA-256 of canonical Git text bytes after CRLF-to-LF normalization; "
    "raw bytes for private evidence"
)


@dataclass(frozen=True, slots=True)
class Issue:
    """One machine-readable gate finding."""

    code: str
    message: str
    kind: str = "error"

    def public_dict(self) -> dict[str, str]:
        return asdict(self)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_repository_file(path: Path) -> str:
    """Hash canonical Git text bytes so Windows checkout settings cannot drift v1."""

    content = path.read_bytes().replace(b"\r\n", b"\n")
    return _sha256_bytes(content)


def _relative_path(value: Any, *, field: str, issues: list[Issue]) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        issues.append(Issue("INVALID_PATH", f"{field} must be a nonempty POSIX relative path"))
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value.startswith("./"):
        issues.append(Issue("INVALID_PATH", f"{field} escapes or ambiguously names the repo"))
        return None
    return value


def load_manifest(root: Path) -> dict[str, Any]:
    """Load the one authoritative JSON manifest embedded in the freeze document."""

    document = root / FREEZE_DOCUMENT
    text = document.read_text(encoding="utf-8")
    if text.count(MANIFEST_BEGIN) != 1 or text.count(MANIFEST_END) != 1:
        raise ValueError("freeze document must contain exactly one manifest marker pair")
    start = text.index(MANIFEST_BEGIN) + len(MANIFEST_BEGIN)
    end = text.index(MANIFEST_END, start)
    payload = text[start:end].strip()
    if payload.startswith("```json") and payload.endswith("```"):
        payload = payload[len("```json") : -len("```")].strip()
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("freeze manifest must be a JSON object")
    return value


def _write_manifest(root: Path, manifest: dict[str, Any]) -> None:
    """Replace only the marked JSON block after an explicit refresh request."""

    document = root / FREEZE_DOCUMENT
    text = document.read_text(encoding="utf-8")
    start = text.index(MANIFEST_BEGIN) + len(MANIFEST_BEGIN)
    end = text.index(MANIFEST_END, start)
    payload = f"\n```json\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n```\n"
    document.write_text(text[:start] + payload + text[end:], encoding="utf-8")


def _check_exact(
    actual: Any,
    expected: Any,
    *,
    code: str,
    label: str,
    issues: list[Issue],
) -> None:
    if actual != expected:
        issues.append(Issue(code, f"{label} drifted from the gate-owned v1 contract"))


def _discover_local_cli_modules(root: Path) -> set[str]:
    """Return the transitive local Python modules statically imported by the CLI."""

    pending = ["cli"]
    visited: set[str] = set()
    paths: set[str] = set()
    while pending:
        module = pending.pop()
        if module in visited:
            continue
        visited.add(module)
        relative = f"src/unchained/{module}.py"
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        paths.add(relative)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 1:
                    if node.module:
                        imported.add(node.module.split(".", maxsplit=1)[0])
                    else:
                        imported.update(
                            alias.name.split(".", maxsplit=1)[0] for alias in node.names
                        )
                elif node.level == 0 and node.module and node.module.startswith("unchained."):
                    imported.add(node.module.split(".", maxsplit=2)[1])
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("unchained."):
                        imported.add(alias.name.split(".", maxsplit=2)[1])
        pending.extend(sorted(imported - visited))
    return paths


def _check_bound_files(root: Path, manifest: dict[str, Any], issues: list[Issue]) -> None:
    bound_files = manifest.get("bound_files")
    if not isinstance(bound_files, dict):
        issues.append(Issue("BOUND_FILES_INVALID", "bound_files must be an object"))
        return
    if set(bound_files) != EXPECTED_BOUND_FILES:
        missing = sorted(EXPECTED_BOUND_FILES - set(bound_files))
        extra = sorted(set(bound_files) - EXPECTED_BOUND_FILES)
        issues.append(
            Issue(
                "BOUND_FILE_SET_DRIFT",
                f"bound file set drifted; missing={missing}, extra={extra}",
            )
        )
    try:
        cli_modules = _discover_local_cli_modules(root)
    except (OSError, UnicodeError, SyntaxError) as exc:
        issues.append(
            Issue(
                "LOCAL_CLI_IMPORT_GRAPH_INVALID",
                f"cannot inspect local CLI import graph: {type(exc).__name__}",
            )
        )
    else:
        unbound_cli_modules = sorted(cli_modules - set(bound_files))
        if unbound_cli_modules:
            issues.append(
                Issue(
                    "LOCAL_CLI_MODULE_UNBOUND",
                    f"transitive local CLI modules are not freeze-bound: {unbound_cli_modules}",
                )
            )
    for raw_path, expected_digest in sorted(bound_files.items()):
        relative = _relative_path(raw_path, field="bound_files key", issues=issues)
        if relative is None:
            continue
        if not isinstance(expected_digest, str) or HEX_SHA256.fullmatch(expected_digest) is None:
            issues.append(
                Issue(
                    "BOUND_DIGEST_INVALID", f"bound digest for {relative} is not lowercase SHA-256"
                )
            )
            continue
        path = root / relative
        if not path.is_file() or path.is_symlink():
            issues.append(Issue("BOUND_FILE_MISSING", f"bound regular file is missing: {relative}"))
            continue
        actual_digest = _sha256_repository_file(path)
        if actual_digest != expected_digest:
            issues.append(
                Issue(
                    "BOUND_FILE_DRIFT",
                    f"{relative} SHA-256 is {actual_digest}, expected {expected_digest}",
                )
            )


def _check_prompt_bundle(root: Path, manifest: dict[str, Any], issues: list[Issue]) -> None:
    prompt = manifest.get("prompt_bundle")
    if not isinstance(prompt, dict):
        issues.append(Issue("PROMPT_BUNDLE_INVALID", "prompt_bundle must be an object"))
        return
    if prompt.get("canonicalization") != (
        "UTF-8 RFC 8259 JSON, sorted keys, separators comma/colon, ensure_ascii=false"
    ):
        issues.append(Issue("PROMPT_CANONICALIZATION_DRIFT", "prompt canonicalization drifted"))
    try:
        namespace = runpy.run_path(str(root / "src/unchained/prompts.py"))
        bundle = {
            "investigator": namespace["INVESTIGATOR_PROMPT"],
            "hostile_data_rule": namespace["HOSTILE_DATA_RULE"],
        }
    except (OSError, KeyError, RuntimeError) as exc:
        issues.append(
            Issue("PROMPT_BUNDLE_UNREADABLE", f"cannot rebuild base prompt: {type(exc).__name__}")
        )
        return
    actual_digest = _sha256_bytes(_canonical_json(bundle).encode("utf-8"))
    if prompt.get("canonical_base_sha256") != actual_digest:
        issues.append(
            Issue(
                "PROMPT_BUNDLE_DRIFT",
                f"canonical base prompt SHA-256 is {actual_digest}",
            )
        )
    expected_sources = {
        "src/unchained/agent.py",
        "src/unchained/prompts.py",
        "src/unchained/reporting.py",
    }
    sources = prompt.get("full_phase_prompt_sources")
    if not isinstance(sources, dict) or set(sources) != expected_sources:
        issues.append(
            Issue(
                "PROMPT_SOURCE_SET_DRIFT",
                "full_phase_prompt_sources must bind prompts.py, agent.py, and reporting.py",
            )
        )
        return
    bound_files = manifest.get("bound_files", {})
    for path, digest in sources.items():
        if digest != bound_files.get(path):
            issues.append(
                Issue("PROMPT_SOURCE_DIGEST_DRIFT", f"prompt source digest drifted: {path}")
            )


def _check_tools(root: Path, manifest: dict[str, Any], issues: list[Issue]) -> None:
    tools = manifest.get("tools")
    if not isinstance(tools, dict):
        issues.append(Issue("TOOLS_INVALID", "tools must be an object"))
        return
    _check_exact(
        tools.get("route"),
        "windows-memory-only",
        code="TOOL_ROUTE_DRIFT",
        label="tool route",
        issues=issues,
    )
    _check_exact(
        tools.get("eligible_names"),
        list(EXPECTED_TOOL_NAMES),
        code="TOOL_NAMES_DRIFT",
        label="eligible Windows-memory tool names",
        issues=issues,
    )
    expected_sources = {
        "src/unchained/_tool_worker.py",
        "src/unchained/models.py",
        "src/unchained/tools.py",
        "requirements/pylock.windows-amd64-cp311.toml",
    }
    sources = tools.get("catalog_sources")
    bound_files = manifest.get("bound_files", {})
    if not isinstance(sources, dict) or set(sources) != expected_sources:
        issues.append(Issue("TOOL_SOURCE_SET_DRIFT", "typed catalog source set drifted"))
    else:
        for path, digest in sources.items():
            if digest != bound_files.get(path):
                issues.append(Issue("TOOL_SOURCE_DIGEST_DRIFT", f"tool source drifted: {path}"))
    names_digest = _sha256_bytes(_canonical_json(list(EXPECTED_TOOL_NAMES)).encode("utf-8"))
    if tools.get("eligible_names_sha256") != names_digest:
        issues.append(Issue("TOOL_NAMES_DIGEST_DRIFT", "eligible tool-name digest drifted"))
    _check_exact(
        tools.get("typed_catalog_count"),
        14,
        code="TOOL_CATALOG_COUNT_DRIFT",
        label="typed catalog count",
        issues=issues,
    )
    _check_exact(
        tools.get("typed_catalog_sha256"),
        "a892308eccf6c23594f355f76ace069e4d2a0d64607cc9d811cc962e6f4e009b",
        code="TOOL_CATALOG_DIGEST_DRIFT",
        label="typed catalog digest",
        issues=issues,
    )
    _check_exact(
        tools.get("adaptive_action_catalog_count"),
        15,
        code="ADAPTIVE_CATALOG_COUNT_DRIFT",
        label="adaptive action catalog count",
        issues=issues,
    )
    _check_exact(
        tools.get("adaptive_action_catalog_sha256"),
        "829a0f788b073ba90f6b529c89945bd24d3d166e317cdd84c2959d1608ff0176",
        code="ADAPTIVE_CATALOG_DIGEST_DRIFT",
        label="adaptive action catalog digest",
        issues=issues,
    )
    try:
        namespace = runpy.run_path(str(root / "src/unchained/models.py"))
        finish_schema = namespace["investigation_finish_schema"]()
    except (OSError, KeyError, RuntimeError, TypeError) as exc:
        issues.append(
            Issue(
                "FINISH_SCHEMA_UNREADABLE",
                f"cannot rebuild typed-DONE schema: {type(exc).__name__}",
            )
        )
    else:
        finish_digest = _sha256_bytes(_canonical_json(finish_schema).encode("utf-8"))
        if tools.get("finish_action_schema_sha256") != finish_digest:
            issues.append(
                Issue(
                    "FINISH_SCHEMA_DRIFT",
                    f"typed-DONE schema SHA-256 is {finish_digest}",
                )
            )
    _check_exact(
        tools.get("adaptive_catalog_policy"),
        (
            "the immutable 14 forensic schemas plus exactly one canonical strict "
            "finish_investigation schema"
        ),
        code="ADAPTIVE_CATALOG_POLICY_DRIFT",
        label="adaptive action catalog policy",
        issues=issues,
    )
    _check_exact(
        tools.get("schema_policy"),
        "strict closed object schemas; controller-owned evidence references and paths",
        code="TOOL_SCHEMA_POLICY_DRIFT",
        label="typed schema policy",
        issues=issues,
    )


def _check_reference_facts(root: Path, manifest: dict[str, Any], issues: list[Issue]) -> None:
    reference = manifest.get("reference_fact_set")
    if not isinstance(reference, dict):
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference_fact_set must be an object"))
        return
    expected_fields = {
        "path",
        "status",
        "sha256",
        "schema_version",
        "fact_set_id",
        "minimum_scored_facts",
        "allowed_behavior_categories",
        "minimum_scored_behavior_categories",
        "small_set_policy",
        "authoring_rule",
    }
    if set(reference) != expected_fields:
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference_fact_set has wrong fields"))
    if reference.get("schema_version") != 1:
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference fact schema drifted"))
    if reference.get("fact_set_id") != "dc01-memory-reference-v1":
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference fact-set ID drifted"))
    if reference.get("path") != "experiment/reference-facts-v1.json":
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference fact-set path drifted"))
    if reference.get("minimum_scored_facts") != MINIMUM_SCORED_FACTS:
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "minimum scored-fact threshold drifted"))
    if reference.get("allowed_behavior_categories") != EXPECTED_BEHAVIOR_CATEGORIES:
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "behavior category vocabulary drifted"))
    if reference.get("minimum_scored_behavior_categories") != MINIMUM_SCORED_BEHAVIOR_CATEGORIES:
        issues.append(
            Issue("REFERENCE_FACT_SET_INVALID", "behavior category coverage threshold drifted")
        )
    if reference.get("small_set_policy") != (
        "withhold confirmed F1 and superiority claims unless both scored-fact and "
        "behavior-category coverage minima pass"
    ):
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "small-set scoring policy drifted"))
    if reference.get("authoring_rule") != (
        "derive from direct evidence and documented sources; do not use the pre-freeze Sol "
        "output as an answer key"
    ):
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference authoring rule drifted"))
    relative = _relative_path(reference.get("path"), field="reference_fact_set.path", issues=issues)
    if relative is None:
        return
    status = reference.get("status")
    expected_digest = reference.get("sha256")
    path = root / relative
    if status == "MISSING_NOT_READY":
        message = (
            "reference facts are not preregistered: create and independently review "
            f"{relative}, set status to READY, and bind its SHA-256"
        )
        issues.append(Issue("REFERENCE_FACT_SET_NOT_READY", message, "not_ready"))
        return
    if status != "READY":
        issues.append(Issue("REFERENCE_FACT_SET_INVALID", "reference fact status is invalid"))
        return
    if not isinstance(expected_digest, str):
        issues.append(
            Issue("REFERENCE_FACT_DIGEST_INVALID", "ready reference facts require SHA-256")
        )
        return
    if HEX_SHA256.fullmatch(expected_digest) is None:
        issues.append(Issue("REFERENCE_FACT_DIGEST_INVALID", "reference fact SHA-256 is invalid"))
        return
    if not path.is_file() or path.is_symlink():
        issues.append(Issue("REFERENCE_FACT_SET_MISSING", f"ready fact set is missing: {relative}"))
        return
    actual_digest = _sha256_repository_file(path)
    if actual_digest != expected_digest:
        issues.append(
            Issue(
                "REFERENCE_FACT_SET_DRIFT",
                f"reference fact SHA-256 is {actual_digest}, expected {expected_digest}",
            )
        )
        return
    try:
        facts = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(
            Issue(
                "REFERENCE_FACT_SET_UNREADABLE", f"fact set is invalid JSON: {type(exc).__name__}"
            )
        )
        return
    _validate_reference_fact_payload(facts, reference, issues)


def _validate_reference_fact_payload(
    payload: Any,
    reference: dict[str, Any],
    issues: list[Issue],
) -> None:
    if not isinstance(payload, dict):
        issues.append(Issue("REFERENCE_FACT_SCHEMA", "reference fact set must be an object"))
        return
    required_top = {
        "schema_version",
        "fact_set_id",
        "case_id",
        "route",
        "adjudication",
        "facts",
    }
    if set(payload) != required_top:
        issues.append(
            Issue("REFERENCE_FACT_SCHEMA", "reference fact set has the wrong top-level fields")
        )
        return
    if payload.get("schema_version") != reference.get("schema_version"):
        issues.append(Issue("REFERENCE_FACT_SCHEMA", "reference fact schema version drifted"))
    if payload.get("fact_set_id") != reference.get("fact_set_id"):
        issues.append(Issue("REFERENCE_FACT_SCHEMA", "reference fact_set_id drifted"))
    if payload.get("case_id") != "CASE-A" or payload.get("route") != "windows-memory-only":
        issues.append(
            Issue("REFERENCE_FACT_SCOPE", "reference facts must target CASE-A memory-only")
        )
    adjudication = payload.get("adjudication")
    if not isinstance(adjudication, dict) or set(adjudication) != {"kind", "reviewer", "notes"}:
        issues.append(Issue("REFERENCE_FACT_ADJUDICATION", "adjudication record is incomplete"))
    elif adjudication.get("kind") not in {
        "blinded_human",
        "project_authored_preregistered",
    }:
        issues.append(Issue("REFERENCE_FACT_ADJUDICATION", "adjudication kind is not allowed"))
    elif any(
        not isinstance(adjudication.get(field), str) or not adjudication[field].strip()
        for field in ("reviewer", "notes")
    ):
        issues.append(
            Issue("REFERENCE_FACT_ADJUDICATION", "reviewer and adjudication notes are required")
        )
    facts = payload.get("facts")
    if not isinstance(facts, list):
        issues.append(Issue("REFERENCE_FACT_SCHEMA", "facts must be an array"))
        return
    required_fact_fields = {
        "fact_id",
        "proposition",
        "behavior_category",
        "observability",
        "required_tool_family",
        "stability",
        "scored",
        "inclusion_rationale",
        "normalized_values",
        "match_mode",
        "tolerance",
        "receipt_sufficiency_guidance",
        "source_notes",
        "independent_check_notes",
        "ambiguity_notes",
        "timestamp_basis",
    }
    identifiers: set[str] = set()
    scored = 0
    scored_categories: set[str] = set()
    for index, fact in enumerate(facts):
        label = f"facts[{index}]"
        if not isinstance(fact, dict) or set(fact) != required_fact_fields:
            issues.append(Issue("REFERENCE_FACT_SCHEMA", f"{label} has the wrong fields"))
            continue
        fact_id = fact.get("fact_id")
        if not isinstance(fact_id, str) or re.fullmatch(r"DC01-F[0-9]{3,}", fact_id) is None:
            issues.append(Issue("REFERENCE_FACT_ID", f"{label} has an invalid stable fact ID"))
        elif fact_id in identifiers:
            issues.append(Issue("REFERENCE_FACT_ID", f"duplicate fact ID: {fact_id}"))
        else:
            identifiers.add(fact_id)
        for field in (
            "proposition",
            "required_tool_family",
            "inclusion_rationale",
            "receipt_sufficiency_guidance",
            "source_notes",
            "independent_check_notes",
            "ambiguity_notes",
            "timestamp_basis",
        ):
            if not isinstance(fact.get(field), str) or not fact[field].strip():
                issues.append(Issue("REFERENCE_FACT_SCHEMA", f"{label}.{field} must be nonempty"))
        observability = fact.get("observability")
        stability = fact.get("stability")
        match_mode = fact.get("match_mode")
        behavior_category = fact.get("behavior_category")
        if behavior_category not in EXPECTED_BEHAVIOR_CATEGORIES:
            issues.append(Issue("REFERENCE_FACT_CATEGORY", f"{label}.behavior_category is invalid"))
        if observability not in {"observable", "unobservable"}:
            issues.append(Issue("REFERENCE_FACT_SCHEMA", f"{label}.observability is invalid"))
        if stability not in {"stable", "approximate", "ambiguous", "unobservable"}:
            issues.append(Issue("REFERENCE_FACT_SCHEMA", f"{label}.stability is invalid"))
        if match_mode not in {
            "exact",
            "casefold_exact",
            "set_contains",
            "numeric_tolerance",
            "timestamp_tolerance",
            "human_adjudication",
        }:
            issues.append(Issue("REFERENCE_FACT_SCHEMA", f"{label}.match_mode is invalid"))
        is_scored = fact.get("scored")
        if not isinstance(is_scored, bool):
            issues.append(Issue("REFERENCE_FACT_SCHEMA", f"{label}.scored must be boolean"))
        elif is_scored:
            scored += 1
            if isinstance(behavior_category, str) and behavior_category in (
                EXPECTED_BEHAVIOR_CATEGORIES
            ):
                scored_categories.add(behavior_category)
            if observability != "observable" or stability not in {"stable", "approximate"}:
                issues.append(
                    Issue(
                        "REFERENCE_FACT_DENOMINATOR",
                        f"{label} is not eligible for a scored denominator",
                    )
                )
            if stability == "approximate" and fact.get("tolerance") is None:
                issues.append(
                    Issue(
                        "REFERENCE_FACT_TOLERANCE",
                        f"{label} is approximate without a frozen tolerance",
                    )
                )
    minimum = reference.get("minimum_scored_facts")
    if minimum != MINIMUM_SCORED_FACTS:
        issues.append(
            Issue(
                "REFERENCE_FACT_MINIMUM",
                f"minimum_scored_facts must equal {MINIMUM_SCORED_FACTS}",
            )
        )
    elif scored < minimum:
        issues.append(
            Issue(
                "REFERENCE_FACT_MINIMUM",
                f"fact set has {scored} scored observable facts; requires at least {minimum}",
            )
        )
    minimum_categories = reference.get("minimum_scored_behavior_categories")
    if minimum_categories != MINIMUM_SCORED_BEHAVIOR_CATEGORIES:
        issues.append(
            Issue(
                "REFERENCE_FACT_CATEGORY_COVERAGE",
                "minimum_scored_behavior_categories drifted",
            )
        )
    elif len(scored_categories) < minimum_categories:
        issues.append(
            Issue(
                "REFERENCE_FACT_CATEGORY_COVERAGE",
                f"fact set covers {len(scored_categories)} scored behavior categories; "
                f"requires at least {minimum_categories}",
            )
        )


def _check_lock(root: Path, manifest: dict[str, Any], issues: list[Issue]) -> None:
    lock_config = manifest.get("lock")
    if not isinstance(lock_config, dict):
        issues.append(Issue("LOCK_CONFIG_INVALID", "lock must be an object"))
        return
    relative = _relative_path(lock_config.get("path"), field="lock.path", issues=issues)
    if relative is None:
        return
    path = root / relative
    if not path.is_file() or path.is_symlink():
        issues.append(
            Issue(
                "FREEZE_LOCK_NOT_READY",
                f"generated lock is absent: {relative}; populate facts, then run --write-lock",
                "not_ready",
            )
        )
        return
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(Issue("FREEZE_LOCK_INVALID", f"lock is invalid JSON: {type(exc).__name__}"))
        return
    expected_fields = {
        "schema_version",
        "freeze_id",
        "foundation_protocol_commit",
        "source_commit",
        "locked_files",
        "aggregate_sha256",
    }
    if not isinstance(lock, dict) or set(lock) != expected_fields:
        issues.append(Issue("FREEZE_LOCK_INVALID", "lock has the wrong fields"))
        return
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        issues.append(Issue("FREEZE_LOCK_INVALID", "lock schema_version drifted"))
    if lock.get("freeze_id") != manifest.get("freeze_id"):
        issues.append(Issue("FREEZE_LOCK_DRIFT", "lock freeze_id drifted"))
    if lock.get("foundation_protocol_commit") != FOUNDATION_COMMIT:
        issues.append(Issue("FREEZE_LOCK_DRIFT", "lock foundation commit drifted"))
    source_commit = lock.get("source_commit")
    if not isinstance(source_commit, str) or HEX_GIT_SHA.fullmatch(source_commit) is None:
        issues.append(Issue("FREEZE_LOCK_INVALID", "lock source_commit is not a full Git SHA"))
    expected_paths = set(manifest.get("bound_files", {})) | {
        FREEZE_DOCUMENT,
        FREEZE_GATE,
        str(manifest.get("reference_fact_set", {}).get("path", "")),
    }
    locked_files = lock.get("locked_files")
    if not isinstance(locked_files, dict) or set(locked_files) != expected_paths:
        issues.append(Issue("FREEZE_LOCK_FILE_SET_DRIFT", "lock file set drifted"))
    else:
        for relative_path, expected_digest in sorted(locked_files.items()):
            path = root / relative_path
            if not path.is_file() or path.is_symlink():
                issues.append(
                    Issue("FREEZE_LOCK_FILE_MISSING", f"locked file missing: {relative_path}")
                )
                continue
            actual_digest = _sha256_repository_file(path)
            if actual_digest != expected_digest:
                issues.append(
                    Issue(
                        "FREEZE_LOCK_FILE_DRIFT",
                        f"locked file drifted: {relative_path} "
                        f"({actual_digest} != {expected_digest})",
                    )
                )
    aggregate = lock.get("aggregate_sha256")
    without_aggregate = {key: value for key, value in lock.items() if key != "aggregate_sha256"}
    expected_aggregate = _sha256_bytes(_canonical_json(without_aggregate).encode("utf-8"))
    if aggregate != expected_aggregate:
        issues.append(Issue("FREEZE_LOCK_AGGREGATE_DRIFT", "lock aggregate SHA-256 drifted"))


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _git_bytes(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        timeout=10,
    )


def _git_ls_remote(
    root: Path,
    canonical_origin_url: str,
    tag: str,
) -> subprocess.CompletedProcess[str]:
    """Perform the one explicit network lookup used by the scored-run gate."""

    environment = os.environ.copy()
    environment.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_ASKPASS": "",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    tag_ref = f"refs/tags/{tag}"
    return subprocess.run(
        [
            "git",
            "-c",
            "credential.interactive=never",
            "-c",
            "http.followRedirects=false",
            "ls-remote",
            "--tags",
            canonical_origin_url,
            tag_ref,
            f"{tag_ref}^{{}}",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )


def _check_git_state(
    root: Path,
    manifest: dict[str, Any],
    issues: list[Issue],
    *,
    require_tag: bool,
) -> None:
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        issues.append(Issue("GIT_REQUIRED", "freeze readiness requires a Git worktree"))
        return
    foundation = _git(root, "cat-file", "-e", f"{FOUNDATION_COMMIT}^{{commit}}")
    if foundation.returncode != 0:
        issues.append(
            Issue("FOUNDATION_COMMIT_MISSING", "protocol foundation commit is unavailable")
        )
    ancestor = _git(root, "merge-base", "--is-ancestor", FOUNDATION_COMMIT, "HEAD")
    if ancestor.returncode != 0:
        issues.append(
            Issue("FOUNDATION_NOT_ANCESTOR", "HEAD does not descend from the protocol foundation")
        )
    tracked_paths = [FREEZE_DOCUMENT, FREEZE_GATE, *sorted(EXPECTED_BOUND_FILES)]
    reference_path = manifest.get("reference_fact_set", {}).get("path")
    lock_path = manifest.get("lock", {}).get("path")
    for value in (reference_path, lock_path):
        if isinstance(value, str):
            tracked_paths.append(value)
    tracked_paths = sorted(set(tracked_paths))
    for relative in tracked_paths:
        if not (root / relative).exists():
            continue
        tracked = _git(root, "ls-files", "--error-unmatch", "--", relative)
        if tracked.returncode != 0:
            issues.append(
                Issue("FREEZE_FILE_UNTRACKED", f"freeze input is not committed: {relative}")
            )
    existing = [path for path in tracked_paths if (root / path).exists()]
    if existing:
        status = _git(root, "status", "--porcelain", "--", *existing)
        if status.returncode != 0 or status.stdout.strip():
            issues.append(
                Issue("FREEZE_FILES_DIRTY", "freeze document, facts, gate, or lock are dirty")
            )
    if isinstance(lock_path, str) and (root / lock_path).is_file():
        try:
            lock = json.loads((root / lock_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            lock = None
        if isinstance(lock, dict) and isinstance(lock.get("source_commit"), str):
            source_commit = lock["source_commit"]
            source_exists = _git(root, "cat-file", "-e", f"{source_commit}^{{commit}}")
            foundation_to_source = _git(
                root,
                "merge-base",
                "--is-ancestor",
                FOUNDATION_COMMIT,
                source_commit,
            )
            source_to_head = _git(
                root,
                "merge-base",
                "--is-ancestor",
                source_commit,
                "HEAD",
            )
            if (
                source_exists.returncode != 0
                or foundation_to_source.returncode != 0
                or source_to_head.returncode != 0
            ):
                issues.append(
                    Issue(
                        "FREEZE_LOCK_SOURCE_COMMIT_INVALID",
                        "lock source commit must exist between the foundation and current HEAD",
                    )
                )
            locked_files = lock.get("locked_files")
            if isinstance(locked_files, dict) and source_exists.returncode == 0:
                for relative, digest in sorted(locked_files.items()):
                    blob = _git_bytes(root, "show", f"{source_commit}:{relative}")
                    if blob.returncode != 0 or _sha256_bytes(blob.stdout) != digest:
                        issues.append(
                            Issue(
                                "FREEZE_LOCK_SOURCE_CONTENT_DRIFT",
                                f"source commit does not bind locked input: {relative}",
                            )
                        )
    if require_tag:
        worktree = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
        if worktree.returncode != 0 or worktree.stdout.strip():
            issues.append(
                Issue(
                    "FREEZE_WORKTREE_DIRTY",
                    "scored-run tag validation requires the entire worktree to be clean",
                )
            )
        tag = manifest.get("public_anchor", {}).get("tag")
        if not isinstance(tag, str) or not tag:
            issues.append(Issue("FREEZE_TAG_INVALID", "public freeze tag is missing"))
        else:
            tag_commit = _git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}")
            tag_type = _git(root, "cat-file", "-t", f"refs/tags/{tag}")
            head = _git(root, "rev-parse", "HEAD")
            if (
                tag_commit.returncode != 0
                or tag_type.stdout.strip() != "tag"
                or tag_commit.stdout.strip() != head.stdout.strip()
            ):
                issues.append(
                    Issue(
                        "FREEZE_TAG_MISMATCH",
                        f"annotated tag {tag} must resolve to current HEAD",
                    )
                )


def _check_remote_tag_visibility(
    root: Path,
    manifest: dict[str, Any],
    issues: list[Issue],
) -> dict[str, Any]:
    """Bind local clean HEAD to one visible annotated tag on canonical origin."""

    public_anchor = manifest.get("public_anchor")
    tag_value = public_anchor.get("tag") if isinstance(public_anchor, dict) else None
    tag = tag_value if isinstance(tag_value, str) else ""
    proof: dict[str, Any] = {
        "checked": True,
        "visible": False,
        "canonical_origin_url": CANONICAL_ORIGIN_URL,
        "tag": tag or None,
        "tag_object": None,
        "peeled_commit": None,
        "claim": REMOTE_VISIBILITY_CLAIM,
    }
    if not tag:
        issues.append(Issue("REMOTE_TAG_INVALID", "public freeze tag is missing"))
        return proof

    fetch_url = _git(root, "remote", "get-url", "--all", "origin")
    push_url = _git(root, "remote", "get-url", "--push", "--all", "origin")
    fetch_urls = [line.strip() for line in fetch_url.stdout.splitlines() if line.strip()]
    push_urls = [line.strip() for line in push_url.stdout.splitlines() if line.strip()]
    if (
        fetch_url.returncode != 0
        or push_url.returncode != 0
        or fetch_urls != [CANONICAL_ORIGIN_URL]
        or push_urls != [CANONICAL_ORIGIN_URL]
    ):
        issues.append(
            Issue(
                "REMOTE_ORIGIN_MISMATCH",
                "origin fetch and push URLs must both equal the frozen canonical GitHub URL",
            )
        )
        return proof

    tag_ref = f"refs/tags/{tag}"
    local_tag_object = _git(root, "rev-parse", "--verify", tag_ref)
    local_tag_type = _git(root, "cat-file", "-t", tag_ref)
    local_peeled_commit = _git(root, "rev-parse", "--verify", f"{tag_ref}^{{commit}}")
    local_head = _git(root, "rev-parse", "--verify", "HEAD")
    local_worktree = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    tag_object = local_tag_object.stdout.strip()
    peeled_commit = local_peeled_commit.stdout.strip()
    head = local_head.stdout.strip()
    if (
        local_tag_object.returncode != 0
        or local_tag_type.returncode != 0
        or local_tag_type.stdout.strip() != "tag"
        or local_peeled_commit.returncode != 0
        or local_head.returncode != 0
        or local_worktree.returncode != 0
        or local_worktree.stdout.strip()
        or HEX_GIT_SHA.fullmatch(tag_object) is None
        or HEX_GIT_SHA.fullmatch(peeled_commit) is None
        or HEX_GIT_SHA.fullmatch(head) is None
        or peeled_commit != head
    ):
        issues.append(
            Issue(
                "REMOTE_LOCAL_TAG_STATE_INVALID",
                "remote visibility requires a clean HEAD with the local annotated tag at HEAD",
            )
        )
        return proof

    try:
        remote = _git_ls_remote(root, CANONICAL_ORIGIN_URL, tag)
    except (OSError, subprocess.SubprocessError):
        issues.append(
            Issue(
                "REMOTE_TAG_LOOKUP_FAILED",
                "noninteractive canonical-origin tag lookup failed",
            )
        )
        return proof
    if remote.returncode != 0:
        issues.append(
            Issue(
                "REMOTE_TAG_LOOKUP_FAILED",
                "noninteractive canonical-origin tag lookup failed",
            )
        )
        return proof

    allowed_refs = {tag_ref, f"{tag_ref}^{{}}"}
    remote_refs: dict[str, str] = {}
    malformed = False
    for raw_line in remote.stdout.splitlines():
        fields = raw_line.split()
        if len(fields) != 2:
            malformed = True
            break
        object_id, ref = fields
        if (
            ref not in allowed_refs
            or ref in remote_refs
            or HEX_GIT_SHA.fullmatch(object_id) is None
        ):
            malformed = True
            break
        remote_refs[ref] = object_id
    if malformed:
        issues.append(
            Issue(
                "REMOTE_TAG_RESPONSE_INVALID",
                "canonical-origin tag lookup returned an invalid ref response",
            )
        )
        return proof
    if tag_ref not in remote_refs:
        issues.append(
            Issue("REMOTE_TAG_NOT_VISIBLE", "the frozen tag is not visible on canonical origin")
        )
        return proof
    peeled_ref = f"{tag_ref}^{{}}"
    if peeled_ref not in remote_refs:
        issues.append(
            Issue(
                "REMOTE_ANNOTATED_TAG_REQUIRED",
                "canonical origin must expose both the annotated tag object and peeled commit",
            )
        )
        return proof
    if remote_refs[tag_ref] != tag_object:
        issues.append(
            Issue(
                "REMOTE_TAG_OBJECT_MISMATCH",
                "canonical-origin tag object differs from the local annotated tag object",
            )
        )
        return proof
    if remote_refs[peeled_ref] != peeled_commit:
        issues.append(
            Issue(
                "REMOTE_TAG_COMMIT_MISMATCH",
                "canonical-origin peeled tag commit differs from clean local HEAD",
            )
        )
        return proof

    proof["visible"] = True
    proof["tag_object"] = tag_object
    proof["peeled_commit"] = peeled_commit
    return proof


def _check_runtime_environment(
    path: Path,
    manifest: dict[str, Any],
    issues: list[Issue],
) -> None:
    try:
        environment = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(
            Issue("RUN_ENVIRONMENT_INVALID", f"cannot read run environment: {type(exc).__name__}")
        )
        return
    expected = {
        "model_configuration.requested_model": manifest.get("model", {}).get("requested_alias"),
        "prompt_bundle.sha256": manifest.get("prompt_bundle", {}).get("canonical_base_sha256"),
        "tool_catalog.count": manifest.get("tools", {}).get("typed_catalog_count"),
        "tool_catalog.sha256": manifest.get("tools", {}).get("typed_catalog_sha256"),
        "dependency_lock.path": EXPECTED_DEPENDENCY_LOCK["path"],
        "dependency_lock.sha256": EXPECTED_DEPENDENCY_LOCK["sha256"],
        "dependency_lock.target": EXPECTED_DEPENDENCY_LOCK["target"],
        "dependency_lock.installed_versions_match": EXPECTED_DEPENDENCY_LOCK[
            "installed_versions_match"
        ],
    }
    for dotted, expected_value in expected.items():
        current: Any = environment
        for component in dotted.split("."):
            current = current.get(component) if isinstance(current, dict) else None
        if current != expected_value:
            issues.append(Issue("RUN_ENVIRONMENT_DRIFT", f"run {dotted} does not match freeze"))
    caps = environment.get("caps") if isinstance(environment, dict) else None
    if not isinstance(caps, dict):
        issues.append(Issue("RUN_ENVIRONMENT_DRIFT", "run caps are missing"))
    else:
        for key, value in EXPECTED_HARD_LIMITS.items():
            if caps.get(key) != value:
                issues.append(
                    Issue("RUN_ENVIRONMENT_DRIFT", f"run caps.{key} does not match freeze")
                )


def _check_evidence(path: Path, manifest: dict[str, Any], issues: list[Issue]) -> None:
    evidence = manifest.get("evidence", {})
    if not path.is_file() or path.is_symlink():
        issues.append(Issue("EVIDENCE_MISSING", "supplied evidence is not a regular file"))
        return
    if path.stat().st_size != evidence.get("size_bytes"):
        issues.append(Issue("EVIDENCE_SIZE_DRIFT", "supplied evidence size does not match freeze"))
        return
    if _sha256_file(path) != evidence.get("sha256"):
        issues.append(
            Issue("EVIDENCE_DIGEST_DRIFT", "supplied evidence SHA-256 does not match freeze")
        )


def evaluate(
    root: Path,
    *,
    require_lock: bool = True,
    require_git: bool = True,
    require_tag: bool = False,
    require_remote_tag: bool = False,
    run_environment: Path | None = None,
    evidence_path: Path | None = None,
) -> dict[str, Any]:
    """Return the complete gate result without printing or exiting."""

    root = root.resolve()
    issues: list[Issue] = []
    try:
        manifest = load_manifest(root)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        issues.append(Issue("FREEZE_MANIFEST_INVALID", str(exc)))
        return _result(None, issues)

    required_top = {
        "schema_version",
        "freeze_id",
        "preregistration_status",
        "digest_semantics",
        "foundation",
        "prior_exposure_disclosure",
        "model",
        "prompt_bundle",
        "tools",
        "caps",
        "retry_policy",
        "price_table",
        "evidence",
        "reference_fact_set",
        "scoring",
        "run_selection",
        "protocol_contract",
        "bound_files",
        "lock",
        "public_anchor",
    }
    if set(manifest) != required_top:
        issues.append(
            Issue("FREEZE_MANIFEST_SHAPE", "freeze manifest has the wrong top-level fields")
        )
    _check_exact(
        manifest.get("freeze_id"),
        "sentinel-dc01-sol-v1",
        code="FREEZE_ID_DRIFT",
        label="freeze identifier",
        issues=issues,
    )
    _check_exact(
        manifest.get("digest_semantics"),
        EXPECTED_DIGEST_SEMANTICS,
        code="DIGEST_SEMANTICS_DRIFT",
        label="cross-platform digest semantics",
        issues=issues,
    )
    status = manifest.get("preregistration_status")
    if status == "CANDIDATE_NOT_READY":
        issues.append(
            Issue(
                "CANDIDATE_NOT_REVIEWED",
                "candidate hashes are not human-reviewed and ready for the layer-two lock",
                "not_ready",
            )
        )
    elif status != "READY_FOR_LOCK":
        issues.append(Issue("PREREGISTRATION_STATUS_INVALID", "preregistration status is invalid"))
    _check_exact(
        manifest.get("schema_version"),
        1,
        code="FREEZE_SCHEMA_DRIFT",
        label="freeze schema",
        issues=issues,
    )
    _check_exact(
        manifest.get("foundation"),
        {
            "protocol_commit": FOUNDATION_COMMIT,
            "role": "immutable OpenAI-native protocol foundation",
            "required_ancestor": True,
        },
        code="FOUNDATION_DRIFT",
        label="foundation",
        issues=issues,
    )
    _check_exact(
        manifest.get("prior_exposure_disclosure"),
        EXPECTED_PRIOR_EXPOSURE,
        code="PRIOR_EXPOSURE_DRIFT",
        label="pre-freeze model exposure disclosure",
        issues=issues,
    )
    _check_exact(
        manifest.get("model"),
        {
            "requested_alias": "gpt-5.6",
            "required_family": "gpt-5.6-sol",
            "accepted_provider_identity": "gpt-5.6-sol or gpt-5.6-sol-*",
            "snapshot_policy": (
                "record exact provider-returned identity per run; an unversioned provider identity "
                "is disclosed and is not represented as a cryptographically pinned snapshot"
            ),
            "responses_api": True,
            "store": False,
        },
        code="MODEL_POLICY_DRIFT",
        label="model identity policy",
        issues=issues,
    )
    _check_exact(
        manifest.get("caps"),
        {
            "profile": "default",
            "hard_limits": EXPECTED_HARD_LIMITS,
            "scored_run_requires_explicit_values": True,
        },
        code="CAPS_DRIFT",
        label="hard caps",
        issues=issues,
    )
    _check_exact(
        manifest.get("retry_policy"),
        EXPECTED_RETRY_POLICY,
        code="RETRY_POLICY_DRIFT",
        label="retry policy",
        issues=issues,
    )
    _check_exact(
        manifest.get("price_table"),
        EXPECTED_PRICE_TABLE,
        code="PRICE_TABLE_DRIFT",
        label="price table",
        issues=issues,
    )
    _check_exact(
        manifest.get("protocol_contract"),
        EXPECTED_PROTOCOL_CONTRACT,
        code="PROTOCOL_CONTRACT_DRIFT",
        label="bounded protocol contract",
        issues=issues,
    )
    _check_exact(
        manifest.get("scoring"),
        EXPECTED_SCORING,
        code="SCORING_DRIFT",
        label="scoring definitions",
        issues=issues,
    )
    _check_exact(
        manifest.get("run_selection"),
        EXPECTED_RUN_SELECTION,
        code="RUN_SELECTION_DRIFT",
        label="no-cherry-picking run selection",
        issues=issues,
    )
    _check_exact(
        manifest.get("evidence"),
        {
            "case_id": "CASE-A",
            "public_evidence_id": "E001",
            "route": "windows-memory-only",
            "source_filename_private_to_operator": "citadeldc01.mem",
            "size_bytes": 2_147_483_648,
            "sha256": "8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62",
            "redistribution": "evidence remains outside Git and proof bundles",
        },
        code="EVIDENCE_CONTRACT_DRIFT",
        label="DC01 E001 identity",
        issues=issues,
    )
    _check_exact(
        manifest.get("lock"),
        EXPECTED_LOCK_CONFIG,
        code="LOCK_CONFIG_DRIFT",
        label="two-layer lock configuration",
        issues=issues,
    )
    _check_exact(
        manifest.get("public_anchor"),
        EXPECTED_PUBLIC_ANCHOR,
        code="PUBLIC_ANCHOR_DRIFT",
        label="public remote tag visibility anchor",
        issues=issues,
    )
    _check_bound_files(root, manifest, issues)
    _check_prompt_bundle(root, manifest, issues)
    _check_tools(root, manifest, issues)
    _check_reference_facts(root, manifest, issues)
    if require_lock:
        _check_lock(root, manifest, issues)
    remote_anchor: dict[str, Any] | None = None
    if require_remote_tag and not require_git:
        issues.append(
            Issue(
                "REMOTE_TAG_REQUIRES_GIT",
                "remote tag validation requires the local Git-state gate",
            )
        )
    if require_git:
        _check_git_state(
            root,
            manifest,
            issues,
            require_tag=require_tag or require_remote_tag,
        )
        if require_remote_tag:
            remote_anchor = _check_remote_tag_visibility(root, manifest, issues)
    if run_environment is not None:
        _check_runtime_environment(run_environment, manifest, issues)
    if evidence_path is not None:
        _check_evidence(evidence_path, manifest, issues)
    result = _result(manifest, issues)
    if require_remote_tag:
        result["remote_anchor"] = remote_anchor
    return result


def _result(manifest: dict[str, Any] | None, issues: list[Issue]) -> dict[str, Any]:
    errors = [issue for issue in issues if issue.kind == "error"]
    pending = [issue for issue in issues if issue.kind == "not_ready"]
    status = "FAIL" if errors else "NOT_READY" if pending else "READY"
    return {
        "schema_version": 1,
        "status": status,
        "ready": status == "READY",
        "freeze_id": manifest.get("freeze_id") if manifest else None,
        "foundation_protocol_commit": FOUNDATION_COMMIT,
        "issues": [issue.public_dict() for issue in issues],
    }


def _refresh_candidate(root: Path, catalog_environment: Path | None) -> dict[str, Any]:
    """Refresh byte digests only after an explicit, reviewable operator command."""

    try:
        manifest = load_manifest(root)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return _result(None, [Issue("FREEZE_MANIFEST_INVALID", str(exc))])
    if catalog_environment is None:
        return _result(
            manifest,
            [
                Issue(
                    "CATALOG_ENVIRONMENT_REQUIRED",
                    "--refresh-candidate requires --catalog-environment from the final DC01 route",
                )
            ],
        )
    lock_path = root / str(manifest.get("lock", {}).get("path", ""))
    if lock_path.is_file():
        return _result(
            manifest,
            [
                Issue(
                    "LOCK_ALREADY_EXISTS",
                    "refusing to refresh a locked v1; retain it and create a new freeze version",
                )
            ],
        )
    tag = str(manifest.get("public_anchor", {}).get("tag", ""))
    if tag and _git(root, "rev-parse", "--verify", f"refs/tags/{tag}").returncode == 0:
        return _result(
            manifest,
            [
                Issue(
                    "FREEZE_TAG_ALREADY_EXISTS",
                    f"refusing to refresh existing public tag {tag}; create a new freeze version",
                )
            ],
        )
    try:
        environment = json.loads(catalog_environment.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _result(
            manifest,
            [
                Issue(
                    "CATALOG_ENVIRONMENT_INVALID",
                    f"cannot read catalog environment: {type(exc).__name__}",
                )
            ],
        )
    if not isinstance(environment, dict):
        return _result(
            manifest,
            [Issue("CATALOG_ENVIRONMENT_INVALID", "catalog environment must be an object")],
        )
    catalog = environment.get("tool_catalog")
    model_record = environment.get("model_configuration")
    if (
        not isinstance(catalog, dict)
        or catalog.get("count") != 14
        or not isinstance(catalog.get("sha256"), str)
        or HEX_SHA256.fullmatch(catalog["sha256"]) is None
    ):
        return _result(
            manifest,
            [
                Issue(
                    "CATALOG_ENVIRONMENT_INVALID",
                    "catalog environment must attest the 14-tool DC01 typed catalog",
                )
            ],
        )
    if catalog.get("sha256") != (
        "a892308eccf6c23594f355f76ace069e4d2a0d64607cc9d811cc962e6f4e009b"
    ):
        return _result(
            manifest,
            [
                Issue(
                    "CATALOG_CHANGE_REQUIRES_REVIEW",
                    "the 14 forensic schemas changed; update the v1 gate and recompute the "
                    "15-action catalog from reviewed schemas before refreshing",
                )
            ],
        )
    if not isinstance(model_record, dict) or model_record.get("requested_model") != "gpt-5.6":
        return _result(
            manifest,
            [Issue("CATALOG_ENVIRONMENT_INVALID", "catalog environment is not a GPT-5.6 run")],
        )
    missing = [
        path
        for path in EXPECTED_BOUND_FILES
        if not (root / path).is_file() or (root / path).is_symlink()
    ]
    if missing:
        return _result(
            manifest,
            [
                Issue(
                    "BOUND_FILE_MISSING", f"cannot refresh; missing bound files: {sorted(missing)}"
                )
            ],
        )
    bound_files = {
        path: _sha256_repository_file(root / path) for path in sorted(EXPECTED_BOUND_FILES)
    }
    try:
        namespace = runpy.run_path(str(root / "src/unchained/prompts.py"))
        prompt_bundle = {
            "investigator": namespace["INVESTIGATOR_PROMPT"],
            "hostile_data_rule": namespace["HOSTILE_DATA_RULE"],
        }
    except (OSError, KeyError, RuntimeError) as exc:
        return _result(
            manifest,
            [
                Issue(
                    "PROMPT_BUNDLE_UNREADABLE",
                    f"cannot rebuild base prompt: {type(exc).__name__}",
                )
            ],
        )
    prompt_digest = _sha256_bytes(_canonical_json(prompt_bundle).encode("utf-8"))
    manifest["bound_files"] = bound_files
    manifest["prompt_bundle"]["canonical_base_sha256"] = prompt_digest
    for path in manifest["prompt_bundle"]["full_phase_prompt_sources"]:
        manifest["prompt_bundle"]["full_phase_prompt_sources"][path] = bound_files[path]
    manifest["tools"]["typed_catalog_count"] = catalog["count"]
    manifest["tools"]["typed_catalog_sha256"] = catalog["sha256"]
    try:
        namespace = runpy.run_path(str(root / "src/unchained/models.py"))
        finish_schema = namespace["investigation_finish_schema"]()
    except (OSError, KeyError, RuntimeError, TypeError) as exc:
        return _result(
            manifest,
            [
                Issue(
                    "FINISH_SCHEMA_UNREADABLE",
                    f"cannot refresh typed-DONE schema: {type(exc).__name__}",
                )
            ],
        )
    manifest["tools"]["finish_action_schema_sha256"] = _sha256_bytes(
        _canonical_json(finish_schema).encode("utf-8")
    )
    manifest["tools"]["adaptive_action_catalog_count"] = 15
    manifest["tools"]["adaptive_action_catalog_sha256"] = (
        "829a0f788b073ba90f6b529c89945bd24d3d166e317cdd84c2959d1608ff0176"
    )
    for path in manifest["tools"]["catalog_sources"]:
        manifest["tools"]["catalog_sources"][path] = bound_files[path]
    manifest["preregistration_status"] = "CANDIDATE_NOT_READY"
    _write_manifest(root, manifest)
    result = _result(manifest, [])
    result["status"] = "CANDIDATE_REFRESHED_NOT_REVIEWED"
    result["ready"] = False
    result["next_action"] = (
        "review the diff and tests, populate the independent reference facts, then commit the "
        "candidate inputs"
    )
    return result


def build_lock(root: Path, manifest: dict[str, Any], source_commit: str) -> dict[str, Any]:
    """Build the second-layer lock payload after all human-owned inputs are ready."""

    if HEX_GIT_SHA.fullmatch(source_commit) is None:
        raise ValueError("source_commit must be a full lowercase Git SHA")
    reference_path = manifest["reference_fact_set"]["path"]
    locked_paths = sorted(
        set(manifest["bound_files"]) | {FREEZE_DOCUMENT, FREEZE_GATE, reference_path}
    )
    locked_files = {path: _sha256_repository_file(root / path) for path in locked_paths}
    payload: dict[str, Any] = {
        "schema_version": LOCK_SCHEMA_VERSION,
        "freeze_id": manifest["freeze_id"],
        "foundation_protocol_commit": FOUNDATION_COMMIT,
        "source_commit": source_commit,
        "locked_files": locked_files,
    }
    payload["aggregate_sha256"] = _sha256_bytes(_canonical_json(payload).encode("utf-8"))
    return payload


def _write_lock(root: Path) -> dict[str, Any]:
    preflight = evaluate(root, require_lock=False, require_git=True)
    if not preflight["ready"]:
        return preflight
    manifest = load_manifest(root)
    if manifest.get("preregistration_status") != "READY_FOR_LOCK":
        return _result(
            manifest,
            [
                Issue(
                    "PREREGISTRATION_STATUS_NOT_READY",
                    "set preregistration_status to READY_FOR_LOCK only after human review",
                    "not_ready",
                )
            ],
        )
    head = _git(root, "rev-parse", "HEAD")
    source_commit = head.stdout.strip()
    if head.returncode != 0 or HEX_GIT_SHA.fullmatch(source_commit) is None:
        return _result(manifest, [Issue("GIT_REQUIRED", "cannot resolve the source commit")])
    lock = build_lock(root, manifest, source_commit)
    lock_path = root / manifest["lock"]["path"]
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = _result(manifest, [])
    result["status"] = "LOCK_WRITTEN_NOT_COMMITTED"
    result["ready"] = False
    result["lock_path"] = manifest["lock"]["path"]
    result["aggregate_sha256"] = lock["aggregate_sha256"]
    result["next_action"] = (
        "review and commit the lock, publish the annotated tag on canonical origin, then rerun "
        "with --require-tag --require-remote-tag"
    )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="emit one machine-readable JSON object")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--write-lock", action="store_true", help="write layer-two lock after readiness"
    )
    action.add_argument(
        "--refresh-candidate",
        action="store_true",
        help="intentionally refresh candidate byte/catalog digests for review",
    )
    parser.add_argument(
        "--catalog-environment",
        type=Path,
        help="sanitized final-route environment.json required by --refresh-candidate",
    )
    parser.add_argument(
        "--require-tag", action="store_true", help="require public freeze tag at HEAD"
    )
    parser.add_argument(
        "--require-remote-tag",
        action="store_true",
        help=(
            "perform one noninteractive network lookup and require the local annotated tag "
            "object and peeled HEAD to be visible on canonical origin"
        ),
    )
    parser.add_argument(
        "--run-environment", type=Path, help="also verify a sanitized environment.json"
    )
    parser.add_argument("--evidence", type=Path, help="also stream-check the private E001 image")
    return parser


def _print_human(result: dict[str, Any]) -> None:
    print(f"Benchmark freeze: {result['status']}")
    print(f"Foundation: {result['foundation_protocol_commit']}")
    for issue in result.get("issues", []):
        print(f"- {issue['kind'].upper()} {issue['code']}: {issue['message']}")
    if result.get("next_action"):
        print(f"Next: {result['next_action']}")


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = arguments.root.resolve()
    if arguments.write_lock:
        result = _write_lock(root)
    elif arguments.refresh_candidate:
        result = _refresh_candidate(root, arguments.catalog_environment)
    elif arguments.catalog_environment is not None:
        result = _result(
            None,
            [
                Issue(
                    "CATALOG_ENVIRONMENT_UNUSED",
                    "--catalog-environment is valid only with --refresh-candidate",
                )
            ],
        )
    else:
        result = evaluate(
            root,
            require_tag=arguments.require_tag,
            require_remote_tag=arguments.require_remote_tag,
            run_environment=arguments.run_environment,
            evidence_path=arguments.evidence,
        )
    if arguments.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(result)
    if result["status"] == "READY":
        return 0
    if result["status"] in {
        "NOT_READY",
        "LOCK_WRITTEN_NOT_COMMITTED",
        "CANDIDATE_REFRESHED_NOT_REVIEWED",
    }:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
