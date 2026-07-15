# Sentinel Unchained - OpenAI Build Week Living Handover

This file is the execution-status source of truth for the OpenAI Build Week
submission. It records verified rules, current proof state, delivery gates,
risks, and the next-session startup procedure.

Priority, sequence, positioning, preregistration, and go/no-go logic are in
[docs/WINNER_ROADMAP.md](docs/WINNER_ROADMAP.md). The detailed product strategy,
experiment, proof contract, prompts, judge path, and submission doctrine are in
[docs/HACKATHON_MASTER_PLAN.md](docs/HACKATHON_MASTER_PLAN.md). Architecture
details remain in [README.md](README.md), and durable technical decisions remain
in [DECISIONS.md](DECISIONS.md). Those files describe what the system is intended
to do. This handover records what is implemented, what has been verified, what
has been demonstrated to a judge, and what is still missing.

> **Update requirement:** every material implementation, verification, artifact,
> scope, schedule, or submission-status change must update this file in the same
> work session. Never mark an item complete merely because corresponding code
> exists.

## Document control

| Field | Current value |
|---|---|
| Last live-rule verification | 2026-07-14 22:04 ET, direct current 2026 Official Rules plus official GPT-5.6, pricing, and Responses API references |
| Last repository verification | 2026-07-14 22:24 ET |
| Current event day | Submission Day 2, not Day 8 |
| Hard deadline | 2026-07-21 17:00 PT / 20:00 ET |
| Time remaining at 2026-07-14 22:22 ET | Approximately 165.6 hours |
| Internal submission deadline | 2026-07-20; July 21 is emergency buffer only |
| Selected track | Developer Tools |
| Current decision | **CONDITIONAL GO with frozen scope; registry alternative parked** |
| Flagship-run readiness | **NOT READY: local Gate A is green; public remote, freeze, funded credentials, and authentic run are red** |
| Submission readiness | **NOT READY** |
| Current `/feedback` Session ID | `019f61e5-5755-7a02-adb4-618d32baab27` |

The local screenshot supporting that ID is outside this repository in the
workspace parent under the filename
`WhatsApp Image 2026-07-14 at 6.30.49 PM.jpeg`.
It is 124,837 bytes with SHA-256
`F013EFDD5DD5C7D8698B378DA88760E8CCB34557BBE85E18979F7C196423B844`, and it
visibly shows the valid ID above. This is local provenance only. It is not
committed, hosted, or judge-accessible. After final core work, the final
successful `/feedback` must be run from the true majority-core Codex thread;
do not assume this earlier ID remains the final submission ID.

### Evidence-state vocabulary

Use these terms literally:

- **IMPLEMENTED** - code exists for the behavior.
- **VERIFIED** - a current command, test, inspection, or reproduction proves the
  claimed behavior in a named environment.
- **DEMONSTRATED** - a retained, judge-accessible artifact proves the real
  workflow or product experience.
- **BLOCKED** - a named prerequisite prevents meaningful progress.
- **NOT STARTED** - no qualifying implementation or artifact exists.
- **DECISION** - a human-owned product, scope, or risk decision.

A unit test can verify a controller behavior. It does not demonstrate a genuine
GPT-5.6 forensic investigation. A replay can demonstrate judge accessibility. It
does not prove that GPT-5.6 produced the original run.

## Executive decision

Proceed conditionally with Sentinel Unchained for Build Week. Do not pivot to a
new dynamic model-registry project now. Unchained is no longer a from-scratch
concept: it is a substantial controller prototype with 14 source modules,
7,889 nonblank physical source lines, 128 passing tests, clean lint and
formatting, a buildable wheel, a verified CPython 3.11.9 environment, exact
dependency records, and a verified Codex feedback thread. The winner story and
experiment are now
governed by the Winner Roadmap and corrected master plan: a trust-measurement
harness for model-directed investigators, not a generic autonomous analyst and
not a clean causal Qwen-versus-GPT-5.6 ablation.

This is nevertheless a hard-scope sprint. The project is not submission-ready
until it has one authentic post-freeze GPT-5.6 investigation, a complete
verified proof bundle from real evidence, frozen-reference evaluation with its
authorship disclosed,
and a frictionless judge path. The self-verifying `INVALID` empty-case bundle
proves failure-path packaging only. It is not an authentic or complete run. No
new breadth work outranks the remaining proof gates.

The deterministic Windows memory path is now proven locally against DC01: the
profile is Windows memory-only and ready, symbols resolve, the sealed registry
exposes 14 Windows tools, authoritative batch
`gate-a-final-20260715T015251Z` returns pstree and psscan rows with sanitized
receipts, repaired run `gate-a-netscan-20260715T014947Z` retains 19,685 netscan
records through bounded delivery, and custody matches. These local artifacts
are outside the repository and are not a scored or authentic model run.

The registry alternative remains parked. A failed live-run gate triggers an
explicit go/no-go review; it does not automatically authorize a late pivot. A
new product started after that gate would carry even greater delivery risk.

## Triple-verification policy

Time-sensitive and submission-critical claims must be checked in three ways
where feasible:

1. **Controlling source:** the current direct Official Rules or the relevant
   source file/API contract.
2. **Independent corroboration:** current FAQ/overview, a second code path, or an
   independent inspection.
3. **Operational evidence:** a raw uncached response, current command/test, or
   retained artifact.

For code behavior, prefer the sequence:

```text
source inspection -> focused reproduction/test -> retained artifact or integration run
```

For event rules, prefer:

```text
direct live Official Rules -> current FAQ/overview -> uncached/raw page check
```

Search snippets, old conversations, generated package metadata, and AI summaries
are leads, not controlling evidence.

## Verified 2026 Build Week rules

### Controlling sources

- [OpenAI Build Week landing page](https://openai.com/build-week/)
- [Live Devpost overview](https://openai.devpost.com/)
- [Live Devpost Official Rules](https://openai.devpost.com/rules)
- [Live Devpost FAQ](https://openai.devpost.com/details/faqs)

The direct rules page was fetched without relying on a search cache on July 14,
2026. Its response identified OpenAI Build Week, Codex, GPT-5.6, the four current
tracks, and the July 2026 dates. It contained no `gpt-oss` event text.

### Stale-page warning

Search indexes can still return an ended 2025 OpenAI Open Model Hackathon
snapshot for the same Devpost domain. That unrelated event used gpt-oss and the
categories Best Overall, Robotics, Weirdest Hardware, Local Agent, Fine-Tune,
Wildcard, and For Humanity. Those are not the 2026 Build Week tracks.

When rechecking rules, open the current page directly. Do not accept a search
snippet whose dates are August–September 2025 or whose model requirement is
gpt-oss.

### Dates

The current Official Rules specify:

- Registration: July 9, 2026 at 10:00 PT through July 21 at 17:00 PT.
- Submission: July 13, 2026 at 09:00 PT through July 21 at 17:00 PT.
- Hard deadline: July 21, 2026 at 17:00 PT / 20:00 ET.
- Judging under the Official Rules: July 22 at 10:00 PT through August 5 at
  17:00 PT.
- Winners: on or around August 12, 2026.

The OpenAI landing page reportedly shows judging through August 7, while the
contract-style rules show August 5. Treat the Official Rules as controlling and
keep the repository, video, viewer, test path, and artifacts available through
at least August 12, covering both dates and the winner announcement.

### Tracks

The four current tracks are:

1. Apps for Your Life.
2. Work and Productivity.
3. **Developer Tools.**
4. Education.

Developer Tools explicitly includes testing, DevOps, agentic workflows, and
security. Sentinel Unchained fits that track. The live rules list a $15,000
first-place and $10,000 second-place prize for Developer Tools.

Do not select a track from an old gpt-oss page. Verify the selected track again
in the live submission form before final submission.

### New and existing projects

The current rule requires a pre-existing project to be meaningfully extended
with Codex and/or GPT-5.6 after the submission period began. It also states:

> “Pre-existing Projects will be evaluated only on work added during the
> Submission Period.”

Entrants must clearly distinguish prior and new work with timestamped Codex
logs, dated commit history, or equivalent evidence.

Although the extension sentence uses “and/or,” the overall project requirements
expect meaningful use of both Codex and GPT-5.6. The submission must demonstrate
both.

### Required submission materials

- A working project built with Codex and GPT-5.6.
- One selected track for this project.
- A product description explaining features and operation.
- A public YouTube demo that is less than three minutes.
- Clear audio explaining what was built and how Codex and GPT-5.6 were used.
- A repository URL for judging and testing.
- A public repository with relevant licensing, or a private repository shared
  with both `testing@devpost.com` and `build-week-event@openai.com`.
- README setup, run/test guidance, supported platforms, and sample data or a
  sample-data path where required.
- README disclosure of Codex collaboration, acceleration, and human-owned
  product/engineering/design decisions.
- A `/feedback` Codex Session ID from the primary thread where most core
  functionality was built.
- For Plugins and Developer Tools: installation instructions, supported
  platforms, and a judge path that does not require rebuilding from scratch.

The project/test path must remain free and unrestricted through judging. Judges
are not required to install or test it; they may judge only from the description,
images, and video. Therefore the video and instant viewer are load-bearing, not
optional polish.

### Video interpretation

The Official Rules say **less than three minutes**. The FAQ says three minutes or
under. Use the stricter controlling language and target 2:40–2:50, never exactly
3:00. Include voiceover, English or an English translation, and a visible working
product. Explain both the Codex build workflow and GPT-5.6's runtime role.

### Judging

Stage One is pass/fail for viability, theme fit, and reasonable use of the
required APIs/SDKs.

Stage Two has four equally weighted criteria:

1. Technological Implementation.
2. Design.
3. Potential Impact.
4. Quality of the Idea.

Treat each as effectively one quarter of the score. Additional backend depth
cannot compensate for a missing coherent judge experience or missing impact
proof.

### Multiple submissions

The rules allow one entrant to submit multiple projects only when each is unique
and substantially different, as determined by OpenAI and Devpost. Each project
enters one track and can win at most one prize.

The current strategy remains one polished Build Week Sentinel entry. That is a
delivery decision, not a false claim that multiple submissions are prohibited.

## Product positioning

### Winning thesis

> **Unchained reasoning. Chained evidence.**

> GPT-5.6 drives the investigation; deterministic code chains every action to
> typed authority, evidence custody, protocol, hard budgets, and a verifiable
> receipt. A fresh review can preserve or downgrade findings, never add or
> upgrade them, and the human analyst retains final authority.

### Relationship to Sentinel Ensemble

Sentinel Ensemble is the production-oriented deterministic trust architecture.
Sentinel Unchained is a controlled GPT-5.6 autonomy experiment built on a pinned,
pre-existing forensic foundation. It asks how much adaptive semantic agency can
be admitted safely when deterministic code retains custody, typed authority,
protocol enforcement, audit receipts, and resource limits.

Unchained is a complementary controlled-autonomy case study, not a repudiation
of Ensemble's “code gets the final word” philosophy. It omits the deterministic
**semantic** validator and measures what happens in a reproducible model-directed
case. Because the model, prompts, orchestration, tool policy, and review system
also differ from Qwen, this is not presented as a one-variable causal ablation.
It does not remove deterministic operational controls, and neither the
investigator nor its fresh reviewer is treated as ground truth. Published
support metrics come from a frozen evidence-observable rubric whose
adjudication authorship must be disclosed.

### Prior-work boundary

Pinned prior-project commit:

```text
9f309c6134e857f7b86f3e6b9c6709ce954944a5
```

Pre-existing foundation reused:

- Evidence mounting support.
- Typed forensic tool functions.
- Low-level parsing/tool adapters permitted by the pinned dependency boundary.

Not reused as Unchained proof or orchestration:

- Qwen pipeline or coordinator.
- Deterministic semantic validator.
- Prior prompts.
- Prior report layer.
- Generic command-execution interface.
- Prior demo video, findings, runtime, cost, or accuracy numbers.

Build Week additions to prove with dated Codex logs and commits:

- GPT-5.6 investigator prompt and adaptive loop.
- Responses API state behavior.
- Opening-book concurrency and one-tool investigation protocol.
- Literal `DONE` plus forced structured serialization.
- Fresh, downgrade-only judge.
- Audit chain and receipt handling.
- Tool/token/time/cost caps.
- Report safety and terminal-status behavior.
- CLI lifecycle/containment additions.
- The genuine run, judge viewer/replay, README story, and demo video.

The pre-existing engine is credibility, not something to hide. The submission
must still make the newly evaluated Build Week layer unmistakable.

## Nine non-negotiables carried into Prompt 3

Prompt 3 and every later major prompt must preserve these constraints.

### 1. Use only the current 2026 event rules

Developer Tools is the selected track. Never substitute the 2025 gpt-oss
categories or their older pre-existing-project language.

### 2. Respect the real clock and freeze scope

The event is on Submission Day 2 with approximately 169 hours remaining at this
baseline. The urgency is real even though “Day 8 of 9” was false. Do not add
macOS breadth, Plaso, a large web application, or unrelated product features.

### 3. Separate prior work from judged Build Week work

Create honest dated Git history now. Never backdate. Preserve the pinned prior
commit and document exact reused/new boundaries. Judges evaluate submission-
period additions only.

### 4. Preserve the research-ablation framing

Unchained explores controlled model agency; it does not claim Ensemble's
deterministic-trust philosophy was wrong. Use “fully agentic” only when qualified
as semantic reasoning and typed-tool selection inside deterministic authority,
custody, protocol, and budget controls.

### 5. Require one authentic GPT-5.6 run

No fake-model test, replay, screenshot, or architecture diagram substitutes for
one genuine GPT-5.6 investigation. The flagship must retain `report.md`,
`profile.json`, `audit.jsonl`, complete tool outputs, a manifest, metrics, and a
final custody result.

Do not let GPT-5.6 investigate the scored DC01 case before the code, prompts,
catalog, caps, retries, rubric, scoring rules, fault criteria, and run-selection
rule are publicly frozen and independently server-timestamped. Pre-freeze model
rehearsals use fake tools, synthetic receipts, generic data, or another
explicitly unscored case. Deterministic DC01 native-tool smoke is allowed.

### 6. Keep proof and replay visibly distinct

The authentic run proves GPT-5.6 participation. The no-key replay/static viewer
provides accessibility. Label replay artifacts as replay/verification, never as
a fresh model run.

### 7. Pass the correctness and environment gate before filming

Fix the three reproduced defects, preserve full tool outputs, pin dependencies,
and demonstrate a clean Python 3.11 supported environment with the required
native route. Do not film or publish measured claims from the incomplete active
environment.

### 8. Optimize for the judge's experience

The judge must understand the promise in 20 seconds, experience the product in
under five minutes without rebuilding a forensic lab, and trace one finding to
its receipt and hash. Design and Impact are equal-weight criteria.

### 9. Maintain submission and feedback discipline

Use one polished Build Week entry, a 2:40–2:50 narrated public YouTube video,
incognito link checks, saved submission confirmation, and the successful
`/feedback` ID from the majority-core thread. Change the current ID only when a
later successful upload from the true primary thread returns a different ID.

## Codebase map

The runtime flow is:

```text
CLI / budget
    -> evidence inventory, classification, routing, and pre-run hashes
    -> typed tool registry and bounded private workers
    -> GPT-5.6 opening selection and adaptive investigator loop
    -> literal DONE and structured investigation serialization
    -> fresh downgrade-only judge
    -> report generation and defanging
    -> cleanup and deterministic post-run custody verification
    -> report.md + audit.jsonl + profile.json
```

| Module | Responsibility |
|---|---|
| `src/unchained/cli.py` | Configuration, run directory, lifecycle, statuses, cleanup, final custody |
| `src/unchained/evidence.py` | Inventory, content classification, OS/shape routing, hashes, mounts, readiness probes |
| `src/unchained/tools.py` | Typed tool schemas, allowlisting, caps, execution, receipts |
| `src/unchained/_tool_worker.py` | Fixed private-worker dispatch for approved forensic functions |
| `src/unchained/model.py` | OpenAI Responses adapter, state replay, wire options, usage validation |
| `src/unchained/agent.py` | Opening book, investigator loop, serialization, judge, report safety |
| `src/unchained/audit.py` | Single-writer hash-chained event log and output receipts |
| `src/unchained/artifacts.py` | Atomic summary, environment record, allowlisted manifest, and detached manifest digest |
| `src/unchained/caps.py` | Atomic tool/token/time/cost enforcement and cost estimates |
| `src/unchained/models.py` | Typed domain records and schemas |
| `src/unchained/prompts.py` | Project-owned authoritative investigator prompt |
| `src/unchained/verify.py` | Standard-library, offline proof-bundle and citation verifier |
| `src/unchained/__main__.py` | Module CLI entry point |

## Current implementation and proof ledger

Verified on July 14, 2026 unless otherwise stated.

| Capability or artifact | State | Evidence | Next proof/action |
|---|---|---|---|
| Python package | IMPLEMENTED + VERIFIED | CPython 3.11.9 primary and independent lockcheck environments; `pip check` clean; wheel build passes | Retain transcript with final submission commit |
| CLI/controller | IMPLEMENTED + VERIFIED offline | 128 tests pass | Genuine run artifact |
| Opening parallel tools | IMPLEMENTED + VERIFIED offline | Controller tests | Authentic audit trace |
| Literal `DONE` protocol | IMPLEMENTED + VERIFIED offline | Controller tests | Authentic trace |
| Typed/no-shell authority | IMPLEMENTED + VERIFIED offline | Schema and worker tests | Native forensic demo |
| Evidence inventory/custody | IMPLEMENTED + VERIFIED locally on real evidence | DC01 profile is Windows memory-only, ready, symbols ready; final custody matches | Publish only the non-evidence proof receipts after freeze |
| Hard caps | IMPLEMENTED + VERIFIED offline | Cap tests | Recorded `PARTIAL` demo |
| Downgrade-only judge | IMPLEMENTED + VERIFIED offline | Simulated `CONFIRMED -> UNSUPPORTED` test; exact bounded-excerpt quote checks | Authentic model example plus external semantic scoring |
| Hash-chained audit | IMPLEMENTED + VERIFIED offline | Audit tests | Genuine retained audit |
| Provider-returned model identity | IMPLEMENTED + VERIFIED offline | Requested alias and provider-returned model, response/request IDs, status, and usage propagate through audit and bundle tests | Authentic provider receipts |
| Bounded audited retries | IMPLEMENTED + VERIFIED offline | Retryable transport/status failures are bounded and audited; protocol/model/schema failures are not retried | Authentic response trace if a retry occurs |
| Report safety | IMPLEMENTED + VERIFIED offline | Fail-closed link-free safe subset; six focused rendered CommonMark tests; adversarial bypass inert | Authentic report artifact and viewer-safe rendering |
| Windows memory route | VERIFIED LOCALLY, NOT JUDGE-DEMONSTRATED | Real DC01 `windows.info` resolves; profile and symbols ready; sealed registry exposes 14 Windows tools; native rows and custody pass; code bound by `6e696a0` | Publish unchanged history, then authentic run only after C4 freeze |
| Windows fixed-console discovery and direct memory catalog | IMPLEMENTED + VERIFIED locally, COMMITTED | Active-interpreter-adjacent launcher and sanitized child `PATH`; Windows direct tools no longer depend on Linux/macOS dynamic mapping; 128 tests plus real smoke pass; commit `6e696a0` | Publish unchanged history and retain server timestamp |
| Linux/macOS routes | PARTIAL/EXPERIMENTAL | No end-to-end proof | Out of flagship scope |
| Full accepted tool-output retention | IMPLEMENTED + VERIFIED offline | Exact UTF-8 bytes are content-addressed before `tool.completed`; hashes, excerpts, and metadata are verified | Genuine retained native-tool outputs |
| Large native-output transport | IMPLEMENTED + VERIFIED locally, COMMITTED | Hard private-worker response limit increased from 2,000,000 to 16,000,000 bytes after an honestly retained `vol_netscan` overflow; successful 3,961,843-byte rerun; commit `6e696a0` | Preserve the pre-fix diagnostic and bind exact values in C4 |
| Bounded explicit model tool view | IMPLEMENTED + VERIFIED locally, COMMITTED | Full accepted output remains retained; provider input is capped at 65,536 UTF-8 bytes with accepted-output hash/size, prefix-character count, selection rule, and `model_view_complete=false`; commit `6e696a0` | Authenticate behavior only after the public freeze |
| Private evidence-path sanitization | IMPLEMENTED + VERIFIED locally, COMMITTED | Worker recursively strips runner-local evidence/mount paths from success values and exception strings, matches Windows path variants case-insensitively, and substitutes the sealed evidence ID; native receipts and the subprocess error-path regression contain no private path; commit `6e696a0` | Recheck the authentic bundle after the public freeze |
| Self-verifying proof bundle | IMPLEMENTED + VERIFIED for invalid path | Run `20260715T012818Z-0c60c234` verifies 4 artifacts and 8 audit entries, terminal `INVALID`, exit 2 | Authentic `COMPLETE` bundle from real evidence |
| Exact quote integrity | IMPLEMENTED + VERIFIED offline | Every reviewer quote must resolve exactly inside its cited bounded receipt excerpt | Keep separate from semantic correctness under the frozen rubric |
| Public authentic run bundle | NOT STARTED | The retained empty-case bundle is invalid, unauthenticated, and incomplete | First valid post-freeze GPT-5.6 run |
| Corrected strategic master plan | VERIFIED + SAVED | `docs/HACKATHON_MASTER_PLAN.md`; rules/code/strategy/dataset audits | Keep synchronized when strategy or requirements change |
| Winner priority and sequencing overlay | VERIFIED + SAVED | `docs/WINNER_ROADMAP.md`; benchmark-leakage, adjudication, provenance, viewer, and C0-C7 red-team audit | Follow order; no GPT-5.6 DC01 call before public freeze |
| Static judge viewer | NOT STARTED | Strategy document exists; no viewer implementation or hosted path | Generate from real run |
| Offline `verify-run` | IMPLEMENTED + VERIFIED on invalid bundle | Standard-library verifier passes integrity checks while reporting terminal `INVALID`; it rechecks recorded custody, not absent original evidence bytes | Verify a complete authentic bundle and publish the command |
| No-key replay/viewer | PARTIAL | Verifier exists; no static viewer or hosted path | Build only over the authentic completed bundle |
| Git provenance | VERIFIED LOCALLY, NOT PUBLICLY ANCHORED | Local history includes `5309e5c`, `7b05d6a`, Gate A commit `6e696a0`, and synchronized strategy/handover commit `207a039`; no remote or server timestamp | Publish without rewriting history |
| Build provenance document | IMPLEMENTED | `BUILD_PROVENANCE.md` records prior/new/Codex boundaries and local-timestamp limitation | Record baseline hash and public/freeze URLs when they exist |
| Public experiment preregistration | NOT STARTED | Protocol/rubric/scorer digest is not frozen or remotely timestamped | Complete after deterministic native smoke and before any GPT-5.6 DC01 call |
| Judge quickstart | NOT STARTED | No `JUDGE-QUICKSTART.md` | Write after replay path exists |
| Demo video | NOT STARTED | No current-project video | Record only after genuine run |
| Devpost submission | NOT STARTED | No confirmation artifact | Draft early; submit July 20 |
| `/feedback` proof | VERIFIED + RETAINED LOCALLY | Current ID `019f61e5-5755-7a02-adb4-618d32baab27` is in project docs and screenshot | Final successful `/feedback` must come from the true majority-core thread after final core work |

### Verified size and quality baseline

- 14 source modules.
- 8,779 total source text lines, of which 7,889 are nonblank physical lines.
- 128 tests collected and passing in CPython 3.11.9.
- Ruff check and format check pass across 25 Python files.
- Wheel and sdist builds pass from the current source.
- Exact Windows AMD64 CPython 3.11 constraints and `pylock.toml` records are
  committed.
- Historical coverage percentages below predate C2 and are not a current
  quality claim: 54% overall; `models.py` 97%, `caps.py` 92%, `agent.py` 80%,
  `tools.py` 56%, `evidence.py` 42%, `cli.py` 21%, `_tool_worker.py` 11%.

Coverage is diagnostic, not a contest metric. Prioritize real CLI/native
integration coverage rather than chasing an arbitrary percentage.

### Current environment

| Item | Current verified state |
|---|---|
| Primary proof Python | CPython 3.11.9 at `%LOCALAPPDATA%\venvs\sentinel-unchained-py311\Scripts\python.exe` |
| Independent lockcheck Python | CPython 3.11.9 at `%LOCALAPPDATA%\venvs\sentinel-unchained-py311-lockcheck\Scripts\python.exe` |
| Dependency integrity | `pip check` clean in both environments; exact constraints plus hash-bearing platform `pylock.toml` committed |
| Key pinned runtime versions | `openai==2.31.0`, `tiktoken==0.12.0`, `volatility3==2.28.0`, pinned Qwen dependency commit |
| API credential in current process | `OPENAI_API_KEY` absent; value was never printed |
| Native Windows memory console | `vol.exe -h` passes; fixed console adapter is the preferred flagship path |
| Qwen catalog smoke | 25 direct functions and 5 allowlisted dynamic functions when the primary venv Scripts directory is on `PATH` |
| Real native plugin proof | VERIFIED LOCALLY: `windows.info` resolves symbols; authoritative `gate-a-final-20260715T015251Z` returns pstree 40 and psscan 72 records; repaired `gate-a-netscan-20260715T014947Z` returns 19,685 records and 3,961,843 accepted-output bytes |
| Public evidence archive outside repo | 561,424,278 bytes; official MD5 match `64A4E2CB47138084A5C2878066B2D7B1`; archive SHA-256 `86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80` |
| Extracted DC01 memory outside repo | 2,147,483,648 bytes; SHA-256 `8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62`; never commit or redistribute |
| Git repository | Local `main`; synchronized documentation commit `207a039` follows Gate A code/test commit `6e696a0`, `7b05d6a`, and `5309e5c`; no remote or server timestamp |
| Proof-bundle smoke | Integrity PASS for invalid empty-case bundle `20260715T012818Z-0c60c234`; 4 artifacts, 8 audit entries, terminal `INVALID`, exit 2 |

Tests alone did not prove the native route. The separate real-evidence smoke
below now proves the local Windows memory route, but not the model or public
submission gates.

### Current local Gate A evidence

- DC01 archive acquisition completed outside the repository.
- Archive size: 561,424,278 bytes.
- Archive official MD5: `64A4E2CB47138084A5C2878066B2D7B1`, matched.
- Archive SHA-256:
  `86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80`.
- Extracted memory size: 2,147,483,648 bytes.
- Extracted memory SHA-256:
  `8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62`.
- `windows.info` identifies the Windows memory image and resolves symbols.
- The deterministic profile is Windows, memory-only, ready, symbols ready.
- The sealed registry exposes 14 Windows memory tools.
- The authoritative post-sanitizer process batch is
  `gate-a-final-20260715T015251Z`, wall time 5,968 ms.
- In that batch, `vol_pstree` succeeded with 40 records and 15,277 accepted
  bytes, SHA-256
  `e2e70d5164939f5a735c450ecc0f2c268e48f22ae4a4dab76a92fa67f04ecac6`.
- In that batch, `vol_psscan` succeeded with 72 records and 16,526 accepted
  bytes, SHA-256
  `836951c95fdcc131064b52cfc229bb3753e389567fcb534174ac3f40d14a7fe4`.
- Both authoritative process receipts identify `E001`, contain no private path,
  and end with matching custody.
- Earlier pstree output of 15,359 bytes with SHA-256
  `031CA68A8AAC1985967CF7820142432E06E366E42069D9C055AFFF37376B3EFE`
  and psscan output of 16,608 bytes with SHA-256
  `c1d5b7f716f8543b6704de84c86e9de68545c5851f2bf6d0bd9dca2bdc3f5792`
  are retained only as pre-sanitizer diagnostics. They are not the headline
  Gate A receipts.
- The first parallel `vol_netscan` attempt failed honestly because its real
  response exceeded the old 2,000,000-byte private-worker transport limit. It
  is retained as an infrastructure diagnostic, not reframed as a forensic
  result and not deleted from the narrative.
- The worker transport now has a 16,000,000-byte hard ceiling. Accepted output
  is scrubbed of local evidence/mount paths before it leaves the worker.
- The deterministic delivery check separately caps the candidate investigator
  payload at 65,536 UTF-8 bytes. The view explicitly carries the full
  accepted-output size and SHA-256, native prefix selection, prefix-character
  count, and `model_view_complete=false`. The full accepted output remains
  retained content-addressably. No model or API received this payload.
- Successful rerun `gate-a-netscan-20260715T014947Z` produced 19,685 records.
  Its accepted output is 3,961,843 bytes with SHA-256
  `efced1af66f99ec2064d14f30a5f018d90e5c169027672be9e3c0110122cb421`.
  Its deterministic candidate investigator view is 65,536 bytes containing
  55,732 native-prefix characters and declares itself incomplete. The receipt
  identifies `E001`, contains no private evidence path, and ends with matching
  custody. No model or API was invoked.
- Successful values and worker exception strings cross the private boundary
  only after recursive path scrubbing. Matching is case-insensitive for Windows
  path variants, and a subprocess regression proves the exception path cannot
  repeat the runner-local evidence path.
- Post-smoke custody matches the baseline.

The evidence and smoke artifacts are local and outside Git. This is valid
deterministic Gate A proof. It is not the post-freeze primary, not an authentic
GPT-5.6 run, not public judge proof, and not authorization to expose DC01 to a
model before Gate B passes.

### Retained native diagnostic narrative

The pre-fix netscan overflow matters. It proved that the old 2,000,000-byte
transport ceiling could reject a valid, high-volume native result before
content-addressed retention. The correction separates three limits that must
never be conflated:

1. The native tool's real result.
2. The full accepted and retained output, bounded by the 16,000,000-byte private
   transport ceiling.
3. The explicit 65,536-byte model view, which states when it is incomplete and
   binds itself to the full accepted-output size and hash.

The successful rerun proves the repaired deterministic route. Neither attempt
called GPT-5.6, and neither is an authentic or scored investigation.

### Current red scoreboard

These are the controlling red states at 2026-07-14 22:22 ET:

| Red state | What turns it green |
|---|---|
| No `OPENAI_API_KEY` or confirmed funded project | Secret configured outside the repo and one bounded authentic provider check after freeze |
| Native fixes and local proof are not committed/public | Review and commit the two fixes and handover, then push current history without rewriting |
| No public remote or server timestamp | Current history and non-evidence proof pushed without rewriting and anonymously verifiable |
| No public rubric/protocol/scorer freeze digest | Complete two-axis preregistration committed, tagged, and server-timestamped |
| No authentic post-freeze GPT-5.6 run | First valid `COMPLETE` primary with requested/returned identity, usage, native receipts, and custody |
| No evaluation against frozen reference facts or viewer | Primary bundle scored by the disclosed project-authored harness, then hosted and offline viewer paths published |
| No public video or Devpost submission | Under-three-minute public video, checked links, submitted form, and saved confirmation |

## Correctness and proof-blocker disposition

### P0-1 - RESOLVED offline: report Markdown is link-free after rendering

The original bypass was:

```markdown
![a\]](//attacker.invalid/pixel)
```

The sanitizer now escapes existing ampersands and raw HTML delimiters, defangs
network/scheme/autolink forms, and makes every attacker-controlled square
bracket Markdown-inert. This disables every link/image form structurally while
preserving readable headings, lists, emphasis, tables, and visible citations.

Verification: focused tests render adversarial input through CommonMark and
reject active tags, URL-bearing attributes, raw HTML, dangerous schemes,
protocol-relative targets, encoded delimiters, nested/malformed forms, and the
exact bypass. The current full 128-test suite passes. Authentic report output
and the future viewer remain separate demonstration gates.

### P0-2 - RESOLVED offline: exact filesystem offset is sealed end to end

Classification now retains the exact byte offset whose filesystem probe
succeeded. The value propagates through `EvidenceItem`, the mount decision, and
trusted TSK execution. The model cannot supply or change it. `tsk_fsstat` is
withheld when the exact offset is unknown; otherwise trusted code seals the
derived sector into `fsstat -o`. Partitioned APFS is withheld when its available
backend cannot accept the offset.

Verification includes a two-partition fixture whose filesystem exists only on
the second partition, exact later-TSK-match propagation, mount-option proof,
sealed worker argv proof, raw offset zero, and unknown-offset withholding. The
current full suite passes 128 tests.

### P0-3 - RESOLVED offline: text log cannot become memory from a banner

Printable text/log recognition now runs before generic memory-banner scanning,
while native crash-dump and LiME signatures retain priority. A Linux boot log
containing `Linux version` remains a log and cannot manufacture a memory
artifact or a strong disk-memory OS conflict.

Verification includes the boot-log fixture and a Windows disk paired with the
Linux text log. Both focused and full suites pass.

### P0-4 - RESOLVED offline: full accepted tool outputs are durable

Exact accepted UTF-8 tool-output bytes are persisted content-addressably before
the corresponding `tool.completed` event is accepted. The receipt retains the
relative artifact path, bytes, encoding, media type, SHA-256, and bounded
excerpt. Atomic write, duplicate-content, tamper, symlink, and failure-path tests
pass.

This proves full retention of the output accepted by the trusted runner. It does
not prove that an upstream native tool emitted no additional bytes before the
adapter accepted its result. Public wording must preserve that distinction.

### P0-5 - RESOLVED by flagship scope: authoritative prompt and claims align

The authoritative prompt and current flagship both target Windows evidence.
Linux remains experimental and macOS remains best-effort in support planning;
neither is a flagship claim without a real demonstration.

### P0-6 - RESOLVED offline: retries are bounded and audited

The SDK retry mechanism remains disabled. Project-owned retries are bounded,
audited, cap-aware, and limited to transient transport and provider status
failures. Protocol, schema, usage, and returned-model failures are not retried.
No forensic tool runs until a final accepted model response supplies the call.

### P0-7 - RESOLVED for the Windows CPython 3.11 proof target

The repository commits exact Windows AMD64 CPython 3.11 constraints and a
hash-bearing `pylock.toml`. The primary and independently created lockcheck
environments both run CPython 3.11.9 and pass `pip check`. The full tests, Ruff,
format, wheel build/install path, Volatility help, and Qwen catalog smoke pass.
This lock is platform-specific and is not claimed as an Ubuntu lock.

### P0-8 - RESOLVED offline: requested and returned model identities are separate

The normalized model response and audit retain the requested alias separately
from the provider-returned model, along with response ID, request ID, status,
usage, and local cost estimate where available. `summary.json` derives the
requested/provider model sets and response/request-ID counts. `environment.json`
records the requested configuration, while the manifest content-hashes the
audit, summary, and environment records. Mocked provider tests prove the
propagation and reject an unexpected returned model without retrying it.

Authentic provider proof remains a Gate C requirement. Offline mocked receipts
cannot establish that GPT-5.6 participated in a real run.

## Flagship-run acceptance gate

The flagship is accepted only when every applicable item below is evidenced.

### Before execution

- [x] The eight P0 implementation blockers above are fixed or explicitly narrowed
  without overstated claims.
- [x] CPython 3.11.9 primary and independent lockcheck environments exist.
- [x] `python -m pip check` passes in both clean environments.
- [x] All 128 tests and Ruff check/format pass.
- [x] The package builds and installs from the exact submission source.
- [x] The real typed forensic catalog imports: 25 direct and 5 allowlisted
      dynamic functions with the primary venv on `PATH`.
- [x] Required native tools for the Windows memory shape pass deterministic
      real-evidence smoke tests.
- [x] The public evidence case, acquisition source, official MD5, sizes, and
      local SHA-256 values are documented without committing evidence.
- [ ] The evidence-observable known-fact rubric is complete and frozen.
- [ ] `OPENAI_API_KEY` is configured outside the repository and never logged.
- [ ] `UNCHAINED_MODEL=gpt-5.6` is explicit.
- [ ] Default/strict caps and maximum expected spend are approved.

### During execution

- [ ] The provider is authentic GPT-5.6, not a fake harness; requested alias and
      provider-returned model/snapshot are both retained.
- [ ] Step 0 produces an honest profile and capability label.
- [ ] Pre-run custody hashes are recorded.
- [ ] Typed tools run without model-selected shell/path/binary authority.
- [ ] Model/tool events and provider request IDs are retained safely.
- [ ] Usage, cost, runtime, and tool status are measured.
- [ ] The investigator terminates through the literal `DONE` protocol.
- [ ] Structured findings are produced.
- [ ] The fresh judge completes with monotonic verdicts.
- [ ] Final report completes.
- [ ] Cleanup succeeds.
- [ ] Post-run custody matches.
- [ ] Terminal status is `COMPLETE` with exit 0.

### Retained proof bundle

```text
examples/public-run/
  report.md
  profile.json
  audit.jsonl
  summary.json
  manifest.json
  manifest.sha256
  tool-outputs/
    <sha256>.*
  viewer/
    index.html
```

The manifest must identify requested and provider-returned model identities,
request IDs where safe, timestamps, evidence
hash, artifact hashes, exact dependency versions, host/evidence support tuple,
caps, terminal status, and custody result.

Current smoke evidence is intentionally weaker: invalid empty-case bundle
`20260715T012818Z-0c60c234` passes integrity verification for 4 artifacts and 8
audit entries while correctly reporting terminal `INVALID`, exit 2. It contains
no authentic model response, native tool row, final evidence-custody match, or
completed investigation. It must never be presented as the flagship bundle.

### Evaluation against known facts

- [ ] Known facts found.
- [ ] Known facts missed.
- [ ] Unsupported or false claims.
- [ ] Investigator course corrections.
- [ ] Proposed versus final judge statuses.
- [ ] Repeated-run variance if budget permits.
- [ ] Runtime, tokens, provider/local cost estimate, and tool success/failure.

Exact quote resolution proves only that a reviewer-quoted string occurs inside
the bounded receipt excerpt for the cited call. It does not prove that the quote
supports the claim, that the claim is factually correct, or that the project
authored reviewer is independent. Semantic correctness and receipt sufficiency
must be reported as separate axes under the publicly frozen rubric and scorer.

A `PARTIAL` run is useful as a secondary safety demonstration but cannot be the
flagship proof.

## Two-layer judge experience

### Layer 1 - Authentic proof

One genuine GPT-5.6 public-evidence run with complete artifacts proves the model
actually performed the investigation.

### Layer 2 - Frictionless access

Provide a no-key, no-rebuild hosted viewer, offline viewer/release bundle, and
prebuilt verifier that let a
judge inspect the genuine run. It should:

- Verify the audit chain.
- Verify retained tool-output hashes.
- Show investigator versus judge status changes.
- Open finding-scoped receipts.
- Show final custody.
- Require no API key, evidence download, compilation, or native tool install.

Every replay surface must visibly say:

```text
Verification/replay of a retained genuine GPT-5.6 run.
This path does not perform a new model call.
```

The fake-model harness remains useful for deterministic controller testing. It
must never be presented as GPT-5.6 evidence.

## Go/no-go gates

### Gate A - Correctness, proof structure, and environment

Target: July 15, 20:00 ET.

Current state at 2026-07-14 22:22 ET: **PASS LOCALLY**. C1, C2, CPython 3.11.9,
dependency locks, clean installs, `pip check`, tests, Ruff, build, Volatility
help, catalog smoke, verified DC01 acquisition, Windows profile/symbols, a
14-tool sealed registry, real pstree/psscan/netscan rows, bounded large-output
delivery, path sanitization, and custody are green. The fixes and proof receipts
still need a commit and public anchor before Gate B.

Pass when:

- all three reproduced correctness fixes and regressions pass;
- full-output proof structure and provider-returned identity are substantially
  working;
- honest Git/provenance baseline exists;
- clean Python 3.11 passes install, `pip check`, tests, lint, build, and catalog
  smoke;
- at least one existing native memory function returns real rows without
  GPT-5.6.

The Build Week primary is now frozen in scope to Windows memory-only. If Gate A
slips, remove nonessential work rather than reopening paired disk or platform
breadth. Do not add a new Volatility adapter unless the existing reviewed route
is first reproduced as incapable of that flagship.

### Gate B - Public experiment freeze

Target: before the first GPT-5.6 investigation of DC01.

Current state: **BLOCKED**. Verified local DC01 hashes exist, but there is no
public remote/server timestamp, public binding of those hashes, frozen rubric,
scorer digest, or public freeze tag.

Pass when the rubric, two-axis scoring specification, metrics, denominators,
fault criteria, first-valid-run rule, code, prompts, catalog, dependencies,
caps, retries, price table, evidence hashes, and scorer are frozen by digest in
a public commit and tag with server-timestamped verification.

No GPT-5.6 DC01 model rehearsal is allowed before this gate. Deterministic
native-tool smoke against DC01 was allowed and has completed locally without
model exposure. That proof does not unlock a model call. Commit the reviewed
fixes and publish the complete freeze first.

### Gate C - Authentic primary run

Target: July 17, 18:00 ET.

Current state: **NOT READY**. `OPENAI_API_KEY` is absent, a funded project is not
confirmed, the public freeze does not exist, and no authentic response or run
artifact exists.

Pass when the first valid post-freeze GPT-5.6 run is `COMPLETE`, retained,
bundle-verified, custody-record-clean, and evaluated for factual correctness and
receipt sufficiency under the frozen rules.

If Gate C fails, stop viewer polish and diagnose only the frozen Windows
memory-only live path. Do not reopen paired disk, substitute a fake replay for
proof, or silently select a nicer later run. Convene an explicit go/no-go review
before spending more time or attempting any alternative project.

### Gate D - Judge path

Target: July 18, 20:00 ET.

Current state: **PARTIAL IMPLEMENTATION**. The offline verifier is implemented
and passes an invalid bundle integrity smoke. There is no complete authentic
bundle, static viewer, hosted path, or judge quickstart.

Pass when an anonymous judge can understand the project in 20 seconds and verify
the genuine run in under five minutes without rebuilding through a hosted
viewer, offline viewer/release bundle, and no-network verifier. A screencast is
supplemental evidence only.

### Gate E - Submission freeze

Target: July 20.

Current state: **NOT READY**. No public repository, authentic evaluated run,
viewer, video, Devpost submission, or confirmation artifact exists.

Pass when the public video, repository, viewer/test path, Devpost fields, metrics,
links, licensing, feedback ID, and confirmation checklist are complete.

## Delivery schedule

### July 14 - Baseline, rules, provenance, scope

- [x] Recover the primary Codex session.
- [x] Verify the successful `/feedback` ID and screenshot.
- [x] Resolve 2026 Build Week versus 2025 gpt-oss rule conflict.
- [x] Save and link this living handover.
- [x] Fix the three reproduced correctness/security defects.
- [x] Design and implement content-addressed full accepted-output retention.
- [x] Freeze the Build Week primary to the proven Windows memory-only route;
  paired disk is future work and not a gate.
- [x] Initialize local Git and create the honest baseline commit.
- [x] Create `BUILD_PROVENANCE.md`.
- [x] Implement provider-returned identity, evidence-grounded reviewer quotes,
  bounded audited retries, self-verifying bundles, and `verify-run`.
- [x] Create commits `5309e5c` and `7b05d6a` for C2 and the locked proof path.

### July 15 - Clean supported path

- [x] Add and pass P0 adversarial regression tests.
- [x] Pin exact Windows AMD64 CPython 3.11 constraints and `pylock.toml`.
- [x] Establish clean CPython 3.11.9 primary and lockcheck environments.
- [x] Install the fixed Volatility console and prove `vol.exe -h`.
- [x] Pass `pip check`, 128 tests, Ruff, wheel/sdist/install, and real catalog
  smoke.
- [ ] Add CI for the clean path.
- [x] Acquire public DC01 memory evidence outside Git and record official MD5,
  sizes, source, and local SHA-256 values.
- [x] Return real rows from deterministic `vol_pstree`; retain its accepted
  output size/hash and matching custody result.
- [x] Run parallel `vol_psscan`/`vol_netscan`; retain the initial netscan
  transport failure as a diagnostic; fix transport, path privacy, and bounded
  model delivery; rerun netscan successfully with full accepted retention.
- [ ] Complete and freeze the evidence-observable known-fact rubric.
- [ ] Create the public remote and retain its server timestamp without rewriting
  local history.

### July 16 - Native proof and public experiment freeze

- [x] Complete C2 proof artifacts and the clean CPython 3.11 environment.
- [x] Complete deterministic native Volatility smoke against verified evidence.
- [ ] Build the evidence-observable rubric and two-axis scoring specification.
- [ ] Freeze code, prompts, catalog, caps, retries, dependencies, price table,
  metrics, infrastructure faults, and primary-run selection.
- [ ] Push and tag the freeze; retain server-timestamped digest verification.
- [ ] Do not run GPT-5.6 on DC01 until this freeze passes.

### July 17 - Authentic primary and live-run gate

- [ ] Run the first valid post-freeze GPT-5.6 DC01 investigation as primary.
- [ ] Verify the proof bundle, audit, cleanup, and retained custody record.
- [ ] Evaluate factual correctness and receipt sufficiency under frozen rules.
- [ ] Repeat once if budget and stability permit.
- [ ] Capture one genuine course correction or judge downgrade.
- [ ] Capture one separate cap or custody-failure safety demonstration.
- [ ] Pass Gate C by 18:00 ET.

### July 18 - Judge experience and story

- [ ] Publish the hosted HTTPS receipt/custody viewer.
- [ ] Publish the offline viewer/release bundle and no-network verifier.
- [ ] Write `JUDGE-QUICKSTART.md`.
- [ ] Rewrite the README hero around outcome, proof, measured results, and the
  instant demo.
- [ ] Add architecture and support matrix.
- [ ] Draft Devpost copy and video storyboard.

### July 19 - Video and independent QA

- [ ] Record a narrated 2:40–2:50 demo.
- [ ] Add captions and readable text.
- [ ] Upload publicly to YouTube.
- [ ] Test from a clean environment and an incognito browser.
- [ ] Have one technical and one nontechnical reviewer watch without coaching.
- [ ] Verify every public metric against retained artifacts.

### July 20 - Freeze and submit

- [ ] Run final tests, lint, install/build, verifier, and link checks.
- [ ] Run final `/feedback` in the true primary build thread.
- [ ] Update the ID only if the successful upload returns a different value.
- [ ] Tag the final commit.
- [ ] Complete the Devpost form.
- [ ] Confirm the video is public, narrated, and under three minutes.
- [ ] Check every URL anonymously on desktop and mobile.
- [ ] Submit and save confirmation screenshots/email.
- [ ] Keep all judge assets stable through at least August 12.

### July 21 - Emergency buffer only

No planned scope. Use only for submission-blocking recovery before 20:00 ET.

## Three-minute demo contract

Target runtime: 2:40–2:50.

| Time | Scene | Proof |
|---|---|---|
| 0:00–0:18 | The analyst problem | Captured memory/disk; alert is not an investigation |
| 0:18–0:35 | Promise + architecture | “Unchained reasoning. Chained evidence.” |
| 0:35–0:58 | Deterministic preflight | Real profile, content detection, capabilities, evidence hash |
| 0:58–1:20 | Agentic opening | GPT-5.6 selects typed tools; no shell/path/binary authority |
| 1:20–1:48 | Course correction | Contradictory/insufficient artifact changes the investigation |
| 1:48–2:10 | Signature moment | Investigator status versus fresh judge downgrade |
| 2:10–2:32 | Receipt drill-down | Typed args, full output, hash, audit chain, custody |
| 2:32–2:48 | Measured result | COMPLETE, runtime, cost, tools, findings, downgrades, custody |

Do not show hidden chain-of-thought. Show observable plans, actions, receipts,
status changes, and measured outcomes.

## Submission readiness checklist

### Repository and provenance

- [x] Local Git repository initialized without backdating.
- [ ] Remote published or private access shared with both required addresses.
- [ ] License present and dependency licenses checked.
- [x] Prior/new work boundary documented.
- [x] `BUILD_PROVENANCE.md` created; append public/freeze/run links later.
- [ ] Public experiment freeze and server-timestamped digest proof exist.
- [ ] Submission tag created.

### Product and proof

- [ ] Authentic GPT-5.6 `COMPLETE` run.
- [ ] Public/licensed evidence source and hash.
- [ ] Complete retained artifacts and outputs.
- [ ] Frozen two-axis evaluation and measured scoreboard.
- [ ] Hosted and offline viewer plus no-network no-rebuild path.
- [ ] Support matrix distinguishes evidence OS from host OS.

### README and Devpost

- [ ] Outcome-first hero and tagline.
- [ ] Video and instant-demo links above the fold.
- [ ] Installation and supported platforms.
- [ ] Sample-data/public-run instructions.
- [ ] Codex collaboration and human-owned decisions.
- [ ] GPT-5.6 runtime role.
- [ ] Prior/new work disclosure.
- [ ] Honest limitations and data boundary.
- [ ] Developer Tools selected in the live form.
- [ ] `/feedback` Session ID exact.

### Video and access

- [ ] 2:40–2:50 runtime.
- [ ] Public YouTube visibility.
- [ ] Clear voiceover and captions.
- [ ] Working product visible.
- [ ] Codex build workflow explained.
- [ ] GPT-5.6 role explained.
- [ ] No unlicensed music/assets or exposed secrets.
- [ ] All links pass incognito/mobile checks.

## Risk register

| Risk | Severity | Current mitigation | Exit evidence |
|---|---|---|---|
| No authentic GPT-5.6 run | Critical | Hard Gate C; public freeze then proof before polish | Retained `COMPLETE` bundle |
| No public dated Git provenance | Critical | Local commits through `7b05d6a` exist without backdating; remote still absent | Public commits/tag + provenance map |
| Benchmark leakage before freeze | Critical | No GPT-5.6 DC01 call before public Gate B | Public freeze + server timestamp + run timestamps |
| Sanitizer bypass | RESOLVED OFFLINE | Link-free safe subset and rendered adversarial tests | Authentic report/viewer demonstration |
| Wrong partition mount | RESOLVED OFFLINE | Exact matched offset sealed end to end | Native paired-disk proof if retained |
| Log misclassified as memory | RESOLVED OFFLINE | Text/log recognition before banner inference | Authentic profile proof |
| Missing full outputs | RESOLVED OFFLINE | Content-addressed accepted-output artifacts and fail-closed tests | Authentic `verify-run` rehashes genuine outputs |
| Large result rejected or silently overfed to model | RESOLVED LOCALLY, AUTHENTIC PROOF PENDING | Pre-fix netscan overflow retained; 16,000,000-byte transport ceiling; full accepted retention; explicit 65,536-byte incomplete model view | Committed diagnostic plus authentic bundle metadata |
| Private evidence path leaks through accepted output | RESOLVED LOCALLY, AUTHENTIC PROOF PENDING | Recursive sealed-worker scrub replaces local path with evidence ID; successful receipt contains `E001` and no private path | Authentic bundle secret/path scan |
| Configured model mistaken for provider proof | RESOLVED OFFLINE, LIVE PROOF PENDING | Requested and returned identities are separate in audit/bundle | Authentic audit + manifest show requested and returned identities |
| No verified DC01 evidence/native rows | RESOLVED LOCALLY, PUBLIC PROOF PENDING | Official archive MD5 and local SHA-256 values retained; authoritative sanitized pstree/psscan plus repaired netscan receipts verified; custody matches | Commit and publish non-evidence proof receipts after freeze |
| No funded runtime credential | Critical | Keep key outside repo; confirm funded project before Gate C | Authentic Gate C response within hard caps |
| Native environment incomplete | RESOLVED FOR WINDOWS MEMORY FLAGSHIP | CPython 3.11.9, clean locks, Volatility help, catalog, profile/symbols, 14 tools, and real rows | Preserve exact proof under committed frozen environment |
| Fake replay mistaken for proof | High | Visible replay labeling | Authentic manifest + replay banner |
| Exact quote mistaken for semantic truth | High | State that exact resolution proves receipt integrity only; score correctness separately | Frozen two-axis scorer output |
| Prior Qwen work mistaken as new | High | Positive disclosure and dated boundary | `BUILD_PROVENANCE.md` + commits |
| Same-model judge overstated | Medium | Call it fresh-context monotonic review | Honest README/video language |
| Evidence privacy exposure | High | Public case only; no secrets/raw private case | Data review + public manifest |
| Stale 2025 rules reused | High | Direct-current-source policy | Retrieval date + correct track/dates |
| Calendar dilution | Critical | Frozen scope and daily exit gates | Gate A-E status |

## Claims discipline

Safe now, with the stated scope:

- 14 source modules, 8,779 total source text lines, and 7,889 nonblank physical
  source lines.
- 128 offline tests pass under CPython 3.11.9.
- Ruff check and format check pass.
- A wheel builds; primary and lockcheck environments pass `pip check`.
- Exact Windows AMD64 CPython 3.11 constraints and a hash-bearing platform lock
  are committed.
- Volatility help passes, and the pinned Qwen catalog exposes 25 direct and 5
  allowlisted dynamic functions with the primary venv active.
- Public DC01 memory evidence was acquired outside Git, its 561,424,278-byte
  archive matches official MD5 `64A4E2CB47138084A5C2878066B2D7B1`, and both
  archive and extracted-memory SHA-256 values are retained above.
- The real local profile is Windows memory-only with symbols ready; the sealed
  registry exposes 14 Windows tools. Authoritative post-sanitizer batch
  `gate-a-final-20260715T015251Z` completed in 5,968 ms: pstree returned 40
  records/15,277 accepted bytes, and psscan returned 72 records/16,526 accepted
  bytes. Both identify `E001`, contain no private path, and have matching
  custody.
- The first parallel `vol_netscan` failed at the old 2,000,000-byte transport
  limit; the failure is retained. Rerun `gate-a-netscan-20260715T014947Z`
  returned 19,685 records and 3,961,843 accepted-output bytes after the bounded
  transport fix.
- The deterministic netscan candidate investigator view is exactly 65,536
  bytes, contains 55,732 native-prefix characters, explicitly says it is
  incomplete, binds to the full accepted-output size/hash, identifies `E001`,
  contains no private path, and ends with matching custody. This was
  deterministic only; no model or API was called.
- Successful and failed worker results apply recursive, case-insensitive path
  scrubbing before crossing the private boundary; the subprocess exception
  regression replaces the runner-local path with the sealed evidence ID.
- Core control-plane semantics are implemented and tested offline.
- C2 durable accepted-output receipts, provider identity, bounded audited retry,
  proof-bundle finalization, and offline verification are implemented and tested.
- Invalid empty-case bundle `20260715T012818Z-0c60c234` passes integrity
  verification while correctly remaining `INVALID`, exit 2.
- The feedback ID and screenshot are verified.
- All three reproduced C1 correctness/security defects are resolved offline with
  adversarial regressions.
- Local Git through commits `5309e5c` and `7b05d6a` and
  `BUILD_PROVENANCE.md` exist; no public remote timestamp exists.

Not safe yet:

- “End-to-end tested.”
- “Production ready.”
- “Accurate” without known-fact evaluation.
- “Immutable audit.”
- “Full outputs are inspectable.”
- “Independent truth verifier.”
- “Exact quotes prove semantic correctness.”
- “The empty-case bundle is an authentic or complete run.”
- “The model sees the complete 3.96 MB netscan output.”
- “The pre-fix netscan transport overflow was a forensic finding.”
- “The deterministic parallel smoke was an authentic opening-book/model run.”
- “Evidence stays local.”
- “Native Windows E01 support.”
- Any Unchained runtime, cost, finding, or accuracy number borrowed from Qwen.

## Commands for the next session

Start in:

```powershell
cd <path-to-clone>\sentinel-unchained
```

Read first:

```powershell
Get-Content .\docs\WINNER_ROADMAP.md
Get-Content .\docs\HACKATHON_MASTER_PLAN.md
Get-Content .\HACKATHON_HANDOVER.md
Get-Content .\DECISIONS.md
```

Current baseline checks:

```powershell
$venv = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311"
$python = "$venv\Scripts\python.exe"
$env:PATH = "$venv\Scripts;$env:PATH"
& $python --version
& $python -m pip check
& $python -m pytest
& $python -m ruff check .
& $python -m ruff format --check .
& "$venv\Scripts\vol.exe" -h
git rev-parse --is-inside-work-tree
git log --oneline -4
git remote -v
```

### Exact next safe sequence

1. Run the full supported-environment verification, then review and commit the
   real-route fixes, their regressions, and the synchronized handover. Keep raw
   evidence outside Git and keep pre-freeze smoke separate and explicitly
   labeled.
2. Create the public Git remote and push current history without rewriting it.
   Verify the remote anonymously and retain its server timestamp.
3. Finish the evidence-observable rubric, two-axis scorer, protocol, fault rules,
   first-valid-run rule, prompts, catalog, caps, retry policy, dependencies,
   price table, and evidence hashes. Commit and publish their digests and tag to
   obtain a server timestamp.
4. Verify the public freeze from an anonymous checkout. Only after this step may
   any DC01 profile, filename, evidence byte, native output, or case fact be sent
   to GPT-5.6.
5. Confirm a funded OpenAI API project and secret handling, then run the first
   valid post-freeze `COMPLETE` investigation as the primary result. Verify its
   bundle before viewer or video work.

Canonical live command only after the public freeze gate passes:

```powershell
$env:OPENAI_API_KEY = "<set securely; never commit>"
$env:UNCHAINED_MODEL = "gpt-5.6"
& $python -m unchained C:\path\to\public-evidence --caps default
```

Do not execute the live command until the flagship pre-execution checklist is
complete. In particular, do not expose DC01 to any model before the public
freeze. Deterministic native-tool smoke remains explicitly allowed.

## Current prompt readiness

The C1 correctness work and C2 proof-artifact work have completed. Do not paste
the retired project kickoff, repeat C1, or repeat C2. The local C3 native leg is
green: the CPython 3.11 environment, locks, Volatility help, catalog, verified
DC01 acquisition, Windows profile/symbols, 14-tool sealed registry, real
sanitized pstree/psscan plus repaired large netscan receipts, bounded model-view
delivery, and custody all pass. Commit the fixes and synchronized docs, publish
the current remote, then complete and publish Gate B
preregistration before any C4-style GPT-5.6 DC01 execution. C5 through C7 remain
blocked behind that authentic primary run.

### Triple-verification record

The older tables below are retained unchanged as historical verification
records. Their old test counts, dependency failures, and Git states describe
the named timestamps only and must not be read as current. The current ledger,
environment table, and gate table above control.

| Pass | What is verified | Result | Evidence | Timestamp ET |
|---|---|---|---|---|
| 1 - Coverage | Rules, all nine constraints, status ledger, proof/replay contract, defects, gates, schedule, risks, feedback ID, and next-session commands are saved | **PASS** | 926-line handover; nine numbered constraints; required-section scan found zero omissions | 2026-07-14 19:05 |
| 2 - Consistency | Handover agrees with live 2026 rules, README, DECISIONS, and actual repository state | **PASS** | Uncached rules/FAQ returned 200 and confirmed Build Week, Developer Tools, GPT-5.6, July 21, pre-existing-only evaluation, `/feedback`, no-rebuild, and under-three-minute requirements; no gpt-oss text | 2026-07-14 19:05 |
| 3 - Executable truth | Links resolve and current Python, dependencies, tests, lint, Git, and artifact state are recorded without hiding failures | **PASS** | Zero local-link failures; 71 tests passed; Ruff passed; expected blockers preserved: `pip check` exit 1, Git check exit 128, submission/run artifacts absent | 2026-07-14 19:05 |

Prompt 3 becomes documentation-ready only after all three rows are marked
`PASS`. Flagship-run readiness remains a separate gate.

### Corrected master-plan triple verification

| Pass | What is verified | Result | Evidence | Timestamp ET |
|---|---|---|---|---|
| 1 - Coverage | Product thesis, official rules, truthful architecture, scope matrices, current state, eight P0 gaps, experiment, DC01 contract, proof bundle, viewer, video, gates, prompts, compliance, ZeroFake rails, and go/no-go are saved | **PASS** | 1,084-line master plan with 18 numbered sections and copy-ready P0, proof, runtime, reviewer, and video prompts | 2026-07-14 19:38 |
| 2 - Consistency | Master plan agrees with the live 2026 rules, official GPT-5.6 guidance, actual allowlists/capabilities, handover evidence states, and durable decisions | **PASS** | Independent rules, code, and strategy audits; false Plaso/Docker/multi-OS/causal-ablation/answer-key claims replaced | 2026-07-14 19:38 |
| 3 - Executable truth | Cross-document links, formatting, tests, lint, dependency/Git blockers, and proof red states remain visible and accurate | **PASS** | Relative-link scan passed; heading blank-line scan passed; master-plan em-dash scan passed; 71 tests passed; Ruff passed; `pip check` still reports three missing dependencies; Git check still fails because no repository exists | 2026-07-14 19:38 |

### Current C2 and Gate A handover triple verification

| Pass | What is verified | Result | Evidence | Timestamp ET |
|---|---|---|---|---|
| 1 - Repository truth | Current commits, dirty-tree scope, module/line counts, tests, lint, format, and build | **PASS** | Gate A implementation commit `6e696a0` and synchronized strategy/handover commit `207a039` follow `7b05d6a` and `5309e5c`; 14 modules; 8,779 total/7,889 nonblank source lines; both CPython 3.11.9 environments pass 128 tests and `pip check`; Ruff, format, wheel, sdist, and diff check pass | 2026-07-14 22:24 |
| 2 - Environment and local Gate A proof | Supported Python, lock integrity, installed dependencies, tool discovery, invalid-bundle behavior, verified evidence, native rows, bounded delivery, privacy, and custody | **PASS FOR CLAIMED LOCAL SCOPE** | Clean CPython 3.11.9/locks/catalog; official hashes; Windows profile/symbols; 14 tools; authoritative `gate-a-final-20260715T015251Z`: pstree 40/15,277 bytes, psscan 72/16,526 bytes, both `E001` and path-free; repaired netscan 19,685/3,961,843 bytes with explicit incomplete 65,536-byte candidate view; case-insensitive success/error path scrub; custody match; no model/API call | 2026-07-14 22:22 |
| 3 - ZeroFake handover truth | All authentic/public red gates, freeze boundary, quote/transport semantics, diagnostic history, screenshot/evidence locality, and next sequence remain explicit | **PASS** | Live rules and API/pricing rechecked; pre-fix netscan failure retained; Windows memory-only primary selected; factual precision separated from receipt support; evaluator authorship disclosed; deterministic local proof is not called authentic/scored; no claim of public timestamp, semantic truth, viewer, video, or submission | 2026-07-14 22:22 |

| Gate | State |
|---|---|
| Rules ambiguity resolved | READY |
| Strategic handover saved and linked | READY |
| Prompt 3 constraints preserved | READY |
| P0 implementation prompt | **COMPLETE, current suite 128 tests** |
| C2 proof-artifact prompt | **COMPLETE OFFLINE in commits `5309e5c` and `7b05d6a`** |
| CPython 3.11 lock/install/build/catalog path | **READY** |
| Verified public evidence acquisition | **READY LOCALLY; raw evidence remains outside Git** |
| Deterministic native plugin rows and custody | **READY LOCALLY; non-evidence receipts not yet public** |
| Public experiment freeze | **NOT READY** |
| Flagship GPT-5.6 run may begin | **NOT READY** |
| Video recording may begin | **NOT READY** |
| Submission may be called complete | **NOT READY** |

C2 implemented durable accepted outputs, provider-returned identity, structured
reviewer quotes, manifest, summary, environment record, verifier, bounded
audited retries, and exact CPython 3.11 dependency records. The verified
empty-case bundle is a packaging smoke only. It is historical proof that the
invalid path finalizes and verifies, not evidence of GPT-5.6 or forensic
performance.

## Living update protocol

At the end of every substantial future session:

1. Update the document-control verification timestamp.
2. Update the implementation/proof ledger using the defined evidence states.
3. Record exact commands and outcomes for newly verified work.
4. Link every new retained artifact.
5. Update the applicable gate and daily checklist.
6. Add or resolve risks without deleting historical truth.
7. Record scope or product decisions and who owns them.
8. Recalculate the remaining clock when schedule decisions change.
9. State the single next highest-leverage action.
10. Record the current commit hashes, source/test counts, supported Python and
    lock state, proof-bundle terminal status, and every still-red external gate.
11. Reconfirm that no scored-case data reached a model before the public freeze.
12. Preserve exact quote integrity and semantic correctness as separate claims.
13. Preserve the current `/feedback` ID, but obtain the final successful ID from
    the true majority-core thread after final core work.

### Change log

| Date/time ET | Change | Evidence | Next action |
|---|---|---|---|
| 2026-07-14 18:58 | Created living handover; reconciled current rules, repository state, defects, positioning, Prompt 3 constraints, and delivery gates | Direct current rules/FAQ/overview; 71 tests; Ruff; wheel build; source inspection; focused reproductions | Fix the three reproduced defects, then implement durable full-output artifacts |
| 2026-07-14 19:05 | Completed all three pre-Prompt-3 documentation verification passes | Current uncached rules and FAQ; nine-constraint coverage scan; zero broken local links; 71 tests; Ruff; truthful dependency/Git/artifact red states | Begin the focused P0 correctness/proof implementation block |
| 2026-07-14 19:30 | Saved the deeply corrected winner master plan and synchronized README, AGENTS, decisions, and handover; added provider-returned-model and partition-aware TSK proof requirements | Independent rules, repository, and experiment audits; official GPT-5.6 guidance; current tests/Ruff/pip/Git checks; DC01 source and answer-page verification | Execute the focused P0 correctness prompt saved in the master plan |
| 2026-07-14 19:38 | Completed three verification passes over the corrected master-plan integration | 1,084-line/18-section coverage; link and heading scans; no em dash in master plan; 71 tests; Ruff; truthful dependency and Git failures retained | Execute the focused P0 correctness prompt saved in the master plan |
| 2026-07-14 20:50 | Deeply red-teamed and saved the Winner Roadmap; corrected the C0-C7 order, forbade GPT-5.6 DC01 rehearsal before a public freeze, split factual correctness from receipt sufficiency, retained the existing Volatility path, and made hosted plus offline viewing the no-rebuild contract | Current Official Rules; official GPT-5.6 and Responses guidance; Qwen adapter/source inspection; independent strategy audit; 881-line roadmap | Finish C1 verification and honest local provenance, then start C2 |
| 2026-07-14 20:50 | Implemented and root-verified all three reproduced C1 defects: rendered Markdown inertness, exact partition-offset propagation into sealed `fsstat`, and log-before-memory classification | 80 tests passed in 1.39s; six rendered report-safety tests; 34 focused evidence/tool tests; Ruff check and format check; wheel build | Commit the honest baseline, then implement C2 proof artifacts |
| 2026-07-14 20:56 | Initialized local Git on `main`, added evidence/secret exclusions, created `BUILD_PROVENANCE.md`, passed high-confidence secret and evidence scans, and created the honest root commit | Commit `5b31b32e995d4d485bf512bb8600ca44b46e6f2c`; 32 reviewed files; no public remote | Publish without history rewriting, then start C2 |
| 2026-07-14 21:31 | Completed C2 provider/evidence-grounding hardening | Commit `5309e5c`; bounded audited retries, requested/provider model separation, durable accepted outputs, and exact reviewer-quote validation | Complete the locked proof path and verify bundle finalization |
| 2026-07-14 21:31 | Completed the locked CPython 3.11 proof path and reconciled the living handover | Commit `7b05d6a`; 14 modules, 7,767 nonblank source lines, 123 tests, Ruff/build pass, clean primary and lockcheck environments, exact constraints/pylock, Volatility help, 25 direct/5 dynamic catalog, and integrity-PASS empty-case bundle that correctly remains `INVALID` | Obtain evidence and a public remote, run deterministic native smoke, then publish the experiment freeze |
| 2026-07-14 21:41 | Hardened the real Windows-memory route in the working tree and reverified the supported environment | Uncommitted review state: active-interpreter-adjacent Volatility launcher, sanitized child `PATH`, Windows direct tools decoupled from the Linux/macOS dynamic map; 14 modules, 7,784 nonblank source lines, 125 tests, Ruff/format and `pip check` pass | Commit reviewed native-routing changes, then obtain evidence and retain real deterministic plugin rows |
| 2026-07-14 21:43 | Passed the first local deterministic Gate A native leg without exposing DC01 to GPT-5.6 | DC01 archive outside Git matches official MD5; archive/extracted SHA-256 retained; Windows memory-only profile and symbols ready; sealed registry exposes 14 tools; pre-sanitizer diagnostic `vol_pstree` output is 15,359 bytes with SHA-256 `031CA68A8AAC1985967CF7820142432E06E366E42069D9C055AFFF37376B3EFE`; custody matches | Add accepted-output path sanitization and rerun the authoritative batch |
| 2026-07-14 21:51 | Preserved and corrected the real large-output netscan failure | Initial parallel psscan succeeded while netscan honestly exceeded the old 2,000,000-byte transport; fix adds 16,000,000-byte hard transport, recursive local-path sanitization, full accepted retention, and explicit 65,536-byte model view; rerun `gate-a-netscan-20260715T014947Z` returned 19,685 records/3,961,843 bytes with retained SHA-256, `E001`, no private path, and custody match | Keep failure diagnostic and corrected rerun together in freeze evidence |
| 2026-07-14 21:51 | Completed the authoritative post-sanitizer process batch and full checkpoint verification | `gate-a-final-20260715T015251Z`, 5,968 ms: pstree 40 records/15,277 bytes/SHA-256 `e2e70d5164939f5a735c450ecc0f2c268e48f22ae4a4dab76a92fa67f04ecac6`; psscan 72 records/16,526 bytes/SHA-256 `836951c95fdcc131064b52cfc229bb3753e389567fcb534174ac3f40d14a7fe4`; both `E001`, no private path, custody match; 127 tests plus Ruff/format/pip/build/diff green | Commit fixes/docs, publish remote, then publish full freeze |
| 2026-07-14 22:06 | Closed the final private-worker error-path leak and fixed the Build Week primary scope | Case-insensitive recursive path scrub now covers success values and exception strings; subprocess regression raises current suite to 128 tests; current source count is 14 modules/8,779 total/7,889 nonblank lines; Windows memory-only is the final primary and paired disk is future work | Run the final verification, commit this checkpoint, publish remote, then publish the full freeze |
| 2026-07-14 22:19 | Bound the real Gate A hardening in Git and completed the final strategy/doc verification | Commit `6e696a08a9aaeaa345638239e5182ec24826724d`; 128 tests, Ruff, format, both-environment `pip check`, wheel, sdist, Volatility help, 25/5 catalog, diff, links, fences, heading spacing, privacy, evidence, and no-em-dash scans green; exact C4 byte limits, two-axis metrics, evaluator authorship, gate names, and memory-only scope reconciled | Publish unchanged history and complete C4 |
| 2026-07-14 22:22 | Refreshed the independent lock-check environment against Gate A commit `6e696a0` | The stale installed project correctly failed the two new worker-privacy regressions; reinstalling the current constrained editable package restored 128 passing tests, clean `pip check`, Ruff, and format. No source fix was required | Preserve this as evidence that the second environment detects stale installs; publish unchanged history |
| 2026-07-14 22:24 | Committed the synchronized winner strategy, handover, provenance, README, and environment record | Commit `207a039836cdaf3045e92a2b74e541a7dd2be77f`; public rules/API references, exact Gate A receipts, Windows memory-only scope, two-axis scoring, evaluator authorship, and all remaining red gates are aligned | Create and anonymously verify the public remote, then complete and publish C4 |

## Single next action

Create and verify the public remote without rewriting history. Finish and publish the
preregistration/freeze with server-timestamped digests. Only after that public
freeze may DC01 be exposed to GPT-5.6 for the first valid post-freeze primary
run. No viewer, video, or prose polish outranks this sequence.
