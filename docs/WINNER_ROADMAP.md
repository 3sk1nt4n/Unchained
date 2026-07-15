# Sentinel Unchained: Winner Roadmap

> **Role:** priority, sequencing, positioning, and go/no-go overlay
> **Status:** Local native Gate A leg green, provenance anchor red
> **Last deep review:** 2026-07-14 22:22 ET
> **Track:** Developer Tools
> **Internal submission deadline:** 2026-07-20
> **Hard deadline:** 2026-07-21 17:00 PT / 20:00 ET

This roadmap sits on top of
[HACKATHON_MASTER_PLAN.md](HACKATHON_MASTER_PLAN.md). It does not authorize a
re-scaffold. The master plan owns the detailed architecture, experiment, proof
bundle, judge experience, and submission contracts. This roadmap controls the
order in which the remaining work is attempted and the claims that may be made
about that work. [HACKATHON_HANDOVER.md](../HACKATHON_HANDOVER.md) remains the
live evidence-backed status ledger. [DECISIONS.md](../DECISIONS.md) remains the
durable architecture record.

If these files conflict, apply this precedence:

1. current OpenAI Build Week Official Rules and logged-in submission form;
2. this roadmap for priority, sequence, and gate order;
3. the master plan for detailed product and proof contracts;
4. the living handover for current execution state;
5. DECISIONS for accepted architecture history.

## 1. Winner verdict

Proceed with Sentinel Unchained. Do not pivot and do not re-scaffold.

### Current execution snapshot: 2026-07-14 22:22 ET

| Stage | State | Evidence and remaining boundary |
|---|---|---|
| C0 provenance | **PARTIAL** | Honest local history includes Gate A commit `6e696a0` and synchronized strategy/handover commit `207a039`; no public remote or independent server timestamp exists |
| C1 correctness | **GREEN** | The three reproduced defects and Windows prompt consistency are fixed and regression-tested |
| C2 proof and reliability | **GREEN OFFLINE** | Content-addressed outputs, provider-returned identity fields, response/request IDs, validated usage, bounded audited retries, manifest, summary, environment record, offline verifier, exact constraints, and `pylock` are implemented |
| Build evidence | **GREEN LOCALLY** | 14 source modules, 8,779 total text lines, 7,889 nonblank lines, 128 tests, Ruff and format, wheel plus sdist build, pip check, and diff check pass |
| Python environment | **GREEN** | Official CPython 3.11.9; clean primary and lockcheck virtual environments; `pip check` clean in both |
| Native readiness | **GREEN LOCALLY** | Official DC01 memory verified outside Git; Windows memory-only profile and symbols ready; 14 sealed tools; authoritative sanitized process batch and post-fix large netscan output retained; custody matched |
| C2 CLI exercise | **LIMITED** | An empty-input terminal `INVALID` bundle verifies. It is not `COMPLETE`, authentic, evidence-backed, tool-backed, or GPT-5.6-backed |
| Gate A | **LOCAL NATIVE LEG GREEN; OVERALL BLOCKED** | Gate A hardening is committed locally; public remote and independent server timestamp remain red |
| C4 freeze | **NOT STARTED** | No public protocol/rubric/scorer/run-selection freeze exists |
| C5 live proof | **NOT STARTED** | No `OPENAI_API_KEY`, funded runtime proof, authentic GPT-5.6 response, or primary run exists |
| C6 and C7 | **NOT STARTED** | No evaluation, viewer, video, submission tag, or Devpost submission exists |

These states are cumulative. The local native smoke makes the real-tool leg
green but does not make the project public or authentic-model proven. A
verifier PASS on an `INVALID` empty case remains separate and does not establish
live model, forensic, or custody claims.

Historical checkpoint discipline: commit `7b05d6a` remains the C2 baseline at
14 modules, 7,767 repository-counted nonblank source lines, and 123 passing
tests. The 8,779 total/7,889 nonblank line and 128-test figures describe the
later 22:22 ET Gate A commit state and must not be back-attributed
to that commit.

The strongest product is not another autonomous DFIR analyst. It is a
developer-facing trust-measurement harness for model-directed investigators,
demonstrated on a forensic benchmark.

Use this public one-line framing:

> Sentinel Unchained is a trust-measurement harness that quantifies
> receipt-grounded reliability for a GPT-5.6-directed investigator on a frozen
> forensic benchmark, then publishes a proof bundle every judge can inspect.

Use this memorable supporting line:

> Unchained reasoning. Chained evidence.

Do not say the experiment measures exactly how far autonomous investigators in
general can be believed. One public case cannot support that generalization.
Do not call the investigator unsupervised. It operates inside deterministic
authority, custody, protocol, audit, and budget boundaries.

### Why this framing is stronger

- The agent itself is not the only product. The experiment protocol, receipt
  store, verifier, adjudication, metrics, and viewer form a reusable developer
  tool for evaluating agents.
- DFIR is an unusually demanding testbed because unsupported claims can look
  convincing and evidence provenance matters.
- The entry has a concrete audience: security-agent developers, DFIR platform
  teams, SOC automation engineers, and agent-evaluation researchers.
- The external benchmark and proof bundle turn a model demo into an inspectable
  measurement product.
- The framing stays consistent with Sentinel Ensemble. Ensemble is the
  production-oriented trust architecture; Unchained is the controlled-autonomy
  measurement instrument.

## 2. The keystone artifact

The keystone is:

> One authentic, complete, post-freeze GPT-5.6 run against real DC01 evidence,
> producing a content-addressed proof bundle, a frozen-reference evaluation,
> and a no-rebuild viewer that a judge can inspect.

That artifact is necessary. It is not sufficient by itself. The current rules
score Technical Implementation, Design, Potential Impact, and Quality of the
Idea equally. The authentic bundle proves the implementation; the viewer and
quickstart prove the product experience; the audience and evaluation prove
impact; the trust-measurement design proves novelty.

No fake model, replay, screenshot, synthetic receipt, or recorded verifier can
substitute for the authentic run. Those artifacts can prove controller behavior
or accessibility only when labeled accurately.

## 3. Critical scientific correction

### Freeze before GPT-5.6 sees DC01

The original overlay placed authentic GPT-5.6 dress rehearsals on DC01 before
the rubric and protocol freeze. That order is rejected.

A fresh API request may be stateless, but the development process is not. Once
the developer sees which DC01 tools GPT-5.6 chose, which facts it missed, which
claims it overreached on, and what the reviewer caught, later prompt, catalog,
rubric, threshold, and metric changes can overfit to the benchmark.

Therefore:

> The complete protocol, code, prompts, eligible tool catalog, caps, retry
> policy, rubric, scoring rules, metric definitions, fault rules, and primary-run
> selection rule must be publicly frozen before the first GPT-5.6 investigation
> of DC01.

### Allowed before the freeze

- download, hash, extract, and inventory DC01;
- confirm read-only access and custody behavior;
- run deterministic native tools directly, without GPT-5.6;
- confirm Windows symbols, output parsing, timeouts, containment, retention,
  hashing, cleanup, and exact partition handling;
- inspect the supplied evidence to determine which reference facts are actually
  observable through the candidate tool surface that C4 will bind;
- rehearse GPT-5.6 function calling against fake typed tools, synthetic
  receipts, generic non-case data, or a different explicitly unscored case.

### Forbidden before the freeze

- a GPT-5.6 investigation of DC01;
- prompt tuning based on a DC01 model run;
- changing tool eligibility because GPT-5.6 missed a DC01 fact;
- building the rubric around facts the model happened to find;
- changing metric definitions or pass thresholds after seeing DC01 proposals;
- hiding or relabeling a semantically weak technically valid run.

If GPT-5.6 has already investigated DC01 before a public freeze, disclose it.
The later run can remain an authentic product demonstration, but it must not be
described as an untouched preregistered evaluation.

## 4. Correct critical path

```text
C0 HONEST PROVENANCE BASELINE [LOCAL GREEN, PUBLIC TIMESTAMP RED]
        |
        v
C1 THREE CORRECTNESS FIXES + WINDOWS PROMPT CONSISTENCY [GREEN]
        |
        v
C2 DURABLE PROOF CONTRACT + VERIFIER + LOCKED ENVIRONMENT [GREEN OFFLINE]
        |
        v
C3 CLEAN PYTHON 3.11 + DETERMINISTIC REAL-TOOL SMOKE [GREEN LOCALLY]
        |
        v
C0 PUBLIC REMOTE + SERVER TIMESTAMP [RED]
        |
        v
C4 PUBLIC PROTOCOL AND RUBRIC FREEZE [RED]
        |
        v
C5 FIRST GPT-5.6 DC01 RUN IS THE PRIMARY RESULT
        |
        v
C6 ADJUDICATION + HOSTED/OFFLINE VIEWER + VERIFY-RUN
        |
        v
C7 README + VIDEO + FEEDBACK + TAG + DEVPOST SUBMISSION
```

If time slips, cut breadth and presentation iterations. Never cut the authentic
run, retained receipts, public freeze, no-rebuild test path, or truthful
disclosure.

## 5. C0: immediate provenance baseline

The local provenance baseline is complete. Commits `5309e5c` and `7b05d6a`
retain the current C1/C2 work after the honest root history and
`BUILD_PROVENANCE.md`. The successful `/feedback` ID and screenshot are
preserved.

Remaining C0 work before the public experiment freeze:

1. Push the existing history to a public remote only after the secret and
   evidence scan passes.
2. Do not force-push, rewrite, squash away, or delete the public Build Week
   history.
3. Establish an independent server timestamp with CI or an equivalent public
   service.
4. Request Codex credits and retain the confirmation if not already complete.
5. Retain the completed DC01 memory acquisition manifest outside the repository;
   do not add the archive, image, or raw outputs to Git.
6. Commit the reviewed native routing, launcher, sanitization, transport, and
   bounded-model-view hardening before publication.
7. Open a Devpost draft early so every live form requirement is visible.
8. Identify the intended adjudicator before the scored run.

Local Git gives exact content binding but not an independently trustworthy
timestamp. Git author and committer dates can be edited, and local history can
be rewritten. Never call a local commit unimpeachable preregistration proof.

The strong future-tense claim is:

> The protocol and rubric will be committed publicly and independently
> server-timestamped before the primary run.

The past-tense claim is allowed only after a public remote commit and
server-side timestamp exist.

### C0 acceptance evidence

- [x] local repository initialized;
- [x] secret/evidence exclusion and scan pass at the retained local checkpoint;
- [x] honest baseline, C1/C2 commits, and provenance map;
- [ ] public remote URL and remote commit;
- [ ] independent server timestamp;
- [ ] retained credit request result;
- [x] DC01 memory archive and extracted-image size/hash evidence retained
      outside the repository;
- [ ] Devpost draft state recorded.

## 6. C1: focused correctness gate

**Current state: GREEN.** This gate was completed at the historical 80-test
checkpoint. C2 reached 123 tests at `7b05d6a`; the current Gate A-hardened
working tree reaches 128 without reopening the three defects.

Fix exactly the reproduced defects before adding proof features:

1. Markdown sanitizer bypass, including malformed link/image syntax,
   protocol-relative targets, dangerous schemes, reference definitions, and raw
   HTML. Test rendered inertness, not only source-text replacement.
2. Exact partition-offset propagation from successful filesystem detection
   through mounting and partition-aware `fsstat` or equivalent tool exposure.
3. Text-log versus memory classification so a small text log containing a
   kernel banner cannot become a memory image.
4. Runtime prompt and public scope consistency: the flagship prompt is one
   Windows route until another evidence OS is genuinely demonstrated.

The phrase "five reproduced defects" is retired. There are three reproduced
defects, plus regression testing and documentation/handover duties.

### C1 acceptance evidence

- [x] adversarial sanitizer fixtures are inert after rendering;
- [x] the exact detected partition offset is retained and used;
- [x] ordinary text logs remain logs;
- [x] focused tests pass;
- [x] current full suite passes with 128 tests;
- [x] Ruff passes;
- [x] Windows investigator prompt and flagship scope agree.

## 7. C2: proof and reliability contract

**Current state: GREEN OFFLINE.** Commits `5309e5c` and `7b05d6a` complete the
C2 implementation contract:

- full accepted tool outputs are stored content-addressably before a completion
  receipt is accepted;
- call ID, tool, typed arguments, status, duration, encoding, media type, byte
  count, completeness state, relative path, and SHA-256 are retained;
- the requested model alias and provider-returned `response.model` are distinct
  fields;
- response IDs, request IDs when available, status, validated usage, and every
  bounded attempt are audited;
- application-owned transient retries are capped at two, audited, wall/cost
  bounded, and cannot replay a forensic tool execution;
- `manifest.json`, `manifest.sha256`, `summary.json`, and `environment.json`
  are generated through an explicit non-self-referential artifact list;
- audit chain, terminal state, exact artifact bytes, tool receipts, citations,
  quote resolution, judge monotonicity, strict live-provider fields, and
  recorded custody rules are checked by a standard-library offline verifier;
- exact Windows CPython 3.11 constraints and a source/hash-bearing `pylock` are
  committed;
- official CPython 3.11.9 passes in clean primary and lockcheck environments,
  including `pip check`, 123 tests, Ruff, build, installed-package smoke,
  Volatility help, and catalog load.

The later public C4 freeze, not C2 alone, must bind the final protocol, rubric,
exact code, prompts, eligible catalog, caps, retries, scorer, and run-selection
rule, together with the exact 16,000,000-byte worker-response ceiling,
case-insensitive slash-variant public-path sanitization across success and
failure surfaces, and exact 65,536 UTF-8-byte investigator-model-view ceiling
with native-order prefix selection and an explicit completeness receipt. Those
experiment artifacts do not exist yet.

`MAX_COST_USD` is not a provider invoice guarantee. The safe claim is:

> The controller applies a conservative code-owned estimated inference budget
> before each request, bounds maximum output, audits every attempt, and stops
> when reported usage reaches the configured limit.

Use a dedicated funded OpenAI project, a low project-level budget or alert, and
the local cap. Provider billing remains authoritative when available.

### C2 acceptance evidence

- [x] synthetic verifier fixtures prove successful strict-live structure and
      fail on tampered blobs, audit records, paths, checksums, extra blobs, and
      missing live-provider proof;
- [x] every fixture-accepted output is present and hash-valid;
- [x] provider-returned-model fixtures verify requested-versus-returned capture;
- [x] retries are bounded, audited, and tool-idempotent;
- [x] the CLI finalizer emits and verifies a terminal `INVALID` empty-input
      bundle;
- [x] exact constraints and `pylock` exist;
- [x] 123 tests, Ruff, build, two clean-environment `pip check` runs, installed
      smoke, Volatility help, and catalog import pass.

The empty-input bundle is not a fake-model complete run. It contains no model
response, no tool call, no evidence profile, and no custody baseline. Calling
it authentic, evidence-backed, or `COMPLETE` would be false.

## 8. C3: clean environment and deterministic native proof

**Current state: GREEN LOCALLY.** The official CPython 3.11.9 environment,
exact dependency state, quality gates, Volatility console help, catalog load,
verified DC01 memory, Windows symbols, sealed tools, real native rows,
large-output boundary, path sanitization, and custody all pass. Commit
`6e696a0` binds the changes locally, but they are not publicly timestamped, so
the overall Gate A remains red on public-provenance anchoring.

Do not build a new cross-platform Volatility Python API adapter unless the
existing reviewed path is reproduced as incapable of running the Windows
flagship.

The current prior dependency already maps fixed tool names to fixed Volatility
plugins and invokes the cross-platform `vol` console entry point through trusted
code. Unchained already wraps that path in a reviewed allowlist, a private
worker, code-owned evidence paths, bounded responses, credential scrubbing,
timeouts, and containment. Replacing it now risks bypassing those guarantees
and expanding scope.

C3 sequence:

1. [x] Create clean primary and lockcheck official CPython 3.11.9
   environments.
2. [x] Install the pinned project and exact locked dependencies.
3. [x] Pass `pip check`, 128 tests, Ruff and format, wheel plus sdist build,
   installed-package smoke, and diff check.
4. [x] Reach Volatility help and load the exact real catalog with 25 direct
   plus 5 dynamic entries.
5. [x] Acquire and verify the official DC01 memory archive and extracted image
   outside Git.
6. [x] Resolve Windows OS and symbols through `windows.info`; profile the case
   as Windows, memory-only, ready, symbols ready, with 14 sealed tools.
7. [x] Retain an authoritative sanitized parallel process batch using
   `vol_pstree` and `vol_psscan` without GPT-5.6.
8. [x] Preserve the first netscan transport failure, increase the worker
   boundary from 2,000,000 to 16,000,000 bytes, and pass a sanitized post-fix
   `vol_netscan` smoke.
9. [x] Retain full accepted-output hashes while bounding the model view to
   65,536 UTF-8 bytes with an explicit incomplete-view receipt.
10. [x] Scrub runner-local evidence and mount paths from successful results,
    nested strings, and case-varied worker exceptions, with subprocess
    regressions.
11. [x] Recheck custody successfully.
12. [x] Cut paired disk from the Build Week primary and select the already
    proven Windows memory-only shape as the scored route.

Do not require `windows.pslist` if that function is not in the project-visible
catalog. Use the actual exposed typed functions. Do not claim symbol download
or resolution succeeded until the live output proves it.

If a new adapter becomes unavoidable, limit it to the demonstrated Windows
memory route and preserve fixed plugins, code-owned paths, process containment,
wall timeout, output limits, credential-free execution, complete receipts, and
adversarial boundary tests.

### C3 acceptance evidence

- [x] official CPython 3.11.9 version transcript;
- [x] clean primary and lockcheck installs with clean `pip check`;
- [x] 128 tests, Ruff and format, wheel plus sdist build, installed smoke, and
      diff check pass;
- [x] Volatility help and the exact 25-direct/5-dynamic real catalog load;
- [x] authoritative `gate-a-final-20260715T015251Z` process batch succeeds in
      5,968 ms with `evidence_id` `E001`, no private path, and custody match;
- [x] `vol_pstree` returns 40 records and a complete sanitized 15,277-byte
      output with SHA-256
      `e2e70d5164939f5a735c450ecc0f2c268e48f22ae4a4dab76a92fa67f04ecac6`;
- [x] `vol_psscan` returns 72 records and a complete sanitized 16,526-byte
      output with SHA-256
      `836951c95fdcc131064b52cfc229bb3753e389567fcb534174ac3f40d14a7fe4`;
- [x] post-fix `gate-a-netscan-20260715T014947Z` returns 19,685 records and a
      complete sanitized 3,961,843-byte accepted output with SHA-256
      `efced1af66f99ec2064d14f30a5f018d90e5c169027672be9e3c0110122cb421`;
- [x] the netscan investigator model view is exactly 65,536 UTF-8 bytes, contains a
      native-order 55,732-character prefix, declares
      `model_view_complete=false`, and retains the accepted-output byte count
      and SHA-256 in its delivery receipt;
- [x] successful and failed worker responses scrub runner-local evidence and
      mount paths across slash and case variants;
- [x] paired disk is explicitly cut from the Build Week primary and is not a
      Gate A or C4 blocker.

The archive is 561,424,278 bytes, matches official MD5
`64A4E2CB47138084A5C2878066B2D7B1`, and has SHA-256
`86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80`.
Extracted `citadeldc01.mem` is 2,147,483,648 bytes with SHA-256
`8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62`.
Both remain outside the repository.

The first parallel netscan attempt failed at the former 2,000,000-byte worker
boundary and is preserved as a diagnostic. It is not hidden, deleted, or
relabeled. Earlier process outputs from before path sanitization are diagnostics
only. The authoritative public-safe local process proof is the final sanitized
batch above.

The complete sanitized accepted output and the bounded investigator model view
have distinct meanings. The first is retained and hashed. The second is a
deterministic native-order prefix plus a completeness receipt. A quote resolving
in either artifact proves occurrence and traceability, not semantic entailment.

No GPT-5.6 DC01 investigation occurred. This was permitted deterministic
pre-freeze native smoke, not a scored, model-directed, API, or authentic primary
run. Continue using the existing fixed Volatility console adapter. Do not
schedule a broad Python API rewrite.

## 9. C4: public experiment freeze

**Current state: NOT STARTED.** No rubric, protocol, scorer, run-selection file,
public tag, remote commit, or server timestamp exists. Therefore no GPT-5.6
DC01 investigator call is permitted.

The public freeze is indivisible. It must bind the protocol, reference rubric,
exact code commit, prompts, eligible tool catalog, caps, retry policy, scorer,
the exact 16,000,000-byte worker-response ceiling, case-insensitive
slash-variant public-path sanitization across success and failure surfaces, the
exact 65,536 UTF-8-byte investigator-model-view ceiling with native-order prefix
selection and an explicit completeness receipt, and the first-valid-run
selection rule. It must also retain the dependency, evidence, model-alias,
native-version, and price-table context needed to reproduce the evaluation. A
rubric-only freeze is not enough.

Before any GPT-5.6 DC01 investigator call, create and freeze:

```text
experiment/protocol-v1.md
experiment/reference-rubric-v1.json
experiment/scoring-spec-v1.md
experiment/run-selection-v1.md
experiment/freeze-manifest-v1.json
```

### Frozen rubric fields

Each reference fact needs:

- stable fact ID;
- one atomic factual proposition;
- observability from the supplied evidence route;
- required artifact/tool family;
- status: stable, approximate, ambiguous, or unobservable;
- inclusion or exclusion rationale;
- normalized objective values where applicable;
- match mode;
- receipt-sufficiency guidance;
- source and independent-evidence-check notes;
- ambiguity and timestamp-basis notes.

Exclude PCAP-only, desktop-only, and disk-only facts because the frozen route is
memory-only. Also exclude
approximate without an accepted tolerance, ambiguous, unobservable, and broad
narrative facts from scored denominators.

### Two evaluation dimensions

Do not collapse truth and receipt support.

Dimension A, factual correctness:

```text
CORRECT | INCORRECT | AMBIGUOUS | OUT_OF_RUBRIC
```

Dimension B, receipt sufficiency:

```text
SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONTRADICTED
```

A fact may be true but unsupported by its cited receipt. A real citation may be
irrelevant. A claim may fall outside the answer rubric yet still have strong
receipt support. Preserve both dimensions.

Exact substring validation proves only that a quote occurs in a retained
receipt. It does not prove that the quote entails the claim. Deterministic code
may score normalized objective fields such as exact hashes, IP addresses, PIDs,
paths, event IDs, and timestamps with a frozen time basis. Relational,
interpretive, maliciousness, causality, absence, and cross-artifact claims need
blinded human or explicitly project-authored reference adjudication.

Preferred adjudication:

- a named human reviewer who did not build the result;
- randomized atomic findings;
- investigator and model-reviewer labels hidden during adjudication;
- factual correctness and receipt sufficiency labeled separately;
- raw labels, rationale, and dispute resolution retained;
- a second reviewer for disputes if time permits.

If no independent reviewer is available, use the honest phrase:

> Project-authored, preregistered reference-rubric evaluation.

Do not call a project-authored rubric independent external adjudication.

### Frozen metrics

Publish numerator and denominator for every rate. Report `not applicable` when
a denominator is zero.

| Metric | Frozen definition |
|---|---|
| Investigator proposal support rate | receipt-supported investigator proposals / all investigator proposals |
| Final-confirmed factual precision | factually `CORRECT` in-rubric final `CONFIRMED` findings / all factually adjudicable in-rubric final `CONFIRMED` findings |
| Final-confirmed receipt-support rate | receipt-`SUPPORTED` final `CONFIRMED` findings / all final `CONFIRMED` findings |
| Discovered-fact recall | scored reference facts correctly surfaced at any status / all scored observable facts |
| Confirmed-fact recall | scored reference facts correctly surfaced and finally `CONFIRMED` / all scored observable facts |
| Reviewer catch rate | receipt-unsupported proposals downgraded / all receipt-unsupported proposals |
| Reviewer escape rate | receipt-unsupported proposals still `CONFIRMED` / all receipt-unsupported proposals |
| Reviewer over-downgrade rate | receipt-supported proposals unjustifiably downgraded / all receipt-supported proposals |
| Supported-claim retention | receipt-supported proposals preserved / all receipt-supported proposals |
| Citation integrity rate | findings whose cited artifacts, hashes, and quoted spans verify / all findings with citations |
| Opening contribution | final supported facts first supported by opening receipts / all final supported facts |
| Tool efficiency | supported facts / successful tool calls |

Also freeze definitions for tool statuses, opening time, time to first supported
fact, total runtime, provider usage fields, local estimated cost, provider-billed
cost if available, artifact size, and recorded custody result.

### Primary-run selection and infrastructure faults

Freeze objective infrastructure-fault criteria before the run. Examples may
include provider unavailability before a usable response, corrupt evidence
read, failed required symbol resolution, a verifier defect that invalidates all
receipts, or a custody failure. A weak finding set, missed fact, unsupported
claim, reviewer escape, high cost within cap, or unattractive score is not an
infrastructure fault.

Use:

> The first post-freeze run that completes without a predeclared infrastructure
> fault is the primary result. A semantically disappointing valid run remains
> primary. Every later valid run is a disclosed replicate.

### Independent time anchor

1. Commit the freeze files and all bound code.
2. Push the commit to the public remote.
3. Create `experiment-freeze-v1`.
4. Run server-timestamped CI that checks out the commit, recomputes every
   digest, prints the freeze table, and retains the manifest artifact.
5. Optionally publish a release containing the freeze manifest and hashes.
6. Retain the public commit, tag, workflow, and release URLs.
7. Never force-push or delete a freeze version.

If a real predeclared infrastructure bug requires change, retain the invalid
run and `v1`, document the reason, create `v2`, push it, and establish a new
server timestamp before the next candidate. Never relabel semantic failure as
infrastructure failure.

### C4 acceptance evidence

- complete rubric and scoring spec;
- all metrics, denominators, thresholds, fault rules, and selection rules
  frozen;
- code, prompts, catalog, caps, retries, dependencies, price table, evidence
  hashes, rubric, scorer, exact 16,000,000-byte worker ceiling,
  success/failure public-path sanitization contract, and exact 65,536-byte UTF-8
  model-view ceiling with prefix/completeness rules bound by digest;
- public commit and freeze tag;
- server-timestamped CI/release verification;
- no prior GPT-5.6 DC01 investigation, or an explicit disclosure if this claim
  can no longer be made.

## 10. C5: authentic primary run

Only after C4 passes:

1. Use a funded OpenAI project key without logging it.
2. Request `gpt-5.6` through the Responses API.
3. Record the provider-returned model, response IDs, request IDs when available,
   statuses, usage, and every attempt.
4. Give the model only a neutral case ID, generic filenames where safe,
   evidence profile, and frozen eligible typed functions.
5. Let it select 1 to 6 opening functions, execute them concurrently, and
   continue with one function per later turn.
6. Retain concise decision summaries, not hidden chain-of-thought.
7. Preserve every exact accepted output and all failures.
8. Retain each investigator model view separately, mark whether it is complete,
   and bind every bounded view to the complete accepted-output byte count and
   SHA-256.
9. Enforce evidence pre/post hashing, cleanup, caps, and terminal status.
10. Do not discard the primary because its semantic result is weak.
11. Run deterministic verification before any public metric is computed.
12. Apply the frozen two-axis adjudication.
13. Run one or two identical replicates only after the primary, if stable and
    affordable, and publish every valid replicate.

The model alias in an environment variable proves only what was requested. The
provider-returned response object is required to show what was returned.

### C5 acceptance evidence

- authentic provider response and returned identity;
- real model-selected typed functions;
- real native execution on DC01;
- `COMPLETE` primary status;
- full retained proof bundle;
- complete accepted outputs plus explicit, hash-bound investigator model-view
  receipts;
- every deterministic bundle and citation check passes;
- recorded pre/post custody values agree;
- frozen two-axis evaluation complete;
- every valid run and invalid attempt disclosed according to the protocol.

## 11. C6: judge product

The no-rebuild path is a hard Developer Tools requirement, not visual polish.
A Dockerfile still requires a build. A screencast lets a judge watch but does
not let a judge test.

Ship three layers:

1. a hosted HTTPS static viewer, preferably on a stable static host;
2. a downloadable offline viewer or release bundle;
3. a no-network `verify-run` command or prebuilt verification artifact.

The viewer must render only the completed proof bundle. It must not call the
model, rerun forensic tools, or imply that replay is live execution.

Required banner:

```text
Inspection of a retained genuine GPT-5.6 run.
No model or forensic tool is executed by this viewer.
```

### Viewer security and portability

- inline or local CSS and JavaScript only;
- no external dependencies or telemetry;
- no module imports for the offline file;
- no `fetch` of sibling JSON under `file://`;
- bundle data embedded at generation time or selected with an explicit file
  picker;
- evidence-derived and model-derived text inserted inertly with `textContent`,
  never trusted as `innerHTML`;
- restrictive Content Security Policy where compatible;
- no active images, external links, embedded SVG, or executable Markdown from
  receipts;
- current Chrome and Edge test required; Firefox and Safari tested where
  available;
- large full outputs kept as inert downloadable text or JSON with escaped
  previews.

The user experience target is:

```text
20 seconds to understand the result
1 click from a claim to its receipt
under 5 minutes to verify the core value
```

The viewer should show the case card, opening selections, turn sequence,
findings, model-reviewer changes, two-axis adjudication, metric numerators and
denominators including factual precision and receipt-support as separate
measures, provider proof, audit state, output hashes, and recorded custody.

A resolving citation makes a claim inspectable. It does not prove the claim is
supported. The evaluator must expose irrelevant or insufficient receipts.

### Verifier wording

Without the original multi-gigabyte evidence, the judge can verify bundle
integrity and that the retained pre-hash and post-hash records agree. The judge
cannot independently rehash evidence bytes they do not possess.

Say:

> The verifier validates the retained custody record, audit chain, bundle
> integrity, output hashes, citation identity, quoted spans, and summary
> consistency.

Do not say the lightweight viewer independently re-verifies the original
evidence.

### C6 acceptance evidence

- hosted viewer works anonymously over HTTPS;
- offline viewer works from a clean download without a server;
- one click resolves each finding to the exact retained receipt context;
- replay banner is always visible;
- tampered bundles fail verification;
- browser security and portability checks are retained;
- verifier recording exists only as supplemental evidence.

## 12. C7: judge-facing submission

Finish:

- README first screen with the trust-measurement framing;
- explicit prior-work versus Build Week bright line;
- installation and supported-platform instructions;
- no-rebuild viewer and verifier path;
- optional funded-key live-run path;
- `JUDGE-QUICKSTART.md` with copy-paste instructions;
- truthful evidence-OS and host-OS matrices;
- Codex collaboration narrative and human decisions;
- GPT-5.6 integration details;
- DC01 credit and no-redistribution instructions;
- single-case and possible training-contamination limitations;
- Devpost description;
- authentic time-compressed video under 3:00, public on YouTube;
- audio that explicitly names both Codex and GPT-5.6;
- final `/feedback` from the true majority-core thread;
- exact submission tag;
- anonymous repository, viewer, video, release, and link QA;
- Devpost submission and retained confirmation.

Do not freeze truthful factual corrections to the result narrative after the
run. Freeze the protocol, metrics, and run-selection rule. Post-run result
documentation may be corrected with a visible history, but the valid primary
run may not be replaced or tuned away.

## 13. Hard gates

### Gate A: 2026-07-15 20:00 ET

- [x] C1 green;
- [x] C2 proof structure and offline verifier green;
- [x] official CPython 3.11.9 in clean primary and lockcheck environments;
- [x] exact constraints and `pylock`, clean `pip check`, 128 tests, Ruff and
      format, wheel plus sdist build, and diff check;
- [x] Volatility help and exact catalog load of 25 direct plus 5 dynamic
      entries;
- [x] honest local Git and provenance through Gate A commit `6e696a0`;
- [x] deterministic real-evidence `vol_pstree`, `vol_psscan`, and post-fix
      `vol_netscan` outputs persist outside Git, scrub runner-local paths from
      public success/failure surfaces, and verify with matching custody;
- [x] reviewed Gate A hardening is committed as `6e696a0` on top of `7b05d6a`
      without rewriting history;
- [ ] public remote and independent server timestamp exist.

**Current result: LOCAL NATIVE LEG GREEN, OVERALL BLOCKED.** The remaining Gate
A proof class is provenance anchoring: push the full unchanged history through
`6e696a0` and obtain an independent server timestamp.
The empty-input terminal `INVALID` bundle remains only a separate
finalization/verifier exercise.

The proven and selected scored shape is Windows memory-only. Paired disk is
future work and is not a Gate A or C4 blocker.

### Gate B: before the first GPT-5.6 DC01 call

- rubric and scoring spec complete;
- factual correctness and receipt sufficiency separated;
- all metrics and denominators frozen;
- infrastructure faults and run-selection rule frozen;
- code, prompts, catalog, dependencies, caps, retry policy, and price table
  frozen;
- exact 16,000,000-byte worker ceiling, success/failure public-path sanitization
  contract, and exact 65,536-byte UTF-8 model-view ceiling with
  prefix/completeness rules frozen with the same exact code and prompt set;
- protocol, rubric, scorer, and first-valid-run selection rule frozen with the
  same exact code and prompt set;
- public remote freeze commit and tag;
- server-timestamped digest verification.

No DC01 GPT-5.6 rehearsal may cross this gate.

### Gate C: 2026-07-17 18:00 ET

- authentic primary run is `COMPLETE`;
- verified proof bundle;
- recorded custody agreement;
- frozen evaluation complete;
- no concealed citation, adjudication, or run-selection failure.

If this gate fails, stop viewer polish and diagnose only the live route.

### Gate D: 2026-07-18 20:00 ET

- hosted viewer;
- offline viewer;
- `verify-run`;
- judge quickstart draft;
- metric and claim table frozen to verified artifacts.

A screencast alone does not pass.

### Gate E: 2026-07-20

- public video;
- public or properly shared repository;
- anonymous viewer/test path;
- correct feedback ID;
- submission tag;
- all links tested;
- Devpost confirmation retained.

## 14. Scope-cut ladder

Apply cuts in this order:

1. **Already applied:** cut the scored flagship scope to Windows memory-only,
   matching the demonstrated route; C4 must still freeze it publicly, and
   paired disk is future work.
2. Remove Linux, macOS, Plaso, Docker, Qwen reruns, and extra tool families.
3. Keep one authentic primary run and label it a single-run, single-case study.
4. Cut replicates before cutting primary proof.
5. Simplify viewer styling, but never remove the functioning hosted and offline
   no-rebuild paths.
6. Cut video retakes before cutting truthful authentication footage.
7. Cut prose length before cutting provenance, limitations, or metric
   denominators.

Never let a schedule slip justify fake output, hidden invalid runs, benchmark
tuning, unsupported claims, or replay presented as live execution.

## 15. Red-to-green scoreboard

```text
[GREEN] LOCAL GIT + PROVENANCE
        -> [YELLOW] COMMIT REVIEWED GATE A HARDENING
        -> [RED] PUBLIC REMOTE + SERVER TIMESTAMP
        -> [GREEN] C1 CORRECTNESS
        -> [GREEN OFFLINE] C2 PROOF CONTRACT
        -> [GREEN] CPYTHON 3.11.9 + LOCK + PIP CHECK
        -> [GREEN LOCALLY] REAL DETERMINISTIC EVIDENCE ROWS + CUSTODY
        -> [RED] PUBLIC EXPERIMENT FREEZE
        -> [RED] FIRST-VALID AUTHENTIC GPT-5.6 PRIMARY
        -> [RED] VERIFIED FROZEN EVALUATION BUNDLE
        -> [RED] HOSTED + OFFLINE VIEWER
        -> [RED] PUBLIC VIDEO
        -> [RED] DEVPOST CONFIRMATION
```

Turn these green in order. A later green state never excuses an earlier red
state.

## 16. Paste-ready Codex sequence

The saved C1 and C2 prompts in the master plan and the C3 prompt below are
completed historical build records. Do not paste them again. First commit and
publish the reviewed Gate A hardening without rewriting history. Then use the
C4 prompt as the next implementation task.

### Completed C3 prompt: real environment and deterministic native proof

```text
Continue the existing sentinel-unchained repository after C1 and C2. Do not add
product features and do not run GPT-5.6 against DC01 yet.

1. Reuse the proven official CPython 3.11.9 primary environment and committed
   exact constraints plus pylock. Reconfirm pip check and the installed smoke;
   do not regenerate dependency state without a reproduced defect.
2. Acquire, verify, and hash the real DC01 Windows memory image outside the
   repository. Record source archive and extracted evidence hashes without
   committing evidence bytes.
3. Load the existing reviewed real tool catalog and worker boundary. Confirm
   the exact 25-direct/5-dynamic inventory and use the existing fixed
   Volatility console path before considering any new adapter.
4. Against the real DC01 Windows memory image, directly execute at least one
   actually exposed native memory function such as vol_pstree, plus one second
   eligible memory function if time permits. Do not require windows.pslist when
   it is not in the model-visible catalog.
5. Prove real returned rows, symbol readiness, complete content-addressed output,
   timeout behavior, credential-free child environment, cleanup, and matching
   recorded custody.
6. Keep paired-disk mounting/probes outside the Build Week primary. The scored
   flagship is definitively Windows memory-only; treat E01 validation as future
   work after submission.
7. Add a regression fixture based on a sanitized captured real output shape.

Do not create a direct cross-platform Volatility Python API adapter unless the
existing reviewed path is first reproduced as incapable of the Windows-memory
flagship. If a minimal replacement becomes necessary, preserve the fixed plugin
allowlist, code-owned evidence path, private process containment, wall timeout,
output bound, credential scrubbing, complete receipts, and adversarial tests.

Update the handover with exact commands, environment, outputs, hashes, gate
state, risks, and the single next action. No fake model or replay may be called
an authentic run.
```

### C4 prompt: preregister and publicly freeze

```text
Prepare the experiment freeze before the first GPT-5.6 investigation of DC01.
Do not call the model on DC01 in this task.

1. Create experiment/protocol-v1.md, reference-rubric-v1.json,
   scoring-spec-v1.md, run-selection-v1.md, and freeze-manifest-v1.json.
2. Build the rubric from atomic facts observable through the frozen evidence
   route and tool catalog. Exclude PCAP-only, desktop-only, unavailable-route,
   ambiguous, approximate-without-tolerance, and unobservable facts.
3. Separate factual correctness labels from receipt-sufficiency labels. Exact
   quote matching is citation integrity only. Use deterministic normalized
   matching only for objective fields with frozen normalization. Require blinded
   human or honestly project-authored adjudication for semantic claims.
4. Freeze every metric, numerator, denominator, zero-denominator rule,
   infrastructure-fault definition, success threshold, and first-valid-run
   selection rule before seeing model proposals.
5. Bind the exact Git commit, prompts, catalog, dependency lock, Python/native
   versions, evidence hashes, rubric, scorer, caps, retry policy, model alias,
   price table, exact 16,000,000-byte worker ceiling, case-insensitive
   slash-variant public-path sanitization across success/failure surfaces, exact
   65,536-byte UTF-8 investigator-model-view ceiling with native-order prefix
   selection and explicit completeness receipt, and selection rule by digest.
6. Commit and push without rewriting history. Tag experiment-freeze-v1. Add a
   server-timestamped CI job that recomputes and publishes the digest table.
7. Save the public commit, tag, workflow, and release URLs in the handover.

Acceptance: every freeze artifact verifies, an independent server timestamp
exists, and no GPT-5.6 DC01 investigation occurred before the freeze. If that
last statement is no longer true, disclose the run and remove the untouched
preregistration claim.
```

### C5 prompt: authentic primary run and frozen evaluation

```text
Run the first authentic post-freeze GPT-5.6 investigation of DC01. The first
run without a predeclared infrastructure fault is the primary result, even if
its forensic performance is disappointing. No fake model or replay may satisfy
this task.

1. Use the OpenAI Responses API with requested alias gpt-5.6 and a funded
   project key. Never log the key.
2. Give the model only a neutral case ID, generic filenames where safe, the
   frozen profile, and the frozen eligible typed functions. Never provide the
   case name, source, answer key, or rubric.
3. Capture requested and provider-returned model identities, response/request
   IDs when available, status, usage, timestamps, and every request attempt.
4. Execute the 1-to-6 model-selected opening concurrently, then one typed
   function per later turn. Preserve concise decision summaries, not hidden
   chain-of-thought.
5. Retain all exact accepted outputs, failures, audit events, manifests,
   summaries, environment records, prompt/catalog/rubric digests, and pre/post
   evidence hashes. Retain each investigator model view separately with its
   completeness flag, exact byte count, and binding to the complete accepted
   output's byte count and SHA-256. Enforce cleanup and caps.
6. Run verify-run. Then apply the frozen two-axis evaluation and publish counts
   with every rate.
7. Never replace a valid primary for a nicer result. Later identical runs are
   disclosed replicates. A protocol change requires a retained new freeze
   version.

Acceptance: COMPLETE authentic primary, provider-returned identity, real typed
tool execution, complete hash-valid bundle, resolving citations, recorded
custody agreement, and frozen factual-correctness plus receipt-sufficiency
evaluation. Citation resolution is traceability, not proof of entailment.
```

### C6 prompt: no-rebuild judge product

```text
Build the judge product from the verified authentic bundle. It must not call a
model or forensic tool.

1. Generate a hosted HTTPS static viewer and a downloadable offline viewer or
   release bundle. The offline viewer must not fetch sibling files under
   file://; embed sanitized data or use an explicit file picker.
2. Render the case card, opening, turn sequence, findings, model-review changes,
   factual and receipt-sufficiency labels, metric numerators/denominators,
   provider proof, hashes, audit state, and retained custody record.
3. Make every finding one click from its exact receipt context and artifact
   hash. Explain that a resolving citation is inspectable, not automatically
   sufficient.
4. Insert all evidence/model text inertly. No trusted innerHTML, active images,
   executable Markdown, external dependencies, or telemetry. Add a restrictive
   CSP where compatible.
5. Keep the replay banner permanently visible. Test anonymous hosted access and
   the offline download on clean current browsers.
6. Ship verify-run and a retained PASS transcript. A screencast may supplement
   the path but may not replace it.

Acceptance: 20 seconds to understand, one click to the receipt, under five
minutes to verify the core value, anonymous hosted access, clean offline access,
and tamper tests that fail closed.
```

### C7 prompt: final docs, video, and submission freeze

```text
Prepare the final judge-facing submission from verified artifacts only.

1. Rewrite the README first screen around the trust-measurement harness. Add an
   unambiguous bright line: prior MIT typed forensic substrate versus Build Week
   agent loop, reviewer, proof contract, frozen evaluation, verifier, and
   viewer. Every number must link to a bundle artifact.
2. Create JUDGE-QUICKSTART.md with three copy-paste paths: hosted viewer,
   offline viewer plus verify-run, and optional funded-key pipeline run.
3. Publish truthful host-platform and evidence-OS matrices with TESTED,
   EXPERIMENTAL, LIMITED, or UNDEMONSTRATED labels.
4. Draft the Devpost description and a 2:45-to-2:50 narration. Show authentic
   time-compressed footage and the viewer. Audio must name Codex and GPT-5.6 and
   state the single-case scope and possible public-case training contamination.
5. Run a final claims-to-artifacts audit, tests, Ruff, build, verifier, secret
   scan, license check, anonymous link check, and video-duration/audio check.
6. Run /feedback in the true majority-core Codex thread, tag the exact
   submission commit, submit by July 20, and save confirmation.

Do not invent numbers, hide valid runs, claim an independent evaluator when the
evaluation is project-authored, call local Git immutable, call a local estimate
an invoice guarantee, or present replay as authentic execution.
```

## 17. Make-no-mistake rails

1. Authenticity starts with provider-returned metadata, not an environment
   variable or screenshot.
2. DC01 model inference starts only after the public experiment freeze.
3. Public Git plus server-side timestamp strengthens preregistration; it is not
   mathematical immutability.
4. Exact quote occurrence proves citation integrity, not semantic support.
5. Truth and receipt sufficiency are separate axes.
6. A same-model fresh reviewer is a downgrade-only check, not ground truth.
7. Resolving citations make claims inspectable, not automatically correct.
8. The local cost cap is conservative estimated control, not an invoice
   guarantee.
9. The existing reviewed Volatility path is preferred over a rushed new
   adapter.
10. A hosted viewer plus offline bundle is the no-rebuild path. A recording is
    supplemental evidence only.
11. The lightweight verifier validates retained custody records and bundle
    integrity, not absent original evidence bytes.
12. Every valid post-freeze run stays disclosed.
13. A protocol change creates a retained new freeze version.
14. No evidence archive, recovered malware, credential, secret, or answer key
    enters the repository, viewer, model context, or public bundle.
15. Every public metric includes its numerator, denominator, source artifact,
    and zero-denominator behavior.

## 18. Single next action

Commit the reviewed Windows direct-tool routing, absolute-venv launcher,
public-path sanitization, 16,000,000-byte worker transport, and 65,536-byte
bounded model-view hardening. Preserve the failed pre-fix netscan diagnostic.
Push the full history without rewriting it and establish an independent server
timestamp. This closes the remaining Gate A provenance leg.

Then publicly freeze the protocol, rubric, exact code, prompts, eligible
catalog, caps, retries, scorer, exact 16,000,000-byte worker ceiling,
case-insensitive slash-variant public-path sanitization across success/failure
surfaces, exact 65,536-byte UTF-8 model-view ceiling with native-order prefix
selection and explicit completeness receipt, and first-valid-run selection
rule. Do not expose DC01 to GPT-5.6 before that freeze. The first post-freeze run
that completes without a predeclared infrastructure fault is the primary, even
when its semantic result is disappointing.
