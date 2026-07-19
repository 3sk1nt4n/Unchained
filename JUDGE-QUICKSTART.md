# Unchained: quick install and run

## Fastest no-key lane (zero spend)

**If Python 3.11 is available, this is instant** — every command below returns
in well under a second and never contacts OpenAI:

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
.judge\Scripts\python.exe -m unchained onboard
.judge\Scripts\python.exe -m unchained profile docker/fixtures --json
```

The `pip install` is the only wait (~1–2 minutes); the product commands
themselves are instantaneous. You see the guided welcome, then deterministic
routing, public evidence IDs, and SHA-256 custody on the committed fixture,
with zero OpenAI calls.

**Prefer full isolation?** The same experience runs in a hardened container
(no network, read-only root, all capabilities dropped) — note
`docker compose build` takes several minutes on a cold cache:

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
docker compose build
docker compose run --rm offline profile /evidence --json
```

Everything below is the fuller walkthrough.

This is the shortest reliable path for a fresh Windows 10 or Windows 11 AMD64
machine. The Build Week flagship is Windows memory evidence. Native Windows E01
or NTFS mounting is not part of the primary path.

There are two separate judge paths:

1. No-key verification of a completed proof bundle.
2. An authentic GPT-5.6 investigation using Python 3.11, public evidence, and
   a funded OpenAI project key.

Never present a fake-model test or replay as an authentic GPT-5.6 run.

## Judge's first screen

After installation, start here—not with a funded run:

```powershell
$sentinel = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
& $sentinel onboard
```

The welcome needs no evidence and no key, reads nothing, and makes zero OpenAI
calls. To produce the first deterministic case card:

```powershell
& $sentinel onboard "C:\Evidence\sentinel\dc01"
```

That default profiles content and rechecks SHA-256 custody locally. Archives
are not unpacked; unsupported documents are hashed/listed and set aside. The
router accepts at most one ready memory image and one ready disk image per case.
Same-class multiples fail closed.

The paid path uses the same GPT-5.6 Sol model with one of two stop-ceiling
profiles:

| Choice | Option | Default hard ceilings |
|---|---|---|
| **CAUTIOUS** | `--caps strict` | 20 tools · 100,000 tokens · 10 min · $2.50 estimated cost |
| **FLAGSHIP** | `--caps default` | 60 tools · 400,000 tokens · 30 min · $10 estimated cost |

These are hard ceilings, not price quotes, reasoning-depth modes, or promises
of finding quality. The effective values appear in the onboarding card. A paid
run requires `--launch` in an interactive terminal and the exact phrase
`LAUNCH GPT-5.6 SOL`; JSON and noninteractive onboarding cannot launch.

The full junior-analyst walkthrough is [Start Here](docs/START-HERE.md).

**Hardware note:** no GPU is needed — GPT-5.6 runs on OpenAI's side. For the
real memory-image path, 4 cores / 8 threads and 16 GB RAM are comfortable (the
opening runs up to six Volatility processes concurrently); keep evidence on a
local SSD path, not a OneDrive/cloud-synced folder.

## 1. Install prerequisites

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

## 2. Clone and install

For the simplest supported setup, the complete install, dependency, and test
gate is one command after cloning:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

The script creates the validated Python 3.11 environment outside OneDrive,
installs the pinned dependencies, runs `pip check`, tests, Ruff, formatting,
and the package build. The individual commands below remain available when a
junior analyst needs to see or diagnose each stage.

Run each block from a new PowerShell window:

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
& $python -m pip install -c requirements/constraints.windows-amd64-cp311.txt -e ".[dev]"
& $python -m pip check
```

Expected final line:

```text
No broken requirements found.
```

Open the guided, zero-key welcome:

```powershell
$sentinel = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\sentinel.exe"
& $sentinel onboard
```

## 3. Run the no-key quality gate

This checks the installation and does not call OpenAI or inspect forensic
evidence:

```powershell
& $python -m pytest
& $python -m ruff check .
& $python -m ruff format --check .
& $python -m build
& "$venv\Scripts\vol.exe" -h
```

The OpenAI-native vNext tree has 267 passing tests across 32 Python files. A
failure should be fixed or reported with its environment details. Do not
silently switch interpreters.

## 4. Verify a completed proof bundle without rebuilding

The no-key demo is one command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo.ps1
```

Expected final lines:

```text
DEMO_BUNDLE_VERIFIED_INVALID_INPUT
BUNDLE=...
```

This verifies lifecycle and bundle construction only. It is not a forensic
investigation and does not prove GPT-5.6 participation.

For a supplied completed run:

```powershell
& "$venv\Scripts\sentinel.exe" verify C:\path\to\completed-run
& "$venv\Scripts\sentinel.exe" view C:\path\to\completed-run
```

The same verifier is available as a one-command wrapper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify.ps1 C:\path\to\completed-run
```

For strict submission-strength verification:

```powershell
& "$venv\Scripts\sentinel.exe" verify C:\path\to\completed-run `
    --require-complete --require-live-gpt56
```

The current synthetic `INVALID` fixture must fail the strict command. That proves
the verifier does not confuse a marked fake or incomplete lifecycle with a
complete one. Offline verification cannot independently authenticate OpenAI from
locally recorded IDs; retain the genuine provider/operator record separately.

## 5. Configure an authentic run

Create a funded project key at:

<https://platform.openai.com/api-keys>

**The one-step path — paste once with hidden input, done forever:**

```powershell
& "$venv\Scripts\sentinel.exe" key
```

Input is masked; the key is written to a private per-user file
(`%LOCALAPPDATA%\sentinel-unchained\openai_api_key`, owner-only) and **every
later sentinel command finds it automatically** — no environment variables,
no terminal restarts. Check or remove any time:

```powershell
& "$venv\Scripts\sentinel.exe" key --status
& "$venv\Scripts\sentinel.exe" key --remove
```

Never paste the key into chat, Git, a screenshot, or a command saved in
history. For automation, `OPENAI_API_KEY` or `OPENAI_API_KEY_FILE` still work
and always take precedence over the saved file.

Set the requested model and hard caps:

```powershell
$env:UNCHAINED_MODEL = "gpt-5.6"
$env:MAX_TOOL_CALLS = "60"
$env:MAX_TOTAL_TOKENS = "400000"
$env:MAX_WALL_SECONDS = "1800"
$env:MAX_COST_USD = "10"
```

Codex build credits and API runtime billing are separate. Runtime calls use the
funded OpenAI project associated with the key.

Run the configuration check without printing the key:

```powershell
& "$venv\Scripts\sentinel.exe" doctor
```

## 6. Acquire permitted public evidence outside Git

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
path-free case card containing OS, shape, readiness, sizes, hashes, available
tools, cloud boundary, and effective caps. It does not unpack an archive; any
permitted extraction happens before onboarding.

Profile and route it before spending an API call:

```powershell
& "$venv\Scripts\sentinel.exe" onboard C:\Evidence\sentinel\dc01
```

## 7. Run the bounded investigator

The recommended live path re-runs the local profile, prints the selected cloud
and hard-cap boundary, and then stops at the explicit confirmation gate:

> Prototype boundary: use an externally read-only or immutable evidence copy
> and a restricted nonsynchronized case workspace. The current router accepts
> at most one ready memory image and one ready disk image per case; same-class
> multiples fail closed. Parser children are credential-scrubbed and bounded
> but do not yet have OS-enforced network denial or scratch-only writes. OpenAI
> requests use implicit prompt caching, so review the provider's cache/retention
> policy before sending sensitive derived content.

```powershell
& "$venv\Scripts\sentinel.exe" onboard C:\Evidence\sentinel\dc01 `
    --launch --caps default
```

Type exactly `LAUNCH GPT-5.6 SOL` only after checking the case and cap cards.
Anything else cancels with no investigation request. Add `--mount` only when an
attempted contained read-only disk mount is needed; otherwise the onboarding
path keeps disk handling raw-only.

The explicit PowerShell wrapper remains available for an operator who wants it
to set the selected cap variables and prompt for the key invisibly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 `
    -EvidencePath C:\Evidence\sentinel\dc01 -Live -Caps default
```

The hidden key prompt appears only in the local PowerShell window. The key is
not printed or written to the repository. Use `-SkipSetup` only after setup has
already passed in the same checkout. Direct `sentinel run` remains the advanced
noninteractive entry point when paid-run authorization is enforced externally.

```powershell
Set-Location "$env:USERPROFILE\src\Unchained"
$python = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\python.exe"
& "$venv\Scripts\sentinel.exe" run C:\Evidence\sentinel\dc01 --caps default
```

The run creates `unchained-runs\<run-id>\` beside the repository. A complete
run contains a report, append-only audit log, manifest, summary, environment
record, custody receipts, retained content-addressed tool outputs, and a
self-contained `viewer.html`.

The GPT-5.6 opening is intentionally all-or-none: it must choose one to six
distinct route-valid typed calls. An unknown, duplicate, malformed, or seventh
call rejects the whole opening rather than running a valid-looking subset. In
the adaptive loop, every response must contain exactly one typed action. A
forensic action continues the loop; only the closed
`finish_investigation({"status":"DONE"})` action terminates it. Empty output,
free-form prose, case variants, extra fields, and Markdown have no terminal
authority. The verifier can still inspect historical literal-`DONE` v1 bundles,
but the current runtime emits typed-DONE-v2.

Exit meanings:

- `0`: complete lifecycle finished.
- `1`: deterministic fatal invariant or cleanup failure.
- `2`: invalid input or configuration. This is not a forensic finding.
- `3`: the result is `PARTIAL`, not complete. A hard cap or an unsafe failure in
  a mandatory model/provider/tool protocol phase can produce this exit.

## 8. Verify the run

```powershell
$run = (Get-ChildItem .\unchained-runs -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1).FullName
& "$venv\Scripts\sentinel.exe" verify $run --require-complete --require-live-gpt56
& "$venv\Scripts\sentinel.exe" view $run
```

Strict verification establishes retry-aware model transaction windows: each
request and exact phase-options record may contain only the bounded retry
error/scheduled pairs permitted by policy, plus a recovery receipt when retried,
before its one accepted response. The audited response authority is the
normalized assistant message and function-call list; raw provider `output_items`
are not stored as a second representation. Status-less retries must name a
code-owned transport/timeout class, HTTP retries must use an eligible status,
and retry timeouts must remain positive, within the run wall cap, and
nonincreasing.

The verifier reconstructs the exact opening, adaptive, finalizer, judge, and
report inputs—including every adaptive ledger, receipt index, budget snapshot,
latest observation, and full finalizer observation sequence—and binds accepted
output usage to the paired request ceiling. It binds strict tool schemas/phase
options, model function calls, tool receipts, visible case-ledger updates,
typed-DONE-v2 (or historical literal-DONE-v1), forced
investigation/judge/report serializers, full artifact descriptors, mandatory
judge quotes, recomputed byte spans/occurrence counts, custody, cleanup, and the
complete terminal state. A claimed `COMPLETE` run may contain no `capped` or
`rejected` receipt, and lifecycle count fields must equal the verified finding,
verdict, and receipt collections. Typed argument values use the same bool-safe
JSON primitive-type contract as runtime. It reconstructs the canonical public
profile from the
profile event, binds its inventory to the initial and final custody receipts,
rederives OS/shape/filesystems/route warnings, validates `profile.json`, rebuilds
`summary.json`, and deterministically
rerenders the report and viewer; both must match the sealed bytes exactly. It
independently recomputes local GPT-5.6 cost estimates from audited token usage
and the configured price table, reconciles cumulative totals, and binds the
final budget snapshot to the configured caps. Those costs are local cap
estimates, not proof of provider billing.

It also validates recorded provider-returned model identity and response IDs,
but it does not independently query or authenticate OpenAI. `sentinel view`
forces this strict lifecycle verification whenever a bundle claims `COMPLETE`,
even if the operator did not pass a strict flag. If any check fails, retain the
failed run and report its actual state.

## 9. Host and evidence capability truth

| Host and evidence | Status | User-facing claim |
|---|---|---|
| Windows AMD64 plus Windows memory | **TESTED** | Primary route, symbols and typed tools demonstrated |
| Windows plus E01 or NTFS disk | **NOT PRIMARY** | Native Windows disk mounting is not promised |
| Linux plus Windows memory | **EXPERIMENTAL** | Verify Volatility and symbols on that host |
| Linux memory | **EXPERIMENTAL** | Matching kernel symbols are required |
| macOS memory | **BEST-EFFORT** | Not part of the scored flagship |
| Linux or macOS disk | **FUTURE/BEST-EFFORT** | Filesystem helpers vary and are not primary evidence |

## 10. Architecture to implementation map

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

## 11. Review of the Qwen and SANS examples

The Qwen repository is the best sample for onboarding because it exposes a
three-step run path, a dedicated judge quickstart, setup scripts, architecture
documents, public-case provenance, and explicit status tables:

<https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen>

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

Only the reviewed typed forensic layer is reused from Qwen, pinned in
`pyproject.toml`. The Qwen pipeline, validator, prompts, and report code are not
imported. The older Sentinel-Ensemble repository is contextual prior work, not
the Unchained implementation.

## 12. Troubleshooting

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

## 13. Optional Docker protocol smoke

This optional path verifies Linux/AMD64 packaging, the no-key CLI/profile/custody
front door, and an explicitly nonqualifying cheap API canary. It does not
replace the native Windows flagship instructions or prove an authentic GPT-5.6
Sol DC01 investigation.

Build and run the offline fixture with no network and no key:

```powershell
docker build --target test -t sentinel-unchained:test .
docker compose build
docker compose run --rm offline
docker compose run --rm offline profile /evidence --json
```

The first run uses the service's `onboard --json` default and exits `0` without
a key, evidence read, or network. `doctor --json` remains an explicit
live-readiness check and correctly reports not ready in this offline/no-secret
service. Expected fixture-profile facts include `logs-only`, evidence ID `E001`,
`openai_called=false`, and matching custody.

For the one-request GPT-5.6 Luna typed-tool canary, store the key in a readable
one-line file outside the repository and mount it as a Compose secret:

```powershell
$env:OPENAI_API_KEY_FILE = "C:\Secure\openai_api_key"
docker compose --profile live run --rm live-smoke
```

The output must say `NONQUALIFYING_CONNECTIVITY_SMOKE`. It reads no evidence,
creates no proof bundle, and cannot satisfy `--require-live-gpt56`. Do not call
it the hackathon primary or include it in the Qwen benchmark.

The safe container deliberately does not use `--privileged`, FUSE, loop
devices, or `CAP_SYS_ADMIN`. Raw inspection remains available; mounted E01/NTFS
parity is outside this smoke.
