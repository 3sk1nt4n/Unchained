# Start here: your first Unchained case

New to this? You're in the right place. It's really just **two commands**:
install once, then run one word that walks you through everything else.

> **You can't break anything.** Everything is local and free until the very
> last step, and even then nothing spends money until you type an exact
> confirmation phrase. If a step ever errors, nothing bad happened — read the
> message and try again.

```text
╔════════════════════════════════════════════════════════════════════╗
║                             UNCHAINED                              ║
║  "Point me at one case. I will profile it before any model call." ║
╚════════════════════════════════════════════════════════════════════╝
   INSTALL ONCE  →  RUN ONE WORD  →  it walks you to a verified proof bundle
```

## The whole thing in two commands

```powershell
# 1) install + verify everything (one command)
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1

# 2) start a whole case (one word — it walks you through the rest)
sentinel
```

That second command does **all** of this for you, in order, asking one simple
thing at a time:

1. shows a full-color welcome;
2. asks **one question** — where the evidence is;
3. profiles and SHA-256-hashes the case **locally** and prints a verified
   **case card** (no key, no OpenAI, `$0`);
4. asks the **depth** (1 = HEAVY, 2 = LIGHT — Enter keeps LIGHT);
5. finds your API key automatically, or asks for it once at a hidden prompt;
6. stops for your explicit launch phrase, then runs the investigation live and
   verifies the sealed proof bundle.

No flags. No environment variables. If you'd rather type a launcher, `.\unchained.ps1`
does exactly the same thing.

---

## Step 0 — Keep your OpenAI key safe (do this once, before the run)

You'll need an OpenAI key for the paid run, but never paste a key into a chat,
screenshot, or shared terminal.

1. Open <https://platform.openai.com/api-keys>.
2. **Revoke** any key that has ever appeared somewhere public.
3. **Create new secret key** and keep it in a private note for a moment.

> New OpenAI accounts have a low rate limit (~200,000 tokens/minute). A full
> investigation needs more than that in one burst, so add a little credit and
> complete verification under **Settings → Billing** to raise the limit before
> your real run. This is the single most common reason a run stops early.

---

## Step 1 — Install (one command)

Open **PowerShell** (Start → type "PowerShell" → Enter). Either paste the
one-liner:

```powershell
irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex
```

…or clone and run the installer directly — **same steps, same result**:

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git
Set-Location .\Unchained
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

`setup.ps1` checks everything and installs what's missing: a private, pinned
Python 3.11 toolchain, all dependencies, and the one-word `sentinel` command. It
also tells you whether Docker is available (optional on Windows). **It reads no
evidence and calls OpenAI zero times.** Re-running is safe.

- Re-verify anytime without reinstalling: `.\setup.ps1 -Check`
- Missing Git or Python? Install these, reopen PowerShell, and run it again:
  - Git for Windows: <https://git-scm.com/download/win>
  - CPython **3.11.9 AMD64**: <https://www.python.org/downloads/release/python-3119/>
    (tick **"Add python.exe to PATH"**)

---

## Step 2 — Run one word (it walks you through the rest)

```powershell
sentinel
```

That's the whole experience. Answer one question (the evidence folder), read the
case card, pick a depth by pressing `1`, `2`, or Enter, and — when it asks — type
the exact phrase to launch:

```text
LAUNCH GPT-5.6 SOL
```

Then **watch it live**: the opening tools with timings, the model's reasoning
each turn, findings, the reviewer keeping or downgrading them, and a sealed,
verified bundle at the end. The run prints the exact `verify` and `view`
commands when it finishes.

> **One folder = one case.** Put at most one ready memory image and one ready
> disk image in a folder. Two of the same kind fail closed — split them into
> separate folders. Archives (`.zip`, `.7z`) are **not** unpacked; extract
> permitted contents yourself first. Original evidence bytes stay local; OpenAI
> only receives the bounded public profile and bounded typed-tool outputs.

Depth is only a set of **hard stop ceilings**, never a different model or a
quality promise. Both depths use the same GPT-5.6 Sol investigator:

| Choice | Hard ceilings (not a price quote) |
|---|---|
| **LIGHT** — recommended first case | 20 tools · 100,000 tokens · 10 min · $2.50 est. |
| **HEAVY** — deeper run | 60 tools · 400,000 tokens · 30 min · $10 est. |

---

## Step 3 — Verify and view the proof (free, no key)

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
> internally consistent. It does **not** prove a model's forensic interpretation
> is true, and it does not authenticate OpenAI. A human analyst owns the final
> judgment.

---

## Linux and macOS (same one-command experience)

The exact same flow runs natively with Bash mirrors of the two scripts:

```bash
./setup.sh        # install + verify everything (one command)
./unchained.sh    # start a whole case (walks you through the rest)
```

Prefer full isolation, or don't want to install anything? The hardened,
network-less container profiles a committed synthetic fixture with **no key and
no evidence**:

```bash
docker compose build
docker compose run --rm offline                 # guided welcome, offline
docker compose run --rm offline profile /evidence --json
```

It proves classification and custody with zero OpenAI calls, and honestly says a
real forensic route isn't ready for that toy fixture.

---

## Advanced: rehearse cheap before the real run

Want to validate the whole pipeline for a few cents before spending on the
flagship? Opt into a clearly-labeled, **nonqualifying** cheap rehearsal by
setting two variables before you run `sentinel`:

```powershell
$env:UNCHAINED_ALLOW_TEST_MODEL = "1"
$env:UNCHAINED_MODEL = "gpt-5.6-luna"
sentinel
```

The banner will warn **"TEST MODEL MODE"** — that's correct. A rehearsal can
never masquerade as the official Sol result and cannot pass
`--require-live-gpt56`. Open a **fresh PowerShell** (to clear those variables)
for the real run. Without these variables, `sentinel` defaults to real GPT-5.6
Sol automatically — no configuration needed.

---

## When a run stops early

A run can end `PARTIAL` — that's honest, not a failure of you. Read
`summary.json` and the last audit lines. Common causes and fixes:

| You see | What it means | What to do |
|---|---|---|
| `429 Request too large ... TPM` | Your account's per-minute token limit is too low for the serializer packet | Add credit / verify to tier up (Step 0), so your TPM exceeds the request size |
| `MAX_TOTAL_TOKENS` before the report | The full lifecycle exceeded the token cap | Raise it: `$env:MAX_TOTAL_TOKENS = "3000000"` before `sentinel` |
| `MAX_TOOL_CALLS` | The tool budget was too small for the investigation | Choose HEAVY at the depth prompt, or raise `MAX_TOOL_CALLS` |
| `ACTION NEEDED` card, no launch offered | Evidence isn't route-ready | Fix the card's "FIX BEFORE LAUNCH" blockers, then run again |

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
sentinel                                      # the guided welcome (safe to explore)
sentinel verify "C:\path\to\supplied-bundle"  # check a bundle offline
sentinel view   "C:\path\to\supplied-bundle"  # open its proof viewer
```

---

## A tiny cheat sheet to keep

| I want to… | Command |
|---|---|
| Install / repair everything | `.\setup.ps1` (Linux/macOS: `./setup.sh`) |
| Re-verify without reinstalling | `.\setup.ps1 -Check` (Linux/macOS: `./setup.sh --check`) |
| Start a whole case | `sentinel` (Linux/macOS: `./unchained.sh`) |
| Save my key manually | `sentinel key` |
| Confirm my key | `sentinel key --status` |
| Check a bundle | `sentinel verify "<bundle>"` |
| Open the viewer | `sentinel view "<bundle>"` |

**If `sentinel` isn't found** (rare — usually just open a new terminal), the
full path always works:

```powershell
& "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
```

Next: [judge quickstart](../JUDGE-QUICKSTART.md) ·
[architecture](ARCHITECTURE.md) ·
[release handoff](OPENAI_VNEXT_RELEASE_HANDOFF.md)
