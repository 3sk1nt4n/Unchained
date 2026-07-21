# 🏆 Unchained - Judge Quickstart

<p align="center">
  <img src="https://img.shields.io/badge/tests-378%2F378%20passing-22c55e" alt="tests 378/378 passing"> <img src="https://img.shields.io/badge/ruff-clean-22c55e" alt="ruff clean"> <img src="https://img.shields.io/badge/strict%20verify-VALID-8b5cf6" alt="strict verify VALID"> <img src="https://img.shields.io/badge/license-MIT-3b82f6" alt="MIT license"> <img src="https://img.shields.io/badge/track-Developer%20Tools-f59e0b" alt="track Developer Tools">
  <br>
  <img src="https://img.shields.io/badge/Windows-flagship%20lane-0078D6?logo=windows&logoColor=white" alt="Windows flagship lane"> <img src="https://img.shields.io/badge/Linux-hardened%20container-1793D1?logo=linux&logoColor=white" alt="Linux hardened container"> <img src="https://img.shields.io/badge/macOS-via%20Docker-000000?logo=apple&logoColor=white" alt="macOS via Docker">
</p>

<p align="center">
  <a href="README.md">🏠 Overview</a> ·
  <a href="README.md#for-judges---the-submission-at-a-glance">🏆 For judges</a> ·
  <a href="README.md#quickstart">⏱️ Quickstart</a> ·
  <a href="docs/ARCHITECTURE.md">🧠 Architecture</a> ·
  <a href="README.md#proof-status">🧾 Proof status</a> ·
  <a href="docs/START-HERE.md">🚀 Start here</a>
</p>

> [!TIP]
> **Fastest proof: strict-verify the shipped COMPLETE GPT-5.6 investigation.
> No API key, no spend, zero OpenAI calls.**
>
> ```powershell
> git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
> py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
> .judge\Scripts\sentinel.exe verify examples\public-run-complete --require-complete --require-live-gpt56
> ```
>
> Expected: **VALID** - 37 artifacts, 194 audit entries, custody match. The
> `pip install` is the only wait (~1-2 min); the verify runs locally in seconds.

## 🧾 Submission at a glance

| | |
|---|---|
| **Repo** | <https://github.com/3sk1nt4n/Unchained> - public, MIT. Track: **Developer Tools** |
| **Flagship proof** | `examples/public-run-complete` - run `20260721T001718Z-f0cd5641`, **gpt-5.6-sol**, 24 responses, **31/31 typed Volatility tools**, 20 adaptive turns, 4 findings (1 CONFIRMED / 2 NEEDS-REVIEW / 1 UNSUPPORTED), ~$2.92 estimated, 9m39s wall, custody match |
| **Strict verify** | `sentinel verify examples/public-run-complete --require-complete --require-live-gpt56` prints **VALID** (37 artifacts, 194 audit entries) |
| **Secondary proof** | `examples/public-run-partial` - **gpt-5.6-luna**, 14/14 tools, honest **PARTIAL** at `MAX_TOOL_CALLS`; verify prints VALID (20 artifacts, 62 audit entries) |
| **Quality gate** | **378/378 tests pass**, Ruff clean (2026-07-21, CPython 3.11.9) |
| **Demo video** | **https://youtu.be/ci2M8LmY2hY** (2:52, public; also ships at `submission/video/unchained-demo-final.mp4`) |
| **Built with Codex** | Sessions `019f61e5-5755-7a02-adb4-618d32baab27` (core build, `/feedback` uploaded) and `019f76f3-a19f-71d1-81b2-eed6305857f6` (release thread). Codex build credits and API runtime billing are separate |

## 🚀 The judge path

1. **Clone**: `git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained`
2. **Setup**: `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1`
   (validated Python 3.11 env, pinned deps; open a new terminal if `sentinel` is not found)
3. **Strict-verify the COMPLETE bundle** (no key):
   `sentinel verify examples\public-run-complete --require-complete --require-live-gpt56` prints `VALID`
4. **View it**: `sentinel view examples\public-run-complete` - report, findings,
   custody, self-contained `viewer.html`
5. **Optional paid run**: run `sentinel`, point it at public evidence (section
   6), pick `3 = qualifying Sol` on the launch card, pass the hidden key step

> [!IMPORTANT]
> There are two separate judge paths: (1) no-key verification of a completed
> proof bundle, and (2) an authentic GPT-5.6 investigation using Python 3.11,
> public evidence, and a funded OpenAI project key. Never present a fake-model
> test or replay as an authentic GPT-5.6 run. This page is the shortest
> reliable path for a fresh Windows 10/11 AMD64 machine; the Build Week
> flagship is Windows memory evidence, and native Windows E01 or NTFS mounting
> is not part of the primary path.

> [!NOTE]
> **More zero-spend proof** (local, never contacts OpenAI):
> `.judge\Scripts\python.exe -m unchained onboard` shows the guided welcome;
> `... -m unchained profile docker/fixtures --json` prints deterministic
> routing, public evidence IDs, and SHA-256 custody on the committed fixture.
> Prefer full isolation? The same front door runs in a hardened container
> (section 13); `docker compose build` takes several minutes on a cold cache.

## ⌨️ Judge's first screen - one word does everything

After installation, `sentinel` is a one-word, self-driving command (setup adds
a tiny shim folder to your user PATH; open a new terminal if it is not found):

```powershell
sentinel
```

It opens a zero-key welcome (reads nothing, zero OpenAI calls) and asks **one
thing** - where the evidence is - with a card showing what a good case folder
looks like (one memory image and/or one disk image from one host). No evidence
handy? Type **`D`** for a guided download of the public DC01 case - the two
direct links (`case001/DC01-memory.zip`, `case001/DC01-E01.zip`) open in your
browser, publisher MD5s are verified, and the case folder is prepared. It then
profiles content and rechecks SHA-256 custody locally to print a deterministic
case card. `.zip` archives are offered for local extraction into a clean
sibling folder; other archives and unsupported documents are hashed/listed and
set aside. The router accepts at most one ready memory image and one ready
disk image per case; same-class multiples fail closed. It then stops at one
launch card that owns model and depth
(`1 = quick Terra test · 2 = full Terra run · 3 = qualifying Sol · Q = quit`),
followed by the one final key step (Enter = saved key, or a hidden paste that
never echoes) - no flags, no environment variables.

If PATH changes are restricted, the full form always works:

```powershell
& "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
```

Each launch-card package maps to one of two stop-ceiling profiles - package `1`
uses LIGHT, packages `2` and `3` use HEAVY:

| Ceiling profile | Hard ceilings (not a price quote) |
|---|---|
| **LIGHT** | 20 tools · 100,000 tokens · 10 min · $2.50 estimated cost |
| **HEAVY** | 60 tools · 400,000 tokens · 30 min · $10 estimated cost |

These are hard ceilings, not price quotes, reasoning-depth modes, or promises
of finding quality; the effective values appear in the case card. A paid run
starts only in an interactive terminal after you pick a package and pass the
final key step - JSON and noninteractive runs cannot launch. The full
junior-analyst walkthrough is [Start Here](docs/START-HERE.md).

> [!NOTE]
> **Hardware:** no GPU is needed - GPT-5.6 runs on OpenAI's side. For the real
> memory-image path, 4 cores / 8 threads and 16 GB RAM are comfortable (the
> opening can fan out up to twelve typed forensic tools concurrently); keep
> evidence on a local SSD path, not a OneDrive/cloud-synced folder.

> [!TIP]
> **Do I need Docker? Only if you want it.**
> - 🪟 **Windows - no Docker at all.** The flagship lane is native PowerShell + CPython 3.11 (`get.ps1` one-liner or `setup.ps1`). Docker is optional extra isolation.
> - 🐧 **Linux - your choice.** Native `./setup.sh` (needs Python 3.11; on stock Ubuntu 24.04 add the deadsnakes PPA first: `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.11 python3.11-venv`) **or** the hardened Docker container via `get.sh`. **Both lanes were executed end to end and verified live on 2026-07-21.**
> - 🍎 **macOS - use the Docker Desktop lane** (the same hardened `linux/amd64` container). Native macOS is not verified on Mac hardware.

## 1. 🧰 Install prerequisites

Install Git for Windows and official CPython 3.11 AMD64:

- <https://git-scm.com/download/win>
- <https://www.python.org/downloads/release/python-3119/>

Enable **Add python.exe to PATH** during Python installation, then open a new
PowerShell window:

```powershell
git --version
py -3.11 --version
```

The validated flagship uses Python 3.11.9. Do not mix Python 3.12 or newer,
Conda, or global packages into the proof environment.

## 2. 📦 Clone and install

For the simplest supported setup, install plus a fast health check is one
command after cloning:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

The script creates the validated Python 3.11 environment outside OneDrive,
installs the pinned dependencies (a **non-editable** copy, so `sentinel` keeps
working if this folder moves), runs `pip check`, and confirms the toolchain
imports and the CLI responds - a fast health check in seconds, not the full
test suite. `-FullTest` also runs pytest, Ruff, the format check, and the
package build; `-Check` re-verifies an existing install without reinstalling.
The manual stages below remain available for diagnosis - run each block from a
new PowerShell window:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\src" | Out-Null
Set-Location "$env:USERPROFILE\src"
git clone https://github.com/3sk1nt4n/Unchained.git
Set-Location .\Unchained
git status --short
```

Create the virtual environment outside OneDrive:

```powershell
$venv = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311"
py -3.11 -m venv $venv
$python = "$venv\Scripts\python.exe"
$env:PIP_REQUIRE_VIRTUALENV = "true"
& $python -m pip install --upgrade pip setuptools wheel
& $python -m pip install -r requirements/bootstrap.txt
& $python -m pip install -c requirements/constraints.windows-amd64-cp311.txt ".[dev]"
& $python -m pip check
```

Expected final line: `No broken requirements found.` After setup, the whole
self-driving flow is the one word `sentinel`.

## 3. ✅ Run the no-key quality gate

This checks the installation and does not call OpenAI or inspect forensic
evidence:

```powershell
& $python -m pytest
& $python -m ruff check .
& $python -m ruff format --check .
& $python -m build
& "$venv\Scripts\vol.exe" -h
```

The OpenAI-native vNext tree passes **378/378 tests** with Ruff clean
(validated 2026-07-21 on CPython 3.11.9). A failure should be fixed or reported
with its environment details. Do not silently switch interpreters.

## 4. 🔏 Verify the shipped proof bundles without a key

Two real bundles ship in the repository:

| Bundle | Model | Outcome | No-key verify result |
|---|---|---|---|
| `examples/public-run-complete` | gpt-5.6-sol | **COMPLETE** | strict verify **VALID** - 37 artifacts, 194 audit entries |
| `examples/public-run-partial` | gpt-5.6-luna | honest **PARTIAL** at `MAX_TOOL_CALLS` | verify **VALID** - 20 artifacts, 62 audit entries |

```powershell
# Flagship COMPLETE run - must pass the strictest gate
& "$venv\Scripts\sentinel.exe" verify examples\public-run-complete --require-complete --require-live-gpt56
& "$venv\Scripts\sentinel.exe" view examples\public-run-complete

# Secondary PARTIAL run - VALID as a lifecycle, honestly labeled PARTIAL
& "$venv\Scripts\sentinel.exe" verify examples\public-run-partial
```

The PARTIAL bundle is never presented as COMPLETE: `--require-complete` must
fail it, and it does. That asymmetry is the point of the verifier.

A synthetic negative control is also one command - it must end with
`DEMO_BUNDLE_VERIFIED_INVALID_INPUT` and `BUNDLE=...`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo.ps1
```

This verifies lifecycle and bundle construction only; the synthetic `INVALID`
fixture must fail the strict command, proving the verifier does not confuse a
marked fake or incomplete lifecycle with a complete one. It is not a forensic
investigation and does not prove GPT-5.6 participation.

For any supplied completed run:

```powershell
& "$venv\Scripts\sentinel.exe" verify C:\path\to\completed-run
& "$venv\Scripts\sentinel.exe" view C:\path\to\completed-run
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify.ps1 C:\path\to\completed-run
```

Offline verification cannot independently authenticate OpenAI from locally
recorded IDs; retain the genuine provider/operator record separately.

## 5. 🔑 Configure an authentic run

Create a funded project key at:

<https://platform.openai.com/api-keys>

**The one-step path - paste once with hidden input, done forever:**

```powershell
& "$venv\Scripts\sentinel.exe" key
```

Input is masked; the key is written to a private per-user file
(`%LOCALAPPDATA%\sentinel-unchained\openai_api_key`, owner-only) and **every
later sentinel command finds it automatically** - no environment variables, no
terminal restarts. Check or remove any time:

```powershell
& "$venv\Scripts\sentinel.exe" key --status
& "$venv\Scripts\sentinel.exe" key --remove
```

> [!WARNING]
> Never paste the key into chat, Git, a screenshot, or a command saved in
> history. For automation, `OPENAI_API_KEY` or `OPENAI_API_KEY_FILE` still work
> and always take precedence over the saved file.

**You do not need to set anything else.** `sentinel` defaults to the public
`gpt-5.6` alias, and the launch card owns the model package and the hard caps
for you. The variables below are optional overrides for automation or a custom
ceiling:

```powershell
# optional - only to override the built-in defaults
$env:UNCHAINED_MODEL   = "gpt-5.6"     # already the default
$env:MAX_TOOL_CALLS    = "60"
$env:MAX_TOTAL_TOKENS  = "400000"
$env:MAX_WALL_SECONDS  = "1800"
$env:MAX_COST_USD      = "10"
```

Codex build credits and API runtime billing are separate. Runtime calls use the
funded OpenAI project associated with the key. Run the configuration check
without printing the key:

```powershell
& "$venv\Scripts\sentinel.exe" doctor
```

## 6. 🧲 Acquire permitted public evidence outside Git

Use the official DFIR Madness source page:

<https://dfirmadness.com/the-stolen-szechuan-sauce/>

Download only permitted public evidence. Do not commit the archive, extracted
memory image, raw tool output, or private acquisition paths. Keep evidence in a
separate directory, for example:

```text
C:\Evidence\sentinel\dc01\
```

The directory should contain the extracted Windows memory image. Unchained
profiles content rather than trusting a filename extension and prints a
path-free case card: OS, shape, readiness, sizes, hashes, available tools,
cloud boundary, and effective caps. It does not unpack an archive; any
permitted extraction happens before onboarding.

Profile and route it first - a `$0` local preview with no key and no spend
(bare `sentinel` does the same profile before it ever asks to launch; this
explicit CLI form stops at the card):

```powershell
& "$venv\Scripts\sentinel.exe" onboard C:\Evidence\sentinel\dc01
```

## 7. 🕵️ Run the bounded investigator

The recommended live path re-runs the local profile, prints the selected cloud
and hard-cap boundary, and then stops at the one launch card:

> [!WARNING]
> Prototype boundary: use an externally read-only or immutable evidence copy
> and a restricted nonsynchronized case workspace. The current router accepts
> at most one ready memory image and one ready disk image per case; same-class
> multiples fail closed. Parser children are credential-scrubbed and bounded
> but do not yet have OS-enforced network denial or scratch-only writes. OpenAI
> requests use implicit prompt caching, so review the provider's
> cache/retention policy before sending sensitive derived content.

```powershell
sentinel
```

You point it at `C:\Evidence\sentinel\dc01` when it asks, then pick
`3 = qualifying Sol` on the launch card only after checking the case and cap
cards (`1` and `2` are the cheaper Terra packages); anything else cancels with
no investigation request. (Prefer a launcher? `.\unchained.ps1` is identical.)
The onboarding path keeps disk handling raw-only unless you later opt into a
contained read-only mount. The explicit PowerShell wrapper remains available
for an operator who wants it to set the selected cap variables and prompt for
the key invisibly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 `
    -EvidencePath C:\Evidence\sentinel\dc01 -Live -Caps default
```

The hidden key prompt appears only in the local PowerShell window. The key is
not printed or written to the repository. Use `-SkipSetup` only after setup has
already passed in the same checkout. Direct `sentinel run` remains the advanced
noninteractive entry point when paid-run authorization is enforced externally:

```powershell
& "$venv\Scripts\sentinel.exe" run C:\Evidence\sentinel\dc01 --caps default
```

The run creates `unchained-runs\<run-id>\` beside the repository: report,
append-only audit log, manifest, summary, environment record, custody
receipts, retained content-addressed tool outputs, self-contained `viewer.html`.

The GPT-5.6 opening is intentionally all-or-none: it must choose one to twelve
distinct route-valid typed calls; an unknown, duplicate, malformed, or
thirteenth call rejects the whole opening rather than running a valid-looking
subset. In the adaptive loop, every response must contain exactly one typed
action. A forensic action continues the loop; only the closed
`finish_investigation({"status":"DONE"})` action terminates it - empty output,
free-form prose, case variants, extra fields, and Markdown have no terminal
authority. The verifier can still inspect historical literal-`DONE` v1
bundles, but the current runtime emits typed-DONE-v2.

Exit meanings:

| Exit | Meaning |
|---|---|
| `0` | complete lifecycle finished |
| `1` | deterministic fatal invariant or cleanup failure |
| `2` | invalid input or configuration - not a forensic finding |
| `3` | the result is `PARTIAL`, not complete - a hard cap or an unsafe failure in a mandatory model/provider/tool protocol phase can produce this exit |

## 8. 🧪 Verify the run

```powershell
$run = (Get-ChildItem .\unchained-runs -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1).FullName
& "$venv\Scripts\sentinel.exe" verify $run --require-complete --require-live-gpt56
& "$venv\Scripts\sentinel.exe" view $run
```

What strict verification establishes:

- **Transaction windows**: retry-aware model windows - each request and exact
  phase-options record may contain only policy-permitted bounded retry
  error/scheduled pairs, plus a recovery receipt when retried, before its one
  accepted response. Status-less retries must name a code-owned
  transport/timeout class, HTTP retries an eligible status; retry timeouts stay
  positive, within the run wall cap, and nonincreasing.
- **Response authority**: the normalized assistant message and function-call
  list; raw provider `output_items` are not stored as a second representation.
- **Full reconstruction**: the exact opening, adaptive, finalizer, judge, and
  report inputs - every adaptive ledger, receipt index, budget snapshot, latest
  observation, and full finalizer observation sequence - with accepted output
  usage bound to the paired request ceiling.
- **Bindings**: strict tool schemas/phase options, model function calls, tool
  receipts, visible case-ledger updates, typed-DONE-v2 (or historical
  literal-DONE-v1), forced investigation/judge/report serializers, full
  artifact descriptors, mandatory judge quotes, recomputed byte
  spans/occurrence counts, custody, cleanup, and the complete terminal state.
- **COMPLETE means complete**: a claimed `COMPLETE` run may contain no `capped`
  or `rejected` receipt; lifecycle count fields must equal the verified
  finding, verdict, and receipt collections. Typed argument values use the same
  bool-safe JSON primitive-type contract as runtime.
- **Deterministic rebuild**: reconstructs the canonical public profile from the
  profile event, binds its inventory to the initial and final custody receipts,
  rederives OS/shape/filesystems/route warnings, validates `profile.json`,
  rebuilds `summary.json`, and deterministically rerenders the report and
  viewer; both must match the sealed bytes exactly.
- **Cost honesty**: independently recomputes local GPT-5.6 cost estimates from
  audited token usage and the configured price table, reconciles cumulative
  totals, and binds the final budget snapshot to the configured caps. Those are
  local cap estimates, not proof of provider billing.
- **Identity honesty**: validates recorded provider-returned model identity and
  response IDs, but does not independently query or authenticate OpenAI.

`sentinel view` forces this strict lifecycle verification whenever a bundle
claims `COMPLETE`, even without a strict flag. If any check fails, retain the
failed run and report its actual state.

## 9. 🖥️ Host and evidence capability truth

| Host and evidence | Status | User-facing claim |
|---|---|---|
| Windows AMD64 plus Windows memory | **TESTED** | Primary route, symbols and typed tools demonstrated |
| Windows plus E01 or NTFS disk | **NOT PRIMARY** | Native Windows disk mounting is not promised |
| Linux plus Windows memory | **EXPERIMENTAL** | Verify Volatility and symbols on that host |
| Linux memory | **EXPERIMENTAL** | Matching kernel symbols are required |
| macOS memory | **BEST-EFFORT** | Not part of the scored flagship |
| Linux or macOS disk | **FUTURE/BEST-EFFORT** | Filesystem helpers vary and are not primary evidence |

## 10. 🗺️ Architecture to implementation map

| Diagram stage | Implementation | Output |
|---|---|---|
| Profile and route | `src/unchained/evidence.py` | Case card, capability profile, hashes |
| Typed runner | `tools.py`, `_tool_worker.py` | Function calls, retained output, delivery receipt |
| Opening book and loop | `agent.py`, `model.py` | Parallel opening, stateless plan-act-observe packets, case ledger |
| Audit | `audit.py` | Ordered append-only `audit.jsonl` |
| Caps | `caps.py` | Graceful partial stop and cap receipt |
| Judge | `agent.py`, `prompts.py` | Preserve or downgrade with exact byte-located spans |
| Report | `reporting.py` | Strict narrative draft and deterministic authoritative Markdown |
| Proof viewer | `viewer.py`, `viewer_policy.py` | Generated inert HTML plus independent positive-policy verification |
| Proof and verification | `artifacts.py`, `verify.py`, CLI | Manifest, summary, lifecycle/span verification |

## 11. 📚 Review of the prior-work and SANS examples

The prior-work forensic package
(<https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen>) is the best sample for
onboarding: a three-step run path, a dedicated judge quickstart, setup scripts,
architecture documents, public-case provenance, and explicit status tables.

Unchained adopts those communication strengths while tightening the experiment:

- no model shell or generic command executor;
- content-based evidence classification;
- fixed private-worker and model-view byte ceilings;
- full accepted output separated from bounded model delivery;
- controller-resolved byte spans instead of judge-visible 2,048-byte prefixes;
- stateless adaptive packets instead of full provider transcript replay;
- case-insensitive success and exception path scrubbing;
- requested and provider-returned model identity separated;
- custody, quote, and artifact hashes independently verified;
- factual correctness separated from receipt support;
- recorded provider metadata kept distinct from external authenticity.

Only the reviewed typed forensic layer is reused from that package, pinned in
`pyproject.toml`. That package's pipeline, validator, prompts, and report code
are not imported. The older Sentinel-Ensemble repository is contextual prior
work, not the Unchained implementation.

## 12. 🛠️ Troubleshooting

**Python not found:** install official 3.11 AMD64, reopen PowerShell, and run
`py -0p`.

**`pip check` fails:** recreate only the virtual environment outside the repo
using the exact constrained install above.

**API key absent:** set it in the Windows user environment, close old terminals,
open a new terminal, and run the presence-only check again.

**Symbols unavailable:** do not claim memory findings. The router must label
memory `UNAVAILABLE` and continue only with a supported route.

**Exit code 3:** the run is `PARTIAL`. A hard cap or a mandatory
model/provider/tool/protocol failure can cause it. Inspect the terminal reason
and `audit.jsonl`, then preserve the partial bundle.

**Large tool output:** use the full retained artifact and its completeness
receipt. Never call a prefix the complete native output.

## 13. 🐳 Optional Docker protocol smoke

This optional path verifies Linux/AMD64 packaging, the no-key
CLI/profile/custody front door, and an explicitly nonqualifying cheap API
canary. It does not replace the native Windows flagship instructions or prove
an authentic GPT-5.6 Sol DC01 investigation. Build and run the offline fixture
with no network and no key:

```powershell
docker build --target test -t sentinel-unchained:test .
docker compose build
docker compose run --rm offline
docker compose run --rm offline profile /evidence --json
```

The first run uses the service's `onboard --json` default and exits `0` without
a key, evidence read, or network. `doctor --json` remains an explicit
live-readiness check and correctly reports not ready in this offline/no-secret
service. Expected fixture-profile facts: `logs-only`, evidence ID `E001`,
`openai_called=false`, matching custody. For the one-request GPT-5.6 Terra
typed-tool canary, store the key in a readable one-line file outside the
repository and mount it as a Compose secret:

```powershell
$env:OPENAI_API_KEY_FILE = "C:\Secure\openai_api_key"
docker compose --profile live run --rm live-smoke
```

> [!NOTE]
> The output must say `NONQUALIFYING_CONNECTIVITY_SMOKE`. It reads no evidence,
> creates no proof bundle, and cannot satisfy `--require-live-gpt56`. Do not
> call it the hackathon primary or include it in a competitive benchmark.

The safe container deliberately does not use `--privileged`, FUSE, loop
devices, or `CAP_SYS_ADMIN`. Raw inspection remains available; mounted
E01/NTFS parity is outside this smoke.
