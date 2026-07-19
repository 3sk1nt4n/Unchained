# Unchained DC01 benchmark freeze v1

> **Preregistration status: NOT READY.** The candidate starts from the
> `51662cf` protocol foundation, but final integration is still changing code and
> the atomic reference fact set does not yet exist in Git. The gate must fail;
> no run may be called the frozen scored primary yet.

This document is the human-readable and machine-readable contract for the
Windows memory-only DC01 comparison. It freezes inputs before the next scored
run. It does not retroactively turn the July 19 capped Sol rehearsal into a
preregistered result.

Run the gate from the repository root:

```powershell
python scripts/benchmark_freeze_gate.py
python scripts/benchmark_freeze_gate.py --json
```

During integration, exit code `1` and status `FAIL` are expected when final code
bytes differ from the seeded foundation hashes. After the explicit candidate
refresh, the expected result is exit code `2` and status `NOT_READY` because the
human-reviewed facts and generated lock remain absent. Exit code `0` is reserved
for a fully locked, internally consistent freeze.

The all-zero `scripts/run_flagship.ps1` digest in the seed manifest is an
intentional fail-closed placeholder because that runner did not exist in the
foundation commit. Only `--refresh-candidate` may replace it after integration
and review.

## What is already bound

### Protocol foundation and the self-reference problem

The OpenAI-native execution protocol is based on commit
`51662cfb809212af3b58a680c0d9265d91692302`. That commit fixes the controller,
prompt sources, tools, verifier, dependencies, Docker/CLI release, and tests that
existed before this freeze work. It is an immutable parent, not the final scored
implementation commit. The final reviewed bytes are bound separately by the
candidate content manifest and later public tag.

A freeze file cannot honestly contain the SHA of the Git commit that contains
that same file: changing the file changes the commit. This freeze therefore
uses two layers:

1. **Foundation layer.** The full foundation commit establishes the immutable
   base. Exact SHA-256 values for every final protocol and dependency file are
   refreshed only after integration and then bind the scored implementation,
   including the exact flagship runner used to set caps and invoke verification.
2. **Lock layer.** After the reference facts are complete, the gate generates
   `docs/BENCHMARK-FREEZE.lock.json`. That lock hashes this document, the gate,
   the fact set, and every bound implementation file. The lock is committed in a
   following commit, and the public `experiment-freeze-v1` annotated tag anchors
   that exact tree. The scored-run gate must see the tag object and its peeled
   commit on the exact canonical GitHub origin immediately before execution.

The lock does not hash itself. The public Git tag identifies the lock-containing
commit, so there is no circular digest or invented future commit SHA. Remote tag
visibility is chronology evidence only: it does not authenticate server time,
provide a signed timestamp, or establish cryptographic provenance.

All repository-file SHA-256 values use canonical Git text bytes: CRLF is
normalized to LF before hashing, and `.gitattributes` is itself bound. This
matches committed blob semantics across Windows and Linux instead of treating a
checkout setting as protocol drift. The private evidence image is always hashed
as raw bytes with no normalization.

### Model and snapshot policy

- Request exactly the public `gpt-5.6` alias through the Responses API.
- Accept only a provider-returned Sol identity: `gpt-5.6-sol` or a
  `gpt-5.6-sol-*` snapshot string.
- Record the exact provider-returned identity for every request.
- If OpenAI returns only the unversioned `gpt-5.6-sol` identity, disclose that
  limitation. Do not claim a cryptographically pinned hidden snapshot.
- Use `store=false`; do not use Luna for a qualifying forensic bundle.

### Prompt bundle

The canonical base prompt is the sorted, compact UTF-8 JSON object containing
`INVESTIGATOR_PROMPT` and `HOSTILE_DATA_RULE`. Its SHA-256 is bound in the
manifest. The complete dynamic phase text is additionally bound by exact byte
digests of:

- `src/unchained/prompts.py`;
- `src/unchained/agent.py`, which assembles opening, adaptive, serialization,
  judge, and report instructions; and
- `src/unchained/reporting.py`, which owns the structured report contract.

This source-level binding is deliberate: phase packets incorporate runtime
profile, ledger, receipt, and budget values, so one static rendered prompt would
not represent every request. The strict verifier later reconstructs each actual
request.

### Tools and schemas

The scored route is exactly Windows memory-only `E001`. Its deterministic
opening registry exposes the 14 forensic names listed in the manifest. The
retained authentic DC01 environment record produced a canonical strict
forensic-catalog digest of
`a892308eccf6c23594f355f76ace069e4d2a0d64607cc9d811cc962e6f4e009b`.
That historical record attests only the frozen 14-tool catalog and requested
model. The refresh gate rebuilds the current prompt digest from local source and
binds those source bytes; it does not represent the old environment as an
attestation of the current prompt.

Adaptive turns expose those same immutable 14 forensic schemas plus exactly one
closed non-forensic action: `finish_investigation({"status":"DONE"})`. The
15-action catalog and standalone finish schema have separate hashes. The action
is the only current terminal authority, `tool_choice` is required, and one turn
may contain exactly one typed action. Blank output, prose, whitespace variants,
case variants, punctuation, and Markdown are not accepted as completion.
Literal-DONE-v1 remains verifier-readable only for historical bundles.

The tool and worker source, exact dependency pin, schema count, sorted name
digest, and complete catalog digest are all bound. Model arguments never contain
an evidence path; the controller binds `E001` and its initial SHA-256 to every
eligible tool.

A qualifying environment must also report dependency-lock path
`requirements/pylock.windows-amd64-cp311.toml`, SHA-256
`2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7`,
target `windows-amd64-cp311`, and `installed_versions_match=true`. The flagship
wrapper checks this parity before execution and again from the retained
environment before it writes qualifying metrics.

### Evidence identity

The only scored evidence route is:

| Field | Frozen value |
|---|---|
| Neutral case ID | `CASE-A` |
| Public evidence ID | `E001` |
| Shape | Windows memory-only |
| Operator-side source file | `citadeldc01.mem` |
| Bytes | `2,147,483,648` |
| SHA-256 | `8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62` |

The image stays outside Git and outside proof bundles. The case title, source
page, answer key, and evaluator rubric must not be included in model context.
The optional `--evidence` gate argument rehashes the private file locally and
prints no path or evidence content.

## Prior-exposure disclosure

GPT-5.6 Sol had five pre-freeze DC01 attempts on July 19, 2026. All five ended
`PARTIAL` and are excluded from every scored denominator. Their successful
forensic-execution counts were `6`, `8`, `8`, `11`, and `6`: 39 executions over
11 unique typed tools, including repeated observations. The first attempt ran
the six-tool opening. The four later attempts added, respectively,
`vol_dlllist` twice; `vol_dlllist` plus `vol_handles`; `vol_dlllist`,
`vol_handles`, `vol_privileges`, `vol_getsids`, and `vol_envars`; and no
additional successful adaptive tool. The six opening tools were `vol_cmdline`,
`vol_pstree`, `vol_svcscan`, `vol_psscan`, `vol_malfind`, and `vol_netscan`.

The four later terminal no-call responses were not empty: their visible message
lengths were 1,750, 1,124, 1,112, and 395 characters. No attempt completed
findings, fresh judge, or report. Code-owned summary estimates total
`$2.74536475` across the five attempts; that figure is a local estimate, not a
provider invoice. No raw model output or private run identifier is part of this
freeze disclosure.

This means the next run may be described as the **first eligible post-freeze
complete primary**, not as the first time GPT-5.6 ever saw DC01. The reference
facts must be checked directly against the public evidence and documented
sources; the partial model output is not an allowed answer-key source.

## Human-owned input still required

Create `experiment/reference-facts-v1.json` before changing the manifest status
to `READY`. Do not infer or copy facts from the prior Sol output. Every record
must have exactly these fields:

```json
{
  "fact_id": "DC01-F001",
  "proposition": "One atomic factual proposition.",
  "behavior_category": "process",
  "observability": "observable",
  "required_tool_family": "volatility3.windows",
  "stability": "stable",
  "scored": true,
  "inclusion_rationale": "Why this belongs in the memory-only denominator.",
  "normalized_values": {},
  "match_mode": "human_adjudication",
  "tolerance": null,
  "receipt_sufficiency_guidance": "What retained output would support it.",
  "source_notes": "Where the candidate fact came from.",
  "independent_check_notes": "How it was checked against evidence.",
  "ambiguity_notes": "Known ambiguity, or 'none identified'.",
  "timestamp_basis": "UTC, local, relative, or not applicable."
}
```

Allowed stability values are `stable`, `approximate`, `ambiguous`, and
`unobservable`. An approximate scored fact requires a numeric or timestamp
tolerance frozen in the record. Ambiguous and unobservable facts may remain in
the explanatory set but cannot enter a scored denominator.

The closed behavior-category vocabulary is `process`, `network`,
`service_persistence`, `memory_injection`, `identity_privilege`, `execution`, and
`environment_registry`. Qualification requires at least 10 scored observable
facts across at least four distinct categories. If either minimum is missed,
confirmed F1 and all superiority claims are withheld; a tiny hand-picked set is
never treated as a winning comparison.

The preferred evaluator is a named blinded human who did not build the result.
If the owner authors the facts, use the exact label
`project_authored_preregistered`; do not call that independent external ground
truth.

## Frozen scoring rules

The layer-two lock also binds the executable comparison aggregator, its closed
machine contract, and the normative comparison protocol. This prevents the
scorer, candidate-selection rules, or disclosure policy from changing after
the freeze while still claiming the same v1 experiment.

Factual correctness and receipt sufficiency are separate labels:

- Factual: `CORRECT`, `INCORRECT`, `AMBIGUOUS`, `OUT_OF_RUBRIC`.
- Receipt: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`.

Every rate publishes its numerator and denominator. A zero denominator is
`NOT_APPLICABLE`, never 100%. The machine manifest freezes the exact formulas
for:

- final-confirmed factual precision;
- discovered-fact recall;
- confirmed-fact recall;
- confirmed precision/recall F1;
- unsupported-finding rate;
- exact-citation-resolution rate;
- Boolean custody pass; and
- Boolean strict-verifier pass.

Exact quote occurrence proves citation integrity, not semantic entailment.
Relational, causal, maliciousness, absence, and broad narrative claims require
human adjudication. A same-model judge is a downgrade-only control, not truth.

## Run selection: no cherry-picking

The primary is the first authentic post-freeze run that reaches `COMPLETE`
without one of the predeclared infrastructure faults in the manifest. A weak,
empty, expensive-within-cap, or semantically disappointing complete result
remains primary. Later valid runs are disclosed replicates.

A cap-stopped `PARTIAL` run is disclosed, is not primary, and is not silently
relabeled as infrastructure failure. Every post-freeze candidate attempt must
be retained in chronological order.

## Completing the freeze

1. Finish all integration changes and pass the complete test/release gate.
2. Produce a sanitized `environment.json` from the final DC01 route, then run:

   ```powershell
   python scripts/benchmark_freeze_gate.py --refresh-candidate `
     --catalog-environment C:\path\to\sanitized\environment.json
   ```

   This explicit command updates only candidate byte and catalog digests, sets
   status back to `CANDIDATE_NOT_READY`, refuses to overwrite an existing lock,
   and exits `2`. Review its diff; it does not bless the code automatically.
   The already disclosed pre-freeze environment receipt may be used solely as
   14-schema catalog and requested-model attestation. Its historical prompt
   digest is not authority for the current prompt; the gate rebuilds that digest
   from current local source. The receipt does not become a scored run or
   authorize another pre-freeze model call.
3. Independently construct and review `experiment/reference-facts-v1.json`.
4. Compute its SHA-256, set the manifest fact status to `READY`, bind the digest,
   and change `preregistration_status` to `READY_FOR_LOCK`.
5. Commit the document, gate, final code, and fact set. The worktree must be
   clean.
6. Run `python scripts/benchmark_freeze_gate.py --write-lock`.
7. Review and commit `docs/BENCHMARK-FREEZE.lock.json`.
8. Create the annotated public tag `experiment-freeze-v1` at the lock commit.
9. Push the commit and tag to the exact canonical origin
   `https://github.com/3sk1nt4n/Unchained.git` without rewriting history.
10. Immediately before execution, run
    `python scripts/benchmark_freeze_gate.py --require-tag --require-remote-tag --json`
    and retain its JSON artifact. This performs one noninteractive remote lookup;
    it is not a server-timestamp or cryptographic-provenance claim.
11. Only then call a subsequent run the frozen scored primary.

Any implementation, prompt, schema, cap, retry, price, fact, scoring, or
selection change after the tag creates a disclosed `v2`; it never rewrites v1.

## Machine-readable contract

The gate parses the following JSON directly. Do not maintain a second manifest
by hand.

<!-- BENCHMARK_FREEZE_MANIFEST_V1_BEGIN -->
```json
{
  "schema_version": 1,
  "freeze_id": "sentinel-dc01-sol-v1",
  "preregistration_status": "CANDIDATE_NOT_READY",
  "digest_semantics": "SHA-256 of canonical Git text bytes after CRLF-to-LF normalization; raw bytes for private evidence",
  "foundation": {
    "protocol_commit": "51662cfb809212af3b58a680c0d9265d91692302",
    "role": "immutable OpenAI-native protocol foundation",
    "required_ancestor": true
  },
  "prior_exposure_disclosure": {
    "occurred": true,
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
      "vol_svcscan"
    ],
    "later_adaptive_successes_by_attempt": [
      ["vol_dlllist", "vol_dlllist"],
      ["vol_dlllist", "vol_handles"],
      ["vol_dlllist", "vol_handles", "vol_privileges", "vol_getsids", "vol_envars"],
      []
    ],
    "later_terminal_no_call_message_characters": [1750, 1124, 1112, 395],
    "aggregate_local_cost_estimate_usd": 2.74536475,
    "cost_basis": "code-owned summary estimates; not provider invoices",
    "scope": "GPT-5.6 Sol saw the DC01 profile and repeated opening/adaptive observations across 39 successful forensic executions; no findings, judge, or report completed",
    "effect": "future primary means first eligible post-freeze COMPLETE run, not first-ever model exposure"
  },
  "model": {
    "requested_alias": "gpt-5.6",
    "required_family": "gpt-5.6-sol",
    "accepted_provider_identity": "gpt-5.6-sol or gpt-5.6-sol-*",
    "snapshot_policy": "record exact provider-returned identity per run; an unversioned provider identity is disclosed and is not represented as a cryptographically pinned snapshot",
    "responses_api": true,
    "store": false
  },
  "prompt_bundle": {
    "canonicalization": "UTF-8 RFC 8259 JSON, sorted keys, separators comma/colon, ensure_ascii=false",
    "canonical_base_sha256": "4f6a120e4234790b58e933c16e7fd9130419d52841b8b4d7fff8bf0cd6fd04bb",
    "full_phase_prompt_sources": {
      "src/unchained/agent.py": "ac0be058b07883b280b28642f5694a70d7d852b81d9d402d3f2ee9dfa14fe534",
      "src/unchained/prompts.py": "43e2daa42bd21385dd8f34e85e46b5dcbfa5968df8b906a15c7c90adaed9bda8",
      "src/unchained/reporting.py": "88bbe0a8648572a04d1a38cec09ce2bb4b4ddda41ffbce826bba22dc511bf405"
    }
  },
  "tools": {
    "route": "windows-memory-only",
    "eligible_names": [
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
      "vol_svcscan"
    ],
    "eligible_names_sha256": "9066fcd6fa43cd119c8381cc164498589f4469a8926a8a5c58ab2f11fa8ea7bb",
    "typed_catalog_count": 14,
    "typed_catalog_sha256": "a892308eccf6c23594f355f76ace069e4d2a0d64607cc9d811cc962e6f4e009b",
    "adaptive_action_catalog_count": 15,
    "adaptive_action_catalog_sha256": "829a0f788b073ba90f6b529c89945bd24d3d166e317cdd84c2959d1608ff0176",
    "finish_action_schema_sha256": "36a0474afe757394b66668e8e7d78e3fada0f998afc6728ad6c7dd81ad7d1b75",
    "adaptive_catalog_policy": "the immutable 14 forensic schemas plus exactly one canonical strict finish_investigation schema",
    "schema_policy": "strict closed object schemas; controller-owned evidence references and paths",
    "catalog_sources": {
      "src/unchained/_tool_worker.py": "fe76c7059e96f463929fffeec566e6e15f31a9f261c211476d01416d25653bed",
      "src/unchained/models.py": "bc33056f375ca17acae83a99a099719d6fcdda1c3e4cb8313b1514af18006729",
      "src/unchained/tools.py": "fa7b923954fa8abd3ef9a91a2393a359545a03a0ef2b5868e7d66836ee266d9e",
      "requirements/pylock.windows-amd64-cp311.toml": "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7"
    }
  },
  "caps": {
    "profile": "default",
    "hard_limits": {
      "max_tool_calls": 60,
      "max_total_tokens": 400000,
      "max_wall_seconds": 1800.0,
      "max_cost_usd": 10.0
    },
    "scored_run_requires_explicit_values": true
  },
  "retry_policy": {
    "sdk_max_retries": 0,
    "controller_max_transient_retries": 2,
    "base_delay_seconds": 0.25,
    "backoff": "base_delay_seconds * 2 ** zero_based_retry_index",
    "retryable_http_statuses": [408, 409, 429, "5xx"],
    "retryable_transport_classes": [
      "APIConnectionError",
      "APITimeoutError",
      "ConnectionError",
      "TimeoutError"
    ],
    "response_or_protocol_error_retryable": false,
    "forensic_tool_action_retried": false
  },
  "price_table": {
    "version": "openai-gpt-5.6-sol-2026-07-18",
    "currency": "USD",
    "unit": "per_1m_tokens",
    "input": 5.0,
    "cached_input": 0.5,
    "cache_write": 6.25,
    "output": 30.0,
    "long_context_threshold_input_tokens": 272000,
    "long_context_input_multiplier": 2.0,
    "long_context_output_multiplier": 1.5,
    "purpose": "deterministic local cap estimate, not provider billing"
  },
  "evidence": {
    "case_id": "CASE-A",
    "public_evidence_id": "E001",
    "route": "windows-memory-only",
    "source_filename_private_to_operator": "citadeldc01.mem",
    "size_bytes": 2147483648,
    "sha256": "8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62",
    "redistribution": "evidence remains outside Git and proof bundles"
  },
  "reference_fact_set": {
    "path": "experiment/reference-facts-v1.json",
    "status": "MISSING_NOT_READY",
    "sha256": null,
    "schema_version": 1,
    "fact_set_id": "dc01-memory-reference-v1",
    "minimum_scored_facts": 10,
    "allowed_behavior_categories": [
      "process",
      "network",
      "service_persistence",
      "memory_injection",
      "identity_privilege",
      "execution",
      "environment_registry"
    ],
    "minimum_scored_behavior_categories": 4,
    "small_set_policy": "withhold confirmed F1 and superiority claims unless both scored-fact and behavior-category coverage minima pass",
    "authoring_rule": "derive from direct evidence and documented sources; do not use the pre-freeze Sol output as an answer key"
  },
  "scoring": {
    "version": "dc01-scoring-v1",
    "zero_denominator": "NOT_APPLICABLE",
    "factual_labels": [
      "CORRECT",
      "INCORRECT",
      "AMBIGUOUS",
      "OUT_OF_RUBRIC"
    ],
    "receipt_labels": [
      "SUPPORTED",
      "PARTIALLY_SUPPORTED",
      "UNSUPPORTED",
      "CONTRADICTED"
    ],
    "metrics": {
      "final_confirmed_factual_precision": {
        "numerator": "in-rubric final CONFIRMED findings labeled CORRECT",
        "denominator": "factually adjudicable in-rubric final CONFIRMED findings"
      },
      "discovered_fact_recall": {
        "numerator": "scored reference facts correctly surfaced at any final status",
        "denominator": "all scored observable reference facts"
      },
      "confirmed_fact_recall": {
        "numerator": "scored reference facts correctly surfaced and finally CONFIRMED",
        "denominator": "all scored observable reference facts"
      },
      "confirmed_f1": {
        "formula": "2 * final_confirmed_factual_precision * confirmed_fact_recall / (final_confirmed_factual_precision + confirmed_fact_recall)",
        "not_applicable_when": "either component rate is NOT_APPLICABLE",
        "zero_when": "both component rates apply and their sum is zero"
      },
      "unsupported_finding_rate": {
        "numerator": "final findings labeled UNSUPPORTED or CONTRADICTED on receipt sufficiency",
        "denominator": "all final findings"
      },
      "exact_citation_resolution_rate": {
        "numerator": "findings for which every cited artifact hash and exact byte span verifies",
        "denominator": "all findings containing one or more citations"
      },
      "custody_pass": {
        "type": "boolean",
        "true_when": "initial and final evidence ID sets, sizes, and SHA-256 values match and mounts release"
      },
      "strict_verifier_pass": {
        "type": "boolean",
        "true_when": "sentinel verify exits 0 with --require-complete --require-live-gpt56"
      }
    }
  },
  "run_selection": {
    "rule_id": "first-eligible-post-freeze-complete-v1",
    "primary": "the first post-freeze authentic run that reaches COMPLETE without a predeclared infrastructure fault",
    "semantic_failure_replacement_allowed": false,
    "later_valid_runs": "disclosed replicates only",
    "partial_or_cap_stopped_runs": "disclose; not primary; do not relabel as infrastructure",
    "pre_freeze_runs": "disclose and exclude from scored denominators",
    "chronology_source": "local audit timestamps plus public remote tag visibility; neither authenticates server time",
    "infrastructure_faults": [
      "provider unavailable before a usable response",
      "evidence read failure or pre-run digest mismatch",
      "required symbol resolution unavailable before opening",
      "host process or storage failure that prevents protocol execution",
      "a verifier defect shown to invalidate all structurally equivalent bundles"
    ],
    "not_infrastructure_faults": [
      "weak or empty findings",
      "missed reference facts",
      "unsupported claims or reviewer escapes",
      "unattractive latency or cost within frozen caps",
      "model-selected tools",
      "a frozen cap firing",
      "low precision, recall, or F1"
    ]
  },
  "protocol_contract": {
    "worker_max_response_bytes": 16000000,
    "model_tool_output_max_bytes": 65536,
    "model_view_selection": "native-order UTF-8 prefix with explicit completeness receipt",
    "case_ledger_update_max_bytes": 8192,
    "opening_min_tools": 1,
    "opening_max_tools": 6,
    "opening_execution": "all-or-none validation then parallel typed execution",
    "adaptive_max_tools_per_turn": 1,
    "terminal_protocol": "typed-DONE-v2",
    "terminal_action": "finish_investigation",
    "terminal_arguments": {
      "status": "DONE"
    },
    "terminal_match": "one canonical strict typed action; closed schema and exact enum",
    "legacy_literal_done": "verifier-readable historical v1 only; not a current runtime policy",
    "provider_store": false,
    "prompt_cache_mode": "implicit",
    "phase_policy": {
      "opening": {
        "reasoning": "low",
        "verbosity": "low",
        "max_output_tokens": 2048,
        "minimum_output_tokens": 1,
        "max_tools": 6
      },
      "adaptive": {
        "reasoning": "medium",
        "verbosity": "low",
        "max_output_tokens": 4096,
        "minimum_output_tokens": 4096,
        "max_tools": 1,
        "tool_choice": "required"
      },
      "serialization": {
        "reasoning": "medium",
        "verbosity": "low",
        "max_output_tokens": 12288,
        "minimum_output_tokens": 4096,
        "max_tools": 1
      },
      "fresh_judge": {
        "reasoning": "high",
        "verbosity": "low",
        "max_output_tokens": 12288,
        "minimum_output_tokens": 4096,
        "max_tools": 1
      },
      "report": {
        "reasoning": "low",
        "verbosity": "medium",
        "max_output_tokens": 8192,
        "minimum_output_tokens": 1,
        "max_tools": 1
      }
    },
    "public_path_sanitization": "recursive case-insensitive Windows-slash-variant replacement on success and failure"
  },
  "bound_files": {
    ".gitattributes": "c667c2985ba332b868f72614896450a68033befcacfa8c171dabc7ecc7d62dc3",
    "pyproject.toml": "386e0fd31da4ab305c208632f7fdcd3fa8bcf8f340be43a8398a2c498d44d029",
    "requirements/bootstrap.txt": "eb6e1808f9ecdf678dd8206ddfcd35ae83198530a10ac3aa0fcbdaeac217bdb6",
    "requirements/constraints.windows-amd64-cp311.txt": "e6d78bba5e062f2ee7cfdf3904d0a61f55691827815d4e8396514633febac653",
    "requirements/pylock.windows-amd64-cp311.toml": "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7",
    "scripts/run_flagship.ps1": "0000000000000000000000000000000000000000000000000000000000000000",
    "src/unchained/__init__.py": "e6f8fc9b8dee423bf114f0aa2f87c7f40936d55cfa4d11368d8bcf582a82c589",
    "src/unchained/__main__.py": "46fcf317d3ea9191caeb36c2f507ac106c6c6ad39048a0a16807427ada904efa",
    "src/unchained/_tool_worker.py": "fe76c7059e96f463929fffeec566e6e15f31a9f261c211476d01416d25653bed",
    "src/unchained/agent.py": "ac0be058b07883b280b28642f5694a70d7d852b81d9d402d3f2ee9dfa14fe534",
    "src/unchained/artifacts.py": "39431274ba0796b33e1e22682ae92bd4a96ba9b17c4299b58cf7e564c676c075",
    "src/unchained/audit.py": "dd93aa9e1a5dfc8fb48d8b612377adf3229056ddd2db0bc1be3aab1126f9d0d0",
    "src/unchained/caps.py": "9a19b29519b4d4d4c51845b82184fc458441918c6aa2befed985a09201379ee2",
    "src/unchained/cli.py": "f7d685339cebfd445a51de36f9eadb504a1c47e111585e2ce51f302d1175a331",
    "src/unchained/evidence.py": "ee43ce3406342c1f085246ac563053faa7ca0a7a6ff99f9b0e7121cdff7a5651",
    "src/unchained/model.py": "a9fce2cfd7610e252c6c422fd54e9d1f6fd26f2627885d02bcb05e7f345bfa02",
    "src/unchained/models.py": "bc33056f375ca17acae83a99a099719d6fcdda1c3e4cb8313b1514af18006729",
    "src/unchained/onboarding.py": "720cc547110bd18c1371d15da5b44939a34269a3b1e7c6abb1df030ab3a5ae1c",
    "src/unchained/prompts.py": "43e2daa42bd21385dd8f34e85e46b5dcbfa5968df8b906a15c7c90adaed9bda8",
    "src/unchained/reporting.py": "88bbe0a8648572a04d1a38cec09ce2bb4b4ddda41ffbce826bba22dc511bf405",
    "src/unchained/tools.py": "fa7b923954fa8abd3ef9a91a2393a359545a03a0ef2b5868e7d66836ee266d9e",
    "src/unchained/verify.py": "70e54a848841f90ac299c93bc47806c7ac5aabfdf460c39db05c9b8c5475acb5",
    "src/unchained/viewer.py": "371aaa9a7022ad68b8f424066c2ed2aef313bf3749ac54af77d74c0d9f0f88c5",
    "src/unchained/viewer_policy.py": "57c81f3b6e5512665610c51a1b705f271b20e3a730fcdb182eeb7c437f9d8f91"
  },
  "lock": {
    "schema_version": 1,
    "path": "docs/BENCHMARK-FREEZE.lock.json",
    "required_for_scored_run": true
  },
  "public_anchor": {
    "tag": "experiment-freeze-v1",
    "canonical_origin_url": "https://github.com/3sk1nt4n/Unchained.git",
    "remote_annotated_tag_required_for_scored_run": true,
    "remote_visibility_claim": "public remote tag visibility is chronology evidence only; it does not authenticate server time, provide a signed timestamp, or establish cryptographic provenance",
    "history_rewrite_allowed": false
  }
}
```
<!-- BENCHMARK_FREEZE_MANIFEST_V1_END -->
