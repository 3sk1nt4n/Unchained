# Unchained — OpenAI Build Week submission draft

> **Status:** DRAFT. This file is not evidence that the Devpost submission,
> public video, authentic COMPLETE bundle, comparison, or final tag exists.
> Replace every `PENDING` field only from a retained artifact produced by the
> frozen workflow.

Paste-ready form blocks live in [submission/DEVPOST-FORM.md](../submission/DEVPOST-FORM.md).

## Submission identity

| Field | Value |
|---|---|
| Project | Unchained |
| Track | Developer Tools |
| Repository | <https://github.com/3sk1nt4n/Unchained> |
| License | MIT |
| Submission commit/tag | PENDING — filled at final submission (see submission/SUBMISSION-CHECKLIST.md) |
| Public video under three minutes | PENDING — filled at final submission (see submission/SUBMISSION-CHECKLIST.md) |
| Public authentic viewer/bundle | PENDING — filled at final submission (see submission/SUBMISSION-CHECKLIST.md) |
| Majority-core `/feedback` Session ID | `019f61e5-5755-7a02-adb4-618d32baab27` — re-evaluate after final core work |
| Docker/README follow-up thread | `019f76f3-a19f-71d1-81b2-eed6305857f6` — thread provenance, not a feedback receipt unless submitted successfully |

The current Official Rules say Stage Two uses four equally weighted criteria:
Technological Implementation, Design, Potential Impact, and Quality of the
Idea. They also require a public repository or judge-shared private repository,
a public YouTube demonstration shorter than three minutes, a majority-core
`/feedback` Session ID, and a no-rebuild test path for Developer Tools. The
[current Official Rules](https://openai.devpost.com/rules) control if this draft
ever conflicts with them.

## One-line pitch

GPT-5.6 chooses where to look; deterministic code controls what may run and
verifies exactly what was executed and cited.

## Short description

Unchained is a bounded autonomous Digital Forensics & Incident Response (DFIR)
investigator built with Codex and GPT-5.6. It profiles an evidence folder without a model call, establishes
SHA-256 custody, exposes only route-eligible typed read-only tools, and lets
GPT-5.6 choose an opening of up to twelve tools that code validates all-or-none and
executes concurrently. Later turns carry a compact visible ledger and allow one
typed action at a time. A strict typed `finish_investigation(status="DONE")`
forces structured findings, a fresh-context
reviewer may preserve or downgrade them, and deterministic code resolves exact
UTF-8 evidence spans, renders the authoritative report and inert viewer, seals a
content-addressed bundle, and verifies the complete lifecycle offline.

The differentiator is not that an LLM can call forensic tools. It is that model
strategy and evidence authority are separated clearly enough for a judge or
analyst to inspect. Receipts prove what ran, what output was retained, and what
exact text was cited. They do not pretend to prove forensic truth; a human still
owns interpretation and response.

## Stage One viability

- The project is a working Developer Tool for security and agentic workflows.
- GPT-5.6 is the strategic investigator and fresh-context reviewer.
- Codex implemented and reviewed the Build Week control plane, proof protocol,
  tests, Docker path, documentation, and submission workflow.
- A real GPT-5.6 Luna connectivity canary has been run with no evidence access.
- A real GPT-5.6 Sol opening selected six typed Volatility tools and executed all
  six against the public DC01 memory image (under the earlier six-tool opening
  cap; the opening now allows up to twelve); the next action was correctly
  capped, producing a verified `PARTIAL` bundle rather than a false `COMPLETE`
  result.
- The authentic COMPLETE findings/judge/report bundle remains `PENDING`.

## 1. Technological Implementation

### What is technically substantial

- Deterministic evidence discovery, content classification, OS/shape routing,
  public evidence IDs, initial/final SHA-256 custody, and fail-closed inventory.
- GPT-5.6 opening-book strategy with one-to-twelve strict typed calls; all-or-none
  validation, atomic cap reservation, and real concurrent execution.
- Stateless adaptive packets with a visible case ledger and one typed action per
  later turn.
- Required typed `DONE` v2, forced structured investigation serialization, and exact
  quote resolution against full content-addressed tool outputs.
- A fresh-context reviewer that can preserve or downgrade existing findings but
  cannot invent or upgrade them.
- Deterministically rendered findings, citations, report, inert viewer, manifest,
  usage/cost accounting, and independent offline lifecycle verification.
- A non-root, read-only Docker runtime with a no-network evidence service and an
  isolated one-request GPT-5.6 Terra connectivity service that has no evidence or
  proof-bundle mounts.

### Retained evidence

- Test target: current full suite, Ruff, formatting, `pip check`, sdist, and wheel.
- Authentic Luna receipt: `docs/runs/luna-canary-receipt.json`.
- Authentic capped Sol opening receipt:
  `docs/runs/sol-capped-dc01-opening.json`.
- Authentic COMPLETE Sol metrics: PENDING — filled at final submission (see submission/SUBMISSION-CHECKLIST.md).
- Frozen same-evidence comparison: PENDING — filled at final submission (see submission/SUBMISSION-CHECKLIST.md).

## 2. Design

The product experience is deliberately six commands, with a zero-key guided
front door before any evidence or provider action:

```text
sentinel onboard [evidence]
sentinel doctor
sentinel profile <evidence>
sentinel run <evidence>
sentinel verify <bundle>
sentinel view <bundle>
```

The README gives three safe paths: no-key Docker profiling, a cheap Terra
connectivity check, and the real Sol proof path. Operators see route/readiness,
public evidence IDs, selected opening tools, receipts, finding/reviewer
transitions, the bundle path, and exact verify/view commands. Judges can inspect
the final static viewer without a server, evidence image, API key, or rebuild.

Design does not hide limitations. Connectivity smoke is visually and
technically separated from forensic qualification; capped runs say `PARTIAL`;
unready evidence says `INVALID`; and strict COMPLETE verification refuses both.

### Design proof still required

- Manual Chrome/Edge and Firefox inspection at desktop and narrow widths.
- Screenshot and public URL from the authentic COMPLETE viewer.
- Video recorded from that retained bundle, not a synthetic fixture.

## 3. Potential Impact

Security teams increasingly want autonomous investigation without surrendering
evidence control to persuasive model prose. Unchained targets DFIR analysts,
incident responders, forensic-tool developers, and builders of regulated or
high-consequence agents.

The architecture generalizes beyond forensics:

```text
model chooses bounded strategy
  -> code validates and executes typed authority
  -> exact outputs and citations are retained
  -> a monotonic reviewer reduces claims
  -> deterministic code renders and verifies the deliverable
```

That pattern can improve the auditability of agents used for security testing,
compliance review, operations, and other workflows where a transcript alone is
not enough. The specific impact claim is inspectable autonomy, not automated
ground truth.

## 4. Quality of the Idea

Most agent demonstrations emphasize what the model is allowed to do. Unchained's
novelty is making the forbidden authority equally visible: GPT-5.6 chooses what
to inspect and interprets observations, while code owns evidence identity,
legality, caps, execution, exact citation spans, verdict monotonicity, report
rows, and verification.

The concept is memorable in one sentence:

> Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a
> bounded investigation whose actions, citations, custody, and final report can
> be checked independently.

No comparative claim is made today: the same-evidence Qwen benchmark was
deliberately cut, and faster, cheaper, and more accurate claims remain blocked
until the frozen same-evidence table is published. What Unchained offers now is
an execution, custody, citation, report, and offline-verification contract that
a judge can inspect directly.

## How Codex contributed

Codex accelerated the Build Week implementation and adversarial review of the
evidence lifecycle, Responses API adapter, typed execution boundary, caps,
retry/usage accounting, typed-DONE-v2 protocol, forced serializer, exact evidence
spans, fresh-context downgrade-only review, report/viewer renderers, independent
verifier, CLI, Docker isolation, tests, benchmark design, and documentation.

The human owner chose the product thesis, Developer Tools track, DFIR testbed,
evidence case, authority split, benchmark, scope cuts, claim language, and final
submission decisions. The dated boundary between prior MIT-licensed Qwen tool
substrate and new Build Week work is in `BUILD_PROVENANCE.md`.

## Judge test path without rebuilding

No key and no spend:

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git
cd Unchained
docker compose build
docker compose run --rm offline
docker compose run --rm offline profile /evidence --json
```

Authentic retained proof after Task 3:

```powershell
sentinel verify <COMPLETE_BUNDLE> --require-complete --require-live-gpt56
python scripts/check_viewer.py <COMPLETE_BUNDLE> --require-complete --require-live-gpt56
sentinel view <COMPLETE_BUNDLE>
```

The submitted test path must replace `<COMPLETE_BUNDLE>` with a judge-accessible
artifact or explicit hosted instructions before the deadline.

## Claims ledger

| Claim | Current allowed status |
|---|---|
| Luna connectivity and strict typed call | DEMONSTRATED through a second-reviewer-attested (project-affiliated) sanitized receipt |
| Live GPT-5.6 Sol opening on real DC01 memory | DEMONSTRATED as a capped `PARTIAL`; six tools succeeded |
| Custody and ordinary bundle verification for capped run | VERIFIED from the retained local bundle |
| Findings, fresh reviewer, deterministic COMPLETE report | PENDING authentic COMPLETE run |
| Faster/cheaper/more accurate than Qwen | PENDING frozen same-evidence comparison |
| Offline verifier authenticates OpenAI | FORBIDDEN; it validates recorded metadata only |
| Exact citations prove forensic truth | FORBIDDEN; they prove traceability only |
| Docker supports privileged E01/FUSE parity | FORBIDDEN |

## Final submission checklist

- [ ] Authentic COMPLETE GPT-5.6 Sol bundle passes both strict flags.
- [ ] Sanitized COMPLETE metrics are committed.
- [ ] Benchmark freeze gate passes and reference facts are sealed.
- [ ] Same-evidence Qwen comparison is committed without cherry-picking.
- [ ] Automated viewer QA passes on the COMPLETE bundle.
- [ ] Manual cross-browser and narrow-width QA passes.
- [ ] Public YouTube video is shorter than three minutes and has clear audio.
- [ ] Repository or private-sharing requirement is satisfied through judging.
- [ ] Judge can test without rebuilding from scratch.
- [ ] Majority-core `/feedback` Session ID is final and accurate.
- [ ] Prior-vs-new Build Week boundary is prominent.
- [ ] Final image digest, OCI revision, commit, and tag agree.
- [ ] Devpost submission confirmation is retained.
