# Unchained - OpenAI Build Week Living Handover

This file is the execution-status source of truth for the OpenAI Build Week
submission. It records verified rules, current proof state, delivery gates,
risks, and the next-session startup procedure.

Priority, sequence, positioning, preregistration, and go/no-go logic are in
[docs/WINNER_ROADMAP.md](docs/WINNER_ROADMAP.md). The detailed product strategy,
experiment, proof contract, prompts, judge path, and submission doctrine are in
[docs/HACKATHON_MASTER_PLAN.md](docs/HACKATHON_MASTER_PLAN.md). The judge-first
product path is in [README.md](README.md), the comprehensive published-release
record is in
[docs/OPENAI_VNEXT_RELEASE_HANDOFF.md](docs/OPENAI_VNEXT_RELEASE_HANDOFF.md), and
durable technical decisions remain in [DECISIONS.md](DECISIONS.md). Those files
describe what the system is intended to do. This handover records what is
implemented, what has been verified, what has been demonstrated to a judge, and
what is still missing.

> **Update requirement:** every material implementation, verification, artifact,
> scope, schedule, or submission-status change must update this file in the same
> work session. Never mark an item complete merely because corresponding code
> exists.

---

## 2026-07-20 ~01:40 ET — 5-agent win-path audit and the WINNER ACTION PLAN

This section is the controlling execution plan for the final ~42 hours. It was
produced by a 5-agent parallel audit (live-rules corroboration on three official
pages, a full repo readiness audit, a live test run, an independent judge
simulation, and a critical-path synthesis), then reconciled with
[docs/HONEST-WIN-ASSESSMENT.md](docs/HONEST-WIN-ASSESSMENT.md). It supersedes
the ordering of section E below and the recording gate in
`docs/DEMO-SCRIPT.md:3-6`. Labels: PROVEN / VERIFIED / INFERRED / GUESSING,
used literally.

### A0. What this audit PROVED (ran on this host, 2026-07-20 ~01:30 ET)

- **404/404 tests pass in 25.11s, ruff check + format clean, `sentinel --help`
  renders correctly** (`.venv` CPython 3.11.9). PROVEN.
- **Live rules re-verified on all three official pages** (rules, FAQ, overview):
  deadline Tue 2026-07-21 17:00 PT confirmed; video safest read is **strictly
  under 3:00**; **AI narration is explicitly allowed** ("A screencast with
  background music won't cut it" — audio must explain Codex use and what
  GPT-5.6 is doing); free-Codex-credit request window is already closed
  (passed 2026-07-17). VERIFIED.
- **Bundle census: 19 run bundles, 0 COMPLETE** (12 PARTIAL / 7 INVALID by
  summary.json iteration). VERIFIED.
- **The load-bearing proof asset already exists**: authentic
  `unchained-runs/20260719T020118Z-ede6c445` — `gpt-5.6-sol` returned on 2
  responses, 6/6 opening tools on real DC01 memory, custody match, offline
  `sentinel verify` **VALID**, honestly terminal PARTIAL at MAX_TOOL_CALLS;
  sanitized receipt committed at `docs/runs/sol-capped-dc01-opening.json`.
  VERIFIED. **Consequence: an honest video can show real GPT-5.6 work today,
  with zero new spend. Stage One is passable without a new live run.**
- DC01 was already exposed to Sol pre-freeze (the 07-19 capped opening), so the
  "untouched preregistration" claim stays retired and the freeze gate no longer
  blocks anything. VERIFIED against `docs/WINNER_ROADMAP.md` section 3.
- `docs/SUBMISSION.md` is a real Devpost draft but stale: line 40 still says
  "up to six tools" (runtime now allows twelve) and lines 3-6/92-93 carry
  PENDING placeholders. VERIFIED.

### A1. Independent judge simulation (equal-weight criteria, harsh)

| Scenario | Tech | Design | Impact | Idea | Stage One |
|---|---|---|---|---|---|
| As-is (no video, no COMPLETE run) | 6 | 5 | 6 | 8 | **FAIL — no video** |
| Video + authentic COMPLETE run + benchmark | 8 | 7 | 7 | 8 | PASS |

Win-probability estimates are GUESSING, stated as ranges: this audit's critic
puts top-2 in Developer Tools at **~0%** with no video, **1–3%** with video but
no COMPLETE run, **3–7%** with both. `docs/HONEST-WIN-ASSESSMENT.md` argues
**12–18%** conditional on a strong video. The difference is field-size
assumptions, not facts; both agree on the same ordering of moves. The critic's
controlling directive: **the video is worth more than the run — never trade
video time for run retries.**

### A2. WINNER ACTION PLAN (all times ET; owner in bold when human-only)

| # | Action | Owner | Target window | Latest safe start | State |
|---|---|---|---|---|---|
| W1 | Refresh `docs/SUBMISSION.md`: fix six→twelve (line 40), strip/fill PENDING placeholders, produce paste-ready Devpost blocks | agent | Mon early | Mon 18:00 | PENDING |
| W2 | Final video script + exact shot list from `docs/DEMO-SCRIPT.md`, overriding its COMPLETE-only recording gate; leave a 20s splice slot for a COMPLETE run | agent | Mon early | Mon 20:00 | PENDING |
| W3 | Pre-position 429/cap mitigations: serializer packet chunking (<~150k tokens/request), documented `MAX_TOTAL_TOKENS` raise, bounded backoff; offline dry-run | agent | Mon early | Mon 10:00 (before any live attempt) | PENDING |
| W4 | OpenAI billing: add credit, confirm real TPM tier | **HUMAN** | Mon 08:30–09:30 | Mon 12:00 | PENDING — ceiling path only |
| W5 | Authentic COMPLETE run attempts on DC01 + strict verify (`--require-complete --require-live-gpt56`) | **HUMAN** key, agent drives | Mon 10:00–16:00 | **HARD ABANDON GATE Mon 16:00** | PENDING — optional ceiling |
| W6 | Benchmark comparison vs open-weight baseline | agent | Mon 14:00–15:30 | Only if W5 COMPLETE by 14:00, else first cut | PENDING |
| W7 | Record video, **strictly under 3:00**, audio names Codex + GPT-5.6 (AI narration allowed). Plan A: splice COMPLETE verify. Plan B: `ede6c445` authentic receipt → offline verify VALID → $0 no-key lane → Codex build story | **HUMAN** (voice) or AI narration; agent preps scenes | Mon 17:00–21:00 | Tue 08:00 (emergency slot) | PENDING — **the only mandatory gap** |
| W8 | YouTube upload public + incognito playback QA (<3:00 runtime, audio audible) | **HUMAN** | Mon 21:00–22:00 | Tue 11:30 | PENDING |
| W9 | Final README/SUBMISSION sync with real artifact IDs, submission tag, push; re-verify repo is live-public (last checked 07-14) | agent | Mon 22:00–23:00 | Tue 09:00 | PENDING |
| W10 | `/feedback` re-run from majority-core Codex thread; if new ID, update all 8 referencing files | **HUMAN** in Codex | Tue 07:00–07:30 | Tue 12:00 — fallback: existing ID stands | PENDING |
| W11 | Devpost form: track = Developer Tools, description, repo URL, video URL, Session ID, install/platform/test-method extras. **SUBMIT Tue ~11:00, hard floor Tue 14:00.** Screenshot confirmation | **HUMAN** submits, agent drafts | Tue 07:30–11:00 | Tue 14:00 | PENDING |

Coordination rule: two Claude sessions have committed to this repo tonight.
**One executor per file**; every session pulls before editing and records its
work here in the same session.

### A3. Kill risks and pre-positioned mitigations

1. **No public video by deadline = automatic fail.** Mitigation: W7 is
   unconditional and independent of W5's outcome; W2 finishes the script hours
   earlier; AI narration removes voiceover as a blocker; Tue 08:00 emergency
   re-record slot.
2. **TPM/billing not fixable in time; run retries eat the window.** The 429 at
   ~271k tokens vs 200k TPM already happened. Mitigation: W3 lands before any
   live attempt; hard abandon gate Mon 16:00; Plan B video and Devpost copy
   stand without a COMPLETE bundle.
3. **End-stage logistics: form left in draft, video private/processing, ID
   mismatch, repo flipped private.** Mitigation: submit ~9h early, incognito QA
   of every link from the Devpost preview, W9 re-verifies public visibility,
   confirmation screenshot, W10 fallback ID already recorded in 8 files.

### A4. Cut list (top-down when behind) and never-cut

Cut in order: (1) W6 benchmark — and delete every unmeasured "faster/better
than Qwen" phrase from judge-facing copy; an unmeasured claim is a liability;
(2) rubric freeze / Gate B (already moot); (3) hosted HTTPS viewer + QA;
(4) W5 the COMPLETE run itself; (5) W10 `/feedback` refresh (existing ID
stands); (6) SUBMISSION.md polish beyond the six→twelve fix and placeholders.

**Never cut:** the public sub-3:00 YouTube video with audio naming Codex and
GPT-5.6; public MIT repo; README Codex disclosure; the fully submitted Devpost
form with track, Session ID, install instructions, platforms, and the no-key
test path.

### A5. Copy directive for everything judge-facing

Lead with the one-line pitch and the $0 sixty-second judge lane; move the
PARTIAL/pending/attested tables below the fold. The judge simulation found the
radical honesty reads as "unfinished" to a skimming judge. The honesty stays;
the ordering changes.

---

## 2026-07-20 session — one-command UX overhaul, honest cross-OS audit, and the path to win

This section is the honest, deep record of the 2026-07-20 session. It supersedes
older UX notes below where they conflict. Verification levels are labeled
literally:

- **PROVEN** — I ran it on this Windows host and saw the output.
- **CODE-FIXED** — edited and covered by the unit suite (404 tests) or a direct
  Python check, but NOT run through the full interactive path end-to-end.
- **STATIC-ONLY** — read and reasoned about; NOT executed. All Linux/macOS/Docker
  claims are STATIC-ONLY — there is no Linux or macOS host in this environment.
- **PENDING** — not done.

### A. What shipped this session (all on `main`, commits `ecc2f75`…`4e53e3b`)

1. **One command runs a whole case.** Bare `sentinel` on a terminal self-drives:
   welcome → one question (evidence path) → local `$0` SHA-256 case card → depth
   pick (1/2) → **visible** key step → exact phrase `LAUNCH GPT-5.6 SOL` → live
   run → verify/view. No `--launch`, no `--caps`, no `$env:` juggling. Covered by
   `tests/test_guided.py`. **CODE-FIXED** (interactive path pieces PROVEN
   individually; full TTY walk not scripted).
2. **Two commands per OS, clone-first.** Windows: `git clone …; cd Unchained` →
   `.\setup.ps1` → `.\unchained.ps1` (or `sentinel`). Linux: `./setup.sh` →
   `./unchained.sh`. Docs, `unchained.ps1`, `setup.sh`, `unchained.sh` all added.
3. **Location-independent install (the "install anywhere, works anywhere"
   requirement).** `setup.ps1`/`setup.sh` now install **non-editable**
   (`pip install .[dev]`, not `-e`), so the package is copied into the isolated
   venv and `sentinel` keeps working if the clone is moved or deleted.
   **PROVEN**: `sentinel` runs from an unrelated directory, no `__editable__`
   `.pth` remains, `import unchained` resolves to the venv copy.
4. **Fast install.** `setup.ps1` default is now a health check (import + CLI
   smoke), not the full 404-test dev suite; the heavy gate is `-FullTest`;
   `-Check` re-verifies; pip output is quiet; PS installers force UTF-8 so the
   banners render on legacy code pages. **PROVEN** (`-Check` run).
5. **Docs harmonized and simplified.** README/START-HERE/JUDGE-QUICKSTART share
   an OS-logo header + nav; the multi-step `sentinel onboard … --launch --caps`
   walkthroughs are gone from the start paths; two inline CLI screenshots removed;
   test counts corrected to **404**; macOS honestly labeled "via Docker."
6. **Benchmark time-bomb fixed.** `tests/test_benchmark_compare.py` pinned the
   freeze tag to a fixed date so the 5 comparison tests are deterministic
   regardless of the system clock. **PROVEN** (35/35 pass).
7. **Honest demo.** `demo.ps1` now seals and verifies exactly this run's fresh
   fail-closed bundle (diffs the run dir), zero OpenAI calls. **PROVEN**
   end-to-end (`DEMO PASSED … VALID`, exit 0).

### B. The 4-way honest audit and its fixes

I ran four parallel auditors (Windows scripts, Linux/macOS+Docker, CLI runtime,
docs) against the current design. Verified defects fixed this session:

| Severity | Defect | Fix | State |
|---|---|---|---|
| **CRITICAL** | `get.ps1` key check `-match "Key configured"` was case-insensitive, so `"No key configured"` matched → the hidden key paste was skipped and the run dead-ended at launch (this is exactly the "I never saw the key step" report) | match `"Key configured via"` | CODE-FIXED |
| HIGH | Launch box said `STRICT`/`DEFAULT` while the flow said `LIGHT`/`HEAVY` | use the LIGHT/HEAVY label | PROVEN (box render) |
| HIGH | `get.ps1` silently set `MAX_TOTAL_TOKENS=3000000`/`MAX_COST_USD=30`, so a "LIGHT $2.50" run showed a `$30/3M` ceiling | dropped the override → honest ceilings | CODE-FIXED |
| HIGH | Hardcoded "GPT-5.6 Sol" appeared during a Luna rehearsal (welcome banner, depth line, onboard success line, launch box) | use `active_model_label()` / drop literal "Sol" | PROVEN (confirm box) |
| HIGH | Guided card printed a pre-choice "HARD CEILINGS" number that went stale after the depth pick | suppressed in guided mode | CODE-FIXED |
| MEDIUM | Interactive prompts used em-dash/middle-dot via bare `print`/`input` → `UnicodeEncodeError` crash risk on cp437/850 consoles | ASCII-only in `cli.py`; PS installers force UTF-8 | CODE-FIXED |
| MEDIUM | `setup.sh` never `cd`-ed into the repo → installed the wrong dir when run from elsewhere; no git guard | added `cd "$REPO_DIR"` + git check | STATIC-ONLY |
| MEDIUM | The "HOW DO YOU WANT TO RUN?" box spilled (double-width emoji) | no right border on emoji lines | CODE-FIXED |
| MEDIUM | `demo.ps1` could print "DEMO PASSED … VALID" against a stale bundle | verify exactly the new run dir | PROVEN |
| LOW-MED | `setup.ps1` READY box off by one column; prereq only checked `py`, not 3.11 | realigned; added `py -3.11` probe | PROVEN (parse + measure) |
| LOW | `get.sh` overstated "walk into your case" (it is Docker-only) | honest banner | STATIC-ONLY |

### C. Honest state matrix

| Path | Level | Note |
|---|---|---|
| Windows two-command install, location independence, `$0` card, `demo.ps1`, confirm box | **PROVEN** | ran on this host |
| `get.ps1` one-liner key gate + launch | **CODE-FIXED** | logic fixed; not run interactively end-to-end |
| Bare `sentinel` full guided TTY walk to a live run | **CODE-FIXED** | pieces PROVEN; full TTY not scripted |
| Linux/macOS `setup.sh`/`unchained.sh`/`get.sh` + Docker offline | **STATIC-ONLY** | no Linux/macOS host here; not executed |
| **Authentic COMPLETE GPT-5.6 Sol bundle** | **PENDING** | the qualifying proof does not exist yet |
| Same-evidence benchmark vs the open-weight baseline | **PENDING** | harness exists; no frozen real run |
| Demo video | **PENDING** | |

### D. Known-remaining backlog (honest, not yet fixed)

1. **Split EWF disk (`.E01` + `.E02` …) is counted as two disks** and false-blocks
   as "more than one ready disk." Every segment carries the EWF magic, so
   `assess_profile` sees two. Fix = group `.Exx` siblings as one logical disk
   BEFORE the readiness count. **Deferred deliberately**: it is proof-critical
   evidence-model code and must be validated against a real split image, which I
   do not have here. (A memory+disk *pair* is handled correctly; a disk-zip
   alongside a memory-zip is set aside because archives are intentionally not
   unpacked — that is by design, not this bug.)
2. **No Linux dependency lock.** Only `constraints.windows-amd64-cp311.txt` exists
   (it even pins `pywin32`, unusable on Linux). Linux installs float transitive
   deps and `capture_environment` emits null lock-hash fields on Linux → weaker,
   platform-divergent provenance.
3. **Non-editable provenance gap.** `capture_environment` uses
   `Path(__file__).resolve().parents[2]`; in a non-editable install that resolves
   into the venv (no `.git`), so `git_commit` is null on Windows (venv is outside
   the repo) and differs on Linux (venv inside the repo). Graceful (`None`), but
   the bundle carries less provenance than a dev checkout.
4. **The pinned `sift-sentinel` git dependency is a single point of failure** for
   every *build* lane (Windows install, Linux install, `docker build`). The
   offline *runtime* container is unaffected (wheels-only, `--no-index`). This is
   the intentional benchmark/prior-work dependency and must stay public and
   reachable.
5. **`get.sh` is Docker-only** and shallower than `get.ps1` (no native install,
   case pick, or launch). Relabeled honestly this session; not feature-matched.
6. Minor/cosmetic: redundant banners across get.ps1 → setup.ps1 → onboard;
   `run.ps1` does not check the child `setup.ps1` exit code; step-count labels
   differ across scripts (`[x/4]` vs `[x/5]` vs `[x/6]`); "tools" vs "calls"
   wording drift on the card.

### E. Next steps to WIN — prioritized and honest

> **Correction (rules-grounded, 2026-07-20):** a full honest scoring against the
> official rules is in [docs/HONEST-WIN-ASSESSMENT.md](docs/HONEST-WIN-ASSESSMENT.md).
> It corrects an earlier overstatement in our own notes: per the rules, the
> **mandatory** gate is the **demo video (< 3 min, audio, shows Codex + GPT-5.6)**
> plus the testable no-key path, the Codex Session ID, and install instructions —
> **NOT** an authentic COMPLETE run. The demo video is the true blocker; the
> COMPLETE Sol bundle raises the ceiling but is optional. Honest win estimate:
> **~12–18%** for a 1st/2nd in Developer Tools *if* a strong video ships and the
> no-key judge path is smooth; **~0%** without the video. Record the video FIRST.

The COMPLETE run below is high-value but, per the rules, secondary to the video.

1. **Produce ONE authentic COMPLETE GPT-5.6 Sol bundle** on a real Windows memory
   image and verify it strictly:
   `sentinel verify <bundle> --require-complete --require-live-gpt56` → VALID.
   Known blockers, all real:
   - **OpenAI account TPM tier.** The forced serializer packet was ~271k tokens
     against a new-account 200k TPM limit → HTTP 429. Add credit / complete
     billing verification to raise TPM before the run.
   - **Token headroom.** The full lifecycle can exceed the 400k HEAVY cap during
     serialization. Run HEAVY and, if needed, deliberately raise
     `MAX_TOTAL_TOKENS` (documented) — this is an honest operator choice, not a
     silent override.
   - **Real evidence.** Use the public DFIR Madness memory image (never committed).
   - Disclose the run; update section C to PROVEN and attach the bundle path.
2. **Freeze the benchmark rubric BEFORE the run**, then run the same case on the
   OpenAI vNext and record numerator/denominator/source for every metric. The
   comparison harness and freeze gate already exist and are tested.
3. **Record the demo video** of the one-command flow to a VALID bundle.
4. **Assemble the DevPost submission**: writeup, the Codex session ID
   (`019f61e5-5755-7a02-adb4-618d32baab27` — re-confirm the final one), the repo
   link, and the proof bundle.
5. **Optional hardening if time allows** (in value order): run the Linux/Docker
   lane on a real host to lift it from STATIC-ONLY; implement the EWF-segment
   grouping against a real split image; add a Linux dependency lock.

### F. Immediate re-run instruction for the operator

Your installed `sentinel` (venv under `%LOCALAPPDATA%`) was refreshed to the
current code this session and is now location-independent. To see the fixed
flow: open a fresh terminal and run `sentinel`. If you use the one-liner,
`get.ps1` now reaches the key paste step correctly on a keyless machine.

### G. Handover review corrections (2026-07-20, full-document pass)

A top-to-bottom review of this document against the repo at `4e53e3b` found and
fixed the following in the CURRENT-state sections (historical checkpoint tables
below are deliberately unchanged — they describe their named timestamps):

1. Document control refreshed: rules re-verified 2026-07-20 (not 07-14), repo
   at `4e53e3b`, time remaining ~42 hours at 2026-07-20 05:36 UTC.
2. Codebase map corrected: the opening is up to **twelve** typed calls
   (raised 2026-07-20; the six-call texts in the 2026-07-18/19 checkpoint
   sections are true historical records of the older cap). Added the three
   modules the map was missing (`viewer_policy.py`, `onboarding.py`,
   `console.py`).
3. **Superseding size/quality baseline (2026-07-20):** 19 source modules,
   **404 tests across 24 test files**, ruff check + format clean. The
   "17 modules / 267 tests / 32 files" figures below are the 2026-07-18
   checkpoint, retained as history.
4. **Superseded guidance:** the proof-ledger row "Demo video … Record only
   after genuine run" predates the rules-grounded correction in section E. A
   genuine retained Sol run already exists (capped opening, terminal `PARTIAL`,
   offline `VALID`) and is legitimate video material with its honest label; do
   NOT hold the video for a `COMPLETE` run. The video is the mandatory gate.
5. Link check: every relative link in this document resolves at `4e53e3b`
   (roadmap, master plan, release handoff, DECISIONS, win assessment,
   provenance, judge quickstart).

---

## Document control

| Field | Current value |
|---|---|
| Last live-rule verification | 2026-07-20, direct fetch of the live Official Rules (judging criteria, mandatory submission items, dates, prizes); grounded in [docs/HONEST-WIN-ASSESSMENT.md](docs/HONEST-WIN-ASSESSMENT.md) |
| Last repository verification | 2026-07-20, `main` at `4e53e3b`; one-command UX overhaul + a 4-way honest cross-OS audit and its fixes + the rules-grounded win assessment; 404-test suite green + ruff clean locally on Windows |
| Current event day | Submission Day 8 (2026-07-20 UTC; 2026-07-19 evening PT) |
| Hard deadline | 2026-07-21 17:00 PT / 20:00 ET |
| Time remaining at 2026-07-20 05:36 UTC | Approximately 42 hours |
| Internal submission deadline | 2026-07-20 PT; July 21 is emergency buffer only. **The mandatory gate is the demo video** (see the rules-grounded correction in section E) |
| Selected track | Developer Tools |
| Current decision | **GO, video-first: execute the WINNER ACTION PLAN (section A2 at top). COMPLETE run is optional ceiling with a hard abandon gate Mon 16:00 ET; registry alternative parked** |
| Flagship-run readiness | **OPTIONAL CEILING per winner plan: authentic capped-PARTIAL Sol bundle `ede6c445` exists and verifies VALID; a COMPLETE run still needs credentials + TPM headroom (W3-W5) and is cut list item 4, not a submission gate** |
| Submission readiness | **NOT READY — video (W7/W8) and Devpost form (W11) outstanding; every other required material is READY or PARTIAL per the 2026-07-20 readiness audit** |
| Retained successful `/feedback` Session ID | `019f61e5-5755-7a02-adb4-618d32baab27` |
| Current Docker/README follow-up thread ID | `019f76f3-a19f-71d1-81b2-eed6305857f6` — not yet a successful `/feedback` receipt |

The local screenshot supporting that ID is outside this repository in the
workspace parent under the filename
`WhatsApp Image 2026-07-14 at 6.30.49 PM.jpeg`.
It is 124,837 bytes with SHA-256
`F013EFDD5DD5C7D8698B378DA88760E8CCB34557BBE85E18979F7C196423B844`, and it
visibly shows the valid ID above. This is local provenance only. It is not
committed, hosted, or judge-accessible. After final core work, the final
successful `/feedback` must be run from the true majority-core Codex thread;
do not assume this earlier ID remains the final submission ID. The current
Docker/README follow-up thread ID is recorded separately so it cannot be
mistaken for a successful upload.

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

Proceed conditionally with Unchained for Build Week. Do not pivot to a
new dynamic model-registry project now. Unchained is no longer a from-scratch
concept: it is a substantial controller prototype with 17 source modules, an
independently verified proof protocol, 274 passing tests after the Docker/Luna
canary follow-up, clean lint and formatting, a buildable package path, and a
verified CPython 3.11.9 Linux container environment,
exact dependency records, and a verified Codex feedback thread. The
OpenAI-native vNext adds stateless model packets, exact evidence spans,
evidence-bound receipts, lifecycle-complete verification, deterministic reports,
a static proof viewer, and a user-facing CLI. The winner story and experiment are now
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
security. Unchained fits that track. The live rules list a $15,000
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

The current strategy remains one polished Build Week Unchained entry. That is a
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
Unchained is a controlled GPT-5.6 autonomy experiment built on a pinned,
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
- Required typed `finish_investigation({"status":"DONE"})` plus forced
  structured serialization; historical literal-DONE-v1 remains verifier-readable.
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
    -> GPT-5.6 opening selection (all-or-none, up to twelve since 2026-07-20; historically six) and adaptive investigator loop
    -> strict typed DONE and forced investigation serialization
    -> deterministic exact evidence-span resolution
    -> fresh downgrade-only judge over those spans
    -> strict report draft and deterministic rendering
    -> cleanup and deterministic post-run custody verification
    -> sealed report.md + viewer.html + audit/profile/summary/manifest
```

| Module | Responsibility |
|---|---|
| `src/unchained/cli.py` | Configuration, run directory, lifecycle, statuses, cleanup, final custody |
| `src/unchained/evidence.py` | Inventory, content classification, OS/shape routing, hashes, mounts, readiness probes |
| `src/unchained/tools.py` | Typed tool schemas, allowlisting, caps, execution, receipts |
| `src/unchained/_tool_worker.py` | Fixed private-worker dispatch for approved forensic functions |
| `src/unchained/model.py` | OpenAI Responses adapter, phase-specific wire options, usage validation |
| `src/unchained/agent.py` | Opening book, stateless ledger loop, serialization, span resolution, judge, structured report draft |
| `src/unchained/reporting.py` | Deterministic authoritative Markdown rendering and hostile-prose defanging |
| `src/unchained/viewer.py` | Deterministic inert static proof viewer |
| `src/unchained/viewer_policy.py` | Independent positive inert-HTML/CSP policy check for the viewer |
| `src/unchained/onboarding.py` | Guided welcome, verified case card, depth choice, and honest model labels |
| `src/unchained/console.py` | Dependency-free 256-color console theme with encoding-safe fallback |
| `src/unchained/audit.py` | Single-writer hash-chained event log and output receipts |
| `src/unchained/artifacts.py` | Atomic summary, environment record, allowlisted manifest, and detached manifest digest |
| `src/unchained/caps.py` | Atomic tool/token/time/cost enforcement and cost estimates |
| `src/unchained/models.py` | Typed domain records and schemas |
| `src/unchained/prompts.py` | Project-owned authoritative investigator prompt |
| `src/unchained/verify.py` | Standard-library lifecycle, proof-bundle, evidence-binding, and exact-span verifier |
| `src/unchained/__main__.py` | Module CLI entry point |

## Current implementation and proof ledger

Verified on July 14, 2026 unless otherwise stated.

| Capability or artifact | State | Evidence | Next proof/action |
|---|---|---|---|
| Python package | IMPLEMENTED + VERIFIED | CPython 3.11.9 primary and independent lockcheck environments; `pip check` clean; wheel build passes | Retain transcript with final submission commit |
| CLI/controller | IMPLEMENTED + VERIFIED offline | 267 tests pass; `sentinel doctor/profile/run/verify/view` CLI tests | Genuine run artifact |
| Opening parallel tools | IMPLEMENTED + VERIFIED offline | The opening is accepted all-or-none; a `COMPLETE` lifecycle has 1–6 distinct valid calls and zero rejected calls | Authentic audit trace |
| Typed `DONE` v2 protocol | IMPLEMENTED + VERIFIED offline | Required-action/schema/controller/verifier tests | Authentic COMPLETE trace |
| Typed/no-shell authority | IMPLEMENTED + VERIFIED offline | Schema and worker tests | Native forensic demo |
| Evidence inventory/custody | IMPLEMENTED + VERIFIED locally on real evidence | DC01 profile is Windows memory-only, ready, symbols ready; final custody matches | Publish only the non-evidence proof receipts after freeze |
| Hard caps | IMPLEMENTED + VERIFIED offline | Cap tests | Recorded `PARTIAL` demo |
| Downgrade-only judge | IMPLEMENTED + VERIFIED offline | Simulated preserve/downgrade lattice; exact content-addressed byte spans beyond 2,048 bytes; unknown findings rejected | Authentic model example plus external semantic scoring |
| Hash-chained audit | IMPLEMENTED + VERIFIED offline | Audit tests | Genuine retained audit |
| Provider-returned model identity | IMPLEMENTED + VERIFIED offline | Requested alias and provider-returned model, response/request IDs, status, and usage propagate through audit and bundle tests | Authentic provider receipts |
| Bounded audited retries | IMPLEMENTED + VERIFIED offline | Retry-aware request windows accept only bounded scheduled transient attempts followed by one accepted response and reject orphan/out-of-order retry events | Authentic response trace if a retry occurs |
| Report safety | IMPLEMENTED + VERIFIED offline | Strict draft references plus byte-exact deterministic report reconstruction; adversarial prose cannot change verdicts/citations | Authentic report artifact |
| Windows memory route | VERIFIED LOCALLY, NOT JUDGE-DEMONSTRATED | Real DC01 `windows.info` resolves; profile and symbols ready; sealed registry exposes 14 Windows tools; native rows and custody pass; code bound by `6e696a0` | Publish unchanged history, then authentic run only after C4 freeze |
| Windows fixed-console discovery and direct memory catalog | IMPLEMENTED + VERIFIED locally, COMMITTED | Active-interpreter-adjacent launcher and sanitized child `PATH`; Windows direct tools no longer depend on Linux/macOS dynamic mapping; 128 tests plus real smoke pass; commit `6e696a0` | Publish unchanged history and retain server timestamp |
| Linux/macOS routes | PARTIAL/EXPERIMENTAL | No end-to-end proof | Out of flagship scope |
| Full accepted tool-output retention | IMPLEMENTED + VERIFIED offline | Exact UTF-8 bytes are content-addressed before `tool.completed`; hashes, excerpts, and metadata are verified | Genuine retained native-tool outputs |
| Large native-output transport | IMPLEMENTED + VERIFIED locally, COMMITTED | Hard private-worker response limit increased from 2,000,000 to 16,000,000 bytes after an honestly retained `vol_netscan` overflow; successful 3,961,843-byte rerun; commit `6e696a0` | Preserve the pre-fix diagnostic and bind exact values in C4 |
| Bounded explicit model tool view | IMPLEMENTED + VERIFIED locally, COMMITTED | Full accepted output remains retained; provider input is capped at 65,536 UTF-8 bytes with accepted-output hash/size, prefix-character count, selection rule, and `model_view_complete=false`; commit `6e696a0` | Authenticate behavior only after the public freeze |
| Private evidence-path sanitization | IMPLEMENTED + VERIFIED locally, COMMITTED | Worker recursively strips runner-local evidence/mount paths from success values and exception strings, matches Windows path variants case-insensitively, and substitutes the sealed evidence ID; native receipts and the subprocess error-path regression contain no private path; commit `6e696a0` | Recheck the authentic bundle after the public freeze |
| Self-verifying proof bundle | IMPLEMENTED + VERIFIED for invalid path | Run `20260715T012818Z-0c60c234` verifies 4 artifacts and 8 audit entries, terminal `INVALID`, exit 2 | Authentic `COMPLETE` bundle from real evidence |
| Exact quote integrity | IMPLEMENTED + VERIFIED offline | Every finding/judge quote binds to a full-artifact SHA-256 and exact UTF-8 byte range; mutation and late-span regressions fail closed | Keep separate from semantic correctness under the frozen rubric |
| Public authentic run bundle | NOT STARTED | The retained empty-case bundle is invalid, unauthenticated, and incomplete | First valid post-freeze GPT-5.6 run |
| Corrected strategic master plan | VERIFIED + SAVED | `docs/HACKATHON_MASTER_PLAN.md`; rules/code/strategy/dataset audits | Keep synchronized when strategy or requirements change |
| Winner priority and sequencing overlay | VERIFIED + SAVED | `docs/WINNER_ROADMAP.md`; benchmark-leakage, adjudication, provenance, viewer, and C0-C7 red-team audit | Follow order; no GPT-5.6 DC01 call before public freeze |
| Static judge viewer | IMPLEMENTED + VERIFIED offline, NOT DEMONSTRATED | Required manifest-bound inert `viewer.html`; verifier reconstructs its exact bytes and applies a no-script/no-external-resource positive policy | Generate from and visually QA an authentic run; publish hosted path |
| Offline verifier | IMPLEMENTED + VERIFIED offline | Requires the complete phase lifecycle/root artifacts, canonical profile/custody binding, rebuilt summary, exact report/viewer bytes, evidence-bound receipts, exact spans, downgrade-only judge, locally recomputed usage cost, and terminal consistency | Verify a complete authentic bundle; add external authenticity layer |
| No-key viewer path | IMPLEMENTED + VERIFIED offline, NOT DEMONSTRATED | `sentinel view` reruns strict lifecycle verification whenever a bundle claims `COMPLETE` before opening sealed HTML | Publish an authentic retained bundle and hosted copy |
| Git provenance | VERIFIED PUBLICLY | Public `origin/main` matches local HEAD `3506d29`; GitHub metadata reports `visibility=public`; server-side commit record retained | Preserve unchanged history and bind the freeze digest |
| Build provenance document | IMPLEMENTED | `BUILD_PROVENANCE.md` records prior/new/Codex boundaries and local-timestamp limitation | Record baseline hash and public/freeze URLs when they exist |
| Public experiment preregistration | NOT STARTED | Protocol/rubric/scorer digest is not frozen or remotely timestamped | Complete after deterministic native smoke and before any GPT-5.6 DC01 call |
| Judge quickstart | IMPLEMENTED FOR CURRENT FLAGSHIP | `JUDGE-QUICKSTART.md` documents fresh Windows install, no-key verification, authentic run, host/evidence capability truth, architecture mapping, troubleshooting, and Qwen boundary review | Revalidate commands after the authentic bundle and add viewer URL |
| Demo video | NOT STARTED | No current-project video | Record only after genuine run |
| Devpost submission | NOT STARTED | No confirmation artifact | Draft early; submit July 20 |
| `/feedback` proof | VERIFIED + RETAINED LOCALLY | Current ID `019f61e5-5755-7a02-adb4-618d32baab27` is in project docs and screenshot | Final successful `/feedback` must come from the true majority-core thread after final core work |

### Verified size and quality baseline

The July 14 values elsewhere in this document remain historical checkpoints.
The superseding 2026-07-18 vNext working-tree baseline is:

- 17 source modules.
- 13,383 physical source lines, of which 12,259 are nonblank.
- 267 tests collected and passing in CPython 3.11.9.
- Ruff check and format check pass across 32 Python files.
- Wheel/sdist build and `pip check` are mandatory final gates; see the current
  checkpoint appended below for their exact outcome.
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
| Git repository | Public `main` base `2b256a7bfd170388d2a8497dd3289af248abae18`; this vNext release is published for review on `agent/openai-native-vnext`; no rewrite or force-push |
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
exact bypass. At the historical Gate A checkpoint, the full 128-test suite
passed. Authentic report output and an authentic-run viewer remain separate
demonstration gates.

### P0-2 - RESOLVED offline: exact filesystem offset is sealed end to end

Classification now retains the exact byte offset whose filesystem probe
succeeded. The value propagates through `EvidenceItem`, the mount decision, and
trusted TSK execution. The model cannot supply or change it. `tsk_fsstat` is
withheld when the exact offset is unknown; otherwise trusted code seals the
derived sector into `fsstat -o`. Partitioned APFS is withheld when its available
backend cannot accept the offset.

Verification includes a two-partition fixture whose filesystem exists only on
the second partition, exact later-TSK-match propagation, mount-option proof,
sealed worker argv proof, raw offset zero, and unknown-offset withholding. At
the historical Gate A checkpoint, the full suite passed 128 tests.

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
- [x] All 267 tests and Ruff check/format pass in the superseding vNext primary
      environment.
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
- [ ] The investigator terminates through the strict typed-DONE-v2 protocol.
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
  viewer.html
  profile.json
  audit.jsonl
  environment.json
  summary.json
  manifest.json
  manifest.sha256
  tool-outputs/
    <sha256>.*
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

Exact span resolution proves only that investigator and reviewer quotes occur at
recorded byte ranges inside the cited content-addressed tool output. It does not
prove that the quote supports the claim, that the claim is factually correct, or
that the project-authored reviewer is independent. Semantic correctness and
receipt sufficiency must be reported as separate axes under the publicly frozen
rubric and scorer.

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

Current state: **PUBLIC PROVENANCE GREEN, EXPERIMENT FREEZE BLOCKED**. The public
remote exists and matches local HEAD. The frozen rubric, scorer digest, and
public freeze tag still do not exist.

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

Current state: **IMPLEMENTED + VERIFIED OFFLINE, NOT DEMONSTRATED**. The strict
offline verifier, static manifest-bound viewer, and judge quickstart are
implemented and tested. There is no complete authentic bundle, human visual QA,
or hosted path.

Pass when an anonymous judge can understand the project in 20 seconds and verify
the genuine run in under five minutes without rebuilding through a hosted
viewer, offline viewer/release bundle, and no-network verifier. A screencast is
supplemental evidence only.

### Gate E - Submission freeze

Target: July 20.

Current state: **NOT READY**. A public repository and offline viewer code exist;
no committed/pushed vNext, authentic evaluated run and viewer artifact, hosted
path, video, Devpost submission, or confirmation artifact exists.

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
- [x] Write `JUDGE-QUICKSTART.md` for the current Windows flagship; add the
      final viewer URL after the authentic bundle exists.
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
| No immutable tagged vNext freeze | High | Reviewed base `origin/main` is `2b256a7`; vNext has a public review-branch commit without rewriting history | Review/merge the branch, then add the protocol freeze digest/tag |
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

Safe now, with the stated scope (superseding the July 14 count):

- 17 source modules, 13,383 physical source lines, and 12,259 nonblank
  source lines.
- 267 offline tests pass under CPython 3.11.9.
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
- The public upstream history through reviewed `main` at `2b256a7` and
  `BUILD_PROVENANCE.md` exists; the vNext release has a public review-branch
  commit, but is not yet merged, freeze-tagged, or externally signed.

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
cd <path-to-clone>\Unchained
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
| P0 implementation prompt | **COMPLETE at the historical Gate A 128-test checkpoint** |
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
| 2026-07-14 22:24 | Committed the synchronized winner strategy, handover, provenance, README, and environment record | Commit `207a039836cdaf3045e92a2b74e541a7dd2be77f`; public rules/API references, exact Gate A receipts, Windows memory-only scope, two-axis scoring, evaluator authorship, and all remaining red gates are aligned | Push and verify public provenance, then complete and publish C4 |
| 2026-07-14 22:32 | Verified public provenance after user push | `origin/main` exactly matches `3506d29003262f22fee2144f12352749fc6cd06f`; GitHub metadata reports `visibility=public`; browser fetch returned a stale 404 and is retained as a non-authoritative discrepancy; API key is not present in this Codex process | Freeze the protocol and rubric before any GPT-5.6 DC01 call |
| 2026-07-18 | Published OpenAI-native vNext foundation and completed the bounded Docker/UX follow-up | Foundation `ed4d3f5` fast-forwarded to public `main`; 274 tests plus Ruff/format/`pip check` in Linux/AMD64 test image; non-root runtime; no-network synthetic profile `E001`; custody match; secret scan pass; Luna canary implemented but no authorized key/live receipt | Push the synchronized follow-up, publish the experiment freeze, retain the Luna canary, then run one harmless complete Sol lifecycle before DC01 |
| 2026-07-19 | Independently reviewed the first live Luna canary and retained Sol run | Luna reported as one nonqualifying typed request; Sol bundle-derived receipt records two `gpt-5.6-sol` responses, six successful opening tools on real Windows memory, an enforced six-call cap, matching recorded custody, and offline `VALID` / terminal `PARTIAL` | Publish sanitized receipts, freeze the complete experiment, then run the missing serializer/reviewer/report lifecycle to `COMPLETE` |

## Historical next action before the vNext publication

Finish and publish the preregistration/freeze with server-timestamped digests.
Only after that public freeze may DC01 be exposed to GPT-5.6 for the first valid
post-freeze primary run. No viewer, video, or prose polish outranks this sequence.
## Current rehearsal disclosure (2026-07-15)

The first real DC01 attempt was a pre-freeze rehearsal, not a scored run. Run
`20260715T040320Z-9b0f5864` reached the native Windows memory tools and opening
book, retained hashed outputs, and finished with matching custody hashes. It
terminated `PARTIAL` before judge/report because the Responses replay included
the provider-only `status` field (`input[1].status`). Commit `57e6124` removes
that field during replay and adds the exact regression test. This rehearsal is
disclosed and cannot become primary. No further live DC01 rehearsal is planned
before freeze. The first valid post-freeze `COMPLETE` run will be the primary;
the judge and report phases receive their first full live exercise there.

## Superseding OpenAI-native vNext checkpoint (2026-07-18)

This section records the pre-publication vNext verification checkpoint and
supersedes earlier current-state rows while preserving their historical truth.
The verified tree was subsequently published as commit
`ed4d3f540a27171c04a7321f4f85efea23d905de`, first on
`agent/openai-native-vnext` and then by safe fast-forward to public `main`.

### Repositories reviewed

- `sentinel-unchained` upstream `main`:
  `2b256a7bfd170388d2a8497dd3289af248abae18`.
- `Sentinel-Ensemble-Qwen` upstream `master`:
  `9f309c6134e857f7b86f3e6b9c6709ce954944a5`.
- Both local checkouts matched those live GitHub heads when the review began.
- The untouched Unchained baseline passed 129 tests, Ruff check/format,
  `pip check`, and wheel/sdist construction.

The detailed comparison and rationale are in
[`docs/OPENAI_VNEXT_REVIEW.md`](docs/OPENAI_VNEXT_REVIEW.md). The decision is to
evolve the smaller Unchained controller, not port Qwen's dual conductor. Qwen's
deterministic onboarding, typed capability filtering, bounded adaptive work, and
fact-provenance ideas remain useful. Its 20-to-35-tool floor, monolithic
orchestration, early/nonfatal custody, fail-open validation, per-call MCP process
churn, promoting/nonfresh finalizer, and unsafe report surface do not carry
forward.

### Implemented and verified offline

- Initial and final custody maps now share the public evidence-ID namespace.
- Tool lifecycle receipts bind controller-owned evidence IDs and initial SHA-256
  values. Multiple ready images fail closed instead of silently selecting item
  zero.
- `profile.json` is canonical JSON reconstructed from the verified evidence
  profile, and that profile is rebound to the initial custody names, hashes,
  byte counts, readiness, and investigation-start event. `summary.json` is also
  rebuilt from the verified audit instead of being trusted as a sealed blob.
- The opening decision is all-or-none. Unknown tools, malformed arguments,
  duplicate call IDs or tool names, or more than six calls fail the opening
  protocol; a `COMPLETE` lifecycle therefore contains 1–6 distinct valid
  opening calls and no `capped` or `rejected` receipt anywhere in the lifecycle.
- Strict verification validates retry-aware model transaction windows: one
  request/options pair, zero to two correctly scheduled transient retry pairs,
  and exactly one accepted response. Orphan, out-of-order, over-limit, or
  non-transient retry receipts fail closed; transport classes, HTTP status,
  backoff, and positive nonincreasing retry timeouts are bounded.
- The authoritative audited response is the normalized request/response
  contract: requested and returned model identity, IDs, completion state,
  message, validated function calls, and usage. Duplicate raw `output_items`
  are deliberately excluded from proof authority so a second representation
  cannot contradict the normalized calls or message.
- Verification revalidates each closed typed catalog and exact phase policy and
  reconstructs every exact phase input. It binds model call
  IDs/names/arguments to tool receipts, controller actions, forced serializers,
  the deterministic report, and every full root-artifact descriptor. Accepted
  response output usage cannot exceed its paired request ceiling, and emitted
  lifecycle counts must match the verified findings, verdicts, and receipts.
  Typed argument values use the runtime's same bool-safe JSON type contract.
- Profile verification rederives OS, evidence shape, canonical filesystems, and
  route-conflict warnings from the evidence inventory; those deterministic
  routing fields cannot be rewritten independently.
- The adaptive investigator uses a compact case ledger, receipt index, remaining
  budget, and latest observation rather than replaying provider transcripts or
  encrypted reasoning. Every nonterminal call must supply a visible UTF-8 ledger
  update of at most 8,192 bytes, recorded before execution and rebound offline.
  The live default no longer requests unused encrypted reasoning content.
- Phase-specific GPT-5.6 reasoning, verbosity, output-token, and tool-call
  ceilings reduce unnecessary latency while code-owned case caps remain hard.
  Implicit prompt caching permits stable-prefix reuse, but cap preflight still
  prices a cache miss. Audited call cost and the final budget snapshot are
  recomputed from normalized token usage, the code-owned price table, and the
  frozen caps. This is local cap accounting, not provider billing. No live
  latency or measured faster-than-Qwen claim is made.
- Findings bind to exact full-artifact UTF-8 byte ranges and stable span IDs. The
  fresh judge sees those spans, can preserve or downgrade only, and cannot add
  unknown findings.
- GPT-5.6 returns a strict narrative-and-reference report draft. Code renders the
  authoritative findings, verdict transitions, citations, IOCs, limitations,
  and safe Markdown; model prose is explicitly nonauthoritative and the exact
  report SHA-256/byte count is audited. Verification reconstructs the report and
  requires byte-for-byte equality.
- Every bundle contains a required, deterministic `viewer.html` with a restrictive
  CSP, no scripts/external resources, and escaped dynamic text. Verification
  reconstructs the viewer byte-for-byte and independently applies a positive
  inert-HTML/CSP policy. `sentinel view` requires the strict lifecycle verifier
  whenever the bundle claims `COMPLETE` before it opens the file.
- The user-facing lifecycle is `sentinel doctor`, `profile`, `run`, `verify`, and
  `view`; compatibility entry points remain.

### Exact verification result

Validated in external CPython 3.11.9 AMD64 environment
`%LOCALAPPDATA%\venvs\sentinel-unchained-py311`:

| Check | Result |
|---|---|
| `python -m pytest -q` | **PASS**, 267 collected tests |
| `python -m ruff check .` | **PASS** |
| `python -m ruff format --check .` | **PASS**, 32 Python files already formatted |
| `python -m pip check` | **PASS**, no broken requirements |
| `python -m build` | **PASS**, wheel and sdist built from the sdist path |
| `git diff --check` | **PASS**; only a line-ending advisory for `run.ps1` |
| `python -m unchained doctor --json` | Expected exit `2`: dependencies ready, model/key absent, no secret printed |

Current source count: 17 modules, 13,383 physical lines, 12,259 nonblank lines.
The suite includes a real-shaped synthetic lifecycle through strict verification,
an exact supporting span after byte 3,000, and fully re-chained adversarial
mutations of model/tool bindings, phase options, normalized responses, retry
windows, exact phase request packets, response output ceilings, impossible
complete receipts, lifecycle counts, visible ledgers,
forced serializer/judge/report arguments, occurrence
counts, profile/custody bindings, rebuilt summaries, local cost/final-budget
accounting, exact report/viewer bytes, artifact descriptors, and active viewer
content. It also covers judge lattice and ID failures, custody namespace
regression, all-or-none opening rejection, and CLI no-call/fail-fast checks.

The in-app browser could not perform human visual QA because its runtime failed
before loading the local file with a sandbox-policy metadata error. This does
not invalidate the automated HTML/security tests, but visual cross-browser QA
remains **NOT DEMONSTRATED**.

### Explicitly not demonstrated or production-ready

1. No authentic completed GPT-5.6 vNext evidence run exists; this session had no
   key and did not spend the frozen DC01 primary call.
2. Offline verification validates recorded provider metadata but cannot
   independently authenticate OpenAI.
3. No live latency benchmark exists, so the phase caps and parallel opening are
   performance design choices, not evidence that vNext is faster than the Qwen
   ensemble or a measured end-to-end baseline.
4. Recomputed local inference cost enforces the frozen price table and caps but
   is not a provider bill; only provider billing records can establish billed
   cost.
5. Third-party parser children are process-contained and credential-scrubbed but
   do not yet have OS-enforced network denial or scratch-only filesystem writes.
6. Final hashing cannot defeat a privileged transient pathname swap; stable
   handles or immutable snapshots remain required for that threat model.
7. Multi-image routing fails closed but does not yet analyze all images.
8. Heavy opening tools are bounded but not scheduled by CPU/RAM/I/O resource
   class.
9. Per-call parser subprocess startup remains measurable overhead; a persistent
   pool must wait for an enforceable OS sandbox rather than weaken isolation.
10. A same-user/administrator actor can still mutate a pathname between offline
   verification and an external browser opening it.
11. The local hash chain and manifest checksum are unsigned and have no trusted
   external timestamp.
12. The current workspace is inside OneDrive; sensitive live outputs should use
    a restricted nonsynchronized case directory.
13. Automated byte-exact viewer and inert-HTML checks pass, but human visual and
    cross-browser QA is still pending because the in-app browser failed before
    loading the local file.

### Historical next highest-leverage action before Docker preflight

After review and an authorized key are available, run one harmless synthetic
GPT-5.6 smoke through all five model phases, verify it, and visually inspect its
sealed viewer. Only then run the frozen authorized evidence case:

```powershell
sentinel doctor
sentinel profile C:\Evidence\case
sentinel run C:\Evidence\case --caps strict
sentinel verify C:\path\to\run --require-complete --require-live-gpt56
sentinel view C:\path\to\run
```

Do not call the result provider-authenticated solely because the strict offline
flags pass. Preserve the provider-side record and add a signature/timestamp or
other independently controlled attestation before making that claim.

## Published vNext and Docker/UX handoff (2026-07-18)

### Publication provenance

| Field | Verified state |
|---|---|
| Public repository | `https://github.com/3sk1nt4n/Unchained` |
| vNext foundation | `ed4d3f540a27171c04a7321f4f85efea23d905de` |
| Working branch | `agent/openai-native-vnext`, remote equal at publication |
| Default branch | `main`, safely fast-forwarded from `2b256a7` to `ed4d3f5` |
| History behavior | No force-push and no history rewrite |
| Publication exclusions | No API key, evidence image, private key, or generated case bundle |

The complete completed-jobs inventory, architectural comparison, winning
narrative, judge demo, benchmark contract, Docker/cheap-model preflight,
scorecard, limitations, and submission sequence are in
[docs/OPENAI_VNEXT_RELEASE_HANDOFF.md](docs/OPENAI_VNEXT_RELEASE_HANDOFF.md).

### Docker preflight result

The Linux/AMD64 multi-stage container now passes the full CPython 3.11 gate:

- 274 tests;
- Ruff lint and formatting;
- `pip check`;
- final-image installation from pre-resolved wheels with Git absent;
- non-root UID/GID 10001;
- Tini entrypoint;
- read-only root and evidence under Compose;
- all Linux capabilities dropped and `no-new-privileges` enabled;
- offline/no-network help, doctor, synthetic profile, public `E001`, and matching
  pre/post custody;
- no credential-like value in image environment or history.

The safe container supports raw Volatility and Sleuth Kit routes. It does not
enable E01/FUSE/loop/device mounting, which would require elevated authority and
would weaken the default isolation story. Native Windows remains the flagship
DC01 memory path.

### Cheap-model decision

`sentinel smoke-openai` performs one forced strict typed-tool request with
`gpt-5.6-luna`, low reasoning/verbosity, 128 output tokens maximum,
`store=false`, no evidence, and no proof bundle. It is permanently labeled
`NONQUALIFYING_CONNECTIVITY_SMOKE` and cannot satisfy the Sol-specific strict
proof gate.

At this 2026-07-18 Docker checkpoint, the machine had no authorized API key.
The canary implementation and mocked container contract were verified, but no
authentic provider receipt was claimed at that time. The next command was:

```powershell
$env:OPENAI_API_KEY_FILE = "C:\Secure\openai_api_key"
docker compose --profile live run --rm live-smoke
```

### Historical next action before the first live receipts

1. Push this synchronized Docker/README/handoff follow-up to public `main`.
2. Publish the experiment freeze binding code, prompts, Sol alias/snapshot,
   schemas/catalog, caps, retries, prices, evidence digest, evaluator, and
   run-selection rule.
3. Run and retain the authentic Luna canary; keep it outside scored results.
4. Run one harmless synthetic Sol lifecycle through all five model phases,
   strict verification, custody, and viewer.
5. Run the first valid frozen evidence primary once.
6. Benchmark the same evidence fairly against Qwen and score semantic accuracy
   separately.
7. Complete viewer visual QA, video, hosted artifact, and submission links.

The current winning line is:

> Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a
> bounded investigation whose actions, citations, custody, and final report can
> be checked independently.

## First live GPT-5.6 receipt checkpoint (2026-07-19)

This checkpoint supersedes older forward-looking statements that no Luna or Sol
live request had been demonstrated. It does not rewrite those dated historical
records, and it does not mark the flagship complete-case gate green.

### Independent review provenance

The supplied independent review report identifies Windows 11, CPython 3.11,
repository commit `51662cfb809212af3b58a680c0d9265d91692302`, and labels its
executed claims `TESTED`. The supplied `REPORT-LIVE-RUN.md` is 4,434 bytes with
SHA-256
`7ebdf230de88b18af3cd8a38acecebc2b1b48ca0d6c0740e596dd0bb0df53c9c`.

The repository stores two deliberately sanitized projections:

- [Luna canary receipt](docs/runs/luna-canary-receipt.json)
- [Sol capped DC01 opening receipt](docs/runs/sol-capped-dc01-opening.json)

The Luna file is a second-reviewer-attested (project-affiliated) projection. The raw Luna JSON
response was not supplied or retained with a proof bundle, so it is neither
bundle-derived nor cryptographic provider proof. It reports one
`gpt-5.6-luna` request, a valid strict typed call, no evidence read, 186 input
tokens, 27 output tokens, and the permanent qualification label
`NONQUALIFYING_CONNECTIVITY_SMOKE`.

The Sol projection is derived from the retained bundle's own files. Its binding
commitments are:

| Retained artifact | Bytes | SHA-256 |
|---|---:|---|
| `audit.jsonl` | 100,445 | `57b3413e5d2c63ce18a3ffc83b70af4f22889b5ea2cdf37fbb5d0984c4774b84` |
| `manifest.json` | 4,872 | `be6ff8b13099cffcd1ca0e2b69c53f106c7b7b3f64b5ad7f628522fb0f59bb3d` |
| `profile.json` | 819 | `15dc2ee77de1cb10a5569ed66a0f81048f23782d045eaeaccd6fe88ff7d28d46` |
| `summary.json` | 1,351 | `89b069bb4fdfe2af0a4f98df775492a6a2eb8a7e7bbe8364c91015aead8f9846` |

### Exact Sol result

Bundle-derived values control over rounded review prose:

| Fact | Exact retained value |
|---|---|
| Run ID | `20260719T020118Z-ede6c445` |
| Evidence | `E001`, ready Windows memory, 2,147,483,648 bytes |
| Provider identity recorded by audit | `gpt-5.6-sol` on both model responses |
| Model responses | 2 |
| Opening | 6 selected, 6 executed, 0 rejected |
| Successful tools | `vol_pstree`, `vol_psscan`, `vol_netscan`, `vol_malfind`, `vol_cmdline`, `vol_svcscan` |
| Adaptive request | `vol_dlllist`, cap-blocked before forensic execution |
| Tool receipt counts | 6 `success`, 1 `capped` |
| Usage | 58,508 input; 746 output; 59,254 provider-total tokens |
| Local cost estimate | `$0.38789875`; not a provider invoice |
| End-to-end wall | 43,702 ms |
| Terminal | `PARTIAL`, exit `3`, `MAX_TOOL_CALLS` |
| Custody | Baseline/final recorded; matching SHA-256; mount released |
| Offline verify | `VALID`; 13 artifacts; 38 chained audit entries |

The verifier warning is material: original evidence was not included and was
not rehashed during later offline verification. The verifier establishes the
consistency of recorded custody receipts, the audit chain, artifacts, caps,
usage, and terminal state. It does not cryptographically authenticate OpenAI,
establish provider billing, or prove semantic forensic correctness.

### Current live-proof scorecard

| Gate | Current state |
|---|---|
| Luna connectivity and strict typed call | **DEMONSTRATED — second-reviewer-attested (project-affiliated) projection** |
| Luna raw/bundle-derived receipt | **NOT RETAINED** |
| Sol provider-model metadata | **RECORDED twice as `gpt-5.6-sol`** |
| Six-way Sol opening | **DEMONSTRATED on real memory** |
| Six typed Volatility executions | **SUCCESS** |
| Deterministic tool cap | **FIRED correctly before seventh forensic execution** |
| Recorded pre/post custody | **MATCH** |
| Retained capped bundle | **OFFLINE `VALID`, terminal `PARTIAL`** |
| Typed `DONE` v2 and forced findings serialization live | **PENDING** |
| Fresh downgrade-only reviewer live | **PENDING** |
| Authentic `COMPLETE` Sol bundle | **PENDING** |
| Same-evidence Qwen benchmark and semantic score | **PENDING** |
| Human/cross-browser authentic viewer QA | **PENDING** |

### Terminal-protocol correction and v2 hardening

The supplied independent report described four later no-call turns as empty.
Direct read-only inspection of their retained `model.response` audit payloads
does not support that diagnosis: every response had provider status
`completed`, no function call, and visible message lengths of 1,750, 1,124,
1,112, and 395 characters. The v1 controller therefore rejected substantial
nonterminal ledger prose, not blank output. Accepting empty text, case variants,
punctuation, or Markdown as completion would both miss the observed failure and
weaken the proof contract.

The integrated v2 remedy is a closed, non-forensic
`finish_investigation({"status":"DONE"})` function appended to the immutable
adaptive catalog. Every adaptive request uses `tool_choice=required` and a
one-call ceiling; code accepts exactly one eligible forensic action or the
canonical finish action. The verifier binds the catalog, required choice,
closed arguments, terminal response, and `typed-DONE-v2` event while retaining
read compatibility for historical literal-DONE-v1 bundles. Investigate,
serializer, and reviewer requests also require a 4,096-token allocation; if the
remaining token or estimated-cost budget cannot preserve it, the run stops by
cap before dispatch instead of degrading into a protocol error. This remedy is
offline-verified; its authentic COMPLETE trace is still pending.

### Current next action

1. Revoke every credential that has appeared in chat, logs, screenshots, or a
   recording. Create a fresh project-scoped key with an explicit spend limit;
   keep it outside Git and do not paste it into an agent thread.
2. Publish these sanitized receipts without publishing evidence bytes, raw
   forensic output, local paths, credentials, or full provider identifiers.
3. Freeze the complete-run code, prompts, models, schemas, tools, caps, price
   table, evidence digest, scoring facts, and run-selection rule.
4. Run a harmless Sol case through typed `DONE`, findings serialization,
   fresh review, deterministic report/viewer, custody, and strict verification.
5. Run and retain the authentic frozen `COMPLETE` case.
6. Run the same-evidence Qwen comparison and frozen semantic scorer.
7. Complete viewer QA, video, hosted artifact, and submission packaging.

The winning claim is now stronger but remains bounded:

> A retained live GPT-5.6 Sol bundle proves the opening, typed tool, cap,
> content-addressed artifact, and recorded-custody path on real memory. It is
> deliberately `PARTIAL`; the complete findings, fresh-review, and report proof
> remains the next gate.
