# Unchained: Final Video Script and Shot List

> **Status: RECORD NOW.** This script supersedes the gate in `docs/DEMO-SCRIPT.md`
> that required a COMPLETE bundle before recording. Per `HACKATHON_HANDOVER.md`
> (2026-07-20, W2/W7), the controlling plan records today with the authentic
> retained PARTIAL bundle, honestly labeled. An optional splice slot below
> upgrades one 20-second segment if a COMPLETE run (W5) lands before upload.

**Runtime target: 2:45. Hard ceiling: 2:59.** Narration paced at ~150 words per
minute. Audio names both Codex (how the project was built) and GPT-5.6 (what it
does at runtime). If AI narration is used, confirm the current rules/FAQ at
https://openai.devpost.com/rules permit it before upload; the read-aloud text is
provided verbatim below either way.

---

## The pitch

> GPT-5.6 chooses where to look; deterministic code controls what may run and
> verifies exactly what was executed and cited.

## What a judge can run in 60 seconds for $0

Every command below returns in well under a second and never contacts OpenAI.
The pip install is the only wait (~1-2 minutes).

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
.judge\Scripts\python.exe -m unchained onboard
.judge\Scripts\python.exe -m unchained profile docker/fixtures --json
```

Full-isolation alternative (build takes several minutes cold):

```powershell
docker compose build
docker compose run --rm offline profile /evidence --json
```

The video demonstrates exactly this lane, plus the retained authentic GPT-5.6
bundle that ships in the repository.

---

## Scene table

| Time | Screen content | Command / slide | Narration (read aloud) |
|---|---|---|---|
| 0:00-0:15 | **Slide 1** (hero + pitch) | Slide 1 | Autonomous forensic agents are easy to demo and hard to trust. Unchained splits the job: GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited. |
| 0:15-0:38 | Terminal. Type the one word `sentinel`. Guided flow appears: onboarding, evidence checks, the API-key step (skip it, type nothing), the launch gate text. | `sentinel` | One word starts a case. Typing sentinel opens the guided flow: onboarding, evidence checks, and a clearly gated launch step. Nothing here spends money. A paid GPT-5.6 run starts only after the exact phrase LAUNCH GPT-5.6 SOL is typed. Everything before that gate is free and offline. |
| 0:38-0:58 | The $0 case card: `E001 · Windows memory · 2,147,483,648 bytes · SHA-256 8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62` and `openai_called: false` highlighted. | `sentinel profile <EVIDENCE_FOLDER> --json` (see Scene 3 note) | Before any model call, deterministic code profiles the evidence: public ID E001, Windows memory, two gigabytes, and its SHA-256 custody hash. Note openai underscore called: false. This step costs zero dollars. Local paths never become model authority. |
| 0:58-1:23 | Run verify on the shipped authentic bundle. As output prints, highlight fourteen typed tool receipts, all status success, and `gpt-5.6-luna` on the model line. On-screen caption: "Committed copy of run 20260720T013927Z-9f12ec6f — clone the repo and run this yourself." | `sentinel verify examples\public-run-partial` | Now the real thing. This bundle ships in the repository: an authentic GPT-5.6 run on that two-gigabyte memory image, provider-recorded gpt-5.6-luna across four responses. GPT-5.6 opened with a parallel batch of typed Volatility tools and kept investigating: fourteen tool receipts, every one successful, every byte of output retained. |
| 1:23-1:43 | Same terminal. Highlight: terminal cap reason `MAX_TOOL_CALLS: reservation would reach 14 > 13`; result **VALID**; terminal status PARTIAL; 20 artifacts and 62 audit entries verified. **[SPLICE SLOT eligible, see below]** | (same command, output already on screen) | Then the hard tool budget ended the run as an honest PARTIAL before any overspend: about fifty-six seconds, one hundred eighty thousand provider tokens, a local cost estimate near a dollar sixteen. The offline verifier reconstructs 20 artifacts and 62 hash-chained audit entries and returns VALID. No network, no key. |
| 1:43-2:06 | The inert viewer. Scroll: custody row (initial SHA-256 equals final), typed tool receipts, the honest hard-budget stop labeled plainly. | `sentinel view examples\public-run-partial` | The bundle ships an inert, no-JavaScript viewer. A judge needs no Python, no key, and no server. Custody intact: initial and final SHA-256 match. A receipt for every tool, and the cap stop labeled plainly. Receipts prove what ran and what was cited. Interpretation stays human. |
| 2:06-2:26 | **Slide 2** (Built with Codex, Session ID on screen) | Slide 2 | Codex was the primary implementation and adversarial-review collaborator: the evidence lifecycle, the Responses API adapter, the typed execution boundary, caps, the forced serializer, exact evidence spans, the downgrade-only review, the renderers, the verifier, and the 404-test offline gate. The Codex session ID is on screen and committed in the repo. |
| 2:26-2:45 | **Slide 3** (track, repo URL, verify-it-yourself commands) | Slide 3 | Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a bounded investigation whose actions, citations, custody, and final report can be checked independently. Clone the repo and verify it yourself, for zero dollars. |

Do not shorten the closing line to "code proves the incident."

### Scene 3 note (evidence folder)

Use the local DC01 evidence folder so the card shows the public case facts
above (E001, 2,147,483,648 bytes, SHA-256 8079a745...). Display only the case
card; if the terminal echoes a private local path, use a neutral directory name
or crop the frame. Fallback if the DC01 folder is unavailable on the recording
machine: `sentinel profile docker/fixtures --json` (committed fixture,
logs-only, still shows E001, SHA-256 custody, and `openai_called: false`).

### Scene 4-5 note (verify flags)

Do **not** pass `--require-complete` on this bundle; it is PARTIAL by design
and plain `sentinel verify` returns VALID — proven on current code 2026-07-20:
20 artifacts, 62 audit entries. The strict flags belong to the splice slot
only.

Never run a live verify on a 2026-07-19 bundle (including
`unchained-runs\20260719T020118Z-ede6c445`): the deterministic renderer has
evolved since they were sealed, so they print INVALID on current code. Their
committed sanitized receipt (`docs/runs/sol-capped-dc01-opening.json`, VALID
recorded at creation with 13 artifacts / 38 audit entries) remains accurate
history and may be shown as a document — never as a live verify.

---

## OPTIONAL 20-SECOND SPLICE SLOT (1:23-1:43)

**Use only if W5 lands: an authentic COMPLETE GPT-5.6 bundle exists before
upload.** This slot replaces the 1:23-1:43 segment one-for-one; total runtime
does not change. If W5 does not land, record the PARTIAL segment as scripted
above and change nothing.

| Time | Screen content | Command | Narration (read aloud) |
|---|---|---|---|
| 1:23-1:43 | Strict verify on the COMPLETE bundle: result VALID, terminal status COMPLETE. | `sentinel verify <COMPLETE_BUNDLE_PATH> --require-complete --require-live-gpt56` | This time the case ran to a typed DONE: forced structured findings, a fresh-context reviewer that can only preserve or downgrade, and a sealed COMPLETE bundle. The strict verifier, require-complete and require-live-GPT-5.6, reconstructs the whole lifecycle and returns VALID. |

`<COMPLETE_BUNDLE_PATH>`: PENDING_COMPLETE_RUN. Exists only if W5 lands.

---

## Slide contents

The three text slides below can be shown as-is or rendered from
`submission/slides/slides.html`: script Slide 1 = deck slide 1, script Slide 2 =
deck slide 6, script Slide 3 = deck slide 9. The deck's close slide shows the
repo URL but omits the command block; either version works — the narration does
not read the commands aloud.

### Slide 1 (cold open, 0:00-0:15)

```text
UNCHAINED
Bounded autonomous DFIR, built with Codex, run by GPT-5.6

GPT-5.6 chooses where to look; deterministic code controls
what may run and verifies exactly what was executed and cited.

OpenAI Build Week · Developer Tools track
```

### Slide 2 (Codex build story, 2:06-2:26)

```text
BUILT WITH CODEX
Codex Session ID: 019f61e5-5755-7a02-adb4-618d32baab27

Codex implemented and adversarially reviewed:
evidence lifecycle · Responses API adapter · typed execution boundary
caps · typed-DONE-v2 · forced serializer · exact evidence spans
fresh-context downgrade-only review · report + inert viewer renderers
independent offline verifier · CLI · Docker isolation · tests · docs

404 passing tests across 24 test files · ruff clean
Runs GPT-5.6 at runtime (Sol investigator/reviewer, Luna canary)
```

### Slide 3 (close, 2:26-2:45)

```text
Developer Tools track · OpenAI Build Week
https://github.com/3sk1nt4n/Unchained   (public, MIT)

Verify it yourself, $0, no key:
  git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
  docker compose build
  docker compose run --rm offline

Inspect the shipped authentic GPT-5.6 bundle:
  sentinel verify examples\public-run-partial
```

---

## Narration-only read script (for AI voice or human read)

Read at ~150 words per minute. Total ~395 words, ~2:40 of speech inside a 2:45
cut. Section breaks match the scene table.

1. Autonomous forensic agents are easy to demo and hard to trust. Unchained
   splits the job: GPT-5.6 chooses where to look; deterministic code controls
   what may run and verifies exactly what was executed and cited.
2. One word starts a case. Typing sentinel opens the guided flow: onboarding,
   evidence checks, and a clearly gated launch step. Nothing here spends money.
   A paid GPT-5.6 run starts only after the exact phrase LAUNCH GPT-5.6 SOL is
   typed. Everything before that gate is free and offline.
3. Before any model call, deterministic code profiles the evidence: public ID
   E001, Windows memory, two gigabytes, and its SHA-256 custody hash. Note
   openai underscore called: false. This step costs zero dollars. Local paths
   never become model authority.
4. Now the real thing. This bundle ships in the repository: an authentic
   GPT-5.6 run on that two-gigabyte memory image, provider-recorded
   gpt-5.6-luna across four responses. GPT-5.6 opened with a parallel batch of
   typed Volatility tools and kept investigating: fourteen tool receipts,
   every one successful, every byte of output retained.
5. Then the hard tool budget ended the run as an honest PARTIAL before any
   overspend: about fifty-six seconds, one hundred eighty thousand provider
   tokens, a local cost estimate near a dollar sixteen. The offline verifier
   reconstructs 20 artifacts and 62 hash-chained audit entries and returns
   VALID. No network, no key.
6. The bundle ships an inert, no-JavaScript viewer. A judge needs no Python, no
   key, and no server. Custody intact: initial and final SHA-256 match. A
   receipt for every tool, and the cap stop labeled plainly. Receipts prove
   what ran and what was cited. Interpretation stays human.
7. Codex was the primary implementation and adversarial-review collaborator:
   the evidence lifecycle, the Responses API adapter, the typed execution
   boundary, caps, the forced serializer, exact evidence spans, the
   downgrade-only review, the renderers, the verifier, and the 404-test offline
   gate. The Codex session ID is on screen and committed in the repo.
8. Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a
   bounded investigation whose actions, citations, custody, and final report
   can be checked independently. Clone the repo and verify it yourself, for
   zero dollars.

---

## Pre-record checklist

- [ ] Recording resolution 1920x1080; terminal window sized to fill the frame.
- [ ] Terminal font large enough that the 64-character SHA-256 lines wrap
      cleanly and are readable at 1080p.
- [ ] Quiet ANSI theme: dark solid background, no transparency, plain prompt,
      no rainbow/powerline segments.
- [ ] Rehearse every command once off camera, in order, on this machine.
      Nothing may error on camera.
- [ ] Confirm before recording that
      `sentinel verify examples\public-run-partial` prints VALID with 20
      artifacts and 62 audit entries (no `--require-complete`; PARTIAL by
      design). Never verify a `20260719T*` bundle on camera — those print
      INVALID on current code.
- [ ] No secrets on screen: never run `sentinel key`; never echo
      `$env:OPENAI_API_KEY`; the key file path under
      `%LOCALAPPDATA%\sentinel-unchained\` must never appear; skip the guided
      key step by typing nothing.
- [ ] No private filesystem paths, hidden browser tabs, or notification pop-ups
      in frame; enable Do Not Disturb.
- [ ] At the guided-flow launch gate, do NOT type LAUNCH GPT-5.6 SOL on camera;
      show the gate, spend nothing.
- [ ] Every number shown exists in a committed artifact
      (`docs/runs/sol-capped-dc01-opening.json` for all bundle figures).
- [ ] Audio clear at normal laptop volume; narration ~150 wpm.
- [ ] Final cut under 2:59; target 2:45. Time it before upload.
- [ ] Upload public on YouTube; confirm the URL plays in a signed-out browser.

---

## Below the fold: honest caveats (kept, not cut)

These stay true in the video and in all submission copy. None of them block
recording.

- The retained Sol bundle proves the live opening/tool/cap/custody path, but it
  is PARTIAL; no authentic COMPLETE GPT-5.6 vNext bundle is published yet. The
  video labels it PARTIAL on screen and in narration.
- The retained run executed six opening tools under the earlier six-tool cap;
  the opening now allows up to twelve. The mandatory on-screen caption in the
  0:58-1:23 scene states this.
- No frozen same-evidence Qwen benchmark is published. The video makes no
  comparative speed, cost, or accuracy claim of any kind. Deliberately cut; no
  unmeasured claims.
- Exact receipts establish execution and citation support, not forensic truth.
  Offline verification validates recorded metadata; it does not authenticate
  OpenAI and does not decide forensic truth. The narration says interpretation
  stays human.
- The fresh reviewer is a same-family model call, not independent ground truth.
- The Luna receipt is a second-reviewer attestation (project-affiliated), not
  bundle-derived proof; it is not shown in the video.
- Linux/macOS/Docker claims are static-only (read and reasoned, not executed on
  a real host); macOS runs the Docker lane under emulation, not yet verified on
  Mac hardware. The video records on Windows and claims only Windows behavior.
- Private worker containment is not a complete OS sandbox; SHA-256 pre/post
  checks do not defeat every privileged concurrent pathname race; a privileged
  actor who can rewrite and reseal the whole local bundle is outside the
  current trust boundary.

## Pending items (labeled plainly)

| Item | Status |
|---|---|
| Video link | Added on upload |
| Submission commit/tag | PENDING_FINAL_FREEZE |
| Authentic COMPLETE bundle / public viewer | PENDING_COMPLETE_RUN (splice slot only) |
| Same-evidence Qwen benchmark | Deliberately cut; no unmeasured claims |

Rules of record: https://openai.devpost.com/rules (video shorter than three
minutes, public on YouTube, clear audio, covers what was built and how Codex
and GPT-5.6 were used). Deadline 2026-07-21 17:00 PT; Devpost submit target
Tuesday ~11:00 ET, hard floor Tuesday 14:00 ET.
