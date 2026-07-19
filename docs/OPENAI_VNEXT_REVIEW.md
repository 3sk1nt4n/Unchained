# OpenAI-native vNext review

Date: 2026-07-18

This review compares the focused `sentinel-unchained` controller with its
`Sentinel-Ensemble-Qwen` predecessor and records the bounded OpenAI-native vNext
implemented in this working tree. It is an engineering review, not a claim that
an authentic end-to-end evidence run has completed.

> **2026-07-19 protocol amendment:** unscored live audits showed completed
> no-call responses containing substantial ledger prose, not empty output.
> Runtime v2 therefore replaces the brittle raw-text terminator with one closed
> required action, `finish_investigation({"status":"DONE"})`. Arbitrary text is
> never normalized into completion; historical literal-DONE-v1 remains
> verifier-readable only.

## Repositories reviewed

- `sentinel-unchained`: upstream `main` at
  `2b256a7bfd170388d2a8497dd3289af248abae18`.
- `Sentinel-Ensemble-Qwen`: upstream `master` at
  `9f309c6134e857f7b86f3e6b9c6709ce954944a5`.

Both local checkouts matched their live GitHub heads at the start of the review.
The original Unchained baseline passed 129 tests, Ruff check, Ruff format check,
`pip check`, and wheel/sdist builds before any change was made.

## Bottom line

Do not port the Qwen conductor and do not restart Unchained. The right successor
is the existing Unchained state machine with a smaller context protocol, exact
evidence spans, an honest proof verifier, deterministic reporting, and a usable
offline front door.

The target remains:

```text
evidence folder
      |
      v
PROFILE + ROUTE [deterministic]
  content classification, evidence OS/shape, SHA-256 custody, capability truth
      |
      v
OPENING BOOK [GPT-5.6]
  choose one to six distinct route-valid typed tools; all-or-none validation
      |
      v
parallel typed execution [deterministic authority]
  atomic reservation, bounded workers, deterministic replay order
      |
      v
PLAN -> ACT -> OBSERVE -> UPDATE [GPT-5.6]
  stateless ledger packet; exactly one required typed action per adaptive turn
      |
      v
finish_investigation({"status":"DONE"}) -> forced structured serialization
  [deterministic typed-DONE-v2 protocol]
      |
      v
exact evidence-span resolution [deterministic]
      |
      v
FRESH JUDGE [GPT-5.6]
  scoped spans only; preserve or downgrade; never add or upgrade
      |
      v
STRUCTURED REPORT DRAFT [GPT-5.6]
      |
      v
close tools/mounts -> post-run full SHA-256 custody verification [deterministic]
      |
      v
deterministic Markdown + offline HTML viewer + content-addressed proof bundle
      |
      v
offline lifecycle/artifact/span verification [deterministic]
```

## What Qwen got right

The Qwen repository contains several patterns worth preserving:

1. Content-first evidence onboarding and a clear case card.
2. Typed, allowlisted forensic functions instead of model-authored shell commands.
3. Concurrent independent collection with deterministic result ordering.
4. Canonical fact/provenance concepts and explicit uncertainty buckets.
5. Bounded adaptive investigation and visibility into blocked or inconclusive work.

Those strengths are substrate and product lessons, not a reason to keep the
Qwen orchestration shape.

## What must not be carried forward from Qwen

### Monolithic and divergent orchestration

The active `run_pipeline.py` and package `coordinator.py` are separate,
materially different conductors. The production script executes work at import
time and grew into a multi-thousand-line pipeline. This makes execution drift
from tests and makes safety properties depend on several later repair layers.

### Tool-volume floor instead of information gain

Qwen pads model choices into a 20-to-35-tool sweep. Its published heavy run used
33 tools and took about 14 minutes 39 seconds. Starting a new MCP process for
many calls adds avoidable initialization and serialization overhead. The vNext
opening remains a maximum of six, followed only by adaptive one-tool turns. This
is designed to reduce work and context growth; it is not a measured speed claim
until both systems are benchmarked on the same evidence and limits.

### Incorrect custody semantics

The active Qwen post-hash begins before later investigative/report phases and a
mismatch is not in the final hard-fail expression. A second conductor may reuse
the initial digest when size and timestamp are unchanged. vNext performs a real
final full read after tool work stops and treats mismatch as fatal.

### Fail-open validation and repair layers

Qwen contains paths that turn validator exceptions into apparent passes, fall
back from a missing typed fact store, or silently change a requested live run
into dry-run behavior. Trust-boundary failures must be explicit `INVALID`,
`PARTIAL`, or `FATAL` states.

### Model and report provenance gaps

The Qwen finalizer can promote findings, raw model-visible evidence is not
consistently isolated as hostile data, and generated HTML interpolates dynamic
values without universal escaping. vNext starts a new downgrade-only judge,
uses exact evidence spans, and renders HTML without scripts or unescaped dynamic
markup.

## What Unchained got right

The focused successor already had the correct safety skeleton:

- complete content inventory and full pre/post SHA-256 reads;
- public evidence IDs that keep normal paths out of model prompts;
- strict typed function schemas and code-owned evidence paths;
- atomic reservation and all-or-none validation of the opening batch before
  launch;
- exact content-addressed retention before `tool.completed` is accepted;
- one required adaptive typed action per turn and closed typed-DONE termination;
- forced structured finalization with forensic tools removed;
- a fresh judge that cannot upgrade a status;
- explicit `COMPLETE`, `PARTIAL`, `INVALID`, and `FATAL` states;
- audited token, cost, time, and tool caps;
- a standard-library offline verifier.

## Blocking defects found in the Unchained baseline

### P0: all real custody receipts failed their own verifier

The initial receipt was keyed by `E001`; the final receipt was keyed by the
private relative filename. The verifier compared the dictionaries exactly. The
retained partial run reproduced `initial and final recorded custody hashes
differ` even though the SHA-256 values matched.

vNext keeps the relative-path map private and emits the sealed evidence-ID map
on both passes.

### P0: strict verification accepted a fabricated, incomplete lifecycle

The former strict test asserted PASS for a bundle containing only an audit, one
tool output, and one self-authored `investigate` response. It did not require the
opening, finalizer, judge, report, report/profile/environment/summary artifacts,
or request/response pairing.

vNext requires the ordered lifecycle, all five model phases, unique
response/request IDs, and all required root artifacts, including the offline
viewer. Each model call must occupy a retry-aware transaction window containing
its request and exact phase options, zero to two valid error/scheduled retry
pairs, a recovery receipt when retried, and one accepted response. It revalidates
strict tool schemas and phase options; requires an opening selection of one to
six distinct valid calls with no rejected subset and forbids any `capped` or
`rejected` receipt in `COMPLETE`; binds each opening/adaptive
call ID, name, and arguments to its receipt/action; binds the forced serializer,
judge, and report arguments to controller outputs; and checks full
artifact-write descriptors.

It also reconstructs the exact opening, adaptive, finalizer, judge, and report
inputs from verified controller state, including each ledger, receipt index,
budget snapshot, latest observation, and finalizer observation sequence.
Accepted response output usage is bounded by the paired request maximum; retry
transport/status/timeout records are constrained to runtime-reachable values;
and controller lifecycle counts must equal the verified collections.
Typed argument values use the exact same bool-safe primitive JSON Schema rule as
runtime. The verifier also rederives OS, shape, canonical filesystems, and route
warnings from the evidence inventory so deterministic routing fields cannot be
rewritten independently.

The normalized assistant message and normalized function calls are the sole
audited response authority. Raw provider `output_items` are intentionally not
recorded as a redundant representation that could contradict those fields.
The verifier independently recomputes local per-call and cumulative cost from
audited token usage and the configured GPT-5.6 price table, then binds the final
budget snapshot to the configured caps. Those figures are controller cap
estimates, not provider billing records. Adversarial tests recompute the entire
audit chain, manifest, and detached checksum after mutation, so PASS no longer
means only that phase labels exist. The unavoidable boundary remains: an
offline verifier can validate recorded provider metadata but cannot authenticate
self-recorded API IDs with OpenAI.

### P0: tool outputs were not bound to their input evidence

The model supplied only forensic arguments such as `pid`; the controller chose
an evidence path out of band, and receipts did not retain its evidence ID or
digest. vNext records the controller-selected `evidence_refs` on both
`tool.started` and `tool.completed`, verifies the pair is unchanged, and checks
every strict receipt against the initial custody map.

### P0: extra images were silently ignored

The registry and mount path selected only the first ready memory and disk item.
Full evidence-ID-selectable multi-image routing needs a larger scheduler/mount
change. Until that exists, vNext fails closed with an actionable split-case
message instead of claiming case-wide completion.

### P1: the fresh judge saw only the first 2,048 bytes

The investigator could see up to 65,536 bytes per output, while the fresh judge
could quote only the audit prefix. A valid record after byte 2,048 was invisible.

vNext requires the investigator finalizer to submit exact supporting text. Code
resolves it against the full retained output and records artifact SHA-256, byte
start/end, occurrence count, and a stable span ID. The judge receives those
scoped spans. The offline verifier rereads the artifact against its earlier
device/inode/digest, checks the exact byte range, and independently recomputes
the occurrence count. A regression test proves a supporting span after byte
3,000 verifies successfully.

### P1: repeated provider transcript replay grew context and broke live input

The previous loop replayed provider output objects, encrypted reasoning items,
and all prior tool views. Besides approximately quadratic request growth, a
provider-only function-call `status` field stopped the retained live rehearsal.

vNext makes every adaptive request stateless. Code sends the public profile, a
compact case ledger, a receipt index without arbitrary excerpts, the remaining
budget, and only the latest paired observation. Every nonterminal tool call must
also carry a visible, valid-UTF-8 ledger update no larger than 8,192 bytes; code
records it before execution and strict verification rebinds it to the model
response. The finalizer receives retained observations once, after the model
calls the closed `finish_investigation({"status":"DONE"})` protocol action.
Empty text, prose, whitespace, punctuation, and Markdown do not terminate the
loop. The verifier retains read compatibility with historical literal-DONE-v1
bundles.

### P1: free-form Markdown was a protocol choke point

A missing model-authored heading or table cell could turn an otherwise valid
investigation into `PARTIAL`. vNext asks GPT-5.6 for a strict narrative-and-reference
draft. Code renders the authoritative findings table, investigator-to-judge
status transition, citations, spans, IOCs, limitations, and unresolved questions.
The model cannot add a row or alter a verdict through formatting. Its prose is
explicitly labeled model-authored and nonauthoritative, while the exact
normalized report bytes and SHA-256 are bound into the audit. Strict verification
reconstructs the canonical profile, binds its evidence inventory to initial and
final custody, rebuilds the summary, and independently rerenders both the report
and viewer from verified inputs; each regenerated artifact must match the sealed
bytes exactly.

## OpenAI-native speed policy

The Responses API remains the provider seam. Every request uses `store=false`.
The exact provider-returned model, response ID, request ID, status, and usage are
audited separately from the requested alias.

vNext records and applies phase-specific controls:

| Phase | Reasoning effort | Text verbosity | Max output tokens | Provider tool-call ceiling |
|---|---:|---:|---:|---:|
| Opening | low | low | 2,048 | 6 |
| Adaptive turn | medium | low | 4,096 | 1 |
| Investigation serialization | medium | low | 12,288 | 1 |
| Fresh judge | high | low | 12,288 | 1 |
| Report draft | low | medium | 8,192 | 1 |

These settings do not replace the code-owned caps. They reduce unnecessary
latency/output while the controller remains authoritative. Requests use
GPT-5.6 implicit prompt caching so matching stable prefixes may be reused; cap
preflight still assumes an uncached request, provider cache reads/writes are
audited and priced, and no live speedup is claimed without a same-evidence
benchmark. Recorded costs are reproducible local estimates used for enforcement,
not an assertion that they equal an OpenAI invoice.

Official references used for the OpenAI-specific design:

- <https://developers.openai.com/api/docs/guides/latest-model>
- <https://developers.openai.com/api/docs/guides/migrate-to-responses>
- <https://developers.openai.com/api/docs/guides/structured-outputs>
- <https://developers.openai.com/api/docs/guides/prompt-caching>

## User-facing vNext

The installed project now exposes both `sentinel` and the compatibility
`sentinel-unchained` entry point:

```powershell
sentinel doctor
sentinel profile C:\Evidence\case --json
sentinel run C:\Evidence\case --caps strict
sentinel verify C:\path\to\run --require-complete --require-live-gpt56
sentinel view C:\path\to\run
```

- `doctor` checks readiness without reading evidence or printing secrets.
- `profile` performs deterministic classification, routing, two custody reads,
  and zero OpenAI calls.
- `run` validates model/key configuration before evidence I/O, prints phase
  progress and the cloud-data boundary, and emits exact verify/view next steps.
- `view` verifies the bundle before opening a required, manifest-covered
  `viewer.html`; a bundle claiming `COMPLETE` is forced through strict lifecycle
  verification.
- `run.ps1` installs only when the environment is missing, respects an existing
  key, and accepts a file or directory.

The viewer is one static HTML file with a restrictive CSP, no scripts, no
external fonts/assets, no links, no network requests, escaped dynamic text,
responsive evidence/tool tables, recorded custody status, and explicit proof
limitations.

## Offline verification snapshot

The completed working tree contains 17 source modules, 32 Python files, 13,383
physical source lines, 12,259 nonblank source lines, and 267 collected tests.
Under the external CPython 3.11.9 AMD64 proof environment on 2026-07-18:

- all 267 tests passed;
- Ruff check and format check passed across 32 Python files;
- `pip check` reported no broken requirements;
- wheel and sdist construction from the isolated build path passed;
- `git diff --check` passed with only a Windows line-ending advisory for
  `run.ps1`;
- `doctor --json` safely reported the missing model/key with exit `2` and no
  secret output.

No OpenAI request was made. The in-app browser runtime failed before it could
load the local viewer because required sandbox-policy metadata was absent, so
human visual/cross-browser QA is still pending. Automated HTML parser and
active-content tests passed, including exact deterministic viewer rerendering
and rejection of manifest-consistent active replacements.

## Remaining release blockers

This working tree is materially better, but the following are not solved and
must remain explicit:

1. **No authentic completed GPT-5.6 evidence run.** The environment used for
   this review had no API key, and the documented freeze says not to spend the
   DC01 primary call yet. Only offline fake-provider lifecycle tests ran.
2. **No OS-enforced parser sandbox.** Credential stripping and process-tree
   termination are implemented, but third-party parser children still have the
   current user's normal filesystem/network authority. Production needs a
   restricted principal/AppContainer or equivalent, network deny, read-only
   handle broker, scratch-only writes, and CPU/RAM/process quotas.
3. **No stable-handle or immutable-snapshot custody.** Pre/post hashes detect
   persistent change but cannot prove which bytes a pathname-reopening parser
   read during a transient swap. Tool receipts now bind the intended digest;
   production still needs brokered read-only handles or immutable snapshots.
4. **Multi-image routing fails closed but is not implemented.** This is honest,
   not complete functionality.
5. **No provider-authentic offline receipt.** Local metadata can be internally
   consistent and still fabricated. Keep provider authenticity, local bundle
   integrity, evidence custody, and external signing/timestamping as four
   separate claims.
6. **No external signature/timestamp.** The local hash chain and detached
   checksum detect changes but an administrator can rewrite the entire bundle.
7. **The reviewed workspace is under OneDrive.** Sensitive outputs may sync.
   Production should default to a restricted local case directory outside
   consumer sync roots.
8. **The opening executor is not resource-aware.** It reserves tool-call caps
   atomically and runs a bounded batch, but does not yet coordinate CPU, RAM,
   sequential I/O, random I/O, or evidence affinity. Several heavy image scans
   can still contend and become slower than a planned schedule.
9. **Per-call parser startup remains overhead.** A restricted persistent worker
   pool could be faster, but it must not be introduced until the pool has
   enforceable network denial, filesystem allowlisting, private scratch, and
   positive process ownership.
10. **External browser opening remains a pathname boundary.** Verification
    rejects a self-consistent active viewer, but a same-user/administrator actor
    can still mutate the file after verification and before an external browser
    consumes it.

## Acceptance gates

Before calling vNext production-ready:

1. Run the full fake lifecycle through strict verification on Windows and Linux.
2. Complete one harmless synthetic live OpenAI smoke.
3. Complete one authorized authentic evidence run through judge, renderer,
   custody, manifest, verifier, and viewer.
4. Demonstrate a supporting span beyond byte 2,048 and a tamper rejection.
5. Prove judge upgrades and unknown/duplicate/omitted findings fail closed.
6. Prove hostile report/evidence text remains inert in the static viewer.
7. Add sandbox write-deny, network-deny, escape, child-process, CPU, and RSS tests.
8. Benchmark time-to-first-observation, total transmitted tokens, peak RSS,
   evidence-hash throughput, and opening concurrency by storage type.
9. Implement evidence-ID-selectable multi-image routing or retain the explicit
   split-case restriction.
10. Add an operator signature/timestamp option without mislabeling it as OpenAI
    provider authenticity.
