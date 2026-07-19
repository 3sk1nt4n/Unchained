# Frozen same-evidence Qwen versus OpenAI protocol

> **Current status: PENDING.** The comparison runner and fail-closed aggregator
> are implemented offline. No provider was called, no evidence byte was read,
> and no faster/cheaper/more-accurate claim is authorized by this artifact. The
> shared fact set, annotated OpenAI freeze anchor, price contracts, immutable
> Qwen image/build/SBOM receipts, shared host-resource receipt, safe
> daemon-owned container lifecycle, and post-freeze candidate ledgers are not
> complete.

This protocol makes the optional Qwen comparison useful without pretending it
is a clean causal ablation. It compares two complete products on one identical
memory image under one external fact-and-metric contract. The model, provider,
prompt, orchestration, tool policy, caps, validation, and report layers remain
different and are disclosed in the output.

The machine contract is
[`QWEN-COMPARISON.v1.json`](QWEN-COMPARISON.v1.json). The generated public table
is [`runs/comparison.md`](runs/comparison.md). The standard-library guard and
aggregator is [`../scripts/benchmark_compare.py`](../scripts/benchmark_compare.py).

## Safe default: plan only

From the repository root:

```powershell
python scripts/benchmark_compare.py
python scripts/benchmark_compare.py --json
```

The default command:

- does not call OpenAI, DashScope, Qwen, Docker, or a forensic tool;
- does not inventory, open, hash, or otherwise read the private evidence;
- does not read a credential value;
- validates the closed comparison contract and any sanitized candidate ledgers;
- returns exit `2` and `PENDING` while a required frozen value or run is absent;
- returns exit `1` and `INVALID` for drift, malformed input, incomplete ledgers,
  or mismatched evidence; and
- returns exit `0` only for a complete, same-evidence, three-valid-run-per-system
  aggregate.

The sanitized JSON includes `provider_or_evidence_accessed: false`. It prints no
local evidence, key, result, or repository path.

## What “same evidence” means

Every candidate record in both ledgers must match all of these fields exactly:

| Invariant | Frozen value or source |
|---|---|
| Neutral case | `CASE-A` |
| Public evidence ID | `E001` |
| Route | `windows-memory-only` |
| Size | `2,147,483,648` bytes |
| SHA-256 | `8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62` |
| Reference facts | Exact SHA-256 from the completed benchmark freeze |
| OpenAI code | Exact final `experiment-freeze-v1` commit |
| Qwen code | Exact pinned public commit in the comparison contract |
| Candidate population | Every post-freeze attempt, in contiguous chronological order |

The external evidence folder must contain exactly one regular non-symlink file.
Any E01, disk segment, second memory image, archive, nested folder, or additional
file makes the execution preflight fail. The script hashes the file only after
the operator deliberately supplies `--execute`, and rechecks it after the
external runs.

If any retained candidate carries a different case ID, evidence ID, route,
size, digest, fact-set digest, repository commit, freeze ID, or tool policy, the
aggregator emits `INCOMPARABLE_EVIDENCE`, sets `same_evidence: false`, and
refuses the table qualification.

## Why the shipped Qwen numbers do not count

The Qwen repository includes useful historical DC01 aggregates. Those runs used
the memory-plus-disk pair and a different experimental contract. Unchained's
Build Week primary is memory-only. Reusing the historical Qwen timing, token,
cost, tool, or finding numbers would therefore violate the same-evidence rule.

Those historical files remain valuable prior-work context. They are never
loaded by this comparison script and never enter a comparison denominator.

## Frozen differences that remain differences

The output must retain, not smooth over, these facts:

1. OpenAI GPT-5.6 Sol and the frozen Qwen/DashScope roster are different models
   and providers.
2. Unchained uses a model-selected parallel opening plus one typed adaptive
   action per turn. Qwen uses its source-filtered ensemble pipeline.
3. Their eligible tool surfaces, tool-selection policies, and resulting call
   counts can differ.
4. Their token, cache, retry, timeout, cap, concurrency, and pricing semantics
   can differ.
5. Their semantic validators, reviewer behavior, report schemas, and native
   verifiers are not equivalent.
6. The only shared semantic authority is the frozen external fact/scoring
   contract. Neither system's own finding labels are copied into precision,
   recall, F1, unsupported-finding, or exact-citation scores.
7. One known public case may have training contamination and cannot establish
   general forensic accuracy.

For that reason, the result is labeled a controlled comparative case study, not
a one-variable causal ablation.

## Frozen metric definitions

Every valid run supplies the following normalized metrics:

| Metric | Common definition and source rule |
|---|---|
| End-to-end wall | External launch to complete terminal artifact; seconds |
| Time to first observation | External launch to first successful forensic output accepted by the system; seconds |
| Model requests | Accepted plus failed provider requests retained by the run's audited request counter |
| Tool calls | Attempted typed forensic actions; deterministic profile probes are excluded |
| Input/output/total tokens | Provider-recorded normalized usage; unavailable fields stay `null` |
| Estimated cost | System's own frozen price contract; never copied across providers; not an invoice |
| Final-confirmed factual precision | Shared scorer numerator and denominator from the frozen facts |
| Discovered-fact recall | Shared scorer numerator and denominator from the frozen facts |
| Confirmed-fact recall | Shared scorer numerator and denominator from the frozen facts |
| Confirmed F1 | Deterministically recomputed from final-confirmed precision and confirmed recall |
| Unsupported-finding rate | Shared receipt-sufficiency scorer numerator and denominator |
| Exact-citation-resolution rate | Shared scorer over retained artifact identity and exact citation resolution |
| Custody pass | Initial and final memory identity, size, and digest agree and mounts release |
| Native verifier pass | Each system's named native verifier; displayed with an explicit non-equivalence warning |

Every rate stores `status`, `numerator`, `denominator`, and `value`. A zero
denominator is `NOT_APPLICABLE`, never 100 percent. A valid candidate cannot
authorize its own metric values. Its ledger binds two additional regular,
non-symlink JSON files by exact filename and SHA-256:

- `candidate-NNN.extraction.json` contains the closed operational extraction
  receipt. The aggregator validates the item types and deterministically
  recomputes `total_tokens` from input plus output tokens.
- `candidate-NNN.adjudication.json` enumerates every scored frozen fact exactly
  once and every final finding once. The aggregator deterministically
  recomputes all five rates and confirmed F1 from those item-level decisions.

Changing only `candidate-NNN.json` cannot change a metric. A missing sidecar,
digest mismatch, omitted scored fact, duplicated finding, impossible confirmed
fact, malformed label, or mismatch with recomputation makes the comparison
`INVALID`.

The sidecars identify their underlying private run/scorer sources as
`HASH_REFERENCE_ONLY_SOURCE_NOT_REVERIFIED_BY_AGGREGATOR`. The public
aggregator rehashes the sanitized sidecars, but does not reopen or authenticate
the private native bundles named by those references. Therefore even a
structurally `COMPLETE` case study keeps both proof-backed performance and
accuracy-superiority claim flags false. Item-level, content-bound operator
adjudication is stronger than asserted aggregate rates; it is still not
independent proof.

Provider token and cost rows can remain `NOT AVAILABLE`. Missing values are
more honest than guessed parity.

## No-cherry-picking population rule

Each system has one candidate ledger with scope
`ALL_POST_FREEZE_CANDIDATE_ATTEMPTS`. It must enumerate every JSON candidate
record and, for every valid candidate, both required sidecars by:

- contiguous sequence beginning at 1;
- safe relative filename;
- exact SHA-256; and
- chronological post-freeze timestamp.

The candidate directory is a closed, flat file set: `ledger.json` plus exactly
the regular non-symlink record/sidecar files named by that ledger. An extra
file, nested directory, symlink, missing record, duplicate sequence, changed
digest, non-increasing timestamp, or pre-freeze timestamp fails the comparison.

Allowed classifications are:

- `VALID`;
- `INFRASTRUCTURE_FAULT` using one predeclared frozen fault code;
- `PARTIAL_CAP`; and
- `PROTOCOL_INVALID`.

The first valid complete run is the primary. Every later valid complete run is
a disclosed replicate. All valid runs enter the aggregate. Infrastructure,
cap, and invalid attempts remain visible but do not enter metric medians.
Semantic weakness, missed facts, unsupported claims, model-selected tools,
unattractive in-cap time/cost, a frozen cap firing, or a low score cannot be
relabeled as infrastructure.

The target is three valid runs per system. The public table reports the median,
minimum, maximum, and min-to-max spread across all applicable valid runs. It
cannot become `COMPLETE` below that target.

## Candidate record shape

This is an illustrative skeleton, not a result:

```json
{
  "schema_version": 1,
  "comparison_id": "sentinel-dc01-memory-qwen-openai-v1",
  "system": "openai",
  "run_id": "public-safe-stable-id",
  "sequence": 1,
  "started_at_utc": "2026-07-20T00:00:00Z",
  "post_freeze": true,
  "classification": "VALID",
  "eligible_for_aggregate": true,
  "infrastructure_fault": null,
  "terminal_status": "COMPLETE",
  "repository_commit": "<40 lowercase hex>",
  "freeze_id": "sentinel-dc01-sol-v1",
  "reference_fact_set_sha256": "<64 lowercase hex>",
  "evidence": {
    "case_id": "CASE-A",
    "public_evidence_id": "E001",
    "route": "windows-memory-only",
    "size_bytes": 2147483648,
    "sha256": "8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62"
  },
  "model": {
    "requested": "<frozen policy>",
    "provider_returned": "<retained identity>"
  },
  "tool_policy": "<exact contract value>",
  "runtime_contract": {
    "policy_id": "TAGGED_CPYTHON311_PACKAGE_LOCK_AND_PROVIDER_RECEIPTS_V1",
    "python_implementation": "CPython",
    "python_version": "3.11.9",
    "dependency_lock_path": "requirements/pylock.windows-amd64-cp311.toml",
    "dependency_lock_sha256": "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7"
  },
  "cap_contract": {
    "profile": "default",
    "max_tool_calls": 60,
    "max_total_tokens": 400000,
    "max_wall_seconds": 1800.0,
    "max_cost_usd": 10.0
  },
  "measurement_regime": "<exact closed measurement_regime object>",
  "metrics": {
    "wall_time_seconds": 0.0,
    "time_to_first_observation_seconds": 0.0,
    "model_request_count": 0,
    "tool_call_count": 0,
    "input_tokens": null,
    "output_tokens": null,
    "total_tokens": null,
    "estimated_cost_usd": null,
    "final_confirmed_factual_precision": {
      "status": "NOT_APPLICABLE",
      "numerator": 0,
      "denominator": 0,
      "value": null
    },
    "discovered_fact_recall": {
      "status": "NOT_APPLICABLE",
      "numerator": 0,
      "denominator": 0,
      "value": null
    },
    "confirmed_fact_recall": {
      "status": "NOT_APPLICABLE",
      "numerator": 0,
      "denominator": 0,
      "value": null
    },
    "unsupported_finding_rate": {
      "status": "NOT_APPLICABLE",
      "numerator": 0,
      "denominator": 0,
      "value": null
    },
    "exact_citation_resolution_rate": {
      "status": "NOT_APPLICABLE",
      "numerator": 0,
      "denominator": 0,
      "value": null
    },
    "confirmed_f1": {
      "status": "NOT_APPLICABLE",
      "value": null
    },
    "custody_pass": true,
    "native_verifier_pass": true
  }
}
```

The real ledger entry also binds the extraction and adjudication sidecars by
path and SHA-256. The record and sidecars must contain no API key, local path,
raw evidence, private tool output, or answer key. Provider identity is retained
only in the closed, policy-validated model receipt.

## Explicit external execution

External execution remains blocked while the committed contract says
`PENDING`. Before changing it to `READY`:

1. Complete and independently review the memory-only reference facts.
2. Generate and commit the benchmark freeze lock.
3. Commit the READY contract and lock, then create the annotated
   `experiment-freeze-v1` tag at that clean commit. The tag must resolve to the
   current controller/runner HEAD; its retained tagger timestamp is the local
   candidate-time floor.
4. Bind the exact OpenAI and Qwen repository SHAs.
5. Bind both price contracts and the exact Qwen model-role configuration.
6. Prebuild one Qwen image outside the measured investigation window. Bind its
   immutable `sha256:` image digest, build provenance receipt, and SBOM. A
   repository SHA alone is insufficient because the reviewed Dockerfile uses
   mutable base, apt, Python, .NET, Zimmerman-tool, and RegRipper inputs.
7. Bind one sanitized host/resource receipt and use the frozen paired order,
   warm dependency-cache/cold case-output state, and identical no-concurrent-
   workload policy. Image build/install time is disclosed separately and never
   mixed into investigation medians.
8. Ensure both target worktrees are clean at those exact commits.
9. Ensure the evidence folder contains only the one frozen memory image.
10. Configure credential sources outside Git. The script requires
   `OPENAI_API_KEY_FILE` for OpenAI and either `DASHSCOPE_API_KEY` or
   `QWEN_API_KEY` for Qwen, but never prints a value.

The owner may deliberately launch an OpenAI candidate from a private
non-repository directory:

```powershell
python scripts/benchmark_compare.py `
  --execute `
  --system openai `
  --candidate-sequence 1 `
  --evidence-dir C:\private\CASE-A-memory-only `
  --private-run-root C:\private\sentinel-comparison-launches `
  --openai-repo C:\work\sentinel-unchained `
  --qwen-repo C:\work\Sentinel-Ensemble-Qwen `
  --json
```

**Qwen execution is currently fail-closed.** The historical public launcher
builds during `setup.ps1 run` and starts a daemon-owned container whose
lifecycle is not proven by the local process tree. The comparison contract now
specifies the future fair surface: run one prebuilt image by immutable digest
with a deterministic name and cidfile, while excluding build/install time from
the investigation timer. That template is not enabled until the controller
retains the container identity and verifies daemon-side cleanup. Therefore
`--system qwen` and `--system both` return
`QWEN_CONTAINER_OWNERSHIP_UNAVAILABLE` before evidence access. Enabling Qwen
requires the immutable image/build/SBOM and host receipts plus verified
daemon-side `docker rm -f` cleanup on timeout and ordinary completion. Until
all of those exist, the scaffold cannot launch the scored Qwen side and the
comparison remains `PENDING`.

There is no shell interpolation. The script runs only the two closed argv
templates committed in the contract. It forces the frozen nonsecret model-role
environment in each child. The child does not inherit the host environment and
then attempt to guess which values are secrets. Its base is a positive,
case-insensitive allowlist containing only `PATH`, `SystemRoot`, `WINDIR`,
`ComSpec`, `PATHEXT`, `TEMP`, `TMP`, `TMPDIR`, `LANG`, `LC_ALL`, `LC_CTYPE`,
`TZ`, `PYTHONUTF8`, and `PYTHONIOENCODING` when present. It receives no home or
profile directory, proxy, cloud credential, package-registry token, Git token,
SSH/GPG agent, or unknown vendor variable. Code then adds only the selected
system's fixed provider credential allowlist and the frozen nonsecret values.

Every candidate also repeats the exact frozen runtime, cap, and measurement
regime contracts. The OpenAI side must run CPython 3.11.9 through `-I`; before
evidence access the controller verifies the canonical-LF package-lock digest,
every versioned installed distribution, the exact locked `sift-sentinel` VCS
URL/commit/requested revision, `unchained.__file__`, editable
`direct_url.json`, and the code-owned default caps. Those caps are 60 tools,
400,000 tokens, 1,800 seconds, and a $10 local estimate. The Qwen side requires
a prebuilt immutable image/build/SBOM receipt and explicitly discloses that it
has no equivalent global token or cost cap beyond its frozen pipeline and
600-second HTTP setting; that difference is not normalized away.

The controller checks exact Git commits and clean worktrees before launch and
again after each child exits, verifies memory identity before execution, and
verifies it again afterward. Child stdout and stderr remain in private launch
logs; they never contaminate the sanitized JSON channel. `SIFT_NO_OPEN=1` also
prevents the Qwen launcher from opening a result in a browser during an
automated benchmark.

Every enabled external child receives the frozen 1,800-second controller wall
timeout inside a controller-owned process tree. On Windows the direct child is
assigned to a kill-on-close Job Object; inability to obtain that ownership is a
launch error. On POSIX it starts a new session/process group. The controller
terminates and reaps the owned tree on timeout and on ordinary completion so a
late descendant cannot outlive the attempt. Timeout or failed tree cleanup is
retained in the private receipt as a launch error and never becomes a scored
result.

Process-tree ownership is a local lifecycle boundary, not a general OS sandbox
or Docker-daemon ownership boundary.
It cannot retract a provider request that reached a remote service before local
termination; the pinned runners' own request/cost caps remain authoritative for
that case. Windows Job assignment occurs immediately after process creation and
fails closed if the OS refuses it. The receipt separately records the ownership
mechanism and whether final tree cleanup succeeded.

The OpenAI commit SHA is deliberately not embedded in the commit that must
contain this contract: doing so would require a Git-hash fixed point. Instead,
the committed policy resolves the annotated tag after the commit exists,
and records the resulting 40-hex commit in every candidate. Provider execution
is allowed only from a clean checkout exactly at that tagged commit B. Read-only
aggregation may run at a clean descendant C only when every B-to-C change is
under `docs/runs/comparison-inputs/` or is the generated
`docs/runs/comparison.md`; therefore source, contract, runner, prompts, and
dependencies remain the tagged B bytes. Moving the tag is never required or
allowed. A missing tag is `PENDING`; a lightweight tag, unrelated HEAD, or
descendant that changes any nonresult path is invalid. An optional external
server/push timestamp may be retained as provenance, but it is not represented
as a local qualification fact and is not required inside the earlier commit.

The launch receipt is intentionally classified
`PRIVATE_EXTERNAL_LAUNCH_NOT_A_SCORED_RESULT`. It records no local paths and is
written outside both repositories. A process exit code is not a benchmark
result. The operator must retain the raw system artifacts privately, create a
sanitized candidate record even for a failed attempt, update the complete
ledger, and then run the aggregator without `--execute`.

## Aggregate and render

After both complete ledgers and their candidate files have been reviewed:

```powershell
python scripts/benchmark_compare.py --json
python scripts/benchmark_compare.py --write-report docs/runs/comparison.md
```

The second command writes only from the sanitized, digest-checked ledgers. The
script refuses to write a comparison report during provider execution.

## Allowed claim after completion

A public statement may report a dimension only as shown in the generated table,
for example:

> On the frozen 2 GiB DC01 memory-only case, across all three retained valid
> post-freeze runs per system, Unchained's median wall time was X with range A–B,
> versus Qwen's Y with range C–D. The systems used different providers,
> orchestration, and tool policies; this is a controlled product comparison, not
> a causal ablation.

If Qwen wins a row, report it. If a cost, token, citation, or verifier field is
not comparable, print `NOT AVAILABLE` and explain why. Do not reduce the table
to a selective “X percent faster” headline, do not hide valid runs, and do not
claim general accuracy from one case.
