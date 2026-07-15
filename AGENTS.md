# Sentinel Unchained repository instructions

`docs/WINNER_ROADMAP.md` controls Build Week priority, sequence, positioning,
and go/no-go gates. `docs/HACKATHON_MASTER_PLAN.md` owns the detailed
experiment, proof, judge-experience, prompt, and submission contracts.
`HACKATHON_HANDOVER.md` is the living execution-status source of truth. Read all
three before substantial work.

For every material implementation, verification, artifact, scope, schedule, or
submission-status change:

1. Update `HACKATHON_HANDOVER.md` in the same work session.
2. Preserve the distinction between `IMPLEMENTED`, `VERIFIED`, and
   `DEMONSTRATED`; do not mark work complete without the required evidence.
3. Record exact commands/outcomes and link retained artifacts.
4. Update the applicable gate, daily checklist, risk, change log, and single
   next action.
5. Preserve the verified prior-work versus Build Week boundary. Never backdate
   provenance or reuse Qwen metrics/artifacts as Unchained proof.
6. Verify current event rules by opening the live 2026 Official Rules directly;
   cached search results may contain the unrelated 2025 gpt-oss event.
7. Update `docs/HACKATHON_MASTER_PLAN.md` whenever a verified rule, thesis,
   flagship scope, experiment, public claim, hard gate, judge path, prompt, or
   submission requirement changes. Keep status evidence in the handover rather
   than duplicating unsupported completion claims in the master plan.
8. Update `docs/WINNER_ROADMAP.md` when priority, execution order,
   preregistration, scope-cut, or go/no-go logic changes. Never run GPT-5.6 on
   the scored DC01 case before the public experiment freeze defined there.
9. At the end of the same session, reconcile current commit hashes, source/test
   counts, Python and dependency-lock proof, native-tool proof, bundle terminal
   state, every red external gate, and the exact next safe sequence. Historical
   rows must remain labeled by timestamp and must never be silently rewritten
   as current evidence.
10. Keep proof claims layered. Exact quote resolution establishes receipt
    integrity only. It does not establish semantic support, factual correctness,
    evaluator independence, or complete native-tool output. Score semantic
    correctness and receipt sufficiency separately under the frozen protocol.
11. Prefer the existing fixed Volatility console adapter for the Windows-memory
    flagship. Deterministic native smoke against DC01 is allowed before the
    public freeze because no model sees the case. Do not add a new adapter unless
    the reviewed path is first demonstrated incapable.
12. The local deterministic Gate A leg is recorded as green in the handover.
    Keep raw evidence outside Git. Keep pre-freeze smoke separate and explicitly
    labeled; publish only reviewed non-evidence receipts after the freeze. Never
    call that work an authentic or scored model run. The next order is fixed:
    preserve local Gate A commit `6e696a0` plus its synchronized docs; create
    and verify the public remote without rewriting history; finish and publish the
    preregistration and freeze with a server timestamp; only then expose DC01 to
    GPT-5.6 and run the first valid post-freeze primary. Viewer, video, and prose
    polish do not outrank this order.
13. Preserve the pre-fix netscan transport overflow as an infrastructure
    diagnostic. Never present it as a forensic result or delete it to make the
    path look cleaner. Keep the three output scopes distinct: the native result,
    the full accepted output admitted through the 16,000,000-byte private
    transport cap, and the explicit 65,536-byte model view. The model view must
    bind to the full accepted size/hash and say when it is incomplete.
    Runner-local evidence and mount paths must be replaced with the sealed
    evidence ID before either success values or exception strings leave the
    worker; matching must cover Windows case variants. Deterministic smoke still
    proves no model use.
14. The Build Week primary is the proven Windows memory-only route. Paired disk,
    Linux/macOS breadth, Plaso, a new Volatility adapter, and generalized Docker
    portability are future work, not open prerequisites. Do not reopen them
    before the authentic primary, viewer, video, and submission are green.

The current retained `/feedback` Session ID is
`019f61e5-5755-7a02-adb4-618d32baab27`. Preserve it as current provenance, but
the final successful `/feedback` must come from the true majority-core Codex
thread after final core work. Do not assume an earlier valid ID is automatically
the final submission ID.

Before handing off code changes, run the narrowest relevant tests and then:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Never expose or commit API keys, private forensic evidence, provider secrets, or
unsanitized private-case tool output.
