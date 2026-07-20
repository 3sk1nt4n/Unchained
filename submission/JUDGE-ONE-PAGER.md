# Unchained — Judge One-Pager

> **GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited.**

Unchained is a bounded autonomous DFIR investigator built with Codex and GPT-5.6. It profiles an evidence folder without a model call, establishes SHA-256 custody, and lets GPT-5.6 open with up to twelve route-valid typed forensic tools that code validates all-or-none and executes in parallel. A typed `finish_investigation(status="DONE")` forces structured findings, a fresh-context reviewer may only preserve or downgrade them, and a strict offline verifier reconstructs the sealed bundle byte for byte.

## Experience it in 60 seconds, $0

No API key. Every command below returns in well under a second and never contacts OpenAI (the pip install is the only wait, ~1-2 minutes):

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
.judge\Scripts\python.exe -m unchained onboard
.judge\Scripts\python.exe -m unchained profile docker/fixtures --json
```

Full-isolation alternative, still no key and no spend (cold build takes several minutes):

```powershell
docker compose build
docker compose run --rm offline profile /evidence --json
```

## Criterion → strongest concrete evidence

| Criterion | Strongest evidence |
|---|---|
| Technological Implementation | Codex Session ID `019f61e5-5755-7a02-adb4-618d32baab27`; Codex-built control plane (evidence lifecycle, Responses API adapter, typed execution boundary, caps, typed-DONE-v2, forced serializer, exact spans, downgrade-only review, renderers, verifier, CLI, Docker, tests); 428/428 tests pass in 23.09s, ruff clean |
| Design | One-word self-driving `sentinel` front door; $0 no-key judge lane above; one launch card owning model + depth with an explicit `1 = LAUNCH` spend gate and hard cost ceilings; static inert no-JS `viewer.html`; honest PARTIAL/INVALID labeling |
| Potential Impact | An IR consultancy must show a regulator or opposing counsel exactly what the AI did; the pattern (model picks bounded strategy, code executes typed authority and retains exact receipts) generalizes to security testing, compliance review, financial operations |
| Quality of the Idea | The authority split: model chooses strategy; code owns evidence identity, legality, caps, execution, citation spans, verdict monotonicity, report rows, and verification — sealed in a content-addressed bundle verified offline |

**Retained live proof, shipped in the repo** (`examples/public-run-partial`): an authentic GPT-5.6 run (`gpt-5.6-luna`, 4 responses) executed 14 model-selected typed Volatility tools on real 2 GiB DC01 Windows memory, custody match true, then stopped honestly at the hard tool budget (`MAX_TOOL_CALLS: reservation would reach 14 > 13`). 180,285 provider-reported tokens, 55.5 s wall, ~$1.16 local estimate. Verify it yourself, no key: `sentinel verify examples/public-run-partial` → VALID, 20 artifacts, 62 hash-chained audit entries (proven on current code 2026-07-20). A second committed receipt (`docs/runs/sol-capped-dc01-opening.json`) records the earlier `gpt-5.6-sol` capped opening: 6/6 tools under the then six-tool cap, VALID recorded at creation (13 artifacts, 38 audit entries), $0.38789875, 43.7 s.

## What we claim / what we do not claim

| We claim | We do not claim |
|---|---|
| Receipts prove what ran, what output was retained, and what exact text was cited | Forensic truth — a human still owns interpretation and response |
| A published COMPLETE GPT-5.6 Sol bundle (findings, fresh judge, sealed report) that passes strict `--require-complete --require-live-gpt56` — `examples/public-run-complete` | That single public case is a measured benchmark (it is one case, not a comparison) |
| 428 passing offline tests; byte-exact offline re-verification of the bundle | Any measured Qwen comparison (deliberately cut — no unmeasured claims) |
| Caps fire before dispatch, ending runs as honest PARTIAL instead of overspending | A complete OS sandbox, or that the fresh reviewer is independent ground truth |

## Links

- Repo (public, MIT): https://github.com/3sk1nt4n/Unchained
- Demo video: ADDED-ON-UPLOAD
- Codex Session ID: `019f61e5-5755-7a02-adb4-618d32baab27`
- Full pipeline diagram: `docs/ARCHITECTURE.md`
- Shipped verifiable bundle: `examples/public-run-partial` (run `sentinel verify` on it — no key)
- Live receipts: `docs/runs/sol-capped-dc01-opening.json`, `docs/runs/luna-canary-receipt.json`
- Public evidence source: https://dfirmadness.com/the-stolen-szechuan-sauce/
