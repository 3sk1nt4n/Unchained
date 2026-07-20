<p align="center">
  <img
    src="docs/assets/readme-hero.png"
    alt="Unchained — GPT-5.6 chooses where to look; code proves what happened"
    width="1000"
  >
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Windows-flagship%20lane-0078D6?logo=windows&logoColor=white" alt="Windows flagship lane">
  <img src="https://img.shields.io/badge/Linux-hardened%20container-1793D1?logo=linux&logoColor=white" alt="Linux hardened container">
  <img src="https://img.shields.io/badge/macOS-via%20Docker-000000?logo=apple&logoColor=white" alt="macOS via Docker">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Python-3.11-3776ab.svg?logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/Docker-Linux%2FAMD64-2496ed.svg?logo=docker&logoColor=white" alt="Docker Linux AMD64">
  <img src="https://img.shields.io/badge/Evidence-read--only-dc2626.svg" alt="Read-only evidence">
  <img src="https://img.shields.io/badge/Proof-offline--verifiable-f59e0b.svg" alt="Offline-verifiable proof">
  <img src="https://img.shields.io/badge/OpenAI-GPT--5.6-111827.svg?logo=openai&logoColor=white" alt="OpenAI GPT-5.6">
</p>

<p align="center">
  <strong>Unchained reasoning. Chained evidence.</strong>
</p>

<p align="center">
  A bounded autonomous Digital Forensics &amp; Incident Response (DFIR)
  investigator: model judgment where it helps, deterministic authority
  everywhere evidence can change.
</p>

<p align="center">
  <a href="docs/START-HERE.md"><strong>🚀 Start here</strong></a> ·
  <a href="#for-judges--the-submission-at-a-glance">🏆 For judges</a> ·
  <a href="#quickstart">⏱️ Quickstart</a> ·
  <a href="#what-you-will-see">🎬 Run experience</a> ·
  <a href="#how-it-works">🧠 Architecture</a> ·
  <a href="#proof-status">🧾 Proof status</a> ·
  <a href="JUDGE-QUICKSTART.md">⚖️ Judge guide</a>
</p>

**The whole idea in one breath:**

- 🔍 **Deterministic code goes first** — before any model call, the evidence is
  enumerated, content-probed, routed, and SHA-256-hashed into custody, locally
  and read-only. Zero OpenAI calls until this front door is green.
- 🧠 **Then GPT-5.6 runs the investigation** — it opens with up to twelve
  high-value typed forensic tools (memory and disk) fired in parallel, reads
  the retained results, chooses the next tool one audited action at a time, and
  finally proposes structured findings that a fresh-context reviewer may only
  preserve or downgrade.
- 🔒 **Code owns the evidence the whole way** — read-only access, hard caps,
  all-or-none validation, exact byte-span citations. The model is never
  allowed to *be* the evidence.
- 🧾 **Every case seals into a proof bundle** — a hash-chained audit log and an
  offline verifier that rebuilds the report and viewer byte-for-byte. If one
  byte changes, verification fails.

**This is the real first screen** — just `sentinel`, no key, no evidence, zero
OpenAI calls:

<p align="center">
  <img src="docs/assets/cli-welcome.svg" alt="The real sentinel welcome: guided cards, budget choice, and an explicit cloud/cost boundary" width="760">
</p>

> **What “proves” means here:** code verifies what ran, what bytes were retained,
> what exact text was cited, and whether custody still matches. It does **not**
> prove that a model's forensic interpretation is true. A human analyst still
> owns that judgment.

> **New analyst? There is exactly one command:** `sentinel`
>
> It opens the welcome, asks one thing (where the evidence is), prints a local
> SHA-256 case card, asks the depth, and only then stops for the exact
> interactive phrase `LAUNCH GPT-5.6 SOL` before any spend. No flags, no
> environment variables. Follow the card-by-card
> [first-case guide](docs/START-HERE.md).

## For judges — the submission at a glance

| Field | Value |
|---|---|
| Track | **Developer Tools** — OpenAI Build Week |
| Built with | **Codex** (implementation + adversarial review) and **GPT-5.6** (Sol investigator/reviewer, Luna canary) |
| Codex Session ID | `019f61e5-5755-7a02-adb4-618d32baab27` — see [Built with Codex](#built-with-codex) |
| Fastest no-key test | A few commands, zero spend — top of the [judge quickstart](JUDGE-QUICKSTART.md) |
| Live receipts | [Sol capped opening on real memory](docs/runs/sol-capped-dc01-opening.json) · [Luna canary](docs/runs/luna-canary-receipt.json) |
| Honest gaps | `COMPLETE` bundle, benchmark, and video are pending; the [proof status](#proof-status) table never overstates |

**Where each judging criterion lives:**

| Criterion | Look at |
|---|---|
| Technological Implementation | [How it works](#how-it-works) · typed opening book, stateless loop, typed `DONE` v2, byte-exact offline verifier |
| Design | one-word `sentinel` self-driving front door · live investigation narration · static inert proof viewer |
| Potential Impact | [Why Unchained is different](#why-unchained-is-different) — inspectable autonomy for any high-consequence agent, not just DFIR |
| Quality of the Idea | The authority split: the model chooses strategy; code owns evidence, execution, citations, custody, and the report |

**🚦 Submission readiness — live and honest:**

| Item | Status |
|---|---|
| 🟢 Public MIT repo, Codex Session ID, provenance boundary | **Done** |
| 🟢 390-test offline gate, ruff clean, hardened Docker | **Done** |
| 🟢 Live GPT-5.6 Sol opening on real 2 GiB Windows memory | **Done** — retained, capped `PARTIAL` by design |
| 🟢 Zero-key guided onboarding + colorful live run experience | **Done** — see the screen above |
| 🟡 Authentic `COMPLETE` proof bundle | **In progress** — the final live run |
| 🟡 Public sub-3-minute video | **In progress** — recorded against the real bundle |
| ⚪ Same-evidence Qwen benchmark | **Deliberately cut** — no unmeasured claims |

## Quickstart

### ⏱️ 60 seconds, any OS, zero keys, zero spend

```powershell
# 🪟 Windows (one line — installs, walks you in, never spends)
irm https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.ps1 | iex
```

```bash
# 🐧 Linux / 🍎 macOS (one line — hardened container, never spends)
curl -fsSL https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.sh | bash
```

**Ready-made samples, no hunting:** a safe synthetic case ships in the repo
(`sentinel onboard docker/fixtures` — instant, free), and the installer walks
you to the public **DFIR Madness 001** practice case (official download page
plus the publisher's checksums; Unchained never fetches evidence for you).

Point it at a folder and you get a local, cryptographic case card — every file
SHA-256-hashed, classified, and routed **before any model is allowed near it**.
The tool refuses to overstate: a synthetic logs-only fixture honestly gets an
amber `ACTION NEEDED` card, not a fake green light:

<p align="center">
  <img src="docs/assets/cli-case-card.svg" alt="The real case card: per-file SHA-256 custody, honest ACTION NEEDED status on a synthetic fixture, budget choice, and cloud/cost boundary" width="760">
</p>

**Pick your machine. Every lane starts with zero keys and zero spend.**

| Your machine | Lane | First result in | Spend | Verified state |
|---|---|---|---|---|
| 🪟 **Windows 10/11** | Native CPython 3.11 — the flagship forensic lane | ~5 min | $0 until you type the launch phrase | ✅ Tested; the live Sol run happened here |
| 🐧 **Linux (AMD64)** | Hardened Docker offline lane | ~3 min | $0 | ✅ Tested: 274-test in-container gate |
| 🍎 **macOS** | Same Docker lane via Docker Desktop | ~3 min | $0 | ⚠️ Expected via Docker's `linux/amd64` emulation; not yet verified on Mac hardware |

Every lane converges on the same experience: a colorful guided onboarding, a
SHA-256 case card, an explicit two-key launch gate, and — after a run — an
offline-verifiable proof bundle.

### Two commands. Any OS.

The first installs and verifies everything; the second walks you through a whole
case. Pick your line:

```powershell
# 🪟 Windows (Git + CPython 3.11)
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
.\setup.ps1          # install + verify everything (one command)
.\unchained.ps1      # start a whole case — it walks you through the rest
```

```bash
# 🐧 Linux / 🍎 macOS (Git + Python 3.11)
git clone https://github.com/3sk1nt4n/Unchained.git && cd Unchained
./setup.sh           # install + verify everything (one command)
./unchained.sh       # start a whole case — it walks you through the rest
```

> Prefer a one-liner install? `irm …/get.ps1 | iex` (Windows) or
> `curl -fsSL …/get.sh | bash` (Linux/macOS) do the clone + install for you.
> After install, bare `sentinel` is identical to the launcher; re-verify anytime
> with `.\setup.ps1 -Check` (or `./setup.sh --check`).

**What the second command does** (identical on every OS): a full-color welcome,
**one question** (where the evidence is), a SHA-256 verified case card computed
locally (`$0`, no key, no OpenAI), a depth pick, automatic key resolution (or one
hidden prompt), and only then a stop for the exact phrase `LAUNCH GPT-5.6 SOL`
before it runs live and verifies the sealed bundle. No flags, no environment
variables. Depth sets only hard stop ceilings — the same GPT-5.6 Sol
investigator either way:

| Depth | Hard ceilings (not a price quote) |
|---|---|
| **LIGHT** — first case | 20 tools · 100,000 tokens · 10 min · $2.50 estimated cost |
| **HEAVY** — deeper run | 60 tools · 400,000 tokens · 30 min · $10 estimated cost |

Read the concise [Start Here guide](docs/START-HERE.md) for evidence formats,
mount outcomes, cloud boundaries, and the post-run verify/view steps.

**Zero-install, fully isolated** (any OS with Docker): the hardened container
reads no evidence, takes no key, and has **no network** —

```bash
docker compose run --rm offline
```

It profiles a committed synthetic fixture with zero OpenAI calls (public evidence
ID `E001`, matching custody), runs non-root with a read-only filesystem and every
Linux capability dropped, and honestly reports `logs-only`.

> **Honest macOS label:** the container is the same hardened `linux/amd64` image
> running under Docker Desktop through emulation. It has not been verified on
> Mac hardware, and emulation makes large-image work slower — same container,
> same commands, not yet a tested macOS forensic route.

### 💡 Cheap live check: one GPT-5.6 Luna request

This canary tests only container → OpenAI authentication, the Responses API,
returned model/request identity, usage accounting, and one forced strict typed
tool call. It reads no evidence and creates no proof bundle.

Put the key in a one-line file outside the repository, then point Compose to
that file:

> Revoke any key that has appeared in chat, logs, screenshots, or recordings.
> Use a fresh project-scoped key with an explicit spend limit for the canary.

```powershell
$env:OPENAI_API_KEY_FILE = "C:\Secure\openai_api_key"
docker compose --profile live run --rm live-smoke
```

The key is mounted as a Docker secret and read through
`OPENAI_API_KEY_FILE`; it is not copied into the image or placed in ordinary
container environment metadata. The command defaults to `gpt-5.6-luna`, one
request, low reasoning, low verbosity, a 128-output-token ceiling, `store=false`,
and no retry layer.

> The result is labeled `NONQUALIFYING_CONNECTIVITY_SMOKE`. It cannot satisfy
> `--require-live-gpt56`, enter the Qwen benchmark, or stand in for a forensic
> run. Luna is used here because OpenAI positions it for efficient,
> high-volume work at lower cost; the proof-compatible investigation remains
> Sol-specific. See OpenAI's [latest-model guide](https://developers.openai.com/api/docs/guides/latest-model)
> and [current pricing](https://developers.openai.com/api/docs/pricing).

The first live canary has now been independently reported as one valid Luna
request with 186 input and 27 output tokens. Because its raw JSON receipt was
not retained with the supplied artifacts, the committed
[Luna receipt](docs/runs/luna-canary-receipt.json) is explicitly an attested
sanitized projection—not bundle-derived cryptographic proof.

<details>
<summary>Linux/macOS secret-file command</summary>

```bash
export OPENAI_API_KEY_FILE=/secure/openai_api_key
docker compose --profile live run --rm live-smoke
```

</details>

### 🔬 Real investigation: the GPT-5.6 Sol proof path

The flagship path is native Windows + CPython 3.11 for Windows memory evidence.
After `setup.ps1`, it is the **same one command** — `sentinel` defaults to the
public `gpt-5.6` alias (Sol) automatically, so there is nothing to configure:

```powershell
sentinel
```

It profiles the case, asks the depth, saves your key at a one-time hidden prompt
if you have not already (`sentinel key`), and stops for the exact interactive
phrase `LAUNCH GPT-5.6 SOL` before spending. At completion it prints the exact
next `verify` and `view` commands. Advanced automation may still invoke
`sentinel run` directly when authorization is established outside the CLI.

The live Sol opening/tool route is now demonstrated on real memory. Before the
flagship `COMPLETE` run, use a harmless case to exercise the still-pending live
typed `finish_investigation({"status":"DONE"})` → serializer → reviewer →
final-report phases under the intended submission caps.

## What you will see

1. **Case card** — evidence is classified by bounded content probes, assigned
   public IDs, routed by OS/shape, and SHA-256 hashed before any model call.
2. **Opening book** — GPT-5.6 chooses up to twelve eligible typed tools. Code
   validates the complete decision and runs them concurrently; the terminal
   narrates each tool with its retained bytes and execution time.
3. **Visible investigation** — each adaptive turn is
   `PLAN → one ACT → OBSERVE → UPDATE`. The run shows GPT-5.6's per-turn
   reasoning (its visible case-ledger update), the one typed action it chose,
   and per-response token counts with a running cost estimate; growing provider
   transcripts are never replayed.
4. **Grounded review** — exact quotes become content-addressed UTF-8 byte spans;
   a fresh-context reviewer may preserve or downgrade, never upgrade, and each
   verdict prints as a green *preserved* or amber *downgraded* line with its
   rationale.
5. **Proof handoff** — a final status badge prints the bundle path, terminal
   status, the strict verification gates, and the exact verify/view commands.

The model never receives a shell, local evidence path, executable name,
subprocess authority, or budget authority. Fixed private workers may invoke
allowlisted forensic operations; the model cannot construct those commands.

## What you get

Every finalized run lives under
`unchained-runs/<UTC-timestamp>-<id>/` outside the evidence tree.

| Artifact | Plain-English purpose |
|---|---|
| `viewer.html` | Self-contained, no-JavaScript proof viewer; no server required |
| `report.md` | Human-readable report with deterministic finding rows and citations |
| `audit.jsonl` | Ordered, hash-chained lifecycle receipts |
| `tool-outputs/` | Exact sanitized outputs cited by findings |
| `profile.json` | Evidence inventory, route, readiness, and capability label |
| `environment.json` | Allowlisted runtime, dependency, model, prompt, catalog, and cap facts |
| `summary.json` | Audit-derived status, usage, finding, receipt, and custody counters |
| `manifest.json` + `manifest.sha256` | Content-addressed bundle inventory and detached checksum |

```powershell
sentinel view C:\path\to\bundle
```

`view` verifies the bundle before opening it. A bundle claiming `COMPLETE`
automatically receives strict lifecycle verification first.

## Who needs this

An incident-response consultancy wants AI triage on a compromised host image,
but must show the client — and possibly a regulator or opposing counsel —
exactly what the AI did to the evidence. A transcript is not an answer.
Unchained gives them a sealed bundle: which tools ran, on which evidence, with
which SHA-256 identities, what exact bytes each finding cites, and a verifier
anyone can run offline to confirm none of it changed. The same need appears
wherever an autonomous agent touches something that can end up in a dispute:
security testing, compliance review, financial operations. The audience is
anyone who wants model autonomy **and** has to answer for it afterward.

## Why not just guardrails, evals, or attestation?

Each existing trust family solves a different problem, and none closes this one:

- **Guardrails / structured outputs** constrain what the model may *say* in one
  response. They do not bind a multi-step investigation to retained evidence
  bytes, and nothing re-checks the transcript afterward.
- **Evals and LLM-as-judge** measure quality offline or ask a second model for
  an opinion. Unchained's reviewer is deliberately weaker and therefore
  stronger: it can only **preserve or downgrade** existing findings — a
  monotonic review lattice, not a second opinion that can invent support.
- **Supply-chain attestation (in-toto/SLSA-style)** proves how software was
  built. Unchained applies the same content-addressed discipline to what an
  *agent did at runtime*: every tool call, output byte, citation span, custody
  hash, and report row is reconstructed and byte-compared by an independent
  offline verifier.

The delta in one sentence: **existing tools constrain or score the model;
Unchained makes the investigation itself independently re-checkable.**

## Why Unchained is different

| Layer | Authority |
|---|---|
| GPT-5.6 investigator | Chooses bounded strategy, updates the visible ledger, interprets retained observations, proposes findings |
| Deterministic controller | Routes evidence, validates typed calls, enforces caps, executes tools, hashes custody, resolves exact spans |
| Fresh-context reviewer | Preserves or downgrades existing findings; cannot create or upgrade them |
| Deterministic renderer | Owns authoritative finding rows, transitions, citations, status, report, and viewer |
| Offline verifier | Reconstructs phase inputs, receipts, spans, costs, report, viewer, custody, and terminal state |
| Human analyst | Decides whether the interpretation is correct and what action to take |

That separation is the product: **GPT-5.6 decides where to look; deterministic
code controls what is legal and proves what the system actually retained and
cited.**

## How it works

```mermaid
flowchart TD
    E[Evidence folder] --> P[Profile · route · initial SHA-256]
    P --> O[GPT-5.6 opening book<br/>choose up to 12 typed tools]
    O --> X[All-or-none validation<br/>parallel deterministic execution]
    X --> L[Plan → one action → observe → visible update]
    L --> D{Typed action is<br/>finish status DONE?}
    D -- Forensic tool --> L
    D -- Typed DONE --> S[Forced structured findings]
    S --> J[Fresh-context<br/>downgrade-only review]
    J --> R[Deterministic report<br/>inert viewer · proof manifest]
    R --> V[Final custody check<br/>strict offline verification]

    classDef model fill:#172554,stroke:#60a5fa,color:#fff;
    classDef code fill:#422006,stroke:#f59e0b,color:#fff;
    class O,L,S,J model;
    class P,X,D,R,V code;
```

- **Blue:** GPT-5.6 judgment inside a bounded protocol.
- **Amber:** deterministic code authority and proof reconstruction.

**Invocation budget:** a completed case makes exactly **4 fixed GPT-5.6
requests** (opening book, findings serialization, fresh review, report draft)
**plus one per adaptive action** — minimum five, never an unbounded loop. Every
request is audited and charged before use, and the hard caps fire *before*
dispatch, ending the run as honest `PARTIAL` instead of overspending. Details:
[Model invocation budget](docs/ARCHITECTURE.md#model-invocation-budget).

Read the full [architecture](docs/ARCHITECTURE.md) or the detailed
[OpenAI vNext review](docs/OPENAI_VNEXT_REVIEW.md).

## Current release status

| Capability | State |
|---|---|
| OpenAI-native controller and independent offline verifier | ✅ Verified offline |
| Linux/AMD64 Docker build, 274-test gate, CLI, profile, and custody | ✅ Verified locally |
| Cheap GPT-5.6 Luna typed-tool canary | ✅ Demonstrated live; second-reviewer-attested (project-affiliated) sanitized receipt |
| Authentic GPT-5.6 Sol capped opening on real Windows memory | ✅ Retained bundle verifies `VALID`; terminal state is intentionally `PARTIAL` |
| Authentic `COMPLETE` GPT-5.6 Sol evidence bundle | ⏳ Opening/tool path proven; findings → reviewer → final report still pending |
| Same-evidence speed/cost/accuracy comparison with Qwen | ⏳ Fail-closed comparison scaffold ready; fact set, freeze lock, and measurements pending |

**Live milestone:** the first retained Sol run used a 2 GiB Windows memory image,
recorded `gpt-5.6-sol` on both model responses, executed all six model-selected
opening tools successfully (under the earlier six-tool opening cap; the opening
now allows up to twelve), and stopped honestly when the next reservation would
exceed that cap. It used 59,254 provider-reported tokens, took
43.702 seconds end to end, and produced a local cost estimate of $0.38789875.
This proves the live opening, typed execution, cap, custody, and bundle path—not
a completed investigation. See the
[release handoff](docs/OPENAI_VNEXT_RELEASE_HANDOFF.md) for the full scorecard
and fastest submission path.

**Post-rehearsal hardening:** four later unscored attempts exposed a real
terminal-contract problem. Their retained audits show completed responses with
395–1,750 characters of visible ledger text but no typed action—not empty
responses. The v2 controller therefore does not normalize blank text,
punctuation, Markdown, or prose into completion. Every adaptive response must
choose exactly one typed action: one eligible forensic tool or the closed
`finish_investigation` action with the sole argument `status="DONE"`. The
offline verifier understands historical literal-DONE-v1 bundles but requires
the new runtime's typed catalog, `tool_choice=required`, and exact terminal
schema. A live `COMPLETE` v2 bundle remains pending.

## Proof status

| Claim | Current evidence |
|---|---|
| Deterministic profile, routing, public IDs, and pre/post custody | Unit/adversarial tests + containerized synthetic profile |
| Up-to-twelve all-or-none parallel opening | Controller and synchronization-barrier regression tests |
| Stateless one-action adaptive loop and typed `DONE` | Required-action, closed-schema, malformed-status, exact-input, and protocol-mutation tests; literal v1 remains verifier-readable only |
| Exact evidence spans | Full-artifact late-span and byte-mutation tests |
| Downgrade-only fresh review | Finding-ID, status-lattice, span, and receipt tests |
| Deterministic report and inert viewer | Independent rerender + exact-byte and positive HTML/CSP policy tests |
| Independent strict verifier | Re-chained adversarial mutations across lifecycle, usage, retry, cost, and custody |
| Linux Docker packaging | CPython 3.11 test target: 274 tests, Ruff, format, and `pip check`; non-root runtime/profile gate |
| Live GPT-5.6 Luna canary | Independently demonstrated; [attested sanitized projection](docs/runs/luna-canary-receipt.json), with no raw receipt available for bundle proof |
| Authentic GPT-5.6 Sol opening on real memory | [Bundle-derived sanitized receipt](docs/runs/sol-capped-dc01-opening.json): 2 model responses, 6 successful opening tools, recorded custody match, offline `VALID` |
| Authentic complete GPT-5.6 Sol case | Pending; retained Sol run is explicitly `PARTIAL` at `MAX_TOOL_CALLS` |
| Faster/better than Qwen | Architectural thesis only until the frozen benchmark is run |

The verifier establishes local protocol and bundle consistency. It does not
cryptographically authenticate OpenAI, replace semantic accuracy scoring, or
turn a same-family reviewer into external ground truth.

## Inspect a proof bundle without a key

```powershell
sentinel verify C:\path\to\bundle --require-complete --require-live-gpt56
sentinel view C:\path\to\bundle
```

Strict verification does more than recompute manifest hashes:

- it reconstructs every model-visible phase packet and typed-call contract;
- it resolves finding quotes against retained artifacts and exact UTF-8 ranges;
- it recomputes usage, local cost estimates, lifecycle counts, and custody;
- it rebuilds `report.md` and `viewer.html` and requires byte-for-byte equality.

Offline consistency is not provider authenticity. Preserve provider-side logs
and externally anchor the final checksum if that threat model matters.

## Supported paths

| Evidence / host route | Status |
|---|---|
| Windows memory image on native Windows | Live Sol opening and six typed tools demonstrated; `COMPLETE` findings/review/report case pending |
| Raw memory image in the safe Linux container | Supported by Volatility; case-specific symbols/readiness still apply |
| Raw disk image with Sleuth Kit in the safe container | Unprivileged raw inspection available |
| Mounted E01/NTFS/APFS inside Docker | Not enabled; would require elevated device/FUSE authority |
| Windows disk/E01 on a properly configured native host | Implemented; authentic vNext route pending |
| Linux evidence | Experimental |
| macOS evidence | Best effort |
| Logs-only folder | Profile/custody smoke only; not a complete investigation route |
| Two ready memory images or two ready disk images | Fails closed; split them into separate cases |

Evidence capability is route-specific. “Docker runs on this laptop” is not the
same claim as “every forensic image type is fully supported on this host.”

## Docker safety boundary

The default Compose service is intentionally conservative:

- non-root UID/GID `10001:10001`;
- read-only root filesystem and read-only evidence bind;
- all Linux capabilities dropped;
- `no-new-privileges` and bounded process count;
- no Docker socket, host PID namespace, or privileged mode;
- no network for the offline service;
- Git exists only in the networked builder, not the final runtime;
- `sleuthkit`, Volatility, CA certificates, and Tini in the runtime.

The live canary necessarily has outbound network access. Safe Docker mode does
not mount filesystems: E01/FUSE/loop-device support would weaken isolation and
is deliberately outside this default.

For multi-gigabyte evidence on Docker Desktop, use a local non-OneDrive path or
WSL2 ext4 storage. A cloud-synced bind can dominate runtime.

## CLI at a glance

```text
sentinel                              # the one command: self-drives a whole case
sentinel onboard [<evidence>] [--mount] [--json]   # $0 preview / scripting surface
sentinel key [--status | --remove]
sentinel doctor
sentinel profile <evidence> --json
sentinel smoke-openai --json
sentinel run <evidence> --caps strict              # advanced non-interactive entry
sentinel verify <bundle> --require-complete --require-live-gpt56
sentinel view <bundle>
```

Bare `sentinel` on a terminal walks you through everything (welcome → one
question → verified card → depth → explicit launch). The subcommands above
remain for `$0` previews, scripting, and advanced non-interactive runs.

| Exit | Meaning |
|---:|---|
| `0` | Command completed within its policy; not an accuracy guarantee |
| `1` | Fatal runtime, provider, verification, or custody failure |
| `2` | Invalid input or configuration |
| `3` | `PARTIAL`: a cap or mandatory phase failed safely |

## Performance and recommended hardware

All GPT-5.6 compute runs on OpenAI's side — **no local GPU is used or
required**. Local performance is decided by CPU, RAM, and the disk path:

| Component | Minimum | Recommended | Why it matters |
|---|---|---|---|
| CPU | 4 cores / 8 threads | 8+ cores | The opening fires up to **twelve typed tools**, executed in bounded concurrent waves, each in its own private child process |
| RAM | 8 GB | **16 GB** | Several Volatility processes read the same multi-GiB memory image at once; 16 GB keeps the opening out of swap (the OS page cache shares the image bytes) |
| Disk | SSD, local path | NVMe, non-synced folder | Full SHA-256 custody hashing plus parallel image reads; a OneDrive/cloud-synced or network path can dominate total runtime |
| GPU | none | none | Model inference is an OpenAI API call, not local |
| Network | stable HTTPS egress | — | Used only for GPT-5.6 requests; evidence bytes never leave the machine |

**Measured reference point** (retained live run, Windows 11): a 2 GiB Windows
memory image, six-tool concurrent opening, 43.7 seconds end to end. Rows above
are sizing recommendations, not measurements.

For the Docker Desktop lane with multi-gigabyte evidence, give WSL2 enough
headroom and keep evidence on WSL2 ext4 (not a Windows OneDrive bind):

```ini
# %UserProfile%\.wslconfig  — then run: wsl --shutdown
[wsl2]
memory=12GB
processors=6
```

## Troubleshooting

| Symptom | What to do |
|---|---|
| `doctor` says model/key missing | Set `UNCHAINED_MODEL=gpt-5.6` and either `OPENAI_API_KEY` or `OPENAI_API_KEY_FILE` |
| Docker `doctor` exits `2` with no key | Expected for the offline/no-secret service; use `profile` or `--help` for the no-key gate |
| Luna smoke cannot find its secret | Set host `OPENAI_API_KEY_FILE` to a readable one-line file and add `--profile live` |
| Profile says mount unavailable | Use raw inspection or a properly configured native forensic host; do not add `--privileged` casually |
| Multiple same-class images fail | Put each ready memory/disk image in a separate case folder |
| `view` cannot open from Docker | Verify in the container, then open the bind-mounted `viewer.html` on the host |
| A run is `PARTIAL` | Read `summary.json`, `report.md`, and the last audit events; do not relabel it complete |
| `PARTIAL` with a `429 Request too large ... TPM` audit error | The findings-serializer re-sends every retained observation in one request, which can exceed a low tokens-per-minute limit. New OpenAI accounts cap at ~200k TPM; a rich 12-tool investigation's serializer can be ~270k. Use an account whose TPM exceeds your serializer size (add credit / verify to tier up), or run a smaller opening. |
| `PARTIAL` with `MAX_TOTAL_TOKENS` before the report | The full lifecycle (opening + adaptive turns + serializer + judge + report) on a real memory image can exceed the default 400k token cap. Raise it for the complete run, e.g. `MAX_TOTAL_TOKENS=3000000 MAX_COST_USD=30`. |

## Honest limits

- A real Sol evidence bundle now proves the live opening/tool/cap/custody path,
  but it is `PARTIAL`; no authentic `COMPLETE` GPT-5.6 vNext bundle is published
  yet.
- The Luna receipt is a second-reviewer attestation (project-affiliated) because
  its raw JSON response was not retained; it is not bundle-derived proof.
- No frozen same-evidence Qwen latency/cost/accuracy benchmark is published yet.
- Exact receipts establish execution and citation support, not forensic truth.
- The fresh reviewer is a same-family model call, not independent ground truth.
- Private worker containment and process-tree cleanup are not a complete OS sandbox.
- SHA-256 pre/post checks do not defeat every privileged concurrent pathname race.
- A privileged actor who can rewrite and reseal the whole local bundle is outside
  the current trust boundary; signed/timestamped external anchoring is future work.

## Documentation map

| Read this | When |
|---|---|
| [Start Here](docs/START-HERE.md) | First install, first case card, safe launch choice, and verify/view handoff |
| [Judge quickstart](JUDGE-QUICKSTART.md) | First judge walkthrough or native setup |
| [OpenAI vNext release handoff](docs/OPENAI_VNEXT_RELEASE_HANDOFF.md) | Completed jobs, comparison, Docker gate, winning story, demo, and next actions |
| [Architecture](docs/ARCHITECTURE.md) | Trust boundary and lifecycle design |
| [OpenAI vNext review](docs/OPENAI_VNEXT_REVIEW.md) | Baseline comparison and defect disposition |
| [Hackathon handover](HACKATHON_HANDOVER.md) | Current proof ledger and execution checklist |
| [Sanitized Sol live receipt](docs/runs/sol-capped-dc01-opening.json) | Bundle-bound `PARTIAL` opening, tool, cap, usage, custody, and verification facts |
| [Attested Luna receipt](docs/runs/luna-canary-receipt.json) | Nonqualifying connectivity result and explicit retention limitation |
| [Winner roadmap](docs/WINNER_ROADMAP.md) | Scoring strategy and benchmark plan |
| [Build provenance](BUILD_PROVENANCE.md) | Submission-period contribution boundary |
| [Decisions](DECISIONS.md) | Detailed protocol and scope decisions |

## Development

Native CPython 3.11 gate:

```powershell
python -m pip check
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m build
```

Clean Linux/AMD64 Docker gate:

```powershell
docker build --target test -t sentinel-unchained:test .
docker build --target runtime -t sentinel-unchained:local .
docker compose run --rm offline profile /evidence --json
```

The package requires CPython `>=3.11,<3.12`. The Qwen reference-tool dependency
is pinned to commit
`9f309c6134e857f7b86f3e6b9c6709ce954944a5`; Docker resolves it only in the
builder and installs the final image from prebuilt wheels.

## Built with Codex

Codex was the primary implementation and adversarial-review collaborator for
the Build Week work in this repository: the evidence lifecycle, Responses API
adapter, typed execution boundary, caps, retry/usage accounting, typed-DONE-v2
protocol, forced serializer, exact evidence spans, fresh-context downgrade-only
review, report/viewer renderers, independent verifier, CLI, Docker isolation,
tests, benchmark design, and documentation.

The human owner chose the product thesis, Developer Tools track, DFIR testbed,
evidence case, authority split, benchmark, scope cuts, claim language, and
final submission decisions. The dated boundary between prior MIT-licensed work
and new Build Week work is in [BUILD_PROVENANCE.md](BUILD_PROVENANCE.md).

**Codex Session ID (core functionality build):**
`019f61e5-5755-7a02-adb4-618d32baab27`

A later Docker/README follow-up thread
(`019f76f3-a19f-71d1-81b2-eed6305857f6`) is retained as thread provenance.

## Provenance and license

Unchained is an MIT-licensed OpenAI Build Week project by Adil Eskintan.
It was built from the reviewed Unchained baseline while retaining
selected, commit-pinned typed forensic tooling from
[Sentinel Qwen Ensemble](https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen).

The contribution boundary and preserved pre-event Git provenance are documented
in [BUILD_PROVENANCE.md](BUILD_PROVENANCE.md). Detailed current work, validation,
and remaining claims are in the
[release handoff](docs/OPENAI_VNEXT_RELEASE_HANDOFF.md).

> **Winning line:** Unchained is not an LLM pretending to be evidence. It is
> GPT-5.6 directing a bounded investigation whose actions, citations, custody,
> and final report can be checked independently.
