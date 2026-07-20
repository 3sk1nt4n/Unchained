# Start here: your first Unchained case

New to this? You're in the right place. This is the gentle, one-step-at-a-time
walkthrough — from a fresh Windows machine to a verified proof bundle you can
open in your browser.

> **You can't break anything.** Everything is local and free until the very
> last step, and even then nothing spends money until you type an exact
> confirmation phrase. If a step ever errors, nothing bad happened — just read
> the message and try again.

```text
╔════════════════════════════════════════════════════════════════════╗
║                             UNCHAINED                              ║
║  "Point me at one case. I will profile it before any model call." ║
╚════════════════════════════════════════════════════════════════════╝
   $0 LOCAL PREVIEW  →  CASE CARD  →  DEPTH  →  LAUNCH  →  VERIFY  →  VIEW
```

## The journey at a glance

| Step | What you do | What happens | Costs? |
|---:|---|---|---|
| **0** | Keep your key safe | You revoke any exposed key and make a fresh one | Free |
| **1** | Install (one line) | Tools install; `sentinel` becomes a one-word command | Free |
| **2** | Save your key (hidden) | `sentinel key` stores it privately, found automatically | Free |
| **3** | Point at a case | You see a **case card** with a `PROFILE READY` status | Free ($0) |
| **4** | Pick a depth | LIGHT or HEAVY — sets spending limits only | Free to choose |
| **5** | Launch and watch | You type a phrase; the live investigation runs on screen | A few cents+ |
| **6** | Verify and view | An offline checker says **VALID**; the proof viewer opens | Free |

After Step 1, every command is one word: `sentinel ...`. (Setup adds it to your
PATH. If a new terminal says "not found," open a fresh PowerShell window, or use
the full path shown at the bottom of this page.)

---

## Step 0 — Keep your OpenAI key safe

You'll need an OpenAI key for the paid run (Step 5), but never paste a key into
a chat, screenshot, or shared terminal.

1. Open <https://platform.openai.com/api-keys>.
2. **Revoke** any key that has ever appeared somewhere public.
3. **Create new secret key** and keep it in a private note for a moment.

> New OpenAI accounts have a low rate limit (~200,000 tokens/minute). A full
> investigation needs more than that in one burst, so add a little credit and
> complete any verification under **Settings → Billing** to raise the limit
> before your real run. This is the single most common reason a run stops early.

---

## Step 1 — Install Unchained (one line)

Open **PowerShell** (Start → type "PowerShell" → Enter), then paste:

```powershell
irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex
```

This clones the project, installs a private, pinned Python 3.11 toolchain, and
walks you in. **It reads no evidence and calls OpenAI zero times.** "OK already
done" just means it is safe to re-run.

Missing Git or Python? Install these, reopen PowerShell, and paste the line
again:

- Git for Windows: <https://git-scm.com/download/win>
- CPython **3.11.9 AMD64**: <https://www.python.org/downloads/release/python-3119/>
  (tick **"Add python.exe to PATH"** during install)

Prefer the manual path instead of the one-liner? It does the same thing:

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git
Set-Location .\Unchained
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

---

## Step 2 — Save your key the safe way (hidden, once)

```powershell
sentinel key
```

The prompt is **hidden** — you won't see the characters as you paste. That's on
purpose. Paste your fresh key, press Enter. It's saved to a private, owner-only
file and every command finds it automatically from now on. You never type it
again. Confirm it worked:

```powershell
sentinel key --status
```

You want to see **"Key configured."** (Automation can use `OPENAI_API_KEY` or
`OPENAI_API_KEY_FILE` instead; those always take precedence.)

---

## Step 3 — Look at a case (still $0, no OpenAI)

First, meet the friendly welcome — no evidence, no key, no cost:

```powershell
sentinel onboard
```

Then point it at one case folder to get a **case card**:

```powershell
sentinel onboard "C:\Evidence\CASE-A"
```

**What you'll see:** a colorful card. The line that matters is
**`Status: PROFILE READY`** — that means it's good to investigate. You'll also
see the OS, the evidence's SHA-256 custody hash (proof it hasn't changed), and
which forensic tools are ready.

What this safe preview does, in plain terms:

- looks at every file and decides memory vs disk vs document by **probing the
  contents**, not the filename;
- gives each item a path-free public ID like `E001`;
- takes a SHA-256 fingerprint before and after (chain of custody);
- makes **zero OpenAI calls** and starts **no paid run**;
- never prints your file paths, mountpoints, or secrets.

> **One folder = one case.** Put at most one ready memory image and one ready
> disk image in a folder. Two of the same kind fail closed — split them into
> separate folders. Archives (`.zip`, `.7z`) are **not** unpacked; extract
> permitted contents yourself first.

Optional extras:

```powershell
sentinel onboard "C:\Evidence\CASE-A" --mount   # attempt a read-only disk mount
sentinel onboard "C:\Evidence\CASE-A" --json    # machine-readable; can never launch
```

If the card says **ACTION NEEDED** instead of READY, read the "FIX BEFORE
LAUNCH" list — usually the evidence kind isn't supported yet, or an archive
still needs extracting. No paid run is offered until it's READY.

---

## Step 4 — Choose a depth (LIGHT or HEAVY)

When you launch you'll pick one. Both use the **same GPT-5.6 Sol investigator** —
the depth only sets **spending limits**, not quality.

| Choice | Option | Hard ceilings (not a price quote) |
|---|---|---|
| **LIGHT** — recommended first case | `--caps strict` | 20 tools · 100,000 tokens · 10 min · $2.50 est. |
| **HEAVY** — deeper run | `--caps default` | 60 tools · 400,000 tokens · 30 min · $10 est. |

Ceilings are **stop limits**, not the price you'll pay. Real spend is usually
far lower. Check your live-run readiness any time (no evidence, no key printed):

```powershell
$env:UNCHAINED_MODEL = "gpt-5.6"
sentinel doctor
```

You want **READY**. If it says a cap or model is missing, follow the one-line
hint it prints.

---

## Step 5 — The smart way: rehearse cheap, then run for real

### 5a. Practice on the cheapest model first (a few cents)

This validates the whole pipeline before you spend on the flagship. Paste the
block:

```powershell
$env:UNCHAINED_ALLOW_TEST_MODEL = "1"
$env:UNCHAINED_MODEL = "gpt-5.6-luna"
$env:MAX_TOTAL_TOKENS = "3000000"
$env:MAX_COST_USD = "30"
sentinel onboard "C:\Evidence\CASE-A" --launch --caps strict
```

Then, in order:

1. It shows the case card again.
2. It asks your depth — press **Enter** for LIGHT.
3. It asks you to confirm spending. Type **exactly**: `LAUNCH GPT-5.6 SOL`
4. **Watch it live**: opening tools with timings, the model's reasoning each
   turn, findings, the reviewer keeping or downgrading them, and a sealed bundle.

The banner will warn **"TEST MODEL MODE"** — that's correct. A test run is a
cheap rehearsal, clearly labeled **nonqualifying**; it can never masquerade as
the official Sol result. Why the generous ceilings and higher-tier account? The
full lifecycle on a real memory image can otherwise stop early on token or
rate limits — see [When a run stops early](#when-a-run-stops-early).

### 5b. The official run (GPT-5.6 Sol)

Once the rehearsal completes cleanly, open a **fresh PowerShell** (to clear the
test settings) and do the real one:

```powershell
$env:UNCHAINED_MODEL = "gpt-5.6"
$env:MAX_TOTAL_TOKENS = "3000000"
$env:MAX_COST_USD = "30"
sentinel onboard "C:\Evidence\CASE-A" --launch --caps strict
```

Type `LAUNCH GPT-5.6 SOL` to confirm. This one uses the real Sol model (costs a
bit more) and produces your official bundle. Original evidence bytes stay local;
OpenAI only receives the bounded public profile and bounded typed-tool outputs.

---

## Step 6 — Verify and view the proof (free, no key)

The run prints the exact **bundle folder path** at the end. Use it:

```powershell
sentinel verify "C:\path\to\bundle"
sentinel view   "C:\path\to\bundle"
```

- `verify` should say **VALID** — an independent, offline checker rebuilt the
  report and confirmed nothing was tampered with.
- `view` opens a self-contained **proof viewer** in your browser (findings,
  citations, custody, receipts) — no server, no JavaScript, no internet.

For the qualifying Sol bundle, verify strictly:

```powershell
sentinel verify "C:\path\to\bundle" --require-complete --require-live-gpt56
```

🎉 **VALID with those flags is submission-grade proof.**

> Verification proves the lifecycle, custody, citations, report, and viewer are
> internally consistent. It does **not** prove a model's forensic
> interpretation is true, and it does not authenticate OpenAI. A human analyst
> owns the final judgment.

---

## When a run stops early

A run can end `PARTIAL` — that's honest, not a failure of you. Read
`summary.json` and the last audit lines. Common causes and fixes:

| You see | What it means | What to do |
|---|---|---|
| `429 Request too large ... TPM` | Your account's per-minute token limit is too low for the serializer packet | Add credit / verify to tier up (Step 0), so your TPM exceeds the request size |
| `MAX_TOTAL_TOKENS` before the report | The full lifecycle exceeded the token cap | Raise it: `MAX_TOTAL_TOKENS=3000000 MAX_COST_USD=30` |
| `MAX_TOOL_CALLS` | The tool budget was too small for the investigation | Use `--caps default`, or raise `MAX_TOOL_CALLS` |
| `ACTION NEEDED` card, no launch offered | Evidence isn't route-ready | Fix the card's "FIX BEFORE LAUNCH" blockers, then re-profile |

Exit codes, if you script this:

| Exit | Meaning | Junior action |
|---:|---|---|
| `0` | Completed within policy | Read the reported status; not an accuracy guarantee |
| `1` | Fatal runtime/provider/verification/custody failure | Preserve output; don't rely on the result |
| `2` | Invalid input/config or no ready route | Fix the case-card blocker; don't force a launch |
| `3` | `PARTIAL` — a cap or phase stopped safely | Preserve the bundle; report it as partial, never as complete |

---

## No key? No evidence? You can still explore

A judge or curious newcomer can inspect the experience and verify a supplied
bundle without any key or evidence:

```powershell
sentinel onboard                              # the guided welcome
sentinel verify "C:\path\to\supplied-bundle"  # check a bundle offline
sentinel view   "C:\path\to\supplied-bundle"  # open its proof viewer
```

Or the fully isolated container front door (no network, no key):

```powershell
docker compose build
docker compose run --rm offline
docker compose run --rm offline profile /evidence --json
```

The offline container profiles a committed synthetic log fixture with zero
OpenAI calls — it proves classification and custody, and honestly says a real
forensic route isn't ready for that toy fixture.

---

## A tiny cheat sheet to keep

| I want to… | Command |
|---|---|
| See the welcome | `sentinel onboard` |
| Confirm my key | `sentinel key --status` |
| Look at a case ($0) | `sentinel onboard "<folder>"` |
| Rehearse cheap | set `UNCHAINED_ALLOW_TEST_MODEL=1` + `UNCHAINED_MODEL=gpt-5.6-luna`, then `... --launch` |
| Real Sol run | `UNCHAINED_MODEL=gpt-5.6`, then `... --launch` |
| Check a bundle | `sentinel verify "<bundle>"` |
| Open the viewer | `sentinel view "<bundle>"` |

**If `sentinel` isn't found** (rare — usually just open a new terminal), the
full path always works:

```powershell
& "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\sentinel.exe" onboard
```

Next: [judge quickstart](../JUDGE-QUICKSTART.md) ·
[architecture](ARCHITECTURE.md) ·
[release handoff](OPENAI_VNEXT_RELEASE_HANDOFF.md)
