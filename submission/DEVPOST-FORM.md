# Devpost Submission Form — OpenAI Build Week (Developer Tools)

Paste-ready blocks for every field. Every number traces to the repo's retained receipt
(`docs/runs/sol-capped-dc01-opening.json`), the 2026-07-20 test run, or the committed docs.
Pending items are labeled plainly. Deadline: 2026-07-21 17:00 PT (internal hard floor: Tue 14:00 ET).

Judge-first rule used throughout: the pitch and the $0 no-key lane lead; honest caveats follow below the fold, never deleted.

---

## Project name

One line, keep short (Devpost truncates long names in listings). The CLI installs as `sentinel`.

```
Unchained
```

---

## Tagline

Aim for 60 characters or fewer.

```
GPT-5.6 chooses where to look; code owns the evidence.
```

If the field allows ~200 characters, use the exact one-line pitch instead:

```
GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited.
```

---

## Track

Select from the dropdown.

```
Developer Tools
```

---

## What it does

Main description field. Judge fast path first, differentiator second, receipt facts third, honest limits last.

```
GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited.

**Try it in about 60 seconds, $0, no API key.** After a 1-2 minute pip install, every command below returns in well under a second and never contacts OpenAI:

    git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
    py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
    .judge\Scripts\python.exe -m unchained onboard
    .judge\Scripts\python.exe -m unchained profile docker/fixtures --json

**What it is.** Unchained is a bounded autonomous Digital Forensics & Incident Response (DFIR) investigator built with Codex and GPT-5.6. It profiles an evidence folder without a model call, establishes SHA-256 custody, exposes only route-eligible typed read-only tools, and lets GPT-5.6 choose an opening of up to twelve tools that code validates all-or-none and executes concurrently. Later turns carry a compact visible ledger and allow one typed action at a time. A strict typed `finish_investigation(status="DONE")` forces structured findings, a fresh-context reviewer may preserve or downgrade them, and deterministic code resolves exact UTF-8 evidence spans, renders the authoritative report and inert viewer, seals a content-addressed bundle, and verifies the complete lifecycle offline.

The differentiator is not that an LLM can call forensic tools. It is that model strategy and evidence authority are separated clearly enough for a judge or analyst to inspect. Receipts prove what ran, what output was retained, and what exact text was cited. They do not pretend to prove forensic truth; a human still owns interpretation and response.

**Two real, retained GPT-5.6 runs back this.**

**The first ships in the repository and re-verifies on current code** (`examples/public-run-partial`, a committed copy of run `20260720T013927Z-9f12ec6f`):

- Provider recorded `gpt-5.6-luna` across 4 responses, request/response IDs retained.
- Same 2,147,483,648-byte DC01 Windows memory image; custody match true.
- 14 typed Volatility tool receipts, all status "success"; the hard tool budget then ended the run honestly — terminal_reason "MAX_TOOL_CALLS: reservation would reach 14 > 13", status PARTIAL, exit code 3.
- Measured: 55.5 s wall, 180,285 provider-reported tokens, local cost estimate $1.16.
- Verify it yourself after cloning, no key, no network: `sentinel verify examples/public-run-partial` → VALID, 20 artifacts, 62 hash-chained audit entries (proven 2026-07-20).

**The second is the earlier `gpt-5.6-sol` capped opening** (sanitized receipt committed at `docs/runs/sol-capped-dc01-opening.json`, run `20260719T020118Z-ede6c445`):

- Requested model `gpt-5.6`; provider recorded `gpt-5.6-sol` on both of 2 responses, request/response IDs retained.
- Real evidence: 2,147,483,648-byte DC01 Windows memory image (public Stolen Szechuan Sauce case), SHA-256 `8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62`, custody match true (initial == final hash).
- Opening phase: 6 typed Volatility tools selected, 6 executed, 0 rejected — vol_pstree, vol_psscan, vol_netscan, vol_malfind, vol_cmdline, vol_svcscan, all status "success"; vol_netscan alone retained 3,961,843 output bytes. (This run predates the current cap; the opening now allows up to twelve tools.)
- Fail-closed cap: the 7th requested tool (vol_dlllist) was refused before dispatch — terminal_reason "MAX_TOOL_CALLS: reservation would reach 7 > 6" — and received a capped receipt with duration_ms 0: "No successful forensic execution is claimed." Terminal status PARTIAL, exit code 3.
- Measured: 43.702 s wall, 59,254 provider-reported tokens, local cost estimate $0.38789875 under a $1.00 cap.
- Offline verification recorded at creation (2026-07-19): VALID, 13 artifacts and 38 hash-chained audit entries. Proof bundles bind byte-exactly to the renderer that produced them, so this earlier bundle re-verifies only against its creating code version; the shipped bundle above is the one to re-verify on current code.

**A completed case makes exactly 4 fixed GPT-5.6 requests (opening book, findings serialization, fresh review, report draft) plus one per adaptive action — minimum five, never an unbounded loop.**

**Honest limits (kept on purpose):**
- The retained Sol bundle proves the live opening/tool/cap/custody path, but it is PARTIAL; no authentic COMPLETE GPT-5.6 vNext bundle is published yet. Bundle census: 19 run bundles, 0 COMPLETE (12 PARTIAL / 7 INVALID).
- Exact receipts establish execution and citation support, not forensic truth. The fresh reviewer is a same-family model call, not independent ground truth.
- No frozen same-evidence Qwen latency/cost/accuracy benchmark is published yet — deliberately cut rather than making unmeasured claims.
- Private worker containment and process-tree cleanup are not a complete OS sandbox; SHA-256 pre/post checks do not defeat every privileged concurrent pathname race; a privileged actor who can rewrite and reseal the whole local bundle is outside the current trust boundary (signed/timestamped external anchoring is future work).
- Linux/macOS/Docker claims are STATIC-ONLY (read and reasoned, not executed on a real host); macOS is via Docker emulation, not yet verified on Mac hardware.

Closing: "Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a bounded investigation whose actions, citations, custody, and final report can be checked independently."
```

---

## How we built it

The Codex collaboration story. Cite the Session ID verbatim.

```
**Codex Session ID: 019f61e5-5755-7a02-adb4-618d32baab27** (majority-core /feedback session; core functionality build).

Codex was the primary implementation and adversarial-review collaborator for the Build Week work in this repository: the evidence lifecycle, Responses API adapter, typed execution boundary, caps, retry/usage accounting, typed-DONE-v2 protocol, forced serializer, exact evidence spans, fresh-context downgrade-only review, report/viewer renderers, independent verifier, CLI, Docker isolation, tests, benchmark design, and documentation.

**What Codex accelerated** (recorded in BUILD_PROVENANCE.md):
- Repository inspection and architecture implementation.
- Typed controller, evidence, tool, audit, cap, and report-safety code.
- Adversarial tests and defect reproduction.
- Live-rules and official-API verification.
- Code, security, experiment, judge-experience, and strategy review.
- Documentation, handover, and prompt construction.
- Proof-bundle, provider-proof, verifier, reproducible-environment, and dependency-lock implementation recorded by later commits.

**Concrete Build Week code built with Codex** (BUILD_PROVENANCE.md section 4): src/unchained/evidence.py, tools.py + _tool_worker.py, model.py (Responses API integration), agent.py (opening selection, adaptive loop, forced finalization, fresh review), audit.py, artifacts.py, verify.py, caps.py, models.py, prompts.py, cli.py, __main__.py, all tests under tests/, plus the README, decision record, roadmap, and handover docs.

**What the human owned.** The human owner chose the product thesis, Developer Tools track, DFIR testbed, evidence case, authority split, benchmark, scope cuts, claim language, and final submission decisions. Specifically: choosing the controlled-autonomy versus deterministic-trust comparison; choosing Developer Tools and the trust-measurement framing; selecting DFIR as the demonstration domain; choosing DC01 as the known-answer public benchmark; accepting the single-case and possible training-contamination limitations; requiring truthful scope labels and a no-fake-evidence policy; approving scope cuts, public claims, the frozen rubric, and final submission.

**GPT-5.6 at runtime:** GPT-5.6 is the Sol investigator/reviewer, with a Luna canary connectivity check (one request, 186 input + 27 output tokens, labeled NONQUALIFYING_CONNECTIVITY_SMOKE).

A follow-up Codex thread covered Docker/README work: 019f76f3-a19f-71d1-81b2-eed6305857f6 (thread provenance only, not a feedback receipt unless submitted successfully).
```

---

## Challenges we ran into

Honest, framed as engineering maturity: the failures are recorded, capped, and labeled instead of hidden.

```
**Token throughput vs. rich context.** New OpenAI accounts cap around 200k tokens per minute, while a rich 12-tool serializer packet can reach ~270k tokens. Result: 429s that end a run as an honest PARTIAL rather than a silent retry storm. A full lifecycle can also exceed the 400k default token cap, so the README documents explicit overrides (e.g. MAX_TOTAL_TOKENS=3000000, MAX_COST_USD=30 for a complete run on real memory) instead of pretending defaults always suffice.

**Fail-closed by design, proven in the retained run.** Caps fire BEFORE dispatch. In the committed receipt, the 7th requested tool (vol_dlllist) was refused with terminal_reason "MAX_TOOL_CALLS: reservation would reach 7 > 6" and received a capped receipt with duration_ms 0 stating "No successful forensic execution is claimed." The run ended PARTIAL with exit code 3 — under budget ($0.38789875 local estimate against a $1.00 cap) and fully audited (38 hash-chained entries). The same fail-closed behavior repeats on current code in the shipped bundle `examples/public-run-partial`: 14 successful receipts, then terminal_reason "MAX_TOOL_CALLS: reservation would reach 14 > 13".

**All-or-none opening validation.** The GPT-5.6 opening must choose one to twelve distinct route-valid typed calls. An unknown, duplicate, malformed, or thirteenth call rejects the whole opening rather than running a valid-looking subset. Getting the model to reliably meet a strict typed contract — and refusing everything that misses it — was harder than accepting best-effort output, and worth it.

**Terminal authority.** Prose, Markdown, and empty output have no terminal authority. Only the typed finish_investigation({"status":"DONE"}) call terminates a case (terminal contract v2; the verifier still reads historical literal-DONE-v1 bundles).

**Honest bundle census.** 19 run bundles exist: 0 COMPLETE, 12 PARTIAL, 7 INVALID. We publish that count rather than cherry-picking.
```

---

## Accomplishments that we're proud of

```
- **404/404 tests pass in 25.11s** across 24 test files, ruff check + format clean, verified 2026-07-20 on CPython 3.11.9.
- **Two authentic, retained GPT-5.6 runs on real evidence**: a judge-verifiable bundle shipped in the repo (`examples/public-run-partial`: `gpt-5.6-luna`, 14/14 model-selected typed Volatility tools on a 2 GiB DC01 Windows memory image, custody hash match) and a committed sanitized `gpt-5.6-sol` receipt (6 of 6 opening tools with provider request/response IDs, docs/runs/sol-capped-dc01-opening.json).
- **Byte-exact offline verification**: the shipped bundle verifies VALID on current code — 20 artifacts and 62 hash-chained audit entries reconstructed and checked with no network and no key (proven 2026-07-20).
- **Measured, capped spend**: shipped run 180,285 provider-reported tokens, 55.5 s, ~$1.16 local estimate; Sol opening 59,254 tokens, 43.702 s, $0.38789875 under a $1.00 cap.
- **A $0 judge lane**: onboarding, fixture profiling, bundle verify/view, an offline Docker container, and a no-key demo script — none of which contact OpenAI.
- **A two-key spend gate**: paid runs require typing the exact phrase LAUNCH GPT-5.6 SOL. No accidental spend.
- **A bounded invocation budget**: exactly 4 fixed GPT-5.6 requests plus one per adaptive action — minimum five, never an unbounded loop.
- **An inert deliverable**: a static no-JS viewer.html plus an authoritative report, sealed in a content-addressed bundle with a manifest and SHA-256.
```

---

## What we learned

```
- The valuable line is not "an LLM can call forensic tools." It is drawing the authority split sharply enough to inspect: the model chooses bounded strategy and proposes findings; deterministic code owns evidence identity, legality, caps, execution, citation spans, verdict monotonicity, report rows, and verification.
- Receipts should prove execution and citation support — and explicitly not claim forensic truth. Saying what a proof does NOT establish is as important as saying what it does.
- Fail-closed beats optimistic. Refusing a 7th tool before dispatch and ending PARTIAL produced a more trustworthy artifact than any best-effort completion would have.
- Typed terminal contracts work. Once prose lost terminal authority and only finish_investigation({"status":"DONE"}) could end a case, "did it finish?" became a checkable fact instead of a judgment call.
- Token budgeting is a first-class design constraint: TPM ceilings and serializer packet size shape the protocol, not just the bill.
- Monotonic review is a cheap, honest safety layer: a fresh-context reviewer that can only preserve or downgrade findings can never inflate them.
```

---

## What's next

```
- Publish an authentic COMPLETE GPT-5.6 vNext bundle and its public viewer (currently PENDING_COMPLETE_RUN; the retained run is PARTIAL by cap, by design).
- Ship the frozen same-evidence Qwen benchmark that was deliberately cut for Build Week — we make no unmeasured comparative claims until it exists (prior-work boundary pinned at github.com/3sk1nt4n/Sentinel-Ensemble-Qwen, commit 9f309c6134e857f7b86f3e6b9c6709ce954944a5).
- Signed/timestamped external anchoring of bundles, since a privileged actor who can rewrite and reseal a whole local bundle is outside the current trust boundary.
- Verify the Linux and macOS lanes on real hosts (today those claims are honestly labeled STATIC-ONLY / Docker-emulation).
- Generalize the pattern beyond DFIR — security testing, compliance review, financial operations: model chooses bounded strategy -> code validates and executes typed authority -> exact outputs and citations are retained -> a monotonic reviewer reduces claims -> deterministic code renders and verifies the deliverable.
```

---

## Built with

Devpost tag list, comma-separated.

```
python, openai, gpt-5.6, codex, responses-api, docker, volatility, powershell, bash, sha-256
```

---

## "Try it out" links / Repo URL

```
https://github.com/3sk1nt4n/Unchained
```

Public repo, MIT license. Live receipts in-repo: `docs/runs/sol-capped-dc01-opening.json` and `docs/runs/luna-canary-receipt.json`. Public evidence source: https://dfirmadness.com/the-stolen-szechuan-sauce/

---

## Video URL

PENDING — video link: added on upload. This is the only mandatory gap; do not submit without it.

```
ADDED-ON-UPLOAD
```

---

## Codex Session ID

Paste exactly. This is the majority-core /feedback session covering the core functionality build.

```
019f61e5-5755-7a02-adb4-618d32baab27
```

Optional secondary thread (Docker/README work; thread provenance only, not a feedback receipt unless submitted successfully): `019f76f3-a19f-71d1-81b2-eed6305857f6`

---

## Developer Tools extras — Installation instructions

```
**Windows one-liner** (installs, walks you in, never spends):

    irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex

**Linux/macOS one-liner** (hardened container, never spends):

    curl -fsSL https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.sh | bash

**Windows, two commands** (Git + CPython 3.11; validated flagship interpreter is 3.11.9 AMD64, package requires CPython >=3.11,<3.12):

    git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
    .\setup.ps1        # install + verify everything
    .\unchained.ps1    # start a whole case

**Linux** (Git + Python 3.11):

    git clone https://github.com/3sk1nt4n/Unchained.git && cd Unchained
    ./setup.sh
    ./unchained.sh

**macOS**: use the Docker lane (tested route). Honest label: same hardened linux/amd64 image under Docker Desktop emulation, not yet verified on Mac hardware.

After install, bare `sentinel` is identical to the launcher. Re-verify anytime with `.\setup.ps1 -Check` (or `./setup.sh --check`). `-FullTest` runs pytest/Ruff/format/build. Installs are non-editable, so `sentinel` keeps working if the clone moves.

**API key (only for paid runs)**: `sentinel key` prompts hidden and saves to `%LOCALAPPDATA%\sentinel-unchained\openai_api_key` (owner-only). Paid runs are gated behind typing the exact phrase: LAUNCH GPT-5.6 SOL
```

---

## Developer Tools extras — Supported platforms

Honest lane table; labels come straight from the repo's own assessment docs.

```
| Platform | Lane | Honest status |
| --- | --- | --- |
| Windows 10/11 (AMD64, CPython 3.11.9) | Native install via setup.ps1 or get.ps1 | Validated flagship. 404/404 tests pass in 25.11s, ruff clean (run 2026-07-20). |
| Linux | setup.sh / hardened Docker image | STATIC-ONLY: read and reasoned, not executed on a real host. README notes the same suite runs in the Linux container with a few Windows-only tests skipping. |
| macOS | Docker lane only | Same hardened linux/amd64 image under Docker Desktop emulation; not yet verified on Mac hardware. |
```

---

## Developer Tools extras — How judges can test it ($0, no key)

```
**Fastest no-key lane (zero spend).** Every command below returns in well under a second and never contacts OpenAI; the pip install is the only wait (~1-2 minutes):

    git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
    py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
    .judge\Scripts\python.exe -m unchained onboard
    .judge\Scripts\python.exe -m unchained profile docker/fixtures --json

**Full-isolation alternative** (docker compose build takes several minutes cold):

    git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
    docker compose build
    docker compose run --rm offline profile /evidence --json

The offline container reads no evidence you did not mount, takes no key, and has no network. Expected fixture facts: logs-only shape, evidence ID E001, openai_called=false, matching custody hashes.

**No-key demo script** (Windows):

    powershell -NoProfile -ExecutionPolicy Bypass -File .\demo.ps1

Expected final lines: DEMO_BUNDLE_VERIFIED_INVALID_INPUT / BUNDLE=...

**No-key bundle inspection** of any run bundle:

    sentinel verify C:\path\to\bundle --require-complete --require-live-gpt56
    sentinel view C:\path\to\bundle

Exit codes: 0 complete, 1 fatal, 2 invalid input/config, 3 PARTIAL (cap or safe mandatory-phase failure).

**If a judge chooses to spend** (optional, never required): depth ceilings are hard stops, not price quotes, reasoning-depth modes, or promises of finding quality — LIGHT: 20 tools / 100,000 tokens / 10 min / $2.50 estimated; HEAVY: 60 tools / 400,000 tokens / 30 min / $10 estimated. Same GPT-5.6 Sol investigator either way; caps fire before dispatch and end the run as an honest PARTIAL instead of overspending. Real measured spend of retained runs: shipped bundle ~$1.16 local estimate, 180,285 tokens, 55.5 s; Sol opening $0.38789875, 59,254 tokens, 43.702 s.
```

---

## 30-second reviewer sanity list

Run this checklist against the pasted form before hitting Submit.

- [ ] Opening tool count says **up to twelve** everywhere. The only permitted "six" is the historical note that the retained run executed 6/6 under the earlier six-tool cap.
- [ ] Zero banned claims: no "faster/better than Qwen" (benchmark is unpublished), no "production-ready", no "should work", no invented numbers or URLs.
- [ ] Numbers spot-check against the receipts and test run: 404/404 tests in 25.11s (24 files); shipped bundle `examples/public-run-partial` — 180,285 tokens, ~$1.16, 55.5 s, 14/14 tools, VALID with 20 artifacts / 62 audit entries; Sol receipt — 59,254 tokens, $0.38789875, 43.702 s, 3,961,843 vol_netscan bytes, 13 artifacts / 38 audit entries recorded at creation; 2,147,483,648 evidence bytes; SHA-256 starting `8079a745`; 19 local bundles (0 COMPLETE / 12 PARTIAL / 7 INVALID); exit code 3.
- [ ] Only real URLs appear: github.com/3sk1nt4n/Unchained, openai.devpost.com/rules, github.com/3sk1nt4n/Sentinel-Ensemble-Qwen (pinned 9f309c61...), dfirmadness.com/the-stolen-szechuan-sauce/.
- [ ] Codex Session ID pasted exactly: `019f61e5-5755-7a02-adb4-618d32baab27`.
- [ ] Video URL no longer says ADDED-ON-UPLOAD. It is the one mandatory gap.
- [ ] PARTIAL is labeled PARTIAL; nothing claims a COMPLETE bundle exists.
- [ ] Submission commit/tag PENDING_FINAL_FREEZE has been resolved to a real frozen commit before submitting.
- [ ] Track reads Developer Tools; deadline 2026-07-21 17:00 PT respected (target Tue ~11:00 ET, hard floor Tue 14:00 ET).
