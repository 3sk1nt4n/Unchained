# ⚡ Unchained - Judge One-Pager

![tests](https://img.shields.io/badge/tests-378%2F378-22c55e) ![verify](https://img.shields.io/badge/sentinel_verify-VALID-22c55e) ![license](https://img.shields.io/badge/license-MIT-3b82f6)

> **GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited.**

Unchained is a bounded autonomous DFIR investigator built with Codex and GPT-5.6. Code profiles evidence and establishes SHA-256 custody before any model call; GPT-5.6 drives typed forensic tools that code validates all-or-none and executes in parallel; a typed `finish_investigation(status="DONE")` forces structured findings; a fresh-context reviewer may only preserve or downgrade; a strict offline verifier reconstructs the sealed bundle byte for byte.

> [!IMPORTANT]
> **🏆 One command proves it - no key, no spend:**
> ```
> sentinel verify examples/public-run-complete --require-complete --require-live-gpt56
> ```
> **→ VALID · 37 artifacts · 194 hash-chained audit entries** (proven on current code, 2026-07-21). Byte-exact re-verification of the shipped COMPLETE GPT-5.6 run.

## 🚀 60 seconds, $0

No API key. Every command returns in under a second and never contacts OpenAI (pip install is the only wait, ~1-2 min):

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
.judge\Scripts\python.exe -m unchained onboard
.judge\Scripts\python.exe -m unchained profile docker/fixtures --json
```

> [!TIP]
> Full isolation, still no key, no spend (cold build takes several minutes): `docker compose build` then `docker compose run --rm offline profile /evidence --json`

## 📦 Shipped live GPT-5.6 proof (no key needed)

| Bundle | Model | Tools | Result | Strict verify |
|---|---|---|---|---|
| `examples/public-run-complete` · run `20260721T001718Z-f0cd5641` | `gpt-5.6-sol`, 24 responses | **31/31 typed Volatility tools**, 20 adaptive turns, 2 GiB DC01 Windows memory, custody match | **COMPLETE** - 4 findings (1 CONFIRMED · 2 NEEDS-REVIEW · 1 UNSUPPORTED), ~$2.92, 9m39s | **VALID** · 37 artifacts · 194 audit entries |
| `examples/public-run-partial` | `gpt-5.6-luna` | 14/14 typed tools | Honest **PARTIAL** at the `MAX_TOOL_CALLS` budget | **VALID** · 20 artifacts · 62 audit entries |

## 🎯 Criterion → strongest evidence

| Criterion | Strongest evidence |
|---|---|
| Technological Implementation | Codex-built control plane, two Codex sessions (IDs below): evidence lifecycle, Responses API adapter, typed execution boundary, caps, typed-DONE-v2, forced serializer, exact spans, downgrade-only review, renderers, verifier, CLI, Docker, tests; **378/378 tests pass, ruff clean** (CPython 3.11.9, 2026-07-21) |
| Design | One-word self-driving `sentinel` front door; $0 no-key judge lane above; launch card `1 = quick Terra test / 2 = full Terra run / 3 = qualifying Sol / Q = quit` followed by a key step before any spend; inert no-JS `viewer.html`; honest PARTIAL/INVALID labeling |
| Potential Impact | An IR consultancy must show a regulator or opposing counsel exactly what the AI did; the pattern (model picks bounded strategy, code executes typed authority, retains exact receipts) generalizes to security testing, compliance review, financial operations |
| Quality of the Idea | The authority split: model chooses strategy; code owns evidence identity, legality, caps, execution, citation spans, verdict monotonicity, report rows, and verification - sealed in a content-addressed bundle verified offline |

## ⚖️ What we claim / what we do not claim

| ✅ We claim | 🚫 We do not claim |
|---|---|
| Receipts prove what ran, what output was retained, and what exact text was cited | Forensic truth - a human still owns interpretation and response |
| A shipped COMPLETE GPT-5.6 Sol bundle (findings, fresh judge, sealed report) passing strict `--require-complete --require-live-gpt56` | That one public case is a measured benchmark, or that the bundle is externally anchored (signing/timestamping is future work) |
| 378 passing offline tests; byte-exact offline re-verification of the bundle | Any measured competitive comparison (deliberately cut - no unmeasured claims) |
| Caps fire before dispatch, ending runs as honest PARTIAL instead of overspending | A complete OS sandbox, or that the fresh reviewer is independent ground truth |

> [!NOTE]
> Known and kept: the sealed flagship viewer has cosmetic defects (empty exit-code card, "Literal DONE" timeline label, raw escaped Markdown in the embedded report) - deliberately unfixed post-seal: changing one byte would break byte-exact verification, the seal working as designed. One error span carries an identifier from the pinned forensic-tool dependency (commit `9f309c6134e857f7b86f3e6b9c6709ce954944a5`); it is deliberately not edited post-seal.

## 🔗 Links

- Repo (public, MIT, Developer Tools track): https://github.com/3sk1nt4n/Unchained · Evidence source: https://dfirmadness.com/the-stolen-szechuan-sauce/
- Demo video (2:52, also ships at `submission/video/unchained-demo-final.mp4`): **https://youtu.be/ci2M8LmY2hY**
- Codex Sessions: `019f61e5-5755-7a02-adb4-618d32baab27` (core build, /feedback uploaded) · `019f76f3-a19f-71d1-81b2-eed6305857f6` (release thread)
- Pipeline diagram: `docs/ARCHITECTURE.md` · Live receipts: `docs/runs/sol-capped-dc01-opening.json` (earlier capped `gpt-5.6-sol` opening, 6/6 tools, VALID recorded at creation), `docs/runs/luna-canary-receipt.json`
