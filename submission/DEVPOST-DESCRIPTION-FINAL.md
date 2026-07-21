## Inspiration

Agentic AI is being pointed at real evidence and real infrastructure, but what it produces today is a transcript: a self-reported narrative of what the model says it did. In DFIR that is not an input anyone can act on. An incident response consultancy cannot hand a chat log to a regulator or opposing counsel and call it findings; a compliance reviewer cannot certify a conclusion whose citations cannot be resolved to exact bytes; an expert witness cannot testify to an analysis whose tool executions were never independently retained. The gap is structural, not a model-quality problem: the model's narrative and the evidentiary record are the same object, so there is nothing to check the narrative against. Unchained was built to separate them. The thesis in one sentence: agentic AI in high-consequence domains is only sellable when every action it took can be checked by someone who does not trust the agent, the vendor, or the transcript.

## What it does

GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited.

**Try it in about 60 seconds, $0, no API key.** After a 1-2 minute pip install, every command below returns in well under a second and never contacts OpenAI:

    git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
    py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
    .judge\Scripts\python.exe -m unchained onboard
    .judge\Scripts\python.exe -m unchained profile docker/fixtures --json

Linux/macOS: the same $0 lane runs natively via ./setup.sh or in the hardened Docker container - both executed and verified live on 2026-07-21 (see the README's "Do I need Docker?" tip).

**What it is.** Unchained is a bounded autonomous Digital Forensics & Incident Response (DFIR) investigator built with Codex and GPT-5.6. It profiles an evidence folder without a model call, establishes SHA-256 custody, exposes only route-eligible typed read-only tools, and lets GPT-5.6 choose an opening of up to twelve tools that code validates all-or-none and executes concurrently. Later turns carry a compact visible ledger and allow one typed action at a time. A strict typed `finish_investigation(status="DONE")` forces structured findings, a fresh-context reviewer may preserve or downgrade them, and deterministic code resolves exact UTF-8 evidence spans, renders the authoritative report and inert viewer, seals a content-addressed bundle, and verifies the complete lifecycle offline.

The differentiator is not that an LLM can call forensic tools. It is that model strategy and evidence authority are separated clearly enough for a judge or analyst to inspect. Receipts prove what ran, what output was retained, and what exact text was cited. They do not pretend to prove forensic truth; a human still owns interpretation and response.

**Three real, retained GPT-5.6 runs back this.**

**The flagship ships in the repository and strict-verifies on current code** (`examples/public-run-complete`, a committed copy of run `20260721T001718Z-f0cd5641`):

- Provider recorded `gpt-5.6-sol` across 24 responses, request/response IDs retained.
- Real 2,147,483,648-byte DC01 Windows memory image; custody match true.
- 31/31 typed tool receipts across 20 turns; terminal status COMPLETE with 4 adjudicated findings (1 CONFIRMED, 2 NEEDS-REVIEW, 1 UNSUPPORTED) after fresh-context judge review.
- Measured: 9m39s wall, ~395,555 provider-reported tokens, local cost estimate $2.92 - within the stock HEAVY caps ($10 / 400,000 tokens).
- Verify it yourself after cloning, no key, no network: `sentinel verify examples/public-run-complete --require-complete --require-live-gpt56` → VALID, 37 artifacts, 194 hash-chained audit entries (proven 2026-07-21).

**The second proof is a clearly labeled PARTIAL bundle, also shipped in the repository and re-verifiable on current code** (`examples/public-run-partial`, a committed copy of run `20260720T013927Z-9f12ec6f`):

- Provider recorded `gpt-5.6-luna` across 4 responses, request/response IDs retained.
- Same 2,147,483,648-byte DC01 Windows memory image; custody match true.
- 14 typed Volatility tool receipts, all status "success"; the hard tool budget then ended the run honestly - terminal_reason "MAX_TOOL_CALLS: reservation would reach 14 > 13", status PARTIAL, exit code 3.
- Measured: 55.5 s wall, 180,285 provider-reported tokens, local cost estimate $1.16.
- Verify it yourself after cloning, no key, no network: `sentinel verify examples/public-run-partial` → VALID, 20 artifacts, 62 hash-chained audit entries (proven 2026-07-20).

**The third is the earlier `gpt-5.6-sol` capped opening** (sanitized receipt committed at `docs/runs/sol-capped-dc01-opening.json`, run `20260719T020118Z-ede6c445`):

- Requested model `gpt-5.6`; provider recorded `gpt-5.6-sol` on both of 2 responses, request/response IDs retained.
- Real evidence: 2,147,483,648-byte DC01 Windows memory image (public Stolen Szechuan Sauce case), SHA-256 `8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62`, custody match true (initial == final hash).
- Opening phase: 6 typed Volatility tools selected, 6 executed, 0 rejected - vol_pstree, vol_psscan, vol_netscan, vol_malfind, vol_cmdline, vol_svcscan, all status "success"; vol_netscan alone retained 3,961,843 output bytes. (This run predates the current cap; the opening now allows up to twelve tools.)
- Fail-closed cap: the 7th requested tool (vol_dlllist) was refused before dispatch - terminal_reason "MAX_TOOL_CALLS: reservation would reach 7 > 6" - and received a capped receipt with duration_ms 0: "No successful forensic execution is claimed." Terminal status PARTIAL, exit code 3.
- Measured: 43.702 s wall, 59,254 provider-reported tokens, local cost estimate $0.38789875 under a $1.00 cap.
- Offline verification recorded at creation (2026-07-19): VALID, 13 artifacts and 38 hash-chained audit entries. Proof bundles bind byte-exactly to the renderer that produced them, so this earlier bundle re-verifies only against its creating code version; the shipped bundle above is the one to re-verify on current code.

**A completed case makes exactly 4 fixed GPT-5.6 requests (opening book, findings serialization, fresh review, report draft) plus one per adaptive action - minimum five, never an unbounded loop.**

**Honest limits (kept on purpose):**
- The shipped COMPLETE bundle is one public case (DC01) on one OS route, not a measured benchmark; earlier retained runs also include PARTIAL and INVALID states, which we keep rather than cherry-pick.
- Exact receipts establish execution and citation support, not forensic truth. The fresh reviewer is a same-family model call, not independent ground truth.
- No frozen same-evidence competitive latency/cost/accuracy benchmark is published yet - deliberately cut rather than making unmeasured claims.
- Private worker containment and process-tree cleanup are not a complete OS sandbox; SHA-256 pre/post checks do not defeat every privileged concurrent pathname race; a privileged actor who can rewrite and reseal the whole local bundle is outside the current trust boundary (signed/timestamped external anchoring is future work).
- The Linux lanes are no longer static claims: on 2026-07-21 the hardened Docker container built clean and passed the suite in-container (369 passed + 9 Windows-only skips), the native Linux lane ran end to end in WSL Ubuntu (setup -> $0 flow -> verify), and the Windows-sealed COMPLETE bundle strict-verified VALID inside the no-network Linux container - byte-exact across operating systems. macOS remains the same hardened linux/amd64 container via Docker Desktop, not yet verified on Mac hardware.

Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a bounded investigation whose actions, citations, custody, and final report can be checked independently.

## How we built it

**Codex Session ID: 019f61e5-5755-7a02-adb4-618d32baab27** (majority-core /feedback session; core functionality build).

Codex was the primary implementation and adversarial-review collaborator for the Build Week work in this repository: the evidence lifecycle, Responses API adapter, typed execution boundary, caps, retry/usage accounting, typed-DONE-v2 protocol, forced serializer, exact evidence spans, fresh-context downgrade-only review, report/viewer renderers, independent verifier, CLI, Docker isolation, tests, benchmark design, and documentation.

**What Codex accelerated**:
- Repository inspection and architecture implementation.
- Typed controller, evidence, tool, audit, cap, and report-safety code.
- Adversarial tests and defect reproduction.
- Live-rules and official-API verification.
- Code, security, experiment, judge-experience, and strategy review.
- Documentation, handover, and prompt construction.
- Proof-bundle, provider-proof, verifier, reproducible-environment, and dependency-lock implementation recorded by later commits.

**Concrete Build Week code built with Codex** (all in this repo's Git history): src/unchained/evidence.py, tools.py + _tool_worker.py, model.py (Responses API integration), agent.py (opening selection, adaptive loop, forced finalization, fresh review), audit.py, artifacts.py, verify.py, caps.py, models.py, prompts.py, cli.py, __main__.py, all tests under tests/, plus the README and submission docs.

**What the human owned.** The human owner chose the product thesis, Developer Tools track, DFIR testbed, evidence case, authority split, benchmark, scope cuts, claim language, and final submission decisions. Specifically: choosing the controlled-autonomy versus deterministic-trust comparison; choosing Developer Tools and the trust-measurement framing; selecting DFIR as the demonstration domain; choosing DC01 as the known-answer public benchmark; accepting the single-case and possible training-contamination limitations; requiring truthful scope labels and a no-fake-evidence policy; approving scope cuts, public claims, the frozen rubric, and final submission.

**GPT-5.6 at runtime:** GPT-5.6 is the Sol investigator/reviewer, with a Terra connectivity smoke lane (the retained live canary was one Luna request, 186 input + 27 output tokens, labeled NONQUALIFYING_CONNECTIVITY_SMOKE).

A follow-up Codex thread covered Docker/README work: 019f76f3-a19f-71d1-81b2-eed6305857f6 (thread provenance only, not a feedback receipt unless submitted successfully).

## Challenges we ran into

**Token throughput vs. rich context.** New OpenAI accounts cap around 200k tokens per minute, while a rich 12-tool serializer packet can reach ~270k tokens. Result: 429s that end a run as an honest PARTIAL rather than a silent retry storm. The shipped COMPLETE run finished within the stock HEAVY ceilings ($2.92 of $10, ~395,555 of 400,000 tokens); for richer or longer runs the README documents optional headroom overrides (e.g. MAX_TOTAL_TOKENS=3000000, MAX_COST_USD=30).

**Fail-closed by design, proven in the retained run.** Caps fire BEFORE dispatch. In the committed receipt, the 7th requested tool (vol_dlllist) was refused with terminal_reason "MAX_TOOL_CALLS: reservation would reach 7 > 6" and received a capped receipt with duration_ms 0 stating "No successful forensic execution is claimed." The run ended PARTIAL with exit code 3 - under budget ($0.38789875 local estimate against a $1.00 cap) and fully audited (38 hash-chained entries). The same fail-closed behavior repeats on current code in the shipped bundle `examples/public-run-partial`: 14 successful receipts, then terminal_reason "MAX_TOOL_CALLS: reservation would reach 14 > 13".

**All-or-none opening validation.** The GPT-5.6 opening must choose one to twelve distinct route-valid typed calls. An unknown, duplicate, malformed, or thirteenth call rejects the whole opening rather than running a valid-looking subset. Getting the model to reliably meet a strict typed contract - and refusing everything that misses it - was harder than accepting best-effort output, and worth it.

**Terminal authority.** Prose, Markdown, and empty output have no terminal authority. Only the typed finish_investigation({"status":"DONE"}) call terminates a case (terminal contract v2; the verifier still reads historical literal-DONE-v1 bundles).

**Honest bundle census.** A COMPLETE Sol + HEAVY bundle now exists and ships at `examples/public-run-complete`; earlier retained runs span PARTIAL and INVALID states, which we keep and label rather than cherry-picking.

## Accomplishments that we're proud of

- **378/378 tests pass in 22.5s** across 23 test files, ruff check + format clean, verified 2026-07-21 on CPython 3.11.9.
- **Three authentic, retained GPT-5.6 runs on real evidence**: the flagship COMPLETE bundle shipped in the repo (`examples/public-run-complete`: `gpt-5.6-sol`, 31/31 typed Volatility tools across 20 adaptive turns on a 2 GiB DC01 Windows memory image, 4 adjudicated findings, custody hash match), a clearly labeled PARTIAL bundle also shipped (`examples/public-run-partial`: `gpt-5.6-luna`, 14/14 typed tools, honest stop at the hard tool budget), and a committed sanitized `gpt-5.6-sol` receipt (6 of 6 opening tools with provider request/response IDs, docs/runs/sol-capped-dc01-opening.json).
- **Byte-exact offline verification**: the flagship bundle strict-verifies VALID on current code - `sentinel verify examples/public-run-complete --require-complete --require-live-gpt56`, 37 artifacts and 194 hash-chained audit entries reconstructed and checked with no network and no key (proven 2026-07-21); the PARTIAL bundle verifies VALID with 20 artifacts and 62 audit entries (proven 2026-07-20).
- **Measured, capped spend**: flagship COMPLETE run ~395,555 provider-reported tokens, 9m39s, ~$2.92 local estimate within the stock HEAVY caps; PARTIAL run 180,285 tokens, 55.5 s, ~$1.16; Sol opening 59,254 tokens, 43.702 s, $0.38789875 under a $1.00 cap.
- **A $0 judge lane**: onboarding, fixture profiling, bundle verify/view, an offline Docker container, and a no-key demo script - none of which contact OpenAI.
- **An explicit spend gate**: a paid run starts only after a launch-card choice (1 = quick Terra test, 2 = full Terra run, 3 = qualifying Sol, Q = quit) plus a saved-key step showing hard cost ceilings. No accidental spend.
- **A bounded invocation budget**: exactly 4 fixed GPT-5.6 requests plus one per adaptive action - minimum five, never an unbounded loop.
- **An inert deliverable**: a static no-JS viewer.html plus an authoritative report, sealed in a content-addressed bundle with a manifest and SHA-256.

## What we learned

- The valuable line is not "an LLM can call forensic tools." It is drawing the authority split sharply enough to inspect: the model chooses bounded strategy and proposes findings; deterministic code owns evidence identity, legality, caps, execution, citation spans, verdict monotonicity, report rows, and verification.
- Receipts should prove execution and citation support - and explicitly not claim forensic truth. Saying what a proof does NOT establish is as important as saying what it does.
- Fail-closed beats optimistic. Refusing a 7th tool before dispatch and ending PARTIAL produced a more trustworthy artifact than any best-effort completion would have.
- Typed terminal contracts work. Once prose lost terminal authority and only finish_investigation({"status":"DONE"}) could end a case, "did it finish?" became a checkable fact instead of a judgment call.
- Token budgeting is a first-class design constraint: TPM ceilings and serializer packet size shape the protocol, not just the bill.
- Monotonic review is a cheap, honest safety layer: a fresh-context reviewer that can only preserve or downgrade findings can never inflate them.

## What's next for Unchained

- Broaden the COMPLETE proof beyond one case: the first authentic COMPLETE GPT-5.6 Sol bundle now ships at `examples/public-run-complete`; next is a second case and a frozen benchmark.
- Ship the frozen same-evidence competitive benchmark that was deliberately cut for Build Week - we make no unmeasured comparative claims until it exists (prior-work boundary pinned at github.com/3sk1nt4n/Sentinel-Ensemble-Qwen, commit 9f309c6134e857f7b86f3e6b9c6709ce954944a5).
- Signed/timestamped external anchoring of bundles, since a privileged actor who can rewrite and reseal a whole local bundle is outside the current trust boundary.
- Verify the macOS lane on real Mac hardware (the Linux container and native lanes were executed and verified live on 2026-07-21; macOS still runs the same container under emulation).
- Generalize the pattern beyond DFIR - security testing, compliance review, financial operations: model chooses bounded strategy -> code validates and executes typed authority -> exact outputs and citations are retained -> a monotonic reviewer reduces claims -> deterministic code renders and verifies the deliverable.
