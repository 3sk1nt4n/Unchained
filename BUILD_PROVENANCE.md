# Unchained Build Provenance

> **Created:** 2026-07-14 during the OpenAI Build Week submission period
> **Purpose:** distinguish prior work, new Build Week work, Codex work, and
> current proof limits
> **Current status:** honest local baseline plus C2 provider/reviewer and
> self-verifying-bundle commits exist; reproducible CPython 3.11 proof passes;
> DC01 native Windows-memory smoke passes locally; public remote is verified;
> authentic experiment proof remains pending

This document records provenance without backdating or overstating what Git can
prove. It must be updated whenever a material dependency, source boundary,
Codex thread, freeze version, or submission artifact changes.

## 1. Important timing limitation

The project directory acquired its first Git repository after a substantial
amount of the initial Unchained scaffold, controller, tests, and documentation
had already been created in Codex on July 14, 2026.

The initial commit therefore proves the exact state captured at that baseline.
It does not, by itself, prove the creation time of every line in that state.
Local filesystem timestamps and local Git dates are not independent time
anchors. The retained Codex thread and successful `/feedback` upload provide
additional Build Week evidence, while later public commits and server-side CI
timestamps will provide stronger independent anchors.

No commit will be backdated. Public Build Week history must not be force-pushed,
rebased, or deleted after publication.

## 2. Codex thread evidence

Current successful `/feedback` Codex Session ID:

```text
019f61e5-5755-7a02-adb4-618d32baab27
```

This is the current majority-core implementation thread. Re-evaluate that fact
near submission after material later work. Use the final successful `/feedback`
ID from the thread where the majority of core functionality was actually built.

The current Docker, Luna-canary, README, and release-handoff follow-up is being
completed in Codex thread:

```text
019f76f3-a19f-71d1-81b2-eed6305857f6
```

That identifier is thread provenance only. It must not be represented as a
successful `/feedback` receipt unless `/feedback` is submitted successfully
from that thread.

The screenshot of the successful upload is retained outside the repository. It
must not be used as a substitute for source history, working code, or an
authentic GPT-5.6 runtime proof.

## 3. Prior work boundary

The prior project is the author's MIT-licensed repository:

```text
https://github.com/3sk1nt4n/Sentinel-Ensemble-Qwen
commit 9f309c6134e857f7b86f3e6b9c6709ce954944a5
```

Prior work used by this project:

- selected typed forensic tool functions;
- selected evidence-mounting substrate;
- fixed forensic plugin metadata used by the reviewed allowlist.

The dependency is declared at the exact commit in `pyproject.toml`. It is not
copied into this repository as a pretense of new Build Week code.

Prior work not claimed as new Unchained implementation:

- the Sentinel Ensemble pipeline;
- the prior deterministic semantic validator;
- prior prompts;
- prior reporting code;
- prior metrics, findings, runs, screenshots, or videos.

## 4. New Build Week work

The following project-owned areas were built for Unchained during this
Build Week effort and are the work intended for evaluation:

- `src/unchained/evidence.py`: bounded discovery, content classification,
  capability routing, read-only mount control, symbol readiness, and custody;
- `src/unchained/tools.py` and `src/unchained/_tool_worker.py`: reviewed typed
  authority boundary, private worker execution, containment, output limits, and
  profile-dependent catalog;
- `src/unchained/model.py`: OpenAI Responses API integration and normalized
  provider responses, provider-returned identity, validated usage, and bounded
  audited retries;
- `src/unchained/agent.py`: opening selection, adaptive loop, forced structured
  finalization, fresh downgrade-only review, reporting, and report safety;
- `src/unchained/audit.py`, `artifacts.py`, `verify.py`, `caps.py`, `models.py`,
  `prompts.py`, `cli.py`, and `__main__.py`: exact content-addressed output
  receipts, audit chain, proof bundle, offline verifier, budgets, domain types,
  runtime instruction, lifecycle, terminal states, and CLI;
- all project-owned tests under `tests/`;
- the Unchained README, decision record, master plan, winner roadmap, handover,
  dependency records, and currently implemented proof artifacts.

This boundary must remain visible in the README and Devpost description because
the Official Rules evaluate a pre-existing project's submission-period
additions only.

## 5. Human and Codex roles

Human-owned product and research decisions include:

- choosing the controlled-autonomy versus deterministic-trust comparison;
- choosing Developer Tools and the trust-measurement framing;
- selecting DFIR as the demonstration domain;
- choosing DC01 as the known-answer public benchmark;
- accepting the single-case and possible training-contamination limitations;
- requiring truthful scope labels and a no-fake evidence policy;
- approving scope cuts, public claims, the frozen rubric, and final submission.

Codex has accelerated:

- repository inspection and architecture implementation;
- typed controller, evidence, tool, audit, cap, and report-safety code;
- adversarial tests and defect reproduction;
- live-rules and official-API verification;
- code, security, experiment, judge-experience, and strategy review;
- documentation, handover, and prompt construction;
- proof-bundle, provider-proof, verifier, reproducible-environment, and
  dependency-lock implementation recorded by later commits.

The static viewer, frozen reference evaluation with authorship disclosed,
video, and submission QA remain future work and are not included in this
completed-work list.

These role descriptions must be updated from actual retained work. They are not
permission to claim a future artifact as complete.

## 6. Baseline state captured on July 14

The honest local baseline is:

```text
commit 5b31b32e995d4d485bf512bb8600ca44b46e6f2c
authored/committed 2026-07-14T20:56:22-04:00
subject Establish honest Build Week baseline after C1 hardening
```

At that baseline:

- the offline controller and safety boundaries are substantial;
- the three reproduced C1 defects have code fixes and adversarial regressions;
- the current suite contains 80 passing tests in the active environment;
- Ruff source checks pass;
- the active Python environment is 3.14.3, not the required clean Python 3.11
  proof environment;
- live runtime dependencies remain incomplete in the active environment;
- no authentic GPT-5.6 DC01 investigation exists;
- no public proof bundle, hosted viewer, public video, or Devpost confirmation
  exists;
- the public Git remote now exists and matches local HEAD; the experiment freeze
  still requires its own tagged digest and server-timestamped verification.

These statements describe the baseline only. The living
`HACKATHON_HANDOVER.md` controls current status after later work.

## 7. Current local operational proof

Two later local commits bind the C2 implementation:

```text
5309e5c279521aaa7d65c0857120e1c8ddd77344
Harden provider proof and evidence-grounded review

7b05d6a241a530c37b6f31fedbad8b4dbe7d294c
Ship self-verifying proof bundles and a locked Python 3.11 path
```

The C2 commit snapshot is:

- 14 project-owned source modules and 7,767 nonblank source lines;
- 123 passing offline tests;
- clean Ruff check and Ruff format check;
- successful wheel build;
- official CPython 3.11.9 AMD64 in primary and independent lock-check virtual
  environments under `%LOCALAPPDATA%\venvs`, outside OneDrive;
- clean `pip check` in both environments;
- exact Windows CPython 3.11 constraints and a pip 25.3 `pylock` source/hash
  record;
- successful `vol -h` and a pinned Qwen catalog result of 25 direct tools plus
  5 dynamic Volatility tools;
- exact tool-output retention, bounded UTF-8 excerpts, structured
  exact reviewer quotes, provider-returned identity fields, response/request
  IDs, mandatory usage, and bounded audited transient retries;
- allowlisted environment, audit-derived summary, manifest, detached manifest
  checksum, and standard-library `verify-run`; and
- an empty-evidence lifecycle bundle that passes base internal verification
  while remaining visibly `INVALID`.

The `INVALID` bundle contains no real evidence profile, native plugin rows,
findings, reviewer verdicts, provider response, or model usage. It correctly
fails `--require-complete --require-live-gpt56`. It is operational proof of
finalization and verification only.

Gate A commit `6e696a0` has 14 source modules, 8,779 total physical source
lines, 7,889 nonblank lines, and 128 passing tests. It fixes
three defects discovered by the native smokes:

- fixed Windows direct tools are no longer incorrectly filtered through the
  Linux/macOS dynamic-plugin catalog; and
- an absolute-venv evidence probe can find the adjacent `vol.exe` even when the
  virtual environment is absent from inherited `PATH`; and
- the bounded private-worker transport now accepts at most 16,000,000 bytes,
  while a separate explicit model view remains capped at 65,536 bytes.

A final privacy hardening recursively applies the same path scrub to worker
exception strings and matches paths case-insensitively so Windows case variants
cannot leak. A subprocess regression covers this deterministic error path. It
did not invoke a model or API.

The official DC01 memory archive and all smoke artifacts remain outside the
repository. Retained local facts are:

| Item | Local fact |
|---|---|
| Archive size | 561,424,278 bytes |
| Archive MD5 | `64A4E2CB47138084A5C2878066B2D7B1`, matching the publisher-listed value |
| Archive SHA-256 | `86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80` |
| Extracted memory size | 2,147,483,648 bytes |
| Extracted memory SHA-256 | `8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62` |
| Readiness | `windows.info` resolved exact symbols; profile ready |
| Sealed Windows-memory registry | 14 tools |
| Authoritative process batch | `gate-a-final-20260715T015251Z`, wall time 5,968 ms |
| `vol_pstree` | 40 records; 15,277 sanitized accepted bytes; SHA-256 `E2E70D5164939F5A735C450ECC0F2C268E48F22AE4A4DAB76A92FA67F04ECAC6` |
| `vol_psscan` | 72 records; 16,526 sanitized accepted bytes; SHA-256 `836951C95FDCC131064B52CFC229BB3753E389567FCB534174AC3F40D14A7FE4` |
| First `vol_netscan` | Honest error receipt because the legitimate response exceeded the old 2,000,000-byte boundary |
| Successful `vol_netscan` | `gate-a-netscan-20260715T014947Z`; 19,685 records |
| Full sanitized `vol_netscan` output | 3,961,843 accepted bytes; SHA-256 `EFCED1AF66F99EC2064D14F30A5F018D90E5C169027672BE9E3C0110122CB421` |
| Deterministic `vol_netscan` delivery-view check | Candidate investigator payload: 65,536 bytes; 55,732 prefix characters; incomplete flag plus full bytes/hash receipt; no model received it |
| Successful-output privacy | `E001` present; runner-local evidence path absent from all current sanitized outputs |
| Error-path privacy regression | Subprocess exception string scrubbed recursively with case-insensitive Windows-path matching; no model or API invoked |
| Custody | Post-smoke evidence hash matched |

Earlier pre-sanitizer diagnostics remain outside the repository:

- `vol_pstree`: 15,359 bytes, SHA-256
  `031CA68A8AAC1985967CF7820142432E06E366E42069D9C055AFFF37376B3EFE`;
- `vol_psscan`: 72 records, 16,608 bytes, SHA-256
  `C1D5B7F716F8543B6704DE84C86E9DE68545C5851F2BF6D0BD9DCA2BDC3F5792`.

Those are diagnostic artifacts, not the current publication-safe proof values.
The failed pre-fix `vol_netscan` receipt is also retained honestly; the
successful rerun does not erase it.

For large results, three byte scopes must remain distinct:

1. the complete sanitized accepted output is content-addressed and retained;
2. the investigator receives at most 65,536 bytes with an explicit delivery
   receipt and `model_view_complete=false` when truncated; and
3. the audit and fresh-review packet carry an exact UTF-8 prefix capped at
   2,048 bytes.

This closes the local native-execution leg of Gate A. It is not independently
timestamped, public, frozen, model-directed, reference-scored, or submitted.

Current blockers remain:

- no public freeze digest or server-timestamped experiment verification;
- no confirmed funded `OPENAI_API_KEY` runtime;
- no public experiment freeze, frozen rubric, or disclosed reference scoring;
- no authentic complete GPT-5.6 run;
- no static viewer, public video, or Devpost submission confirmation.

## 8. Local proof versus public and authentic proof

| Evidence | What it proves | What it does not prove |
|---|---|---|
| Local Git commits | Exact local content and ancestry | Independent creation time or public availability |
| Two clean CPython 3.11.9 environments | Reproducible install and dependency consistency on the named target | Native forensic correctness or host portability beyond that target |
| C2 snapshot: 123 tests; Gate A commit `6e696a0`: 128 tests; Ruff and wheel build | Offline controller behavior and build quality | Accuracy of model findings |
| `vol -h` plus 25/5 catalog | Runtime and pinned catalog load | Native rows by itself |
| Hashed DC01 plus successful sealed process/netscan outputs and matching custody | Local real-evidence native execution, sanitization, and bounded delivery through the reviewed adapter | A public, scored, or GPT-5.6 investigation |
| Verified `INVALID` bundle | Finalization, manifest, audit, and verifier consistency for its declared status | A complete investigation, authentic GPT-5.6 use, or custody of real evidence |
| Future public freeze commit | Public, server-timestamped protocol binding | Runtime completion or factual accuracy |
| Future strict authentic bundle | Retained evidence that the frozen lifecycle completed with provider-returned GPT-5.6 receipts | General reliability beyond the frozen single-case demonstration |

No local proof is described as a public timestamp. No fake, synthetic,
`INVALID`, or replay bundle is described as an authentic run. No authentic
response is inferred from the configured model alias alone.

## 9. Planned independent experiment anchor

Before the first GPT-5.6 investigation of DC01, the project must publicly bind:

- exact source commit;
- prompt hashes;
- tool-catalog digest;
- dependency lock and runtime versions;
- evidence hashes;
- rubric and scoring-code hashes;
- model alias;
- caps, retry policy, and price-table digest;
- metric definitions;
- infrastructure-fault definition;
- primary-run selection rule.

The freeze commit will be pushed publicly, tagged, and checked by a
server-timestamped CI run that recomputes every digest. A local commit alone is
not described as immutable or unimpeachable.

## 10. Artifact provenance rules

- Every public model, investigation, scoring, token, cost, or performance claim
  must derive from a verified authentic-run bundle. Deterministic preflight
  timing, byte, record, and native-smoke numbers may appear only when explicitly
  labeled local, pre-freeze, non-model, and non-scored with retained hashes or
  receipts.
- Requested and provider-returned model identities must be stored separately.
- Fake-model fixtures and synthetic receipts must remain labeled as offline
  controller tests.
- The empty-evidence bundle must remain labeled `INVALID` and may demonstrate
  only finalization and base verifier behavior.
- Every valid post-freeze run and every invalid attempt required by the frozen
  protocol must remain disclosed.
- Evidence archives, recovered malware, credentials, secrets, private-case
  output, and answer keys must never be committed.
- The DC01 archive, extracted image, and pre-freeze smoke output stay outside
  the repository until a deliberately sanitized public proof artifact is
  approved. Their hashes and bounded provenance may be recorded.
- A resolving citation proves traceability, not semantic support.
- Project-authored evaluation must not be described as independent human
  evaluation.
- Final proof links, freeze links, tags, release links, workflow links, and the
  submission commit must be appended here when they exist.

## 11. Provenance ledger

| Date | Event | Independent anchor | Notes |
|---|---|---|---|
| 2026-07-14 | Majority-core Codex thread and successful feedback upload retained | Codex Session ID above | Supports Build Week development history; not runtime proof |
| 2026-07-14 | Honest local Git baseline created | `5b31b32e995d4d485bf512bb8600ca44b46e6f2c` | Exact content binding; no independent timestamp yet |
| 2026-07-14 | Provider, retry, exact-output, and reviewer proof hardened | `5309e5c279521aaa7d65c0857120e1c8ddd77344` | Local content binding; no independent timestamp yet |
| 2026-07-14 | Proof bundle, verifier, lock, and CPython 3.11 path shipped | `7b05d6a241a530c37b6f31fedbad8b4dbe7d294c` | Local content binding; no independent timestamp yet |
| 2026-07-14 | Real Windows-memory Gate A hardening committed | `6e696a08a9aaeaa345638239e5182ec24826724d` | Native routing, 16,000,000-byte transport, bounded delivery, case-insensitive success/error path privacy, and regressions; local content binding only |
| 2026-07-14 | Winner strategy, handover, provenance, and judge-facing architecture synchronized | `207a039836cdaf3045e92a2b74e541a7dd2be77f` | Local content binding for the current reviewed documentation; no independent timestamp yet |
| 2026-07-14 | Primary and lock-check CPython 3.11.9 environments verified | Local command evidence | `pip check` clean; C2 snapshot has 123 tests; Ruff, build, `vol -h`, and 25/5 catalog pass |
| 2026-07-14 | Empty-evidence lifecycle bundle verified | Local `verify-run` output | Status is `INVALID`; strict complete/live verification fails as intended |
| 2026-07-14 | Initial DC01 native Windows-memory smoke passed | Local archive/image hashes, diagnostic output, and custody recheck | Exposed two adapter defects; pre-sanitizer output retained outside repo, not current public-safe proof |
| 2026-07-14 | First high-volume `vol_netscan` attempt failed at old transport boundary | Explicit local error receipt | Legitimate response exceeded 2,000,000 bytes; recorded as infrastructure failure |
| 2026-07-14 | Post-fix DC01 process and high-volume network smokes plus final privacy regression passed | Local sanitized output hashes, byte/record counts, privacy checks, custody rechecks, and subprocess regression | 128-test tree; recursive case-insensitive success/error path scrub; 16,000,000-byte transport; deterministic 65,536-byte candidate investigator view; no model invocation; complete accepted outputs outside repo |
| Pending | Public baseline push | Public remote commit | Do not backdate or rewrite |
| Pending | Experiment freeze | Public tag plus server-timestamped digest CI | Must precede first GPT-5.6 DC01 investigation |
| Pending | Authentic primary run | Verified proof bundle | First valid post-freeze run controls |
| Pending | Submission freeze | Public tag and Devpost confirmation | Exact submitted state |
