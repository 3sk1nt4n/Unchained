# Unchained architecture

Unchained is a trust-measurement harness for model-directed digital
forensics. The forensic case is the testbed; the product is the auditable,
deterministic boundary around an autonomous GPT-5.6 investigator.

## OpenAI-native vNext pipeline

<p align="center">
  <img src="assets/architecture.png"
       alt="Unchained pipeline — GPT-5.6 judgment stages in blue, deterministic code authority in amber, offline verification in green"
       width="1000">
</p>

```text
evidence file or folder
      |
      v
PROFILE + ROUTE [deterministic]
  content classification, evidence OS/shape, EID-keyed SHA-256, capability truth
      |
      v
OPENING BOOK [GPT-5.6]
  choose up to twelve distinct route-valid typed tools; the batch is all-or-none
      |
      v
PARALLEL TYPED EXECUTION [deterministic authority]
  reserve caps atomically, own paths, bind each receipt to evidence ID + digest
      |
      v
CASE LEDGER + LATEST OBSERVATION [deterministic packet]
      |
      v
PLAN -> ACT -> OBSERVE -> UPDATE [GPT-5.6]
  exactly one typed action per turn: an eligible forensic tool with a visible
  <=8,192-byte ledger update, or finish_investigation({"status":"DONE"})
      |
      v
FORCED INVESTIGATION SERIALIZATION [strict schema, no forensic tools]
      |
      v
EXACT SPAN RESOLUTION [deterministic]
  quote -> artifact SHA-256 + UTF-8 byte start/end + stable span ID
      |
      v
FRESH JUDGE [GPT-5.6]
  existing findings + their spans only; preserve or downgrade, never promote
      |
      v
STRUCTURED REPORT DRAFT [GPT-5.6]
  narrative fields plus exact existing finding/span references
      |
      v
DETERMINISTIC RENDERER [code authority]
  authoritative rows/verdicts/citations; model prose labeled nonauthoritative
      |
      v
CLOSE TOOLS/MOUNTS -> FINAL FULL SHA-256 CUSTODY CHECK [deterministic]
      |
      v
SEAL REPORT + STATIC VIEWER + CONTENT-ADDRESSED PROOF BUNDLE
      |
      v
OFFLINE LIFECYCLE, HASH, RECEIPT, AND SPAN VERIFICATION
```

The report model never owns the authoritative findings table. The final custody
pass occurs only after forensic work and mount access have stopped; bundle
artifacts are sealed afterward so the manifest records that result.

## Model invocation budget

Every provider request site is fixed in code; there is no unbounded loop:

| Phase | Provider requests | Call site |
|---|---|---|
| Opening book | exactly 1 | `agent.py` `_opening` |
| Adaptive investigation | 1 per turn; each turn must return exactly one typed action, and the final turn is `finish_investigation({"status":"DONE"})` | `agent.py` `_investigate` |
| Forced findings serialization | exactly 1 | `agent.py` `_finalize_investigation` |
| Fresh downgrade-only review | exactly 1 | `agent.py` `_judge` |
| Structured report draft | exactly 1 | `agent.py` `_report` |

A completed case therefore makes **4 + T** provider requests, where **T ≥ 1**
is the number of adaptive turns — minimum five requests total. T is bounded by
the hard caps (tool calls, total tokens, wall time, estimated cost): every
request is audited and charged before its response is used, and a cap firing
before dispatch ends the run as `PARTIAL` rather than exceeding the budget.
Transient provider failures may add at most two audited retries per dispatch; a
forensic action is never re-executed because a dispatch retried.

Reference point: the retained capped live run recorded exactly two provider
requests — the opening plus one adaptive turn whose tool reservation was
cap-blocked — matching this formula at the point the cap fired.

## Authority boundary

| Domain | Deterministic authority | GPT-5.6 authority | Explicit limit |
|---|---|---|---|
| Evidence | Complete inventory, public evidence IDs, pre/post hashes, capability route | Interpret the public profile | Hashes detect end-state changes; they do not defeat privileged pathname swaps |
| Tools | Registry, evidence paths, schemas, process ownership, caps, evidence/hash bindings | Choose route-valid tool and typed arguments | Registered third-party adapters are not yet network/filesystem sandboxed by the OS |
| State | Case ledger facts, completed calls, receipts, budgets, latest observation, closed typed-DONE action | Notes, hypotheses, course corrections, decision to finish | No prior provider transcript or encrypted reasoning replay |
| Findings | IDs, citations, exact quote resolution, status lattice | Propose findings and supporting quotes | Structural provenance is not a semantic truth validator |
| Judge | Fresh packet, known IDs/spans, downgrade-only enforcement | Preserve or downgrade with rationale and span quote | Same model family can share investigator failure modes |
| Report | Authoritative rows, transitions, citations, limitations, escaping | Narrative draft and commentary | Prose remains analyst-facing and requires human review |
| Proof | Audit chain, artifacts, manifest, viewer, custody, offline verification | No authority | Local bundle is unsigned and has no external timestamp |

The model cannot access a shell, choose an arbitrary path or binary, change the
evidence, write the audit, modify a cap, add a judge finding, promote a verdict,
or control authoritative report rows. An opening response containing an unknown,
duplicate, malformed, or thirteenth tool call rejects the whole opening batch; no
valid subset is executed. Adaptive termination is equally strict: empty text,
whitespace, punctuation, Markdown, and narrative prose have no terminal
authority. Only the closed non-forensic
`finish_investigation({"status":"DONE"})` action completes the loop. The
verifier can still read historical literal-DONE-v1 bundles, but the v2 runtime
does not emit them.

## Context and speed policy

Every Responses API call uses `store=false` and
`reasoning.context="current_turn"`. Adaptive turns are stateless provider calls:
the controller sends the public profile, a compact case ledger, receipt index,
remaining budget, and only the latest observation. The forced finalizer receives
the retained observations once. The judge receives exact spans rather than a
full transcript or the old 2,048-byte audit prefixes.

| Phase | Reasoning effort | Text verbosity | Max output tokens | Max calls exposed |
|---|---|---|---:|---:|
| Opening | low | low | 4,096 | 12 typed forensic calls |
| Adaptive turn | medium | medium | 4,096 (also the request-allocation minimum) | 1 typed action: forensic or finish |
| Finalization | medium | low | 12,288 (4,096 minimum allocation) | 1 strict schema call |
| Judge | high | low | 12,288 (4,096 minimum allocation) | 1 strict schema call |
| Report | low | medium | 8,192 | 1 strict schema call |

Case-wide tool, token, wall-time, and estimated-cost caps remain code-enforced.
If the remaining token or cost budget cannot preserve a phase's minimum output
allocation, code fires the corresponding cap before dispatch instead of
sending a predictably starved reasoning request. `max_output_tokens` includes
reasoning and visible output; the minimum is a request-allocation guard, not a
promise of a particular number of visible tokens.
Opening calls reserve their entire batch before concurrent execution. The
current scheduler is bounded but not yet resource-aware; running several heavy
full-image scans on one slow disk remains a production optimization target.
Requests use implicit GPT-5.6 prompt caching so matching stable prefixes may be
reused. Cache hits are optional: cap preflight prices an uncached request and
provider-reported cache reads/writes are audited and reconciled. This design
removes transcript replay and unnecessary tool volume, but no live latency
improvement is claimed until it is measured against the same evidence and caps.

## Data boundary

Original evidence bytes stay local. The provider receives the public evidence
profile, bounded model views of sanitized tool output, controller-owned ledger
state, and exact evidence-span text needed for findings and judgment. Tool output
and model-authored text are hostile data: neither may change instructions,
authority, caps, or verdict rules. Operators must still review case sensitivity,
provider retention, residency, and organization policy before a live run.

## Proof and verification boundary

Each accepted model response records the requested model, provider-returned
model identity, response ID, request correlation when available, phase policy,
validated usage, and a controller-estimated cost. The normalized assistant
message and normalized function calls are the audited response authority; raw
provider `output_items` are deliberately not retained as a second, potentially
contradictory proof representation. Tool receipts bind call IDs to controller-
owned evidence IDs and initial SHA-256 values. Findings bind to exact spans in
content-addressed output artifacts.

Strict offline verification requires retry-aware model transaction windows: a
request and phase options, zero to two bounded error/scheduled retry pairs, a
recovery receipt when retried, and exactly one accepted response. It revalidates
the strict catalog and asymmetric phase options, retry status/backoff policy,
response identity, and usage accounting. It independently recomputes each local
GPT-5.6 cost estimate from audited tokens and the code-owned configured price
table, reconciles the running totals, and binds the final budget snapshot to the
configured caps. These are reproducible local cap estimates, not an OpenAI
invoice or proof of provider billing.

Every phase input is reconstructed exactly from verified controller state.
Adaptive packets include their profile, visible ledger, receipt index, budget,
latest call IDs, and corresponding bounded observations; the finalizer, fresh
judge, and report inputs are similarly rebound. Accepted output usage cannot
exceed its paired request ceiling. Retry transport/status/timeout metadata must
be runtime-reachable, `COMPLETE` admits no `capped` or `rejected` receipt, and
lifecycle counts must match the verified findings, verdicts, and receipts.
Typed argument values use one shared bool-safe JSON Schema primitive-type rule.
The public OS route, evidence shape, canonical filesystem set, and route warnings
are independently rederived from the evidence-item inventory.

The verifier also binds model call IDs/names/arguments to tool receipts and
controller actions; visible ledger updates to adaptive responses; and forced
serializer, judge, and report arguments to their controller outputs. It
reconstructs the canonical public profile; binds its evidence IDs, sizes, hashes,
and count to initial custody and the matching final receipt; checks canonical
`profile.json`; and rebuilds `summary.json`. It deterministically rerenders the
report and static viewer and requires their exact bytes, rather than merely
trusting their manifest hashes. Finally, it validates every full artifact-write
descriptor, rereads cited artifacts against device/inode/digest, recomputes span
occurrence counts, requires exact judge quotes, enforces downgrade-only
decisions, and checks terminal consistency and matching custody maps.

`--require-live-gpt56` validates recorded GPT-5.6 metadata and rejects explicit
fake/replay markers. An offline verifier cannot independently prove that OpenAI
issued locally recorded fields. Provider authenticity requires an external
provider retrieval, signature, trusted timestamp, or independently controlled
attestation layer.

## Static proof viewer

`viewer.html` is generated deterministically before sealing and is a required
manifest artifact with role `proof-viewer`. It contains no JavaScript, external
resource, image, frame, or live link; dynamic values are escaped and a restrictive
CSP is embedded. `sentinel view <run>` verifies the bundle and viewer descriptor
before opening the already-generated file, and a run that claims `COMPLETE`
always receives full strict lifecycle verification even if the operator omits a
strict flag. Verification independently rerenders the viewer from verified
inputs and requires byte equality, then applies a positive passive HTML policy,
exact CSP requirements, and active-tag/attribute/CSS rejection. A
manifest-consistent replacement containing active content still fails. Viewing
never regenerates findings or contacts OpenAI. A same-user concurrent mutation
between verification and an external browser open remains outside the
prototype's guarantee.

## Current verified state

- 2026-07-20: the offline suite passes 430 tests plus Ruff check and format
  check. The source tree is 19 modules, 16,133 physical source lines
  (14,728 nonblank).
- An authentic `COMPLETE` GPT-5.6 Sol bundle **ships in this repository** at
  [`examples/public-run-complete`](../examples/public-run-complete): 3 findings,
  fresh-judge verdicts, and a sealed report on the public DC01 case; strict
  `--require-complete --require-live-gpt56` verifies `VALID` (27 artifacts,
  124 audit entries). A second authentic `gpt-5.6-luna` `PARTIAL` bundle ships
  at [`examples/public-run-partial`](../examples/public-run-partial) (14/14
  typed tools, honest hard-cap stop, `VALID`: 20 artifacts, 62 audit entries).
- Every pipeline stage in the diagram above has executed live end to end in the
  shipped `COMPLETE` bundle: opening book, adaptive turns, forced serialization,
  exact span resolution, fresh judge, report draft, deterministic renderer,
  final custody, sealing, and offline verification.
- No live same-evidence latency benchmark has been run; human visual and
  cross-browser viewer QA remains pending (parser-based inertness tests pass).
- OS-enforced parser sandboxing, stable evidence handles/immutable snapshots,
  multi-image scheduling, resource-aware heavy-tool scheduling, and signed or
  externally timestamped proof remain production work.

The implementation is concentrated in `unchained.evidence`, `unchained.tools`,
`unchained.agent`, `unchained.model`, `unchained.reporting`, `unchained.viewer`,
`unchained.viewer_policy`, `unchained.audit`, `unchained.caps`, `unchained.artifacts`, and
`unchained.verify`. The full repository comparison and release gates are in
[`OPENAI_VNEXT_REVIEW.md`](OPENAI_VNEXT_REVIEW.md).
