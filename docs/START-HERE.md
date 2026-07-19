# Start here: your first Unchained case

> **The safe default**
>
> Point Unchained at one case. It profiles, classifies, and hashes the evidence
> locally first. No API key is required, OpenAI is not called, and no paid run
> starts unless you explicitly request one and type the exact confirmation.

```text
╔════════════════════════════════════════════════════════════════════╗
║                             UNCHAINED                             ║
║  "Point me at one case. I will profile it before any model call." ║
╚════════════════════════════════════════════════════════════════════╝
   $0 LOCAL PREVIEW  →  CASE CARD  →  EXPLICIT SOL  →  VERIFY  →  VIEW
```

## The five-step path

| Step | You do | Unchained does |
|---:|---|---|
| **1** | Install once | Creates an isolated CPython 3.11 environment and runs the local quality gate |
| **2** | Open the welcome | Explains one-case scope, privacy, mounts, cloud boundary, and hard ceilings |
| **3** | Point at evidence | Probes content, assigns public IDs, hashes custody, and shows a case card—locally |
| **4** | Choose whether to launch | Requires an interactive, exact confirmation before a paid GPT-5.6 Sol run |
| **5** | Verify and view | Checks the retained proof bundle before opening the inert report viewer |

## 1. Install once

Use Windows 10/11 AMD64, Git, PowerShell, and official CPython **3.11.9
AMD64** for the primary Windows-memory path.

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git
Set-Location .\Unchained
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

The setup script creates the environment outside the repository, installs the
pinned dependencies, and runs the no-key checks. It does **not** read evidence,
ask for an API key, or call OpenAI.

Keep this shortcut for the remaining commands:

```powershell
$sentinel = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
```

## 2. Open the welcome—still no key

```powershell
& $sentinel onboard
```

This performs no evidence I/O and no provider request. It shows the supported
case shape, the local/cloud boundary, the optional Luna connectivity canary,
and both Sol cap profiles.

For machine-readable output or a terminal without color:

```powershell
& $sentinel onboard --json
& $sentinel onboard --no-color
```

`NO_COLOR` is also honored. Older Windows consoles automatically receive an
ASCII card instead of unsupported box-drawing characters.

## 3. Prepare and profile one case

> **One folder = one case**
>
> The current typed-tool router accepts at most **one ready memory image** and
> **one ready disk image** in a case. Memory-only and disk-only cases are fine
> when a route-valid forensic tool family is ready. Multiple ready images of
> the same class fail closed; split them into separate case folders.

Common inputs include:

| Kind | Common containers | Treatment |
|---|---|---|
| Memory | `.raw`, `.img`, `.mem`, `.vmem`, `.dmp` | Bounded content/readiness probes; eligible read-only Volatility tools |
| Disk | `.E01`, `.dd`, `.raw`, `.img` | Bounded content/filesystem probes; raw inspection or an explicitly requested read-only mount |
| Documents and other unsupported files | Notes, PDFs, spreadsheets, miscellaneous files | Hashed and listed, then set aside from forensic analysis |
| Archives | `.zip`, `.7z`, and similar | **Not unpacked**; prepare permitted contents outside Unchained first |

Extensions are hints, not authority. Unchained uses bounded content probes and
deterministic forensic metadata to decide the evidence kind.

Run the safe preview:

```powershell
& $sentinel onboard "C:\Evidence\CASE-A"
```

What this default does:

- enumerates regular files safely;
- assigns path-free public IDs such as `E001`;
- computes SHA-256 before and after profiling;
- derives OS, evidence shape, health, symbols, filesystems, and eligible tool
  families;
- prints a junior-friendly case card and precise blockers;
- makes **zero OpenAI calls** and starts **no paid run**;
- does not print child evidence paths, mountpoints, or secrets.

Optional variants:

```powershell
# Request only a contained read-only mount attempt; the card reports the outcome.
& $sentinel onboard "C:\Evidence\CASE-A" --mount

# Path-free JSON for automation. It can never launch a paid run.
& $sentinel onboard "C:\Evidence\CASE-A" --json
```

Mount wording is literal: the result distinguishes `not-requested`, no ready
disk, requested-but-unavailable/raw-only, and verified-read-only-and-released.

## 4. Choose the cloud boundary and hard ceilings

First check local live-run readiness without reading evidence or printing the
key:

```powershell
$env:UNCHAINED_MODEL = "gpt-5.6"
& $sentinel doctor
```

If desired, run the one-request Luna connectivity canary before a forensic
case:

```powershell
& $sentinel smoke-openai
```

The Luna command is a paid but tightly bounded connectivity test. It reads no
evidence, creates no proof bundle, and is explicitly **not** a qualifying
forensic result.

For a Sol investigation, choose a hard-cap profile:

| Choice | Command option | Default hard ceilings |
|---|---|---|
| **CAUTIOUS** — recommended first case | `--caps strict` | 20 forensic calls · 100,000 tokens · 10 minutes · $2.50 estimated cost |
| **FLAGSHIP** — larger permitted run | `--caps default` | 60 forensic calls · 400,000 tokens · 30 minutes · $10 estimated cost |

Both choices use the same GPT-5.6 Sol controller and phase policies. They are
stop ceilings—not price quotes, model-quality promises, or separate reasoning
depths. Environment overrides can change the effective values; the onboarding
card always prints the effective selected ceilings.

Store the authorized OpenAI project key outside Git. The helper accepts it
without echoing it and keeps it only in the current PowerShell process:

> **Credential safety:** never reuse a key that appeared in chat, a recording,
> a shell transcript, or a committed file. Revoke it at the provider first,
> then create a fresh project-scoped key with an explicit spend limit.

```powershell
.\scripts\set-openai-key.ps1
```

Then explicitly request the paid path:

```powershell
& $sentinel onboard "C:\Evidence\CASE-A" --launch --caps strict
```

Unchained profiles and verifies the case before offering launch. It then shows
the cloud/cost card and requires this exact phrase:

```text
LAUNCH GPT-5.6 SOL
```

Anything else cancels. `--launch` is refused in JSON or noninteractive mode.
If confirmed, OpenAI receives the bounded public profile and bounded typed-tool
observations. Original evidence bytes and runner-local evidence paths remain
local. Add `--mount` only when the case needs an attempted read-only disk mount.

## 5. Verify and view the result

The completed CLI prints the exact bundle path and next commands. Preserve the
actual terminal status: `PARTIAL` or `INVALID` is not `COMPLETE`.

```powershell
& $sentinel verify "C:\path\to\bundle"
& $sentinel verify "C:\path\to\bundle" --require-complete --require-live-gpt56
& $sentinel view "C:\path\to\bundle"
```

- Ordinary `verify` checks the retained bundle in its claimed state.
- The strict command additionally requires a complete live GPT-5.6 lifecycle.
- `view` verifies before opening `viewer.html`; a bundle claiming `COMPLETE`
  automatically receives strict lifecycle verification.
- The viewer is self-contained, contains no JavaScript or external resources,
  and needs no report server.

Verification establishes lifecycle, custody, receipt, citation, report, and
viewer consistency. It does not prove that a model's forensic interpretation is
true or independently authenticate OpenAI. A human analyst owns the final
forensic judgment.

## Judge/no-key lane

If you have no evidence or API key, you can still inspect the UX and verify a
supplied bundle without rebuilding it:

```powershell
& $sentinel onboard
& $sentinel verify "C:\path\to\supplied-bundle"
& $sentinel view "C:\path\to\supplied-bundle"
```

For the containerized no-network front door:

```powershell
docker compose build
docker compose run --rm offline
docker compose run --rm offline profile /evidence --json
```

The offline service defaults to `onboard --json`, exits `0`, reads no evidence,
uses no key, and has no network. The committed Docker fixture is a synthetic
standalone log. Profiling it proves classification and custody; it correctly
does not pretend that a forensic tool route or authentic investigation is
ready. Run `docker compose run --rm offline doctor --json` only as an explicit
live-readiness check; without a Sol model/key it correctly reports not ready.

## When something stops

| Exit | Meaning | Junior-analyst action |
|---:|---|---|
| `0` | Command completed within policy | Read the reported status; this is not an accuracy guarantee |
| `1` | Fatal runtime, provider, verification, or custody invariant | Preserve the output and do not rely on the result |
| `2` | Invalid input/configuration or no ready route | Fix the case-card blocker; do not force a launch |
| `3` | `PARTIAL` because a cap or mandatory phase stopped safely | Preserve the bundle and report it as partial |

Next references: [judge quickstart](../JUDGE-QUICKSTART.md),
[architecture](ARCHITECTURE.md), and
[release handoff](OPENAI_VNEXT_RELEASE_HANDOFF.md).
