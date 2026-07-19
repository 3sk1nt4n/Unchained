# Adversarial judge-panel review — 2026-07-19

> **What this is:** an internal, adversarial self-review run two days before the
> OpenAI Build Week deadline. Four independent reviewers scored the project
> against the four official criteria; a skeptic then re-opened every cited file
> and tried to refute each scorecard in both directions. A separate rules
> auditor, a hands-on walkthrough (real commands on a real machine), and a
> competitive-field researcher completed the panel. Only claims that survived
> refutation are recorded here. Scores are calibrated so 50 = median hackathon
> submission and 85+ = prize contender.
>
> The execution plan built from this review is [FINAL-SPRINT.md](FINAL-SPRINT.md).

## Scoreboard

| Criterion | Judge | Skeptic-adjusted | One-line verdict |
|---|---:|---:|---|
| Technological Implementation | 72 | **73** | Deep GPT-5.6 Responses API engineering and a concrete Codex story; the deepest half of the pipeline has not yet run live |
| Design | 61 | **59** | A well-crafted CLI product loop that no judge can currently see: no video, no screenshots, no clickable artifact |
| Potential Impact | 63 | **60** | Real problem, calibrated claims; the tool has not yet completed a single live investigation |
| Quality of the Idea | 72 | **74** | "The model is never the evidence" is memorable and code-real, not paper-real; kept out of the 80s only by the missing COMPLETE bundle |
| **Average** | | **66.5** | Top-quartile project; not yet a prize contender as submitted |

## What survived adversarial verification as genuinely strong

- Per-phase GPT-5.6 Responses API policies exist in code exactly as documented:
  opening `tool_choice=required` + parallel + six-call ceiling; one required
  typed action per adaptive turn; pinned judge function with high reasoning
  (`agent.py`, `model.py` — line-verified by the skeptic).
- Typed-DONE-v2, all-or-none opening validation, the downgrade-only reviewer,
  and the 4,434-line offline verifier are enforced mechanisms, not
  documentation claims. The Idea skeptic **raised** the score for this.
- The full test gate passes: 383/383, re-run independently by two agents.
- The hands-on walkthrough ran the complete no-key path: every command finished
  in ~0.1 s and behaved exactly as documented. Verdict: "the best zero-key
  first screen I have seen in a hackathon CLI." Minutes to first value: 2.
- The honesty discipline (PARTIAL is labeled PARTIAL; claims ledger blocks
  unmeasured comparisons) was repeatedly identified as a differentiator.

## What is costing points

| Weakness | Severity | Evidence |
|---|---|---|
| No public sub-3-minute video | **Fatal (DQ-level)** | Required by the rules; zero video URLs exist in the repo |
| No authentic COMPLETE live run | Major | All 12 retained live bundles are `PARTIAL`; findings → reviewer → report has never executed live |
| No judge-verifiable proof bundle shipped | Major | Committed receipts are sanitized projections; the raw bundle is local-only |
| Zero screenshots/GIFs of the product | Major | The README's best design work is invisible to a browsing judge |
| Prior-art position undefended | Major | No named differentiation from guardrails / LLM-as-judge / attestation lineages |
| README density before payoff | Minor | Status tables and hedging vocabulary precede any visual or benefit statement |

## Rules-compliance audit

| Requirement | Status |
|---|---|
| README describes Codex collaboration | PASS |
| Codex Session ID present | PASS |
| Built with Codex and GPT-5.6 (evidence) | PASS |
| New/extended work inside Jul 13–21 with a prior-work boundary | PASS |
| Public repo with MIT LICENSE | PASS |
| No third-party IP problems | PASS |
| Working no-rebuild judge test path | **AT_RISK** — the headline lane is `docker compose build`; the instant native path works (re-tested) but is presented second, and no verifiable bundle is shipped |
| Public YouTube video under 3 minutes | **PENDING — the only DQ-level gap** |
| Devpost submission checklist | AT_RISK — all 13 boxes unchecked at review time |

## Competitive field and realistic odds

**VERIFIED:** 8,600+ registered participants were reported mid-week; prizes are
$15K/$10K per track with exactly two winners per track.
**ESTIMATE (labeled, not measured):** roughly 200–450 Developer Tools
submissions, of which perhaps 10–20 genuinely contend.

| Scenario | Combined odds of 1st or 2nd (Developer Tools) |
|---|---|
| As submitted today (no video) | ~0% — non-compliant; can be screened out before human judging |
| Video shipped, bundle still PARTIAL | ~2–4% |
| Video + one authentic COMPLETE bundle | ~5–10% — a legitimate top-10% entry |

The ordering is robust even where the percentages are estimates: **the video is
worth more than everything else combined, and the COMPLETE run roughly doubles
the odds on top of it.**

Sources: openai.devpost.com/rules; the Devpost project gallery; third-party
Build Week coverage; published winner profiles from comparable OpenAI and
Gemini hackathons (full list in the retained panel output).

## Known live-run risk

Seven fresh Sol attempts from 2026-07-19 are retained and all ended `PARTIAL`;
one failure reason reads "investigator without a tool call must output exactly
DONE" — the literal-DONE-v1 failure mode that typed-DONE-v2 was built to fix.
Typed-DONE-v2 is verified offline but has **never succeeded live**. Budget two
to three attempts for the COMPLETE run and dry-run a harmless case first.
