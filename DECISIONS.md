# Unchained - Design Decisions

This is the design contract for the Python 3.11 prototype. It records the
choices made without interrupting the kickoff for questions.

Status date: 2026-07-18.

## D-001 - Product boundary

Unchained investigates captured evidence and produces an auditable
report. GPT-5.6 plans, acts, interprets, judges, and reports. The product does
not remediate systems, delete artifacts, isolate hosts, disable accounts, or
turn model conclusions into destructive authority.

The system deliberately has no deterministic semantic validator. Code may
prove which bytes a tool returned and which receipt a finding cited; code does
not prove that an intrusion occurred or that an artifact is malicious.

## D-002 - Package and CLI contract

The distribution is `sentinel-unchained`; the import package is `unchained`,
using the source-layout path `src/unchained`. The canonical installed lifecycle is:

```text
sentinel doctor
sentinel profile <evidence>
sentinel run <evidence> [--caps default|strict]
sentinel verify <run>
sentinel view <run>
```

`sentinel-unchained` and `python -m unchained` remain compatibility entry points.

The main module boundaries are:

| Module | Responsibility |
|---|---|
| `unchained.evidence` | Content probes, OS/shape route, read-only mount/access, symbol readiness, pre/post hashes, profile and case card |
| `unchained.tools` | Strict function schemas, eligibility checks, trusted execution, concurrent opening batch |
| `unchained.audit` | Single-writer append-only JSONL and hash-chain verification |
| `unchained.caps` | Atomic hard-cap accounting and cost estimation |
| `unchained.model` | Narrow OpenAI Responses API adapter and offline-fake protocol |
| `unchained.prompts` | Project-owned authoritative investigator and hostile-evidence instructions |
| `unchained.agent` | Opening book, stateless single-tool loop, literal-DONE transition, structured serialization, exact spans, fresh judge, report draft |
| `unchained.reporting` | Deterministic authoritative Markdown rendering |
| `unchained.viewer` | Inert static proof viewer rendering |
| `unchained.verify` | Offline lifecycle, artifact, receipt, span, and custody verification |
| `unchained.cli` / `unchained.__main__` | Doctor/profile/run/verify/view dispatch, custody, artifacts, and exit-code propagation |
| `unchained.models` | Dependency-free typed records shared by the runtime |

Extra helpers may exist, but orchestration from the prior Qwen project must not
enter this call graph.

## D-003 - Prior-project dependency boundary

Reuse is by pip-installed direct Git dependency, pinned to a full commit:

```text
sift-sentinel @ git+https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen.git@9f309c6134e857f7b86f3e6b9c6709ce954944a5
```

Allowed reuse is limited to evidence-mounting support and typed forensic tool
functions under `src/sift_sentinel`. Imports occur lazily inside adapters.
Unchained code must not import, copy, or invoke the old pipeline/coordinator,
deterministic validator, Qwen prompts, report/finalizer code, or generic
interfaces that accept model-supplied commands, binaries, paths, plugins, or
raw argument vectors.

The authoritative investigator instructions in `src/unchained/prompts.py` are
owned by Unchained. They are neither copied nor imported from Qwen.
Phase-specific protocol text may wrap them, but the prior project's prompt
layer never enters the model request.

Pinning makes the reviewed dependency revision repeatable. Updating it is an
explicit security/design change requiring adapter review and tests.

## D-004 - The four deterministic safety domains

Four named domains form the deterministic safety floor:

1. `evidence.py` protects evidence and produces the route/profile.
2. `tools.py` exposes and executes only typed forensic functions.
3. `audit.py` records the complete ordered model/tool run.
4. `caps.py` enforces hard resource ceilings.

Supporting deterministic controller/API/CLI code also enforces schema validity,
tool eligibility, lifecycle, status, containment, citation shape, report safety,
cleanup, and protocol. The four-domain framing does not mean that only four
modules or four individual behaviors are deterministic. These controls must not
quietly become a forensic truth engine. They may reject malformed model output
or illegal tool calls; they may not promote a finding to `CONFIRMED` based on
handcrafted maliciousness rules.

## D-005 - Evidence classification, custody, and routing

The profiler recursively inventories regular input files and classifies them
from content signatures, filesystem structures, and memory banners, not file
extensions. It detects:

- OS: Windows, Linux, macOS, or unknown;
- shape: memory-only, disk-only, both, or an honest degraded/unknown route;
- filesystem: NTFS, APFS/HFS+, ext4/xfs, or unknown;
- size, health, symbol readiness, pre-run SHA-256, available tool families,
  and a capability label.

Disk and memory OS hints are cross-checked. A conflict is reported instead of
silently selecting a fully capable route. Evidence is mounted or accessed
strictly read-only, and generated files live outside the evidence folder.

Every discovered input is SHA-256 hashed before model-directed analysis and
re-hashed after all analysis work. Any mismatch aborts as a custody error; it
is not softened into a successful or merely incomplete finding.

The CLI constructs `RunBudget` after validating cap configuration and before it
creates the `EvidenceSession` or starts Step 0. File-set enumeration checks the
budget before traversal and at every directory/file; initial streaming hashes
check before reading and after each chunk. Content classifiers and fixed
forensic probes check it, probe subprocesses are bounded by remaining wall
time, and Linux/macOS symbol searches check each root and walked directory.
This remains cooperative deadline enforcement around individual synchronous
filesystem operations and kernel reads, which can block between checks.

Inventory never follows or silently skips symlinked evidence. A symlinked input
or descendant, a nonregular traversal entry, and any walk/stat failure close
initial discovery as invalid. The final inventory uses the same complete-set
rule; an enumeration failure there becomes a fatal custody error.

Linux/macOS memory is not made available merely because a plausible symbol file
exists. Its evidence-specific `pslist` probe must resolve successfully. A
present-but-failing table is labeled `configured-unverified`, marked
`UNAVAILABLE`, and omitted from the memory tool route while disk work continues.
Windows may use Volatility's supported automatic-symbol path: with a runtime
present, a failed `windows.info` readiness probe remains routable only as
degraded `auto-download-pending`, and the capability label explicitly says
`Windows symbol auto-download/probe pending` rather than `memory ready`. A
missing Windows runtime still makes memory unavailable. Missing or unresolved
capability is profile data, never a fabricated zero-result tool run.

Capability labels are fixed honestly as Windows **tested**, Linux
**experimental**, and macOS **best effort**, with per-run degradation noted.
These labels describe the evidence OS, not universal host support. In
particular, the current E01/NTFS mount route requires Linux or WSL, root, and
readable `/proc/self/mountinfo`, and the pinned backend's native
`ewfmount`/libewf and `ntfs-3g` helpers; it is not a native-Windows mount
implementation. The reference route deliberately requires direct root rather
than delegating this stateful backend through `sudo`.

Each allowlisted pinned method (`raw@0`, `ntfs_offsets`, or `dmpad`) runs in a
fresh fixed `[sys.executable, "-P", "-m", "unchained.evidence",
"--internal-reference-mount-worker"]` process, never in the profiler process.
It uses `shell=False`, a new POSIX session, a private scratch working directory,
a bounded JSON protocol, the remaining Step 0 wall allowance, and a minimal
environment with scratch-local home/cache/temp paths and no inherited Python
import override, OpenAI/cloud/provider credential, key/token/secret/password,
proxy, SSH-agent, or GPG-agent variable. The worker alone imports and owns
`RealProbes`; a successful worker remains live until it receives the fixed
cleanup action.

Before launch the parent records loop state and whether the run-specific
device-mapper name pre-exists. Timeout/protocol failure sends `SIGTERM` to the
worker process group, allows a bounded cleanup interval, and escalates to group
`SIGKILL`. The parent then independently cleans and verifies mounts below the
run's mount/scratch roots, the run-specific mapper name, and new loops backed by
the evidence/scratch roots while loop inventory remains knowable. `dmpad` is
refused unless the loop baseline and `losetup`/`dmsetup` controls are available.
Normal close asks the live owner to clean up, then repeats external cleanup and
verification. Unverified release preserves recovery paths and is a fatal
containment failure, including when it supersedes an already-fired cap.

This is lifecycle/resource containment, not a root sandbox. A deliberately
detached POSIX process can escape group signaling, uninterruptible kernel I/O
can outlive bounded reap attempts, and the verification scope cannot prove the
absence of arbitrary effects outside the defined run-owned mount, loop, and
mapper resources. The pinned backend/native helpers retain root network and
filesystem authority and the controls depend on Linux mountinfo plus trusted,
available `umount`, `losetup`, and `dmsetup` utilities.

Linux ext4/xfs and HFS+ direct mounts use fixed native `mount`/`umount` argv
with root or non-interactive `sudo`: respectively `ro,noload,loop`,
`ro,norecovery,loop`, and `ro,loop`, with a detected partition offset when
needed. APFS best effort uses fixed `apfs-fuse -o ro` argv. These commands run
in a new process group with a remaining-wall timeout and accept a mount only
after independent read-only verification. A rejected/capped attempt and normal
close use fixed `umount` and require the mountpoint to verify inactive; failure
is fatal. Unlike the reference worker, the direct route does not baseline
arbitrary loop/device-mapper deltas and relies on the native helper/kernel to
release ancillary state. Fixed probe/mount/cleanup subprocesses inherit needed
runtime settings only after stripping Python import overrides, provider/cloud
credentials, API-key/token/secret/password/private-key/credential variables,
proxies, and SSH/GPG agent sockets. They also force `PYTHONSAFEPATH=1`.

Fixed Sleuth Kit probes require available `fsstat`, `img_stat`, or `mmls`
binaries. Volatility 3 and the Windows Registry adapters require their declared
Python runtimes, `volatility3` and `python-registry`. The prototype exposes no
Plaso adapter and never includes Plaso in `available_tool_families`. Standalone
logs-only folders are outside the CLI investigation contract; log parsers are
used only when a supported mounted-disk route provides their artifacts. Linux
disk support is limited to the content route, best-effort read-only mount, and
fixed TSK metadata probes actually present. Linux remains experimental and
macOS remains best effort.

## D-006 - Typed tool authority and no shell

The model receives only strict OpenAI function schemas derived from registered
tools eligible for the detected OS/evidence shape. Every property is typed,
unknown properties are rejected, and evidence location plus native executable
selection remain trusted-runner state.

The model cannot provide a shell string, binary path, working directory,
environment mutation, output path, plugin identifier, pipe, redirection, or
raw CLI arguments. It receives no general shell and no internet or browsing
tool; its forensic access is read-only. Some pinned forensic functions may
internally launch native parsers with argument vectors; that does not grant
command-construction authority to the model.

Turn 0 may select at most six eligible function names. Distinctness is by name,
not argument tuple, so a second call to the same function with another PID is
rejected and receipted rather than executed. The runner reserves accepted calls
atomically, executes them concurrently, and returns all results together.
Afterward, `parallel_tool_calls=false` and the controller accepts no more than
one forensic tool call per investigator turn.

Tool denial, timeout, or failure is returned as an explicit observation and
audited; it is not rewritten as an empty successful result. If a single or
opening-batch reservation hits a cap before launch, no denied executor starts.
Every already-issued call nevertheless gets ordered `tool.started` and
`tool.completed` events, status `capped`, and a canonical error output with its
SHA-256/excerpt, so the audit has no unexplained model call.

Production Qwen metadata discovery, parser calls, and registered Sleuth Kit tool
execution use a fixed private worker rather than importing Qwen or executing
parser bodies in the parent/thread-pool process. The parent launches
`python -P -m unchained._tool_worker` with `shell=False` and an environment
stripped of Python import overrides,
OpenAI/provider/cloud credentials, API-key/token/secret/password/private-key/
credential variables, proxies, and SSH/GPG agent sockets. It forces
`PYTHONSAFEPATH=1` and sends one sealed JSON request on standard input. The
worker owns exact direct-function, Volatility-plugin, and TSK action/binary
allowlists; a module, callable import target, raw plugin path, arbitrary binary,
command, or evidence path cannot be supplied by the model. The model may select
only a logical tool name already present in its typed schema and provide that
schema's validated arguments. The remaining run-wall allowance bounds the
parent protocol read and is also passed into the worker's Qwen timeout
configuration.

For the pinned event-log parser, the worker enables its priority-preserving
return gate at 500,000 bytes. The parent independently accepts no more than one
newline-terminated 16,000,000-byte worker envelope. An oversized or
unterminated reply becomes an explicit error observation and complete tool
receipt. The earlier 2,000,000-byte limit remains recorded in provenance because
it rejected the first legitimate high-volume `netscan` response; it was raised
only after that reproduced failure and a bounded regression was added.

Before any result crosses the private boundary, runner-local evidence and mount
paths are recursively removed or replaced with the sealed public evidence ID.
Path matching is case-insensitive so Windows case variants cannot bypass the
scrub. Worker exception strings receive the same transformation before their
error receipt crosses the boundary. Apart from that privacy transformation, the
event-log gate, and the outer protocol-envelope bound, sub-limit forensic output
is accepted in native order rather than summarized by deterministic code. The
complete sanitized accepted result becomes `ToolResult.output` and is
content-addressed. A separate
`ToolResult.model_output()` view is capped at 65,536 UTF-8 bytes. When truncated,
it contains a native-order prefix and a delivery receipt with the complete
accepted byte count and SHA-256, prefix character count, maximum view size, and
`model_view_complete=false`.

The worker emits one JSON response line and then deliberately waits on standard
input instead of exiting. The parent consequently retains a live, unique tree
leader and destroys the owned tree after every response as well as on timeout.
On POSIX, each child starts in its own session and the parent sends `SIGKILL` to
that process group while the leader is still alive. Windows creates a new
no-window process group and assigns the waiting worker to a
`KILL_ON_JOB_CLOSE` Job Object before sending its JSON request. Assignment
failure is fail-closed; every completion explicitly terminates and closes the
Job Object.

These controls cannot manufacture a perfect portable sandbox. They contain the
owned process lifecycle; they do not create a network, filesystem, namespace,
seccomp, or privilege sandbox. Qwen/TSK code retains the host authority of the
account running Unchained, including root authority when applicable, although
unrelated credentials are withheld from its environment. A POSIX
descendant that deliberately creates a different process group or session can
escape the original group kill, and uninterruptible kernel I/O can delay
reaping. Windows provides the stronger descendant boundary and refuses to
execute Qwen code if it cannot establish that boundary, but still depends on
the operating system's Job Object assignment, termination, and handle-close
semantics.

Step 0's deterministic Sleuth Kit probes remain separate fixed
`[binary, evidence_path]` subprocesses with `shell=False`, a new process group,
a scrubbed environment, and a remaining-wall timeout. Registered TSK functions
used by the model take the private-worker path above. Arbitrary
`ToolDefinition` executors injected by offline tests or embedding callers still
run in-process; the production CLI's `ToolRegistry.from_reference` path does not
use those fake executors.

## D-007 - Authoritative prompt and agent protocol

`src/unchained/prompts.py` is the authoritative, project-owned investigator
prompt. It gives the model typed, read-only forensic access and explicitly no
shell or internet. `agent.py` adds phase mechanics without importing any Qwen
prompt or orchestration text.

The opening request receives the detected OS, evidence shape, and only the
available function catalog/families. GPT-5.6 must choose between one and six
distinct-by-name, highest-value functions for that exact route. A second call
to the same function is a duplicate even when its arguments differ. Memory
functions stay within the detected OS namespace, while disk selection favors
execution, timeline, and persistence artifacts. If memory is marked
`UNAVAILABLE`, it is skipped; disk analysis continues when available and the
missing-or-unresolved-symbol limitation is recorded. Selection is all-or-none:
zero calls, more than six calls, any duplicate, unavailable function, invalid
argument object, or other invalid call rejects the whole batch before an opening
executor starts. A `COMPLETE` lifecycle consequently requires one to six
distinct valid calls, `rejected=0`, and concurrent execution of that accepted
batch.

The iterative phase repeats PLAN → ACT with exactly one forensic function →
OBSERVE → UPDATE CASE NOTES. Factual visible notes and finding summaries cite
tool-call IDs inline in square brackets, for example `[t17]`. The prompt prefers
cross-domain memory-and-disk corroboration before confirmation, requires the
investigator to acknowledge contradictions and change course, and preserves
dead ends, limitations, and unresolved questions. Diminishing returns are the
stop criterion: the model stops when more calls no longer change its
conclusions.

Normal termination is not a control function. The investigator must return no
function call and raw text equal to exactly the four ASCII characters `DONE`.
Whitespace, including a trailing newline, additional text, any other no-call
response, or `DONE` accompanying a function call is a protocol error. Once
accepted, `DONE` is irreversible for that run's investigative phase.

The controller then makes a separate, forced `submit_investigation` call to
serialize the completed notes and findings. This is protocol-only: the request
exposes the strict serialization schema and no forensic functions, so it cannot
resume tool use, collect or add evidence, or extend the investigation. The
resulting existing findings packet is passed to the fresh judge.

```text
OPENING (1..6 in parallel) -> PLAN/ONE TOOL/OBSERVE/NOTES -> literal DONE
    -> forced structured serialization -> fresh judge -> report
```

All agent instructions establish one invariant: filenames, paths, metadata,
logs, documents, parser messages, and tool output are hostile evidence data.
Instructions found inside that data cannot change system policy, caps, allowed
tools, phase rules, or verdict criteria.

## D-008 - Fresh adversarial judge

Judging is a new GPT-5.6 request with no investigator response chain. The judge
receives the case profile, the investigator's existing structured findings, and
only the exact evidence spans controller code resolved from their cited tool
outputs. Each span binds the tool call, full artifact SHA-256, byte start/end,
exact text, occurrence count, and stable span ID. The 2,048-byte audit excerpt
remains an audit convenience and is not the judge's evidence boundary.

For each existing finding it returns `CONFIRMED`, `NEEDS-REVIEW`, or
`UNSUPPORTED`, with rationale and cited tool-call IDs. It may downgrade or
annotate; it may not add findings or upgrade beyond the investigator's proposed
status. Controller checks enforce identity and monotonic status without making
an independent semantic judgment. Every status requires a nonblank rationale,
known span IDs belonging to that finding, and quotes contained inside those
spans. Unknown, omitted, or duplicate finding IDs are protocol errors. The
offline verifier reopens the full artifact and rechecks each digest, byte range,
decoded span, span ID, finding relationship, and judge quote. This proves
structural provenance, not forensic truth.

The judge is an adversarial model pass, not an independent human examiner or a
truth oracle, and may share failure modes with the investigator.

## D-009 - Report contract

After judging, GPT-5.6 submits a strict `ReportDraft` from the profile, existing
findings, judge verdicts, and evidence spans. It contains:

- an executive summary and investigative narrative;
- IOC and limitation commentary;
- exact existing finding and span references.

Code requires the reference sets to equal the adjudicated finding/span sets and
then deterministically renders `report.md`. Code owns the status banner,
authoritative findings table, investigator-to-judge transitions, citations,
IOCs, limitations, and custody wording. GPT cannot add a row, omit a finding,
promote a verdict, or invent a citation through formatting. Model narrative is
defanged before insertion and appears only below headings explicitly labeled
`model-authored, nonauthoritative`. `report.completed` records the exact
normalized report SHA-256 and byte count. Strict verification reconstructs the
renderer input from the verified canonical profile, `investigator.finished`,
`judge.completed`, evidence spans, and submitted `ReportDraft`; reruns the
code-owned renderer; and requires byte-for-byte equality while rebinding the
submitted references and prose. A self-consistent replacement report with
rewritten hashes is therefore rejected.
`PARTIAL`, `FATAL`, and `INVALID` fallbacks use the same inert rendering
boundary. The resulting text remains untrusted output for analyst review.

## D-010 - Audit semantics

`audit.jsonl` has one trusted application writer. Every canonical UTF-8 JSON
record includes a run ID, monotonic sequence, UTC timestamp, elapsed time,
previous-record hash, event payload, and entry hash. Canonical encoding rejects
non-standard NaN and infinity values.

Before `tool.completed` is accepted, the writer strictly encodes the complete
sanitized accepted output as UTF-8, recomputes and compares its SHA-256, and
atomically installs the exact bytes under a digest-derived `.json` or `.txt` name in
`tool-outputs/`. Installation uses exclusive temporary files, no-follow checks
where supported, regular-file validation, exact duplicate validation, and
`fsync` when enabled. A traversal-like digest, symlink, nonregular target,
conflicting content, or write failure cannot create a completion receipt. The
writer attempts a bounded `tool.output_persistence_failed` event before
propagating that failure.

Every completion receipt records the artifact's relative path, SHA-256, byte
count, UTF-8 encoding, media type, and complete-retention flag, plus the longest
valid UTF-8 prefix no larger than 2,048 bytes. Model request audit records keep
function-call outputs bounded to receipts. That audit prefix is not the fresh
reviewer's evidence boundary. The investigator view may contain up to 65,536
bytes and explicitly reports incompleteness. After finalization, controller code
resolves supporting quotes against the exact full sanitized artifact; the judge
receives those byte-located spans, and the artifact remains available for
verification and viewer inspection.

The writer uses append mode, a process lock, flush/`fsync`, and end-to-end
sequence/hash verification. Calls denied by a prelaunch cap still receive a
paired start/completion receipt with deterministic `capped` output, so every
model-issued call remains accounted for. This is application-level append-only
and hash-chained. It detects many accidental or local edits but is not immutable
against an administrator able to replace the entire writable run directory;
stronger tamper evidence would require signing or an external anchor.

Runtime provider credentials and unrelated host secrets are not intentionally
included in model input or audit data. Evidence-derived content itself can
contain secrets and is deliberately sent to the model and recorded in excerpts.

## D-011 - Hard caps and cost estimate

The default hard caps are exactly:

| Cap | Default | Strict profile |
|---|---:|---:|
| `MAX_TOOL_CALLS` | 60 | 20 |
| `MAX_TOTAL_TOKENS` | 400,000 | 100,000 |
| `MAX_WALL_SECONDS` | 1,800 | 600 |
| `MAX_COST_USD` | 10.00 | 2.50 |

Only those four cap values are configurable from the environment, using each
exact name or its `UNCHAINED_`-prefixed alias. Price-like environment variables
are ignored. Tool-call reservations are atomic so the opening batch cannot race
past its allowance. Token and cost counters use observed API usage. The
code-owned GPT-5.6 Sol rates are $5.00/M uncached input, $0.50/M cached
input, $6.25/M cache-write, and $30.00/M output tokens. Cache writes therefore
cost 1.25x uncached input. A request with more than 272,000 input tokens applies
2x input and 1.5x output pricing to its full request.

Live requests use implicit prompt caching, but every model-request preflight
still prices estimated input at the ordinary uncached GPT-5.6 Sol rate because
a cache hit is never guaranteed. After a response, provider-reported
cached-input and cache-write usage fields are audited and reconciled. Strict
complete verification recomputes each call estimate and the cumulative estimate
from those audited token counts and the code-owned price table, then binds the
totals to the final budget snapshot and configured tool, token, wall, and cost
caps. These rates produce a local safety estimate based on the published GPT-5.6
Sol rules. They do not reproduce or authenticate an OpenAI invoice; provider
usage and billing are authoritative, and pricing, cache retention, tokenizer
behavior, or usage-field semantics may change.
Source:
[GPT-5.6 Sol model and pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

Every live provider response must include nonnegative integer `input_tokens`,
`output_tokens`, and `total_tokens`; optional cached-input, cache-write, and
reasoning counters must also be nonnegative when present. The provider total
must equal input plus output. Missing, negative, or inconsistent usage is
audited as a usage-protocol failure and rejected before that response can
advance the investigation. In a mandatory agent phase this normally produces a
`PARTIAL` result and exit `3`, subject to the later cleanup/custody override.

Any cap firing terminates further agent work gracefully, marks the preserved
report and run `PARTIAL`, rechecks evidence custody, and normally exits `3`.
Failure to contain or release a mount, or a custody mismatch during that final
work, supersedes the earlier cap result as `FATAL`/exit `1`.

The wall cap begins before Step 0 and is checked during inventory, hashing,
classification, and symbol work. Remaining wall time bounds OpenAI requests,
fixed forensic probe/mount subprocesses, isolated reference-mount workers, and
private Qwen/TSK tool workers as described in D-005 and D-006. No new agent work
starts after it fires.

Teardown and final custody are intentionally not abandoned at the deadline.
The CLI always attempts mount cleanup in `finally`; once Step 0 produced a
complete baseline, it performs a complete fresh file-set/identity/metadata and
SHA-256 comparison without consulting the already-fired budget. Cleanup and
custody can therefore make process time exceed `MAX_WALL_SECONDS`. Mount
release failure or custody mismatch changes the terminal result to `FATAL`. If
the cap interrupts Step 0 before a baseline exists, cleanup still runs, but a
final comparison is impossible and is not fabricated.

## D-012 - OpenAI API choice

Use the OpenAI Responses API with model ID read from `UNCHAINED_MODEL` and the
credential from `OPENAI_API_KEY`. The model adapter follows the Responses
function loop: receive `function_call`, execute locally, and return
`function_call_output` with the matching call ID. Strict schemas are used.

The live adapter accepts only the `gpt-5.6` alias and GPT-5.6 Sol IDs/snapshots
whose IDs begin `gpt-5.6-sol`. Terra, Luna, and all other model families are
rejected during configuration; Sol pricing is therefore the sole built-in
pricing contract.

All requests use `store=false` and do not rely on provider-stored response
state. Each adaptive turn is a new request containing a controller-owned case
ledger, compact receipt index, latest observation, public profile, and remaining
budget. Prior provider output items and encrypted reasoning items are not
replayed. The final serializer receives retained observations once; the judge
receives only findings and resolved evidence spans. Every phase uses
`reasoning.context="current_turn"`, which keeps context growth bounded and the
judge independent.

Requests set `prompt_cache_options.mode="implicit"`. Under GPT-5.6's cache
rules this permits automatic reuse of matching stable prefixes without making
cache availability part of the protocol. It may produce cache reads or writes,
both of which are audited and priced. It does not keep forensic content local:
evidence-derived profiles and bounded tool output are sent to OpenAI for
inference. Provider and organization cache/retention policy, Zero Data
Retention eligibility, residency, and access controls remain external
deployment boundaries.

The tested `openai==2.31.0` `Responses.create` signature has a typed
`reasoning` parameter but no typed top-level keyword for GPT-5.6's experimental
`prompt_cache_options`. The adapter therefore supplies the latter through the
SDK-supported [`extra_body` request option](https://github.com/openai/openai-python#undocumented-request-params).
This is an SDK compatibility mechanism, not the name of an API request field:
the SDK merges the mapping into the outgoing JSON body, where
`prompt_cache_options` and `reasoning` are top-level properties. No
`extra_body` property is sent on the wire.

These state choices follow the
[GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model)
and
[prompt-caching contract](https://developers.openai.com/api/docs/guides/prompt-caching)
current at the status date above; they require review when the API changes.

Turn-0 calls allow parallel function requests; iterative and judge control
requests enforce at most one function call. The requested model is recorded
separately from the provider-returned `response.model`. A live response is not
accepted unless the latter is an explicit GPT-5.6 identifier. Response IDs,
request IDs, status, the canonical normalized message/function calls, and
mandatory validated usage are audited. Raw SDK/provider `output_items` remain
adapter-local transport data: they are normalized once, neither retained as a
second proof authority nor replayed, and cannot contradict the canonical proof
fields inside a bundle. The provider URL and API secret are never made
model-controlled tool arguments.

The SDK is constructed with `max_retries=0`. `AuditedModel` owns the only retry
policy: no more than two retries, for no more than three total dispatch
attempts, with 0.25-second then 0.5-second backoff. Only connection/time-out
errors, HTTP 408/409/429, and HTTP 5xx are retryable. Every failed attempt,
scheduled or skipped retry, terminal error, and eventual retry success is
audited with bounded provider metadata. Remaining wall time gates every attempt
and delay. Once a response exists, usage, identity, schema, and protocol errors
are never retried. Only the final accepted response reaches the controller, so
no discarded attempt can execute a forensic tool. Strict lifecycle verification
recognizes this bounded retry window between a request/options pair and its one
accepted response and rejects orphan, reordered, excessive, or ineligible retry
receipts.

## D-013 - Status and artifacts

Each run has an isolated writable directory at
`<working-directory>/unchained-runs/<UTC-timestamp>-<id>/`. Finalization writes
`report.md`, `viewer.html`, `audit.jsonl`, `environment.json`, `summary.json`,
`manifest.json`, and `manifest.sha256`; `profile.json` is present when profiling
succeeds, and `tool-outputs/` contains exact sanitized accepted outputs when tools
complete. If the working directory is the evidence folder or is nested beneath
it, the run-directory base moves to the evidence folder's parent.

`profile.json` is canonical JSON of the exact public profile in
`profile.completed`; strict verification round-trips that profile and binds its
evidence IDs, SHA-256 values, sizes, and item count to the initial custody
receipt. `summary.json` derives counters from the audit rather than parallel
mutable state, and verification rebuilds its canonical bytes instead of trusting
the stored counters. `environment.json` is an allowlisted record of Python,
dependencies, lock match, Git state, requested model, native-tool availability,
prompt digest, tool-catalog digest, and caps; it does not dump the host
environment. The non-self-referential manifest explicitly binds artifact paths,
hashes, byte counts, media types, audit entry count and tip, terminal status, and
recorded custody state. `manifest.sha256` is the detached checksum for the
manifest.
Findings cite completed tool-call IDs and exact byte-located spans; judge
verdicts cite those spans and include structured exact quotes. The deterministic
viewer is a required manifest artifact with role `proof-viewer`, contains no
scripts or external resources, and is opened only after bundle verification. It
is rerendered from verified state and byte-compared in addition to its inert HTML
policy.

| Status | Exit | Meaning |
|---|---:|---|
| `COMPLETE` | 0 | Required phases completed within policy; no accuracy guarantee. |
| `FATAL` | 1 | Custody or unrecoverable runtime invariant failed. |
| `INVALID` | 2 | Input/configuration was invalid before meaningful analysis. |
| `PARTIAL` | 3 | A cap fired, or a mandatory investigator/judge/report phase could not safely complete because of a model/provider/tool protocol failure; preserved output is explicitly incomplete. |

Absent a later cleanup, containment, or custody failure, every cap produces
`PARTIAL`/exit `3`. The broader protocol case keeps usable receipts without
mislabeling an incomplete required model phase as complete. An unrecoverable
runtime failure, inability to release or verify run-owned mount resources, or a
custody mismatch supersedes an earlier partial result as `FATAL`/exit `1`.

## D-014 - Offline verification strategy

The test suite performs no network calls. Its behavioral coverage includes:

- all four cap paths, real opening overlap, all-or-none
  distinct-by-function-name opening enforcement with `rejected=0` in
  `COMPLETE`, and complete deterministic receipts for issued calls capped before
  launch;
- complete, hash-valid, ordered audit events under concurrency, atomic exact
  output retention, duplicate-content races, persistence failures, raw text
  exactly equal to four-ASCII-character `DONE` plus forced serialization,
  protocol-error preservation, and a fresh
  judge downgrading a deliberately unsupported finding while enforcing
  nonblank rationale, finding-scoped receipts, and exact quoted spans;
- mandatory nonnegative and internally consistent provider usage,
  provider-returned model identity, retry-aware transaction windows for bounded
  audited transient retries that cannot duplicate tool execution, and
  per-call/cumulative/final-budget recomputation from code-owned price rates that
  price-like environment variables cannot zero;
- the real OpenAI 2.31.0 SDK over `httpx.MockTransport`, proving
  `reasoning.context` and `prompt_cache_options` survive wire serialization
  without a network call;
- cooperative, fail-closed Step 0 inventory/symbol deadlines (including symlink
  and walk-error rejection), Linux/macOS configured-but-unverified symbol
  rejection, and Windows' degraded-auto-download-pending route;
- reference-mount prelaunch deadline checks, timeout containment, fail-closed
  resource verification, fixed `-P` invocation, hostile-working-directory
  resistance, and credential-free child environments;
- private parser/TSK-worker allowlisting, credential scrubbing, event-log return
  gating, blocked-child reap, recursive case-insensitive runner-local-path
  replacement across success values and exception strings, subprocess
  error-path coverage, the fixed 16,000,000-byte worker ceiling,
  oversized-response rejection, and the receipt-bearing 65,536-byte
  large-output model view;
- one-line hostile-diagnostic fallback defanging plus removal of inline and
  reference links/images and dangerous schemes from complete reports; and
- artifact-store, canonical profile/custody, rebuilt summary, exact report and
  viewer rerender, environment, manifest, detached-checksum, and standard-library
  verifier failures across path traversal, symlinks, hashes, byte counts,
  excerpts, citations, quotes, terminal state, recorded custody, and strict
  live-GPT-5.6 requirements.

The fake forensic executors used to prove opening parallelism are intentionally
in-process. Their behavior validates dependency injection, ordering, and cap
accounting; it is not evidence that arbitrary in-process Python functions can
be preempted. Production Qwen parser and registered TSK execution are covered by
the isolated-worker tests and boundary above.

Ruff and type hints/docstrings keep the implementation reviewable, but static
quality checks do not validate forensic truth.

`sentinel verify <bundle>` is intentionally dependency-light and offline. It
verifies the terminal state the bundle actually declares. The stricter
`--require-complete --require-live-gpt56` mode is the submission-integrity gate
for complete recorded GPT-5.6 metadata, not independent provider authentication.
A finalized `INVALID` synthetic bundle may pass base integrity while correctly
failing strict verification. The verifier does not independently rehash original
evidence bytes absent from the bundle; it validates the retained custody
receipts and emits that limitation.

## D-015 - Trust and threat boundaries

Evidence bytes, names, metadata, parser output, tool output, and all model
output are untrusted. The deterministic floor is the application's trusted
control boundary. The pinned dependency and native forensic tools remain
supply-chain/parser attack surface even though their callable interfaces are
constrained. The OpenAI API is an external service boundary. The host kernel,
administrator, hypervisor, and storage administrator are outside the
application's guarantees.

The pre/post custody pass checks the exact discovered path set plus file
identity, size, modification time, and SHA-256. It detects persistent changes,
but external tools reopen evidence by path. Any actor with concurrent
write/rename access to the evidence directory could temporarily replace an
evidence path during analysis and restore the original object and metadata
before final verification. Preventing that path-swap and restore attack requires
an externally protected evidence device/store or stronger OS-level handle
isolation and is outside this prototype's guarantee.

## D-016 - Session 1 `/feedback` ID

**Status: captured from the successful Session 1 feedback upload on
2026-07-14.**

OpenAI Build Week `/feedback` Codex Session ID:

```text
019f61e5-5755-7a02-adb4-618d32baab27
```

The upload confirmation identified this value as the thread ID. This is the
project thread where the majority of Unchained's core functionality
was implemented, so the same exact value is the one recorded for the Devpost
submission field. Re-evaluate this fact after material later core work and run
`/feedback` near submission; the qualifying majority-core thread controls, not
the historical “Session 1” label by itself.

## D-017 - Living hackathon handover and evidence-backed status

**Status: accepted on 2026-07-14 before Prompt 3.**

`HACKATHON_HANDOVER.md` is the living source of truth for Build Week execution
state, verified rules, proof gaps, delivery gates, risks, and next-session work.
`README.md` remains the product/setup contract, and `DECISIONS.md` remains the
durable architecture contract.

Status terms are evidence-gated. `IMPLEMENTED` means code exists; `VERIFIED`
requires a dated command, inspection, test, or reproduction; `DEMONSTRATED`
requires a retained, judge-accessible artifact proving the real workflow. Code
existence or conversation prose alone cannot promote an item to complete.

Every material session must update the handover's state transitions, blockers,
evidence, delivery gate, change log, and single next action. Architecture changes
also update this file; user-facing setup/product changes also update the README.

Current live Official Rules and the logged-in submission form override cached
search results, generated plugin output, old conversations, and stale event
pages. This is necessary because search indexes can still surface the unrelated
2025 gpt-oss event for the current Devpost domain.

## D-018 - Corrected Build Week master plan and evaluation method

**Status: accepted on 2026-07-14 after the deep rules, code, strategy, dataset,
and judge-experience audit.**

`docs/HACKATHON_MASTER_PLAN.md` is the strategic plan. It owns the product
positioning, truthful scope matrices, experimental method, proof-bundle
contract, no-rebuild judge path, prompts, schedule, and submission doctrine.
`HACKATHON_HANDOVER.md` continues to own live status and evidence. The files have
different jobs and must not become competing completion ledgers.

The project is a controlled-autonomy case study and evaluation harness, not a
clean causal ablation of Sentinel Ensemble. A Qwen-versus-GPT-5.6 comparison
changes too many variables to isolate the deterministic validator. Qwen results
may appear only as labeled historical context unless a genuinely controlled
comparison is built later.

The primary measurement is within each Unchained run: investigator proposals,
fresh-context downgrade-only review, and frozen-reference adjudication against
an evidence-observable atomic-fact rubric. The adjudication is labeled
independent or project-authored according to who performs it. The fresh GPT-5.6
reviewer is not independent truth. DC01 is a public known-answer benchmark with
possible training contamination, not an unseen dataset.

The flagship is frozen to the demonstrated Windows memory-only route. Paired
E01 disk is future work and not a Build Week gate. Linux/macOS breadth, Plaso,
Qwen reruns, generalized Docker portability, and dashboard work do not outrank
the authentic run, durable outputs, provider-returned model proof,
frozen-reference evaluation, browser viewer, video, and submission gates.

## D-019 - Winner roadmap, public experiment freeze, and two-axis evaluation

**Status: accepted on 2026-07-14 after a second deep strategy and scientific
validity audit.**

`docs/WINNER_ROADMAP.md` is the active sequencing and priority overlay above the
detailed master plan. It does not replace the handover or architecture record.

The project is publicly positioned as a trust-measurement harness for
model-directed investigators, demonstrated on DFIR. One case measures
receipt-grounded reliability under one frozen protocol; it does not establish
how much autonomous investigators in general can be trusted. The investigator
is model-directed inside deterministic authority, custody, protocol, audit, and
budget boundaries, not unsupervised.

The primary experiment uses the already demonstrated Windows memory-only
shape. Paired E01 disk is excluded from the primary rubric, freeze, and run;
reopening it before submission would trade proof certainty for unsupported
breadth.

No GPT-5.6 investigation of DC01 may occur before the complete experiment is
publicly frozen. Pre-freeze rehearsals use fake typed tools, synthetic receipts,
generic data, or an explicitly unscored case. Deterministic native tools may be
smoked directly on DC01 to prove the substrate. This order prevents DC01 model
behavior from silently tuning prompts, catalog, rubric, thresholds, metrics, or
run selection.

The freeze binds code, prompts, tool catalog, dependencies, evidence hashes,
rubric, scorer, caps, retry policy, model alias, price table, metric definitions,
infrastructure-fault criteria, and the primary-run selection rule. A public
remote commit and server-timestamped digest check provide the intended external
time anchor. A local Git timestamp alone is not called immutable or
unimpeachable.

The first post-freeze run without a predeclared infrastructure fault is the
primary result even when its semantic performance is weak. Later valid runs are
disclosed replicates. Any protocol change creates and retains a new freeze
version. A disappointing finding set, reviewer escape, or low score is not an
infrastructure fault.

Evaluation has two separate axes: factual correctness and receipt sufficiency.
Exact span occurrence and artifact hashing prove citation integrity, not
semantic entailment. Normalized deterministic matching is limited to objective
fields under frozen rules. Interpretive, relational, causal, maliciousness, and
absence claims require blinded human or explicitly project-authored reference
adjudication. Project-authored evaluation is never described as independent.

The required no-rebuild path is a hosted static viewer plus an offline viewer
or release bundle, supported by a no-network verifier. A screencast is
supplemental evidence, not a test path. Without the original evidence bytes,
the lightweight verifier validates the retained custody record and bundle
integrity rather than independently rehashing the original evidence.

## D-020 - P0 report and partition-routing hardening

**Status: implemented and verified offline on 2026-07-14.**

The original C1 implementation reduced model-authored Markdown to a link-free
safe subset and adversarially rendered it through CommonMark. D-009 now
supersedes that report-authority design: GPT submits a structured narrative
draft and code renders the authoritative Markdown. The original defanging helper
remains as a defense-in-depth and legacy-fallback boundary.

Filesystem classification now retains the exact byte offset whose fixed probe
identified the filesystem. That value is carried into the model-safe evidence
record, read-only mount decision, and trusted TSK executor. The model cannot
supply or alter it. `tsk_fsstat` is withheld when no exact matched offset is
known. When known, trusted code converts it into the sealed sector argument used
by `fsstat -o`. A partitioned APFS route is withheld when its available backend
cannot accept the classified offset rather than silently mounting offset zero.

Printable text logs are recognized before generic memory-banner scanning.
Therefore a Linux boot log containing `Linux version` remains a log and cannot
manufacture a memory artifact or a strong disk-memory OS conflict. Native
memory signatures remain higher-confidence classifications.

## D-021 - C2 proof receipts and self-verifying bundles

**Status: implemented and verified locally on 2026-07-14 in commits `5309e5c`
and `7b05d6a`.**

The proof product is the retained receipt graph, not merely the generated
report. Complete sanitized accepted tool output is content-addressed and bound
into the audit before a completion can exist. The vNext serializer returns
supporting quotes that trusted code resolves into exact full-artifact byte spans;
the fresh reviewer cites those spans. The offline verifier rechecks the artifact
digest, range, decoded text, span ID, finding relationship, and judge quote.
These checks establish integrity and traceability. They do not establish
semantic entailment or forensic truth.

Every finalized lifecycle, including an honest `INVALID`, `PARTIAL`, or
`FATAL`, receives an allowlisted environment record, audit-derived summary,
explicit non-self-referential manifest, and detached manifest checksum. The
standard-library verifier checks artifact inventory and hashes, audit chain,
evidence-bound tool receipts, findings, exact spans, downgrade-only semantics,
the ordered model lifecycle, terminal state, and recorded custody. Strict flags
demand `COMPLETE` plus internally consistent recorded GPT-5.6 metadata; they do
not independently authenticate the provider.

The successfully verified empty-evidence bundle is deliberately `INVALID`. It
proves finalization and verifier behavior only. It is not a native-tool proof,
an authentic model proof, a complete run, or a hackathon result.

## D-022 - Reproducible CPython 3.11 environment and lock policy

**Status: implemented and verified locally on 2026-07-14 in commit `7b05d6a`.**

The flagship build target is CPython 3.11 on Windows AMD64, with the validated
interpreter fixed at official CPython 3.11.9. The primary development and
independent lock-check virtual environments live under `%LOCALAPPDATA%\venvs`,
outside OneDrive. Both install cleanly and pass `pip check`. The primary
environment passed 123 tests at the C2 commit snapshot. Gate A commit `6e696a0`
passes 128 tests, Ruff check, Ruff format check, wheel build,
Volatility help, pinned catalog discovery, and the real native smoke recorded
in D-024.

`requirements/constraints.windows-amd64-cp311.txt` is the conventional exact
pip constraint input. `requirements/pylock.windows-amd64-cp311.toml` is the
platform-specific source and hash record generated by pip 25.3. It is not
presented as portable to another Python or operating system, and it is not a
legacy `pip -r` requirements file. Every proof bundle records the lock path,
digest, target, and whether installed distributions match it. A future Ubuntu
lock requires an independent resolution and validation on that exact target.

This local environment proof establishes reproducibility and code quality. It
does not supply a public server timestamp, API funding, provider authenticity,
or experimental validity.

## D-023 - Preserve the existing typed Volatility console adapter

**Status: accepted on 2026-07-14; environment, catalog, and local native
real-evidence smoke proven; public/authentic experiment proof still pending.**

The Windows memory flagship first uses the existing reviewed typed adapter over
Volatility 3's cross-platform `vol` console entry point. The pinned Qwen layer
provides typed forensic functions and fixed plugin metadata. Unchained trusted
code seals the evidence path, callable allowlist, fixed argument vector,
timeout, child-process containment, and receipt. The model never receives a
shell, command string, plugin path, or evidence path.

On the clean CPython 3.11.9 environment, `vol -h` succeeds and the pinned Qwen
catalog returns exactly 25 direct tools and 5 dynamic Volatility tools. This
proves dependency loading and catalog compatibility. The later sealed
`vol_pstree` smoke returned real rows as recorded in D-024.

The smoke exposed two adapter-integration defects. Fixed Windows direct tools
must be selected from the direct catalog and must not be filtered by the
Linux/macOS dynamic-plugin map. Volatility command discovery must also consider
the `vol`/`vol.exe` entry point adjacent to the absolute active interpreter,
because a clean virtual environment may not appear on inherited `PATH`.
Regression tests freeze both behaviors.

A direct Volatility Python API rewrite is not a prerequisite. It would expand
scope and create a second adapter before the reviewed path has failed. Add a
minimal project-owned fallback only if a real Windows memory smoke test
reproduces a blocking incompatibility that cannot be fixed safely in the
current typed console route.

## D-024 - Gate A DC01 Windows-memory native proof

**Status: verified locally on 2026-07-14; retained outside the repository and
not yet public, frozen, scored, or model-directed.**

The official DC01 memory archive is 561,424,278 bytes. Its MD5 is
`64A4E2CB47138084A5C2878066B2D7B1`, matching the publisher-listed value, and
its SHA-256 is
`86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80`.
The extracted memory image is 2,147,483,648 bytes with SHA-256
`8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62`.
Neither file is committed or redistributed by this repository.

`windows.info` resolved the exact symbols and the evidence profile marked the
memory route ready. The sealed profile-dependent registry exposed 14 Windows
memory tools. The authoritative post-sanitizer process batch is
`gate-a-final-20260715T015251Z`, with a 5,968 ms wall time. `vol_pstree`
returned 40 records in 15,277 accepted bytes with SHA-256
`E2E70D5164939F5A735C450ECC0F2C268E48F22AE4A4DAB76A92FA67F04ECAC6`.
`vol_psscan` returned 72 records in 16,526 accepted bytes with SHA-256
`836951C95FDCC131064B52CFC229BB3753E389567FCB534174AC3F40D14A7FE4`.
Both outputs contain public evidence ID `E001`, contain no runner-local path,
and were followed by a matching custody hash.

Earlier `vol_pstree` and `vol_psscan` output hashes were pre-sanitizer
diagnostic artifacts. They remain outside the repository for provenance and
are not the current public-safe proof values.

This evidence closes the local native-execution leg of Gate A. It does not
close the public Git/server timestamp, funded API, experiment freeze, authentic
GPT-5.6, disclosed frozen-reference scoring, viewer, video, or submission gates. The evidence and
smoke artifacts remain outside the repository, so this is not yet a
judge-accessible public proof bundle.

## D-025 - High-volume accepted output and bounded model delivery

**Status: implemented and verified locally on 2026-07-14; no model or API was
used.**

The first live parallel `vol_netscan` smoke produced an explicit error receipt
because its legitimate response exceeded the then-fixed 2,000,000-byte private
worker boundary. `vol_psscan` succeeded in that same diagnostic batch. The
failure is retained as an infrastructure diagnostic; it is not reclassified as
a forensic or semantic failure and is not hidden by the successful rerun.

The worker transport ceiling is now a fixed 16,000,000 bytes. This is large
enough for the reproduced result while remaining finite and tested. Before
acceptance, the worker recursively removes runner-local evidence and mount paths
and uses the sealed evidence ID. Matching is case-insensitive so Windows case
variants cannot leak. Worker exception strings undergo the same scrub before an
error receipt crosses the boundary. A subprocess regression covers that error
path. The complete sanitized accepted result is the value hashed, audited, and
stored content-addressably.

The successful regression run is `gate-a-netscan-20260715T014947Z`.
`vol_netscan` returned 19,685 records. The complete sanitized accepted output is
3,961,843 bytes with SHA-256
`EFCED1AF66F99EC2064D14F30A5F018D90E5C169027672BE9E3C0110122CB421`.
It contains `E001`, contains no runner-local evidence path, and custody matched.

The deterministic Gate A delivery check generated the payload a future
investigator call would receive. It is exactly 65,536 bytes and contains 55,732
native-order prefix characters plus a delivery receipt with the full accepted
byte count and hash, `model_view_complete=false`, the maximum view size, and the
selection rule. No investigator, model, or fresh judge received either payload
because no model was invoked. In an authentic vNext run, the fresh judge receives
controller-resolved evidence spans from the full sanitized accepted artifact.
That artifact remains available to `sentinel verify` and the deterministic viewer.

This three-layer contract prevents high-volume output from consuming the model
budget while preserving complete inspectable evidence. It does not prove model
use, model interpretation, an authentic GPT-5.6 response, a scored run, or a
public artifact.

## D-026 - OpenAI-native vNext is a bounded Unchained evolution

**Status: implemented and verified offline on 2026-07-18; authentic GPT-5.6
evidence run still pending.**

The Qwen repository remains a source of typed forensic adapters and useful
patterns, not the successor's orchestration base. Preserve Unchained's single
state machine, deterministic profiling, code-owned typed authority, hard caps,
literal `DONE`, fresh downgrade-only judge, and content-addressed bundle. Do not
carry forward Qwen's dual conductors, 20-to-35-tool opening floor, per-call MCP
process churn, raw report authority, fail-open repair layers, or early custody
rehash.

The default GPT-5.6 phase policy is intentionally asymmetric:

| Phase | Reasoning | Text verbosity | Max output tokens | Max tool calls |
|---|---|---|---:|---:|
| Opening | low | low | 2,048 | 6 |
| Adaptive investigation | medium | low | 4,096 | 1 |
| Forced finalization | medium | low | 12,288 | 1 schema call |
| Fresh judge | high | low | 12,288 | 1 schema call |
| Report draft | low | medium | 8,192 | 1 schema call |

Code still enforces the case-wide call, token, wall-time, and cost caps. Model
configuration is recorded per request so later verification does not infer it
from global defaults. Every nonterminal adaptive call must include a visible,
valid-UTF-8 case-ledger update no larger than 8,192 bytes; code records and
strict verification rebinds that update before tool execution. Implicit prompt
caching may accelerate repeated stable prefixes, while conservative preflight
continues to assume an uncached request. The six-call maximum parallel opening,
stateless bounded turns, one-tool adaptive loop, and cache-compatible prefixes
are designed to reduce avoidable work; no live latency/cost benchmark or faster
result is measured or guaranteed.

## D-027 - Custody and tool provenance use evidence IDs

**Status: implemented and verified offline on 2026-07-18.**

Initial and final custody maps use the same public evidence-ID namespace. The
private relative-path-to-ID mapping never crosses the public profile boundary.
Every route-specific tool definition carries controller-owned `(evidence_id,
sha256)` references, and the same references must survive `tool.started` through
`tool.completed`. Strict verification requires those digests to match the
initial custody receipt.

The current adapters support one ready memory image and one ready disk image per
case. A profile containing multiple ready images of either class now fails
closed with a split-case instruction instead of silently analyzing the first
item. True multi-image scheduling is future work and must not be inferred from
complete inventory hashing.

## D-028 - Offline verification proves integrity, not provider authenticity

**Status: implemented and verified offline on 2026-07-18.**

Strict verification requires the complete ordered lifecycle and treats each
request/options pair plus its one accepted response as a retry-aware transaction
window. The only intervening events allowed are the controller's bounded,
policy-shaped transient-error/scheduled-retry receipts and eventual success
receipt; orphan, reordered, ineligible, or excessive retries fail verification.
Status-less attempts must use a code-owned transport/timeout class; HTTP status,
backoff, and positive nonincreasing retry timeouts are bounded by the paired
request and wall cap. Each accepted response's output usage must be no greater
than the exact request maximum.
It revalidates the closed strict tool schemas and asymmetric phase policy;
requires an all-or-none opening of one to six distinct valid functions with
no `capped` or `rejected` receipt in `COMPLETE`; binds opening/adaptive model
call IDs, names, and arguments to
complete tool receipts and controller actions; requires every nonterminal visible
ledger update; and accepts terminal raw text only when it is exactly the four
ASCII characters `DONE`.

Runtime and verifier share one primitive JSON Schema type function, including
the rule that a JSON boolean is not an integer or number. The verifier also
rederives the public OS route, evidence shape, canonical filesystem set, and
route-conflict warnings from the retained evidence items instead of accepting
those profile fields as independent assertions.

The verifier reconstructs and byte-compares every exact model input: the opening
profile; each adaptive profile/ledger/receipt-index/budget/latest-observation
packet; the finalizer packet and complete observation sequence; the fresh judge
packet; and the report packet. Lifecycle count fields are bound to the verified
finding, verdict, and receipt collections.

The verifier requires canonical `profile.json` to equal `profile.completed`,
round-trips the public profile, and binds its evidence IDs, SHA-256 values, sizes,
and count to initial custody. It binds forced-finalizer, judge, and report
arguments to their controller events; recomputes full-artifact span occurrence
counts from identity-and-digest-verified rereads; requires exact judge quotes;
rebuilds canonical `summary.json`; reconstructs and byte-compares the exact
deterministic report and viewer; and compares every root and nested artifact
descriptor to the manifest. It also recomputes each local GPT-5.6 call and
cumulative cost estimate from audited token counts and code-owned prices, binds
the final usage/cost/tool totals to the terminal budget snapshot and configured
caps, and requires unique phase-paired request and response IDs. These are local
safety estimates, not provider billing records. Raw SDK/provider `output_items`
are deliberately outside the proof contract; only their normalized canonical
message and function calls are authoritative inside the audit.

An offline verifier can validate only the provider metadata recorded inside the
bundle. It cannot contact or cryptographically authenticate OpenAI, so
`--require-live-gpt56` means "require complete, internally consistent recorded
GPT-5.6 metadata and reject explicit fake/replay markers." It is not an
independent proof that OpenAI issued those fields. External authenticity needs a
provider retrieval mechanism, signed operator record, trusted timestamp, or
immutable external anchor.

## D-029 - The local viewer is deterministic and verification-gated

**Status: implemented and verified offline on 2026-07-18; in-app visual browser
QA unavailable because the browser runtime failed before loading the file.**

Every finalized bundle contains a required `viewer.html` artifact with manifest
role `proof-viewer`. It is generated from trusted structured state before the
manifest is sealed. It contains no JavaScript, external resource, frame, image,
or live link; all dynamic values are HTML-escaped and a restrictive CSP is
embedded. Verification applies a positive passive-element policy, rejects
active/URL/event attributes and active CSS, requires the exact inert CSP and
valid document structure, and rereads the file against its earlier
device/inode/digest before acceptance. It also rerenders the viewer from verified
run status, canonical profile, rebuilt summary, exact report, and the applicable
audit prefix, then requires byte-for-byte equality. `sentinel view` invokes
verification before it opens the required manifest artifact; if the bundle
claims `COMPLETE`, the command forces the complete strict lifecycle verifier even
when the caller supplies no strict flag. Automated parser/security tests replace
the viewer, report, audit hashes, manifest descriptor, and detached checksum
together to prove both self-consistent active content and a passive but
nonauthoritative replacement viewer are rejected.

## D-030 - Remaining containment and immutability limits are explicit

**Status: open production-hardening work.**

Typed adapters run in owned child process trees with scrubbed credentials and
bounded transport, but the host OS does not yet deny their network access or
limit their filesystem writes to scratch. The initial/final rehash also cannot
prevent a privileged concurrent actor from swapping a pathname and restoring
the original bytes before final verification. The local hash chain and detached
manifest checksum are unsigned and lack an external timestamp. Production use
therefore requires OS-enforced sandboxing, stable evidence handles or immutable
snapshots, and an external signature/timestamp/WORM anchor appropriate to the
deployment threat model. The same-user/administrator concurrent-mutation
boundary also applies between proof verification and an external browser
opening a pathname. Per-call parser subprocess startup and unclassified
six-way opening I/O remain performance work; a persistent worker pool is
deferred until its network, filesystem, scratch, and ownership sandbox can be
enforced rather than merely assumed.

No retained authentic end-to-end GPT-5.6 run, controlled latency/cost benchmark,
public experiment freeze, or frozen-reference score exists yet. The architecture
is designed to reduce avoidable work, but it does not establish or guarantee
that vNext is faster, cheaper, or forensically more accurate. Offline metadata
cannot authenticate OpenAI, and the downgrade-only model judge is not ground
truth. Multiple ready memory images or multiple ready disk images fail closed
pending a real multi-image scheduler. In-app browser visual QA also remains
unavailable despite exact viewer rerendering and automated HTML/security tests.
These are consolidated prototype boundaries, not deferred evidence for a claim
of production readiness.

## D-031 - Docker and Luna are bounded preflights, not flagship proof

**Status: implemented and verified offline on 2026-07-18; authentic Luna
provider receipt pending.**

The project permits one narrow container exception to the frozen breadth scope:
a Linux/AMD64 CPython 3.11 packaging/profile/custody preflight and one explicitly
nonqualifying GPT-5.6 Luna Responses canary. The container test target runs the
full suite, lint, format, and dependency gate. The final runtime installs from a
pre-resolved wheelhouse, contains no Git, runs as UID/GID 10001 under Tini, and
uses read-only roots/evidence, dropped capabilities, `no-new-privileges`, bounded
PIDs, and a network-denied offline Compose service.

`sentinel smoke-openai` is a separate one-request typed-tool handshake. It uses
Luna with low reasoning and verbosity, a 128-output-token maximum,
`store=false`, no evidence, no proof bundle, and a fixed strict function schema.
It reports provider model, request/response identity, and normalized usage, and
labels itself `NONQUALIFYING_CONNECTIVITY_SMOKE`. It can read an API key from a
bounded `OPENAI_API_KEY_FILE` Docker secret without printing the value.

This exception does not generalize the audited investigator to arbitrary
models. `sentinel run`, the Sol price table, phase policy, and
`--require-live-gpt56` completion proof remain Sol-specific. Luna cannot produce
a qualifying bundle, enter the scored Qwen comparison, prove Windows/DC01 tool
parity, or substitute for the harmless Sol lifecycle smoke.

Safe Docker mode supports offline CLI/profile/custody plus raw Volatility and
Sleuth Kit inspection. It does not enable E01/FUSE/loop/device mounting, root,
`CAP_SYS_ADMIN`, the Docker socket, or privileged mode. Native Windows remains
the flagship evidence route. A Linux dependency lock, final base-image digest,
OCI digest/revision proof binding, authentic API receipt, and full containerized
Sol lifecycle remain freeze or production-hardening work.
