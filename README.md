# Sentinel Unchained

> **Build Week planning and execution sources:**
> [docs/WINNER_ROADMAP.md](docs/WINNER_ROADMAP.md) controls priority, sequence,
> positioning, and go/no-go gates.
> [docs/HACKATHON_MASTER_PLAN.md](docs/HACKATHON_MASTER_PLAN.md) records the
> detailed experiment, proof, prompts, judge path, and submission contracts.
> [HACKATHON_HANDOVER.md](HACKATHON_HANDOVER.md) records current evidence-backed
> status, risks, and the next action. All three must stay synchronized with
> every material strategy or status change.

Sentinel Unchained is a developer-facing trust-measurement harness for
model-directed investigators, with DFIR as its testbed. GPT-5.6
chooses typed forensic work, interprets results, maintains case notes, proposes
findings, receives a fresh downgrade-only review, and writes the narrative.
Deterministic code retains evidence custody, execution authority, protocol,
audit receipts, and resource limits. A frozen reference evaluation and retained
proof bundle are designed to measure factual correctness and receipt sufficiency
without treating the model or its reviewer as ground truth.

This is a complementary controlled-autonomy experiment, not a repudiation of
Sentinel Ensemble's production-oriented deterministic trust layer. It measures
what happens in a reproducible model-directed case when adaptive semantic agency
operates inside constrained authority. It is not presented as a one-variable
causal ablation of the prior system.

The project intentionally has **no deterministic semantic validator**. Code
protects custody, constrains execution, records the run, and enforces budgets;
it does not decide whether a finding is true. Findings and reports remain model
judgments that require human review.

> Prototype status: Windows is the implemented flagship **evidence-OS** path,
> but no retained authentic end-to-end GPT-5.6 run exists yet. Linux is
> experimental, macOS is best effort, and non-Windows disk analysis is limited
> to fixed metadata probes. This does not mean every host OS can mount every
> evidence format. A capability label describes what was actually available in
> each run; it must never imply that unavailable analysis ran.

### Current proof snapshot

The engineering substrate is locally reproducible and the native Windows-memory
leg now has a real smoke result, but the GPT-5.6 experiment is not yet
demonstrated. Commits `5309e5c` and `7b05d6a` bind the C2 snapshot of 14 source
modules, 7,767 nonblank source lines, and 123 tests. Gate A commit `6e696a0`
binds the later native-integration, high-volume-output, and final
privacy-hardening fixes at 14 modules, 8,779 total physical source lines, 7,889
nonblank lines, and 128 tests.

| Claim | Current evidence-backed state |
|---|---|
| Project implementation | C2 commits: 14 modules and 7,767 nonblank lines; Gate A commit `6e696a0`: 14 modules, 8,779 total physical source lines, and 7,889 nonblank lines |
| Offline quality gate | C2 commits: 123 tests; Gate A commit `6e696a0`: 128 tests; Ruff check, Ruff format check, and wheel build pass |
| Reproducible runtime | CPython 3.11.9 AMD64 in two clean virtual environments outside OneDrive; `pip check` clean |
| Dependency record | Exact Windows CPython 3.11 constraints and `pylock` committed |
| Forensic substrate | `windows.info` resolved symbols; sealed registry exposes 14 Windows-memory tools; real `vol_pstree`, `vol_psscan`, and high-volume `vol_netscan` smokes succeeded |
| Proof machinery | Exact accepted tool outputs, structured quote receipts, manifest, summary, environment record, detached checksum, and offline `verify-run` implemented |
| Synthetic lifecycle proof | One empty-evidence bundle verifies internally as `INVALID`; it contains no evidence bytes, findings, native plugin rows, or model response |
| Authentic experiment | **NOT YET PROVEN**: no authentic GPT-5.6 run, public freeze, or frozen-reference scored bundle |

The non-strict verifier accepting a finalized `INVALID` bundle proves bundle
construction and internal consistency only. The submission-strength command
with `--require-complete --require-live-gpt56` correctly rejects that synthetic
bundle. It must never be presented as an authentic or complete investigation.
The separate native smoke is also pre-freeze local engineering proof, not a
public, scored, or model-directed run.

## Build Week contribution boundary

Only submission-period additions are evaluated. The boundary is explicit:

**Prior work, used as MIT-licensed context:** selected typed forensic tool
functions, fixed forensic plugin metadata, and selected evidence-mounting
substrate from the author's
[Sentinel-Ensemble-Qwen](https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen)
repository at commit
`9f309c6134e857f7b86f3e6b9c6709ce954944a5`.

**Built for Sentinel Unchained during this submission period:** the evidence
profiler and capability router; constrained Responses API adapter; model-chosen
parallel opening; adaptive one-tool loop; literal-DONE and forced-finalization
protocol; fresh-context downgrade-only reviewer with exact quote receipts;
custody, audit, caps, containment, report-safety, and bounded provider-retry
integration; content-addressed exact tool-output retention; provider-returned
identity and usage receipts; proof-bundle construction; a standard-library
offline verifier; Unchained tests; prompts; and documentation.

The public experiment freeze, frozen reference rubric and disclosed scoring, authentic
real-evidence GPT-5.6 bundle, static viewer, video, and submission remain future
gates. They are not claimed as completed Build Week artifacts merely because
their contracts are documented.

The prior pipeline, semantic validator, prompts, reports, metrics, findings, and
runs are not claimed as new Unchained work. See
[BUILD_PROVENANCE.md](BUILD_PROVENANCE.md) for the dated boundary and exact
limitations of the initial Git baseline.

## How Codex contributed

The current majority-core Codex thread implemented and reviewed the Unchained
controller, typed authority boundary, evidence lifecycle, audit and cap
semantics, model protocol, report safety, and offline tests. Codex also performed
live-rules verification, official API-contract review, adversarial code review,
experiment-method review, judge-experience review, and the C1 security and
partition-routing hardening. The successful thread ID is retained below and in
the provenance record. Local commits `5309e5c`, `7b05d6a`, and `6e696a0` bind
the provider/reviewer hardening, self-verifying proof-bundle plus Python 3.11
work, and real Windows-memory Gate A hardening. They are local content
bindings, not independent public timestamps.

The human owner chose the product thesis, Developer Tools track, DFIR testbed,
benchmark, safety boundary, scope cuts, evaluation claims, and final submission
decisions. Codex accelerated implementation and verification; it did not turn
fake-model tests into runtime proof or make the unfinished authentic run,
viewer, video, or submission complete.

## Deterministic floor

Four deterministic safety domains form the control plane. Supporting controller
code enforces their protocol without making semantic forensic judgments:

1. `unchained.evidence` discovers evidence, classifies it by content, detects
   OS and evidence shape, establishes read-only access, checks memory-symbol
   readiness, hashes every input before and after analysis, and emits the case
   profile/card. A pre/post mismatch aborts as a custody error. Linux/macOS
   memory is unavailable when symbols are missing **or merely configured but
   unable to resolve this evidence's process-list probe**; an otherwise usable
   disk investigation continues.
2. `unchained.tools` exposes only registered, typed forensic functions as
   strict OpenAI function schemas. The model cannot select a binary, provide
   an evidence path, construct a command string, or access a shell. The trusted
   runner can execute an opening batch concurrently. Before accepting output,
   the private worker recursively removes runner-local evidence and mount paths
   and replaces path references with the public evidence ID. Matching is
   case-insensitive so Windows path variants are covered, and the same scrub is
   applied to worker exception strings before an error receipt crosses the
   boundary. The complete sanitized result is retained. If it exceeds 65,536
   UTF-8 bytes, the investigator receives a
   separately marked, native-order prefix view no larger than 65,536 bytes,
   including the complete accepted-output byte count and SHA-256 plus
   `model_view_complete=false`.
3. `unchained.audit` is the sole writer of append-only `audit.jsonl`. Before a
   tool completion is accepted, it verifies the output digest and atomically
   retains the exact complete sanitized UTF-8 bytes in a content-addressed
   `tool-outputs/` artifact. The audit receipt records that artifact's path,
   SHA-256, byte count, encoding, media type, completeness, and a distinct
   UTF-8-safe excerpt of at most 2,048 bytes. That 2,048-byte receipt excerpt is
   not the 65,536-byte investigator view and neither is the complete retained
   artifact. Model receipts separately preserve the requested model,
   provider-returned model, response ID, request ID, validated usage,
   timestamps, and running cost estimate.
4. `unchained.caps` atomically enforces tool-call, token, wall-clock, and cost
   limits. A fired cap stops the agent gracefully and normally labels the report
   `PARTIAL` with exit code `3`; a later cleanup, containment, or custody failure
   supersedes that partial result as `FATAL`.

The CLI creates the `RunBudget` before Step 0 starts profiling evidence, so the
wall deadline includes file inventory, initial custody hashing, content
classification, forensic probes, symbol readiness, and mounting, not just
model/tool turns.

Inventory never follows symlinks: a symlinked input or descendant, a nonregular
traversal entry, or any walk/stat failure closes preflight rather than silently
omitting evidence. The final inventory applies the same rule and converts any
such failure into a custody error.

Everything forensic above that floor is model-directed:

```text
PROFILE + ROUTE
       |
       v
OPENING BOOK: GPT-5.6 selects one to six eligible tools; run in parallel
       |
       v
PLAN -> ACT (one typed tool) -> OBSERVE -> UPDATE CASE NOTES -> repeat/DONE
       |
       v
LITERAL DONE -> forced structured serialization (no forensic tools)
       |
       v
FRESH JUDGE: confirm, downgrade, or annotate only existing findings
       |
       v
GPT-5.6 REPORT -> post-run SHA-256 verification
```

All filenames, paths, artifact text, parser output, and tool output are treated
as hostile evidence data. Prompts explicitly prohibit following instructions
found in that data or allowing it to alter policy, caps, tool eligibility, or
verdict rules.

## Investigator prompt contract

[`src/unchained/prompts.py`](src/unchained/prompts.py) is the project-owned,
authoritative investigator prompt. It is not copied from, imported from, or
delegated to the Qwen project. `unchained.agent` combines that prompt with
phase-specific protocol instructions and the hostile-evidence rule.

In the opening book, GPT-5.6 receives the detected OS, evidence shape, and only
the tool families actually available for that route. It must choose between one
and six distinct, high-information **function names** for that OS and shape;
calling the same function with another PID or argument is still a duplicate and
the later call is rejected with a receipt. Windows, Linux, and macOS memory
choices stay within their respective namespaces; disk choices favor execution,
timeline, and persistence artifacts. If the profile marks memory `UNAVAILABLE`,
the model must skip memory tools, continue with disk when possible, and record
the limitation. Accepted opening calls reserve their cap slots atomically and
run in parallel. If that reservation is capped, no executor starts, but every
model-issued call still receives paired audit events and a deterministic
`capped` result payload with an output hash.

The investigator has typed, read-only forensic functions only: no shell, no
internet or browsing tool, and no authority to modify evidence. After opening,
each turn follows PLAN → ACT with at most one forensic function → OBSERVE →
UPDATE CASE NOTES. Factual statements must cite exact tool-call IDs inline,
such as `[t17]`. The prompt prefers cross-domain memory-and-disk corroboration,
requires contradictions to be acknowledged with an explicit course correction,
and retains dead ends rather than silently dropping them. It stops on
diminishing returns, when further calls have stopped changing the conclusions.

The only normal loop terminator is a response with no function call whose
entire trimmed text is the literal `DONE`. Extra text, a different no-call
response, or `DONE` alongside a tool call is a protocol error. After accepting
`DONE`, the controller performs a separate, forced `submit_investigation`
serialization. That request exposes only the strict serialization schema, with
no forensic functions, so it cannot resume the investigation, collect or add new
evidence, or take another forensic action. It only converts the already-finished
notes, supported or contradicted hypotheses, dead ends, limitations, and
findings into the structure consumed by the fresh judge.

The fresh judge may only confirm, downgrade, or annotate those existing
findings; it cannot add one or upgrade the investigator's proposed status.
Every verdict, including `NEEDS-REVIEW` and `UNSUPPORTED`, must provide a nonblank
rationale and at least one unique citation drawn from that finding's own real
tool receipts. For each cited receipt, the reviewer must also return a
structured exact quote of at most 1,024 UTF-8 bytes. Controller code requires
that quote to occur in the exact retained receipt excerpt; `verify-run` also
checks it against the full content-addressed output. A `CONFIRMED` verdict must
cite at least one successful receipt. Quote resolution proves traceability, not
that the quoted text semantically entails the claim.

## Requirements, host support, and installation

- CPython `>=3.11,<3.12`; the validated flagship interpreter is official
  CPython 3.11.9 AMD64 on Windows
- Git, for the pinned direct dependency
- `OPENAI_API_KEY` only for an authentic model run
- `UNCHAINED_MODEL` set to `gpt-5.6` for an authentic model run
- Volatility 3 for memory analysis and `python-registry` for the Windows
  Registry parsers; both are declared Python dependencies
- Native forensic utilities required by the evidence route

An optional future Windows E01/NTFS disk route currently needs a Linux host or
WSL, direct root execution, readable Linux `/proc/self/mountinfo`, and the
native helpers used by the pinned mount backend, notably `ewfmount`/libewf and
`ntfs-3g`. Native Windows cannot perform that mount path. Paired disk is
explicitly outside the Build Week primary and is not a remaining gate.
Sleuth Kit's fixed read-only metadata probes require `fsstat`, `img_stat`,
and/or `mmls` on `PATH`. Linux ext4/xfs and HFS+ mounting uses the host
`mount`/`umount` tools with root or non-interactive `sudo`; APFS best effort
uses `apfs-fuse` when present.

Those direct raw-filesystem mounts use fixed argument vectors and no shell:
ext4 uses `ro,noload,loop`, xfs uses `ro,norecovery,loop`, HFS+ uses `ro,loop`,
and APFS uses `apfs-fuse -o ro`. A mount is accepted only after the resulting
mountpoint independently verifies read-only. A failed, rejected, or capped
attempt is unmounted when active and must verify inactive; normal close runs a
fixed `umount` and makes the same check. Failure to prove release is fatal.

Accordingly, “Windows tested” currently means the demonstrated Windows
**memory-evidence** route. It does not promise E01 mounting on native Windows or
claim that every combination of host, filesystem, symbol table, and native tool
has been validated. The Build Week primary is frozen to memory-only and works
without a disk mount when its Volatility runtime and symbols are ready.

Memory readiness is fail-closed except for Windows' explicit automatic-symbol
path. Linux/macOS symbols that exist on disk but do not resolve the
evidence-specific `pslist` probe are labeled `configured-unverified`, marked
`UNAVAILABLE`, and not exposed as memory tools. If the Windows Volatility
runtime exists but its `windows.info` readiness probe fails, the image remains
routable only as degraded `auto-download-pending`; its capability label says
`Windows symbol auto-download/probe pending` rather than claiming memory ready.
A missing Windows Volatility runtime still makes memory unavailable.

Create the virtual environment outside OneDrive and install against the exact
validated constraints:

```powershell
$venv = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311"
py -3.11 -m venv $venv
$python = "$venv\Scripts\python.exe"
$env:PIP_REQUIRE_VIRTUALENV = "true"
& $python -m pip install -r requirements/bootstrap.txt
& $python -m pip install -c requirements/constraints.windows-amd64-cp311.txt -e ".[dev]"
& $python -m pip check
```

The same dependency set was independently installed and checked in a second
clean environment named `sentinel-unchained-py311-lockcheck`. The conventional
constraints file is the pip installation input. The committed
`requirements/pylock.windows-amd64-cp311.toml` is the stronger source and hash
record, and each proof bundle records its digest plus whether installed versions
match it. A `pylock` file is not a legacy pip `-r` requirements file. See
[`requirements/README.md`](requirements/README.md) for the exact reproduction
and validation contract.

The distribution name is `sentinel-unchained`; its Python import package is
`unchained` (stored under `src/unchained`). The supported CLI contract remains
the module form shown below.

`pyproject.toml` installs the prior project as a direct Git dependency pinned
to the reviewed full commit:

```text
sift-sentinel @ git+https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen.git@9f309c6134e857f7b86f3e6b9c6709ce954944a5
```

Only its evidence-mounting support and typed forensic tool functions are
adapted, and imports are lazy so basic CLI/configuration work does not trigger
the old package's heavy module side effects. Unchained code does **not** import,
copy, or invoke the Qwen pipeline, coordinator, validator, prompts, report
code, or generic command-execution interfaces. The model sees only Unchained's
reviewed typed schemas and the project-owned prompt above; it never receives
the dependency's orchestration or prompt layer.

### Flagship Windows memory path

The preferred route is the existing reviewed typed adapter over Volatility 3's
cross-platform `vol` console entry point. Trusted code owns the plugin mapping,
evidence path, fixed argument vector, timeout, child-process boundary, and
output receipt; the model sees only strict function schemas and never a command
or path. The clean CPython 3.11.9 environment proves that `vol -h` starts and
that the pinned dependency catalog exposes exactly 25 direct tools plus 5
dynamic Volatility tools.

The real pre-freeze native smoke is now green:

| Artifact or check | Verified value |
|---|---|
| Official DC01 memory archive size | 561,424,278 bytes |
| Archive MD5 | `64A4E2CB47138084A5C2878066B2D7B1`, matching the publisher-listed value |
| Archive SHA-256 | `86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80` |
| Extracted memory size | 2,147,483,648 bytes |
| Extracted memory SHA-256 | `8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62` |
| Readiness | `windows.info` resolved the exact symbols; profile marked memory ready |
| Sealed catalog | 14 Windows-memory functions exposed for this profile |
| Authoritative process batch | `gate-a-final-20260715T015251Z`; wall time 5,968 ms |
| `vol_pstree` | 40 records; 15,277 sanitized accepted bytes; SHA-256 `E2E70D5164939F5A735C450ECC0F2C268E48F22AE4A4DAB76A92FA67F04ECAC6` |
| `vol_psscan` | 72 records; 16,526 sanitized accepted bytes; SHA-256 `836951C95FDCC131064B52CFC229BB3753E389567FCB534174AC3F40D14A7FE4` |
| First `vol_netscan` attempt | Honest error receipt: legitimate response exceeded the old 2,000,000-byte worker boundary |
| Successful `vol_netscan` regression | Run `gate-a-netscan-20260715T014947Z`; 19,685 records |
| Full sanitized `vol_netscan` output | 3,961,843 accepted bytes; SHA-256 `EFCED1AF66F99EC2064D14F30A5F018D90E5C169027672BE9E3C0110122CB421` |
| Deterministic `vol_netscan` delivery-view check | Candidate investigator payload exactly 65,536 bytes; 55,732 native-order prefix characters; `model_view_complete=false`; full accepted bytes/hash included; no model received it |
| Output privacy | Public evidence ID `E001` present; runner-local evidence path absent |
| Custody | Post-smoke evidence hash matched the pre-smoke hash |

The evidence, extracted memory, and smoke output remain outside the repository.
This establishes the local Gate A native-execution leg only. It is not a public
proof artifact, scored run, or GPT-5.6 investigation. No model or API was used
for these deterministic native smokes.

Earlier `vol_pstree` and `vol_psscan` hashes were produced before output-path
sanitization. They remain honest diagnostic artifacts outside the repository,
but the post-sanitizer batch above replaces them as the current public-safe
local values.

The native smokes exposed and fixed three integration defects: Windows fixed
direct tools were incorrectly filtered through the Linux/macOS dynamic-plugin
catalog; the absolute-venv evidence probe did not find the adjacent `vol.exe`
when it was absent from inherited `PATH`; and the legitimate `netscan` response
exceeded the original fixed 2,000,000-byte worker boundary. Regression tests
cover all three, including path removal, the 16,000,000-byte transport ceiling,
and deterministic construction of the explicit 65,536-byte candidate
investigator view. No investigator or model received that Gate A payload. A
direct Volatility Python API rewrite remains unnecessary unless the reviewed
typed console path later reproduces a different blocking failure.

A final privacy hardening applies that recursive path scrub to worker exception
strings as well as successful values and matches Windows paths
case-insensitively. A subprocess regression proves that a case-variant private
path in an exception becomes the sealed public evidence ID before the parent
accepts the error receipt. This was an offline deterministic check; it invoked
no investigator, model, or API.

## Configure and run

PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:UNCHAINED_MODEL = "gpt-5.6"
python -m unchained C:\path\to\evidence --caps default
```

POSIX shells:

```bash
export OPENAI_API_KEY="sk-..."
export UNCHAINED_MODEL="gpt-5.6"
python -m unchained /path/to/evidence --caps default
```

The canonical interface is:

```text
python -m unchained /path/to/evidence [--caps default|strict]
```

The input contract accepts a folder containing a memory image and/or disk
image, and discovery uses content rather than filename extensions. The scored
Build Week primary is intentionally narrower: one demonstrated Windows
memory-only route. Windows E01/NTFS disk remains implemented but unproven future
validation, not part of the primary. Linux Volatility 3 and fixed Sleuth Kit
metadata probes are experimental; macOS Volatility/APFS-HFS+ support is best
effort. **Plaso is not exposed by this prototype and is never advertised as an
available family.** A standalone logs-only folder is not a supported CLI
investigation route; log parsers are used against artifacts exposed by a
supported mounted-disk route. Evidence roots and descendants must be regular,
non-symlink files/directories that can be enumerated completely.

### Responses state, reasoning, and data boundary

Every API request sets `store=false`; the implementation does not depend on a
provider-stored response chain, and the API is instructed not to keep a stored
Response object for later retrieval. Investigator turns preserve state locally
by resending prior user input and every prior response output item. Requests add
`include=["reasoning.encrypted_content"]`, so returned encrypted reasoning
items are replayed with the other output items.

Opening-book, judge, and report requests use
`reasoning.context="current_turn"`. The locally replayed, stable-goal
investigation loop and its post-`DONE` structured serializer use
`reasoning.context="all_turns"`. The judge still receives a new, deliberately
independent evidence packet instead of the investigator's response chain. This
follows the
[official GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model)
for manual history management with `store=false`.

Requests also set `prompt_cache_options.mode="explicit"` and provide no cache
breakpoints. For GPT-5.6, that disables prompt-cache reads and writes and avoids
prompt-cache storage and cache-write charges; see the
[official prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).

For the tested `openai==2.31.0` compatibility target, `Responses.create` does
not expose GPT-5.6's experimental `prompt_cache_options` as a typed top-level
Python keyword. The adapter passes that mapping through the OpenAI Python SDK's
supported [`extra_body` request option](https://github.com/openai/openai-python#undocumented-request-params).
`extra_body` is only the SDK call's compatibility escape hatch: the SDK merges
its contents into the outgoing JSON, whose top level contains
`prompt_cache_options` alongside the independently typed `reasoning` object.
The wire body does **not** contain an `extra_body` field.

This is not an assertion that content never leaves the machine: evidence-derived
profiles and raw forensic tool output are transmitted to OpenAI for inference.
Provider and organization retention, Zero Data Retention eligibility, data
residency, and access policy remain external deployment boundaries that an
operator must review.

Default hard limits are:

| Environment variable | Default | Strict profile |
|---|---:|---:|
| `MAX_TOOL_CALLS` | 60 | 20 |
| `MAX_TOTAL_TOKENS` | 400,000 | 100,000 |
| `MAX_WALL_SECONDS` | 1,800 | 600 |
| `MAX_COST_USD` | 10.00 | 2.50 |

Each value can be overridden with the exact variable above or its
`UNCHAINED_`-prefixed alias. The local GPT-5.6 Sol estimator understands
$5.00/M uncached input tokens, $0.50/M cached input tokens, $6.25/M
cache-write tokens, and $30.00/M output tokens. The cache-write rate is 1.25
times uncached input. For a request above 272,000 input tokens, it applies 2x
input and 1.5x output pricing to the full request, matching the published
[GPT-5.6 Sol pricing rules](https://developers.openai.com/api/docs/models/gpt-5.6-sol).
The live adapter accepts only the `gpt-5.6` alias or a GPT-5.6 Sol model ID or
snapshot (`gpt-5.6-sol...`); it rejects Terra, Luna, and other model families.
Only the four cap values in the table are environment-overridable. The Sol
price rates are code-owned; price-like environment variables are ignored so an
operator cannot zero the rate table and silently bypass `MAX_COST_USD`.

Live requests currently disable prompt caching as described above, so observed
cache-read/write token counts should be zero. Preflight therefore prices
estimated input at the ordinary uncached GPT-5.6 Sol rate. After each response,
the audit still records provider-reported cached-input and cache-write fields,
and the cost calculator defensively prices any unexpected nonzero values. This
accounting is a local safety estimate. Provider-side usage and billing remain
authoritative, and pricing, tokenizer behavior, or API usage fields can change.

Usage accounting is mandatory for every live provider response. `input_tokens`,
`output_tokens`, and `total_tokens` must be present nonnegative integers;
cached-input, cache-write, and reasoning counters must also be nonnegative when
present. The provider total must equal input plus output. Missing, negative, or
inconsistent usage is audited as a usage-protocol failure and rejected before
the response can advance the investigation. In the CLI agent flow that ends the
mandatory model phase as `PARTIAL` with exit `3`, subject to the later
cleanup/custody safety override described below.

The configured `UNCHAINED_MODEL` value proves only what was requested. Every
accepted live response must also expose the provider-returned `response.model`,
which is stored separately as `provider_model` together with the response ID,
request ID, status, and usage. A missing or non-GPT-5.6 provider identity is a
protocol failure. No current retained bundle satisfies this live-provider gate.

## Outputs and status

Each run writes an isolated directory at
`<working-directory>/unchained-runs/<UTC-timestamp>-<id>/`. If the working
directory is the evidence folder or is nested beneath it, the base moves to the
evidence folder's parent so outputs are not written into evidence. A finalized
bundle contains:

```text
report.md         narrative or explicit PARTIAL/FATAL/INVALID fallback
audit.jsonl       ordered, hash-chained lifecycle and proof receipts
environment.json allowlisted runtime, dependency, Git, prompt, catalog, and cap facts
summary.json     audit-derived status, timing, usage, tool, finding, and custody counters
manifest.json    explicit artifact allowlist with hashes, sizes, audit tip, and terminal state
manifest.sha256 detached SHA-256 for manifest.json
profile.json      model-safe profile when evidence profiling succeeded
tool-outputs/     exact content-addressed sanitized accepted outputs when tools completed
```

Tool output is not merely represented by a digest and excerpt. The exact full
sanitized accepted UTF-8 bytes are stored before `tool.completed` is appended.
Storage is atomic, duplicate-content safe, and fail-closed on a digest conflict,
unsafe path, symlink, or nonregular target. The 2,048-byte audit receipt excerpt
keeps the fresh-review packet bounded. The separately generated investigator
view is complete only when the accepted output fits; otherwise it is an
explicit receipt-bearing prefix no larger than 65,536 bytes. The full artifact
remains available to the verifier and future viewer.

The report header visibly states the terminal status: `COMPLETE`, `PARTIAL`,
`FATAL`, or `INVALID`. A completed model report's limitations section must
disclose unavailable capabilities, tool failures, and that there is no
deterministic validator by design. The final custody result is a later
deterministic CLI/audit event, not a model-authored claim, and a failure replaces
the terminal result with `FATAL`. Finding citations use tool-call IDs that can
be checked against `audit.jsonl`.

| Exit | Meaning |
|---:|---|
| `0` | Completed within policy; not an accuracy guarantee. |
| `1` | Fatal runtime or custody failure. |
| `2` | Invalid input or configuration. |
| `3` | `PARTIAL`: a cap fired, or a mandatory investigator/judge/report phase could not complete safely because of a model/provider/tool protocol failure. |

Absent a later cleanup or custody safety failure, every fired cap produces
`PARTIAL` and exit `3`. Exit `3` is intentionally a little broader:
malformed/incomplete model output, invalid provider usage, or another
provider/tool protocol failure in a mandatory agent phase also preserves an
explicitly incomplete artifact instead of claiming success. An inability to
contain or release a mount, another unrecoverable runtime failure, or a custody
mismatch overrides an earlier partial result as `FATAL`/exit `1`.

The OpenAI SDK's implicit retry layer is disabled with `max_retries=0` so retry
behavior remains visible. Trusted controller code permits at most two retries,
for at most three dispatch attempts, only for connection/time-out failures,
HTTP 408/409/429, or HTTP 5xx. It audits every failed attempt, scheduled delay,
and eventual success or exhaustion; applies 0.25-second then 0.5-second bounded
backoff; and stops when wall time is insufficient. A returned response is never
retried for malformed usage, wrong provider model, schema, or protocol. The
controller receives only the final accepted response, so discarded dispatch
attempts cannot cause a forensic tool to execute twice.

Before writing a complete report, model-generated Markdown is defanged: raw
HTML angle brackets are escaped; inline and reference-form images are removed;
inline and reference-form link targets and reference definitions are removed;
bare HTTP(S) text is rewritten to `hxxp(s)`; and `javascript:`, `data:`, and
`file:` schemes are blocked. Every controller-generated `PARTIAL`, `FATAL`, or
`INVALID` fallback separately renders hostile provider, parser, mount, cap, and
configuration diagnostics as one inert line: newlines/control characters are
made visible, active Markdown/HTML is removed, and punctuation is escaped so a
diagnostic cannot inject a heading, fence, image, or link. Reports remain
untrusted analyst-facing text and need review.

The audit hash chain makes accidental/local modification detectable, but a
privileged actor who can rewrite the whole run directory is outside this
application's trust boundary. It is append-only at the application level, not
externally anchored immutable storage. Likewise, pre/post SHA-256, file
identity, size, and timestamp checks detect end-state changes but cannot defeat
an actor with concurrent write/rename access to the evidence directory who
swaps an evidence path during a tool run and restores the original object and
metadata before final verification. Use an externally protected evidence store
for that threat model.

### Verify a retained bundle without rebuilding

The verifier uses only the Python standard library. It imports neither the
OpenAI SDK nor the forensic dependency, contacts no network service, and does
not rerun a tool:

```powershell
& $python -m unchained verify-run C:\path\to\run-bundle
```

That base command validates the declared terminal state, including an honestly
finalized `INVALID`, `PARTIAL`, or `FATAL` run. It checks normalized paths,
non-symlink regular files, every manifest hash and byte count, the detached
manifest checksum, audit sequence and hash chain, exact sanitized accepted tool outputs,
receipt excerpts, finding citations, exact reviewer quotes, downgrade-only
review semantics, terminal consistency, and recorded custody receipts.

For submission-strength proof, require both a complete lifecycle and authentic
GPT-5.6 response receipts:

```powershell
& $python -m unchained verify-run C:\path\to\run-bundle `
    --require-complete --require-live-gpt56
```

The strict command requires `COMPLETE`, provider-returned GPT-5.6 identity,
response and request IDs, positive validated usage, and no fake/replay markers.
The current empty-evidence `INVALID` bundle passes the base integrity command
and correctly fails the strict command. Neither command independently rehashes
original evidence bytes that are deliberately absent from the bundle. The
verifier checks the recorded pre/post custody receipts and warns about that
boundary.

### Deadline enforcement and process cleanup

Step 0 cooperatively checks the same budget used by the agent. The file inventory
checks before traversal and for every encountered directory/file; initial
SHA-256 reads check before hashing and after every chunk; content classification
and fixed forensic probes check the budget; probe subprocess deadlines are
shortened to the remaining wall time; and Linux/macOS symbol searches check each
root and walked directory. Individual synchronous filesystem calls, regular-file
reads, or uninterruptible kernel I/O can still block between cooperative checks.

The pinned `RealProbes` E01/NTFS mount ladder is no longer an in-process,
unbounded Step 0 call. On Linux/WSL it is eligible only under direct root with
`/proc/self/mountinfo`, and each `raw@0`, `ntfs_offsets`, or `dmpad` attempt gets
a new fixed child:
`[sys.executable, "-P", "-m", "unchained.evidence",
"--internal-reference-mount-worker"]`. The child runs from a private scratch
directory with `shell=False` and a minimal environment whose home/cache/temp
paths point to that scratch directory and which contains no inherited OpenAI,
cloud, token, secret, password, credential, proxy, SSH-agent, GPG-agent, or
Python import-path variables; it also forces `PYTHONSAFEPATH=1`. It accepts one
bounded JSON mount request and one allowlisted method. The parent's reply wait
is bounded by the smaller of 120 seconds and the run's remaining wall time.

Before launch the parent records the loop-device baseline and whether the
run-specific device-mapper name already exists. A successful worker stays alive
as the `RealProbes` cleanup owner until teardown.
On timeout or a bad protocol reply, the parent sends `SIGTERM` to the POSIX
process group, allows a bounded cleanup interval, escalates to group `SIGKILL`,
and independently cleans and verifies run-owned mounts below the mount/scratch
roots, the run-specific device-mapper name, and, while loop inventory remains
knowable, new loop devices backed by the evidence or scratch tree. `dmpad` is
refused unless loop state is knowable and `losetup`/`dmsetup` are available.
Normal teardown first requests cleanup from
the live owner, then performs the same external verification. If release cannot
be proven, paths are preserved for recovery and the run fails closed as
`FATAL`, even if a wall cap fired first.

This mount worker is process-lifecycle containment, not a privilege, network,
filesystem-namespace, seccomp, or parser sandbox. The pinned backend and native
helpers still execute with root authority. A descendant that deliberately
creates another process group/session can escape group signaling;
uninterruptible kernel I/O can outlive bounded waits; and verification covers
the defined run-owned mount, loop, and device-mapper resources rather than every
possible root-level side effect. It also depends on Linux mountinfo and the
native `umount`, `losetup`, and `dmsetup` controls remaining trustworthy and
available.

The direct ext4/xfs/HFS+/APFS route remains separate from `RealProbes`. Its
fixed subprocess receives the remaining-wall timeout and runs in a new process
group; timeout uses bounded `SIGTERM` then `SIGKILL`. Rejected/capped attempts
and normal close use fixed `umount` calls and accept cleanup only when the
mountpoint is inactive. Unlike the reference-worker containment pass, this
direct route does not baseline arbitrary loop/device-mapper deltas and relies
on the native mount/FUSE helpers and kernel to release their ancillary state.

In the production CLI route, Qwen metadata discovery and Python parser
**execution** do not occur in the parent or opening-batch worker threads. Each
catalog or parser request launches the fixed private child command
`python -P -m unchained._tool_worker`, sends one allowlisted JSON request on
standard input, and receives one JSON envelope. The command and callable
allowlist are code-owned, `shell=False`, and the parent passes the current
remaining wall time as both the outer process deadline and the inner Qwen
timeout. The opening thread pool only supervises up to six such isolated
children concurrently. Each child inherits needed runtime settings but strips
Python import overrides plus OpenAI/provider/cloud credentials, any variable
named like an API key, token, secret, password, private key, or credential,
proxy settings, and SSH/GPG agent sockets, and it forces `PYTHONSAFEPATH=1`.

The worker enables the pinned event-log parser's priority-preserving return gate
at 500,000 bytes. Results below that parser gate remain raw. Independently, the
parent accepts at most one newline-terminated 16,000,000-byte worker envelope.
The old 2,000,000-byte boundary rejected a legitimate high-volume `netscan`
result during the first live parallel smoke, so the bound was raised only after
that reproduced failure and protected with regression tests. An oversized or
unterminated response still becomes an explicit error observation and complete
tool receipt instead of being buffered without bound.

Before any result leaves the private worker, runner-local evidence and mount
paths are recursively removed or replaced with the sealed public evidence ID.
Matching is case-insensitive, including Windows case variants, and exception
strings pass through the same scrub before an error receipt is accepted. The
complete sanitized accepted result is content-addressed. The investigator input
is independently bounded by `ToolResult.model_output()` to 65,536 UTF-8 bytes;
large results include a native-order prefix plus an explicit delivery receipt
with the full accepted byte count, SHA-256, prefix character count, and
`model_view_complete=false`. The fresh reviewer receives the separate audit
receipt excerpt, which is capped at 2,048 bytes.

The worker writes one JSON response line and then deliberately remains alive.
The parent therefore retains an unambiguous process-tree owner and destroys the
owned tree after every response as well as on timeout. On POSIX, each child
starts in a new session and the parent sends `SIGKILL` to that process group
while its leader is still alive. On Windows, the child starts in a new, hidden
process group and must be assigned to a `KILL_ON_JOB_CLOSE` Job Object before it
receives the JSON request; assignment failure is fail-closed. Every completion
terminates and closes that Job Object. No command shell is used on either
platform.

The remaining OS-level caveat is narrower than an in-process parser-thread
overrun: on POSIX, a descendant that deliberately creates a different process
group or session can escape the original group kill. Reaping can also be delayed
if the worker leader is stuck in uninterruptible kernel I/O. Windows Job Objects
provide a stronger descendant boundary, but the implementation still depends
on the operating system honoring job assignment, termination, and handle-close
semantics. This is process-lifecycle containment, not a network/filesystem or
privilege sandbox: the parser can use the host authority of the account running
Unchained (including root, if applicable), although unrelated credentials are
withheld from its environment.

Registered Sleuth Kit tools use the same private-worker boundary through an
exact, code-owned `tsk` action and an allowlist limited to `fsstat`, `img_stat`,
and `mmls`; the evidence path remains runner-owned. Step 0's deterministic TSK
and Volatility probes, and direct mount/cleanup commands, remain separate fixed
subprocesses. They use code-owned argument vectors, `shell=False`, new process
groups, remaining-wall timeouts, and the same Python-import, credential, proxy,
and agent-variable scrub. Tool definitions injected by the offline fake harness
(or an embedding caller using `ToolRegistry` directly) remain in-process; they
are for testing/injection and do not receive the production child-process
cancellation guarantee.

Cleanup and final custody are intentionally outside the fired budget. The CLI
always attempts mount teardown in `finally`. Once Step 0 has produced a complete
pre-run baseline, it then performs the full post-run file-set, identity,
metadata, and SHA-256 verification even if a cap already fired. Those operations
may make process wall time exceed `MAX_WALL_SECONDS`; a release failure or hash
mismatch becomes `FATAL`. If Step 0 itself is capped before a complete baseline
exists, teardown is still attempted, but there is no valid baseline against
which a final custody comparison can be made.

## Development checks

```powershell
& $python -m pip check
& $python -m pytest
& $python -m ruff check .
& $python -m ruff format --check .
& $python -m build
& "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\vol.exe" -h
& $python -c "from unchained.tools import _load_qwen_catalog; c=_load_qwen_catalog(None); print(len(c['direct']), len(c['volatility_plugins']))"
```

At the current reviewed working tree, the expected catalog output is `25 5`.
The verified local quality snapshot is 128 passing tests, clean Ruff check and
format check, a successful wheel build, and clean `pip check` in both CPython
3.11.9 environments. The real `vol_pstree`, `vol_psscan`, and post-fix
high-volume `vol_netscan` smokes described above also pass.
These are operational checks. They do not replace a public server timestamp,
experiment freeze, or authentic GPT-5.6 bundle. The earlier C2 commit snapshot
remains 123 tests and is preserved as such in provenance.

Tests run without network access. Their behavioral coverage includes:

- all four cap paths, opening overlap, distinct-by-name opening enforcement,
  complete `capped` receipts for calls denied before launch, ordered/hash-valid
  audit records, exact atomic tool-output artifacts, concurrent duplicate
  retention, persistence-failure receipts, literal-`DONE` plus forced
  serialization, judge downgrade, and mandatory rationale, finding-scoped
  citations, and exact quoted spans;
- mandatory, nonnegative, internally consistent live provider usage and
  provider-returned model identity; bounded audited transient retries that do
  not duplicate tool execution; and code-owned price rates that price-like
  environment variables cannot zero;
- the real OpenAI Python SDK over `httpx.MockTransport`, proving
  `reasoning.context` and `prompt_cache_options` survive wire serialization
  without making a network request;
- bounded and fail-closed Step 0 inventory/symbol work (including symlink and
  walk-error rejection), Linux/macOS configured-but-unverified symbol rejection,
  and the degraded Windows auto-download-pending route;
- reference-mount prelaunch budget checks, timeout containment, fail-closed
  resource verification, fixed `-P` launch, hostile-CWD resistance, and
  credential-free child environments;
- parser/TSK-worker credential scrubbing, event-log return-gate configuration,
  exact TSK allowlisting, blocked-child reap, import allowlisting,
  recursive case-insensitive runner-local-path replacement across successful
  values and exception strings, subprocess error-path coverage, the fixed
  16,000,000-byte worker ceiling, oversized-response rejection, and an explicit
  65,536-byte large-output model view that preserves the full accepted byte/hash
  receipt;
- one-line hostile-diagnostic fallback defanging plus removal of inline and
  reference links/images and dangerous schemes from complete reports;
- atomic manifest, summary, environment, and detached-checksum construction;
  and a standard-library verifier that fails closed on artifact, path, hash,
  citation, quote, terminal, custody-receipt, or live-model inconsistencies.

See [DECISIONS.md](DECISIONS.md) for the architecture contract and dependency
boundary. See [docs/HACKATHON_MASTER_PLAN.md](docs/HACKATHON_MASTER_PLAN.md) for
the current winner strategy, experiment, proof bundle, judge path, prompts, and
submission doctrine. See [HACKATHON_HANDOVER.md](HACKATHON_HANDOVER.md) for the
current implementation/proof ledger, delivery gates, and next action.

**OpenAI Build Week `/feedback` Codex Session ID:**
`019f61e5-5755-7a02-adb4-618d32baab27`

This ID was returned by a successful feedback upload from the Session 1 thread
where the majority of Sentinel Unchained's core functionality has currently
been built. Use that exact value in the corresponding Devpost submission field
only while this remains the true majority-core thread. Re-run `/feedback` near
submission after material core work and update this value if the qualifying
thread changes.
