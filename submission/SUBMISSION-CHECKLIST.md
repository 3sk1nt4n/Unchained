# Submission Checklist — Operational Runbook (W7-W11)

**Deadline: Tue 2026-07-21 17:00 PT** (Devpost). **Submit target: Tue ~11:00 ET. Hard floor: Tue 14:00 ET.** Judging runs 2026-07-22 → 2026-08-05. Rules: https://openai.devpost.com/rules

The video is the only mandatory gap. Everything below exists to get it recorded, uploaded, linked, and submitted with zero broken links.

---

## W7 — Video recording pre-flight

- [ ] Script covers, in order: the pitch, the $0 no-key lane, the retained live Sol receipt, and the Codex workflow. Total runtime strictly under 3:00.
- [ ] Foreground the Codex story on screen (Session ID visible, README "Built with Codex" section shown). This is the weakest-evidenced criterion until the video shows it.
- [ ] Use the shipped bundle `examples/public-run-partial` for the live-GPT-5.6 segment (verify prints VALID on current code — proven 2026-07-20: 20 artifacts, 62 audit entries). The committed Sol receipt `docs/runs/sol-capped-dc01-opening.json` may be shown as a document. NEVER run a live verify on a `unchained-runs/20260719T*` bundle — those print INVALID on current code (renderer evolved after they were sealed). Zero new spend required: an honest video can show real GPT-5.6 work today.
- [ ] Say "up to twelve" for the opening. Never say six as the current cap (the retained run's 6/6 was under the earlier cap — label it that way if shown).
- [ ] No banned phrases anywhere in narration or slides: no unmeasured faster/better-than-Qwen claims, no "production-ready", no invented numbers.
- [ ] Clean desktop: notifications off, API key never on screen, terminal font legible at 1080p.
- [ ] Rehearse the no-key commands once so they run first-try on camera.
- [ ] Record. Watch the full playback: audio clear, text readable, runtime under 3:00.

## W8 — YouTube upload

- [ ] Upload the final cut. Visibility: **Public** (not Unlisted, not Private).
- [ ] Title: `Unchained — bounded GPT-5.6 DFIR investigator | OpenAI Build Week (Developer Tools)`
- [ ] Paste this description verbatim:

```
Unchained: GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited.

A bounded autonomous DFIR investigator built with Codex and GPT-5.6 for OpenAI Build Week (Developer Tools track).

Repo (public, MIT): https://github.com/3sk1nt4n/Unchained
Codex Session ID: 019f61e5-5755-7a02-adb4-618d32baab27
Try it with no API key and $0 spend: see JUDGE-QUICKSTART.md in the repo.
Public evidence case: The Stolen Szechuan Sauce (DC01) — https://dfirmadness.com/the-stolen-szechuan-sauce/
```

- [ ] Confirm the watch page shows runtime under 3:00.
- [ ] Incognito playback check: full video plays start to finish while logged out.
- [ ] Copy the final URL into `submission/DEVPOST-FORM.md` (video field) and replace `ADDED-ON-UPLOAD` in `submission/JUDGE-ONE-PAGER.md`.

## W9 — Devpost form, field by field

Open the Devpost submission form and `submission/DEVPOST-FORM.md` side by side. Paste block-for-block:

- [ ] **Project name** field ← the "Project name" block of DEVPOST-FORM.md.
- [ ] **Elevator pitch / tagline** field ← the "Tagline" block (60-char line; use the exact one-line pitch variant in the same block if the field allows ~200 characters).
- [ ] **About the project / description** field ← the "What it does" block. VERIFY the pasted text says "up to twelve" typed tools; the only permitted "six" is the labeled note that the retained run's 6/6 ran under the earlier cap.
- [ ] **How Codex was used** field ← the "How we built it" block (Session ID plus control-plane list).
- [ ] **Built with** field ← the "Built with" block (tag list: python, openai, gpt-5.6, codex, ...).
- [ ] **Try it out / links** field ← repo URL `https://github.com/3sk1nt4n/Unchained` from the Try-it-out links / Repo URL block.
- [ ] **Video URL** field ← the YouTube URL from W8.
- [ ] **Track** ← Developer Tools.
- [ ] **Codex Session ID** field (if the form has one) ← `019f61e5-5755-7a02-adb4-618d32baab27`.
- [ ] If the form has Developer Tools extra fields ← the three "Developer Tools extras" blocks (Installation instructions, Supported platforms, How judges can test it).
- [ ] Run the "30-second reviewer sanity list" at the bottom of DEVPOST-FORM.md against the pasted form.
- [ ] Save as draft. Do not submit yet.

## W10 — /feedback refresh

- [ ] In Codex, open the core-build session and run `/feedback`; confirm it submits successfully.
- [ ] Primary Session ID (majority-core, core functionality build): `019f61e5-5755-7a02-adb4-618d32baab27`.
- [ ] Fallback ID, only if the primary cannot be refreshed: `019f76f3-a19f-71d1-81b2-eed6305857f6` (Docker/README thread — thread provenance only, not a feedback receipt unless submitted successfully).
- [ ] Confirm the ID pasted on Devpost matches the session whose /feedback went through.

## W11 — Final QA and SUBMIT

Fresh incognito browser, logged out of everything:

- [ ] Repo loads: https://github.com/3sk1nt4n/Unchained
- [ ] LICENSE visible on the repo front page (MIT).
- [ ] README "Built with Codex" section renders with the Session ID.
- [ ] `docs/runs/sol-capped-dc01-opening.json` opens in the browser.
- [ ] Video plays start to finish, publicly.
- [ ] Every link in the Devpost preview resolves (click each one).
- [ ] Devpost preview text says "up to twelve" opening tools; no banned phrases survived the paste.
- [ ] Freeze the final commit/tag (currently PENDING_FINAL_FREEZE) and record it in DEVPOST-FORM.md before submitting.
- [ ] **SUBMIT.** Target Tue 11:00 ET; hard floor Tue 14:00 ET; Devpost closes Tue 17:00 PT.
- [ ] Screenshot the confirmation page and save it into `submission/`.
