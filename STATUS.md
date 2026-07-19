# Unchained — Status Checklist

> **Unchained reasoning. Chained evidence.**
> A trust-measurement harness for a GPT-5.6-directed DFIR investigator: the model
> chooses where to look; deterministic code proves what happened and seals an
> offline-verifiable proof bundle. Track: **Developer Tools** ·
> Deadline: **2026-07-21, 17:00 PT**.
>
> This is the one-glance scoreboard. The exhaustive ledger is
> [`HACKATHON_HANDOVER.md`](HACKATHON_HANDOVER.md); the sequencing rules are
> [`docs/WINNER_ROADMAP.md`](docs/WINNER_ROADMAP.md).

---

## ✅ Done (verified)

### Engine & correctness (green offline)
- [x] OpenAI-native controller: profile → opening book → parallel typed execution
      → plan/act/observe loop → judge → report → seal.
- [x] Deterministic authority boundary — code owns findings, caps, custody,
      report rows; the model only proposes.
- [x] **typed-DONE-v2** terminal contract (`finish_investigation`); raw-text
      "DONE" is rejected. (`src/unchained/agent.py`)
- [x] Exact evidence-span resolution, downgrade-only fresh judge, deterministic
      report renderer, static inert proof viewer (no JS, CSP).
- [x] Independent standard-library **offline verifier** — re-renders report +
      viewer byte-for-byte, checks custody, receipts, spans, budgets.
- [x] Full offline test suite passes; `ruff check` and `ruff format` clean.

### Runtime & platform
- [x] Cap profiles: **CAUTIOUS** (`--caps strict`) / **FLAGSHIP**
      (`--caps default`); models: **Sol** (investigator) + **Luna** (cheap canary).
- [x] Linux/AMD64 hardened Docker + no-key, no-network offline front door.
- [x] Deterministic native DC01 memory smoke (pstree/psscan/netscan) with
      matching custody — pre-freeze, no model.

### Live milestones (real GPT-5.6, recorded)
- [x] **Luna** connectivity canary — live, attested, explicitly non-qualifying.
- [x] **Sol** capped opening on the real 2 GiB DC01 Windows memory image —
      6 opening tools, 0 rejected; terminal `PARTIAL` (cap fired on purpose);
      bundle verifies **`VALID`** offline. (`docs/OPENAI_VNEXT_RELEASE_HANDOFF.md`)

### Product & provenance
- [x] Rebrand to **Unchained** across all docs, banners, and visible strings
      (deep code identifiers unchanged); README leads with the tagline.
- [x] Public repo, MIT license at root, honest provenance / build boundary.
- [x] Built with **Codex + GPT-5.6**; clean, single-authorship commit history.

---

## ⏳ To do — the winning path, in priority order

> From the rules-vs-repo audit (43 findings). Each numbered block is ordered by
> leverage-per-effort toward the 4 equally-weighted criteria. Never skip the
> freeze, the authentic run, or the honesty rails.

### A. Blockers — do first (cheap, no API key, huge visibility/eligibility gain)
1. **[ ] Push the vNext + rebrand work to the public repo.**
   All of it is committed locally only; GitHub still shows the older, weaker
   project — judges would walk the wrong repo. Fast-forward push to
   `origin`, no history rewrite.
2. **[ ] Add a "Built with Codex + GPT-5.6" section to `README.md`.**
   **Mandatory** — the rules require the Codex-collaboration story *in the
   README*: where Codex accelerated work, which decisions the human owned, how
   GPT-5.6 + Codex shaped the result. (Summarize `BUILD_PROVENANCE.md` §5.)
3. **[ ] Fix the "independent-reviewer-attested" overclaim.**
   Rename to "second-reviewer-attested (project-affiliated)" in the Luna
   receipt kind + `README.md` + `docs/SUBMISSION.md`. Judges can puncture
   "independent."
4. **[ ] Confirm the prior-vs-new-work boundary + Codex Session ID.**
   Judges score **only** work added Jul 13–21; keep `BUILD_PROVENANCE.md`
   crisp and pick the Codex thread that truly holds the majority of core work.

### B. Keystone — the one artifact that unlocks the most points
5. **[ ] Public experiment freeze (C4)** — protocol, rubric, scorer,
   run-selection, code SHA, prompts, catalog, caps, price table, evidence
   hashes, byte ceilings → tag + independent **server timestamp**. *Before
   GPT-5.6 ever investigates DC01.*
6. **[ ] One authentic `COMPLETE` Sol run** (funded key, FLAGSHIP caps) →
   sealed offline-`COMPLETE` proof bundle. *No fake/replay ever counts.*

### C. Ship the proof so a judge can actually test it
7. **[ ] Resolve the rebrand ↔ verify regression, then ship one bundle.**
   The rebranded renderer changed the byte-exact report/viewer output, so any
   bundle sealed *before* the rebrand no longer passes `verify`/`view`. Fix by
   sealing the shipped bundle under the rebranded code (the COMPLETE run will
   be), or make the renderer brand/version-aware for retained bundles. Then
   **commit one sanitized bundle** (viewer.html + receipts) under `docs/runs/`
   or a release — today no real bundle reaches judges at all.
8. **[ ] Make the no-key judge path 2 minutes, not 15.**
   Publish a prebuilt image (GHCR) so the Docker lane is pull-and-run; add a
   `viewer.html` screenshot + report excerpt under the README hero; put a
   3-command no-key lane at the very top of `JUDGE-QUICKSTART.md`.
9. **[ ] Add a Findings/citation card to `viewer.html`** — one row per finding
   (status · quote · evidence ID · byte range · tool-output hash) = true
   one-click claim → receipt.

### D. Submission package (C7)
- [ ] Public **YouTube** demo < 3:00; audio names **Codex + GPT-5.6** and
      states single-case scope; record against the real bundle.
- [ ] Text description on the Devpost form (from `docs/SUBMISSION.md`).
- [ ] Repo public + LICENSE at root (done); working test path.
- [ ] Regenerate `readme-hero.png` / `social-preview.png` with the **Unchained**
      wordmark (they still render "SENTINEL UNCHAINED").
- [ ] Incognito link QA (repo, video, viewer) → submission tag → Devpost →
      retained confirmation.

### E. Stretch
- [ ] Same-evidence Qwen comparison (fail-closed scaffold exists; add frozen
      fact set + measurements). Cut first if time is short.

---

## 🛑 Honesty rails (never cross)
- No fake, replayed, or screenshot "COMPLETE" run — only an authentic
  provider-returned bundle counts.
- Freeze the rubric **before** GPT-5.6 sees DC01; disclose every valid run.
- Don't claim "faster than Qwen," "independent evaluation," or a completed
  investigation until each is measured/true. Single-case, single-OS scope stays
  stated.
- Every published metric carries its numerator, denominator, and source artifact.
