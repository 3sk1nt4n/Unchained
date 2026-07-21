# Unchained: Final Video Script and Shot List

> **Status: RECORD NOW.** This script supersedes the gate in `docs/DEMO-SCRIPT.md`
> that required a COMPLETE bundle before recording. The controlling plan now
> records the strict COMPLETE
> segment: an authentic COMPLETE Sol + HEAVY bundle ships at
> `examples/public-run-complete` (W5 landed). The PARTIAL segment remains a valid
> honest alternative; the splice slot below is now the recommended main path.

**Runtime target: 2:45. Hard ceiling: 2:59.** Narration paced at ~150 words per
minute. Audio names both Codex (how the project was built) and GPT-5.6 (what it
does at runtime). If AI narration is used, confirm the current rules/FAQ at
https://openai.devpost.com/rules permit it before upload; the read-aloud text is
provided verbatim below either way.

---

## The pitch

> Every security team has the same bottleneck: when an incident hits, a human
> has to reconstruct what happened before the damage spreads. GPT-5.6 can do
> that triage in minutes - but no SOC ships a conclusion it can't audit.
> Unchained fixes the trust problem, not just the speed problem.

## The slides

Slides 1-3 are the published showcase page (dark, scrolling): the hero, the
business case, the authority split, the real findings table, the timeline, and
the verify-it-yourself proof. Screen-record it scrolling as the visual backbone
and cut to the live terminal for the verify. Every number on it comes from the
shipped run `20260721T001718Z-f0cd5641`.

## What a judge can run in 60 seconds for $0

Returns in under a second, no key, no network. The pip install is the only wait.

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
.judge\Scripts\python.exe -m unchained verify examples\public-run-complete --require-complete --require-live-gpt56
```

That prints **VALID** on the authentic GPT-5.6 Sol COMPLETE bundle: 37 artifacts,
194 audit entries, exit 0. The video shows exactly this, plus the sealed run it verifies.

---

## Scene table

**Runtime target 2:45. All numbers are from the shipped run 20260721T001718Z-f0cd5641.**

| Time | Screen content | Narration (read aloud) |
|---|---|---|
| 0:00-0:18 | **Showcase hero** (scroll slowly) | Every security team has the same bottleneck. When an incident hits, a human has to reconstruct what happened before the blast radius grows - and that person is a scarce, expensive analyst. AI can do that triage in minutes. But no security team will ship a conclusion it cannot audit. |
| 0:18-0:36 | **Showcase: authority split** | Unchained is built for exactly that gap. It points GPT-5.6 at one case. The model chooses where to look; deterministic code controls what may run, binds every finding to exact evidence bytes, and re-verifies the entire run offline. It does not ask for trust. It ships proof. |
| 0:36-0:54 | Terminal: type `sentinel`; the guided flow, the $0 case card (`openai_called: false`), then quit the launch card with Q | One word starts a case. Everything before the money screen is free and offline: the evidence is classified and SHA-256 hashed locally before any model call. A paid GPT-5.6 run starts only after an explicit launch choice and a hidden key step. |
| 0:54-1:28 | **Showcase: findings table** (hold on it) | I pointed it at a compromised Windows domain controller - the public DFIR Madness case. GPT-5.6 Sol ran a bounded twenty-turn investigation: thirty-one typed Volatility tools, four findings. Watch the discipline. A fresh-context reviewer confirmed one critical finding - private executable payloads inside the SYSTEM print-spooler process - sent two back for review, and withdrew one as unsupported. It does not inflate. The whole investigation cost two dollars and ninety-two cents and finished in nine minutes thirty-nine seconds. |
| 1:28-1:58 | Terminal: `sentinel verify examples\public-run-complete --require-complete --require-live-gpt56` -> highlight **VALID**, 37 artifacts, 194 audit entries | This exact bundle ships in the repository. Anyone can verify it offline, with no key and no network. An independent checker reconstructs every audited request, re-hashes every artifact, and walks the hash-chained audit log. It returns VALID. Change a single byte of the report and it fails. |
| 1:58-2:18 | `sentinel view examples\public-run-complete`; scroll the inert viewer: custody MATCH, the 31 receipts | The proof viewer is inert - no JavaScript - so it cannot fake its own result. Custody matches: the initial and final SHA-256 are identical. Verification proves the recorded pipeline is consistent and untampered. A human still owns the forensic judgment. That honesty is the point. |
| 2:18-2:45 | **Showcase: close slide** (Codex + GPT-5.6, repo URL) | Codex built this: the evidence lifecycle, the Responses adapter, the typed execution boundary, the downgrade-only reviewer, and the verifier behind a comprehensive offline test gate - the session ID is committed in the repo. At runtime, GPT-5.6 Sol is both the investigator and the reviewer. Unchained: reasoning you can follow, evidence you can check. Clone it and verify it yourself. |

Do not shorten the closing line to "code proves the incident."

### Recording notes

- **Evidence folder (scene at 0:36):** use the local DC01 case folder so the card
  shows the public facts (`E001`, memory, SHA-256 custody, `openai_called: false`).
  Show only the case card; crop or rename any private path. Fallback:
  `sentinel profile docker/fixtures --json` (committed fixture, still `openai_called: false`).
- **Verify flags (scene at 1:28):** the shipped bundle is COMPLETE, so pass
  `--require-complete --require-live-gpt56` - it prints VALID (37 artifacts, 194
  audit entries, exit 0). Never live-verify a `20260719T*` or `20260720T*` bundle
  on camera; the renderer has evolved and they may print INVALID. Only
  `examples/public-run-complete` (run `20260721T001718Z-f0cd5641`) is current.

---

## Slide source

Slides 1-3 are the published showcase page (a self-contained dark HTML page built
from run `20260721T001718Z-f0cd5641`). Screen-record it scrolling as the visual
backbone; every figure on it is from that shipped run.

**Slide 2 (Codex build story) text, if shown as a card:**

```text
BUILT WITH CODEX
Codex Session ID: 019f61e5-5755-7a02-adb4-618d32baab27

Codex implemented and adversarially reviewed:
evidence lifecycle - Responses API adapter - typed execution boundary
caps - typed-DONE-v2 - forced serializer - exact evidence spans
fresh-context downgrade-only review - report + inert viewer renderers
independent offline verifier - CLI - Docker isolation - tests - docs

378 passing tests across 23 test files - ruff clean
Runs GPT-5.6 at runtime (Sol investigator/reviewer, Terra smoke canary)
```

---

## Narration-only read script (for AI voice or human read)

Read at ~150 words per minute; ~2:40 of speech inside a 2:45 cut. Sections match
the scene table.

1. Every security team has the same bottleneck. When an incident hits, a human
   has to reconstruct what happened before the blast radius grows - and that
   person is a scarce, expensive analyst. AI can do that triage in minutes. But
   no security team will ship a conclusion it cannot audit.
2. Unchained is built for exactly that gap. It points GPT-5.6 at one case. The
   model chooses where to look; deterministic code controls what may run, binds
   every finding to exact evidence bytes, and re-verifies the entire run offline.
   It does not ask for trust. It ships proof.
3. One word starts a case. Everything before the money screen is free and offline:
   the evidence is classified and SHA-256 hashed locally before any model call. A
   paid GPT-5.6 run starts only after an explicit launch choice and a hidden key step.
4. I pointed it at a compromised Windows domain controller - the public DFIR
   Madness case. GPT-5.6 Sol ran a bounded twenty-turn investigation: thirty-one
   typed Volatility tools, four findings. Watch the discipline. A fresh-context
   reviewer confirmed one critical finding - private executable payloads inside the
   SYSTEM print-spooler process - sent two back for review, and withdrew one as
   unsupported. It does not inflate. The whole investigation cost two dollars and
   ninety-two cents and finished in nine minutes thirty-nine seconds.
5. This exact bundle ships in the repository. Anyone can verify it offline, with no
   key and no network. An independent checker reconstructs every audited request,
   re-hashes every artifact, and walks the hash-chained audit log. It returns VALID.
   Change a single byte of the report and it fails.
6. The proof viewer is inert - no JavaScript - so it cannot fake its own result.
   Custody matches: the initial and final SHA-256 are identical. Verification proves
   the recorded pipeline is consistent and untampered. A human still owns the
   forensic judgment. That honesty is the point.
7. Codex built this: the evidence lifecycle, the Responses adapter, the typed
   execution boundary, the downgrade-only reviewer, and the verifier behind a
   four-hundred-plus-test offline gate - the session ID is committed in the repo.
   At runtime, GPT-5.6 Sol is both the investigator and the reviewer. Unchained:
   reasoning you can follow, evidence you can check. Clone it and verify it yourself.

---

## Pre-record checklist

- [ ] Recording resolution 1920x1080; terminal and showcase page fill the frame.
- [ ] Terminal font large enough that 64-character SHA-256 lines are readable at 1080p.
- [ ] Quiet dark ANSI theme; plain prompt; no powerline/rainbow segments.
- [ ] Rehearse every command once off camera, in order. Nothing may error on camera.
- [ ] Confirm `sentinel verify examples\public-run-complete --require-complete --require-live-gpt56`
      prints VALID (37 artifacts, 194 audit entries) before recording.
- [ ] No secrets on screen: never run `sentinel key`; never echo `$env:OPENAI_API_KEY`;
      the key file path under `%LOCALAPPDATA%\sentinel-unchained\` must never appear.
      The guided key step appears only AFTER a launch-card choice (1/2/3).
- [ ] No private filesystem paths, hidden tabs, or notifications in frame; Do Not Disturb on.
- [ ] Every number shown exists in the shipped bundle `examples/public-run-complete`.
- [ ] Audio clear at normal laptop volume; narration ~150 wpm.
- [ ] Final cut under 2:59; target 2:45. Upload public on YouTube; confirm it plays signed-out.

---

## Below the fold: honest caveats (kept, not cut)

True in the video and in all submission copy; none block recording.

- The video stars the authentic COMPLETE GPT-5.6 Sol bundle at
  `examples/public-run-complete` (run `20260721T001718Z-f0cd5641`), which passes
  strict verify. All figures shown come from it.
- No frozen same-evidence competitive benchmark is published. The video makes no comparative
  speed, cost, or accuracy claim. Deliberately cut; no unmeasured claims.
- Exact receipts establish execution and citation support, not forensic truth. Offline
  verification validates recorded metadata; it does not authenticate OpenAI and does not
  decide forensic truth. The narration says interpretation stays human.
- The fresh reviewer is a same-family model call, not independent ground truth.
- Linux/macOS/Docker claims are static-only; the video records on Windows and claims only Windows behavior.
- Private worker containment is not a complete OS sandbox; a privileged actor who can
  rewrite and reseal the whole local bundle is outside the current trust boundary.

## Pending items (labeled plainly)

| Item | Status |
|---|---|
| Video link | https://youtu.be/ci2M8LmY2hY |
| Submission commit/tag | `buildweek-2026-final` |
| Authentic COMPLETE bundle / public viewer | Shipped: `examples/public-run-complete` (run 20260721T001718Z, strict-VALID) |
| Same-evidence competitive benchmark | Deliberately cut; no unmeasured claims |

Rules of record: https://openai.devpost.com/rules (video under three minutes,
public on YouTube, clear audio, covers what was built and how Codex and GPT-5.6
were used). Deadline 2026-07-21 17:00 PT.
