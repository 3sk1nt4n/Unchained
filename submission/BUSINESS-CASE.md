# Unchained: Business Case

> "GPT-5.6 chooses where to look; deterministic code controls what may run and verifies exactly what was executed and cited."

Unchained is a bounded autonomous DFIR (Digital Forensics and Incident Response) investigator built with Codex and GPT-5.6. Its product thesis in one sentence: agentic AI in high-consequence domains is only sellable when every action it took can be checked by someone who does not trust the agent, the vendor, or the transcript.

"Unchained is not an LLM pretending to be evidence. It is GPT-5.6 directing a bounded investigation whose actions, citations, custody, and final report can be checked independently."

---

## Verify it yourself first: the $0, no-key lane

Before reading a single market claim below, you can run the product. No API key, no spend, no network calls to OpenAI. Every command below returns in well under a second; the pip install is the only wait (about 1 to 2 minutes).

```powershell
git clone https://github.com/3sk1nt4n/Unchained.git; cd Unchained
py -3.11 -m venv .judge; .judge\Scripts\python.exe -m pip install -q .
.judge\Scripts\python.exe -m unchained onboard
.judge\Scripts\python.exe -m unchained profile docker/fixtures --json
```

Full-isolation alternative (Docker; the build takes several minutes cold):

```powershell
docker compose build
docker compose run --rm offline profile /evidence --json
```

What backs this up, all from the repository:

| Proof | Status |
|---|---|
| 404 passing tests across 24 test files (25.11 s run, ruff clean) | Proven, run 2026-07-20 |
| Authentic retained GPT-5.6 run on real Windows DC01 memory (2,147,483,648 bytes, SHA-256 custody match), 14/14 typed tool receipts | Shipped in the repo at `examples/public-run-partial`; verifies VALID on current code (20 artifacts, 62 hash-chained audit entries) |
| Earlier `gpt-5.6-sol` capped opening (6/6 tools, VALID recorded at creation: 13 artifacts, 38 audit entries) | Committed at `docs/runs/sol-capped-dc01-opening.json` |
| Codex Session ID | 019f61e5-5755-7a02-adb4-618d32baab27 |
| Public MIT repository | https://github.com/3sk1nt4n/Unchained |
| Demo video link | Added on upload |

---

## 1. The problem: transcripts are not proof

Agentic AI is being pointed at real evidence and real infrastructure. What it produces today is a transcript: a self-reported narrative of what the model says it did. In regulated and high-consequence domains, that is not an input anyone can act on.

- An incident response consultancy cannot hand a chat log to a regulator or opposing counsel and call it findings. As the README puts it: "A transcript is not an answer."
- A compliance reviewer cannot certify a conclusion whose citations cannot be resolved to exact bytes in the underlying record.
- An expert witness cannot testify to an analysis whose tool executions, inputs, and outputs were never independently retained.

The gap is structural, not a model-quality problem. The model's narrative and the evidentiary record are the same object, so there is nothing to check the narrative against.

Unchained separates them. GPT-5.6 chooses bounded strategy: it opens with up to twelve high-value typed forensic tools fired in parallel, then proceeds one typed action at a time. Deterministic code owns everything with evidentiary weight: SHA-256 custody, all-or-none validation of the opening, tool execution in private child processes, exact UTF-8 citation spans, a hash-chained audit log, a content-addressed sealed bundle, and a strict offline verifier that reconstructs the lifecycle byte-for-byte. A fresh-context reviewer may only preserve or downgrade findings, never inflate them.

The receipts prove what ran, what output was retained, and what exact text was cited. They do not pretend to prove forensic truth; a human still owns interpretation and response. That restraint is the product.

## 2. Who pays, and why

| Buyer | Why they pay |
|---|---|
| DFIR consultancies | Their deliverable is a defensible report. They must show a regulator or opposing counsel exactly what the AI did, or they cannot use AI on billable casework at all. |
| MSSPs and corporate IR teams | Triage volume exceeds analyst hours. Bounded, cap-limited autonomous investigation with receipts lets them delegate the first pass without delegating accountability. |
| Legal and eDiscovery teams | Chain of custody and reproducible citation are already procedural requirements. An AI workflow that cannot satisfy them is unusable regardless of accuracy. |

On market size: Mordor Intelligence (2025) estimates the Digital Forensics and Incident Response (DFIR) solutions market at USD 10.46 billion in 2025, growing at a 20.37% CAGR to USD 26.43 billion by 2030, and the adjacent incident response and digital forensics services market at USD 55.94 billion in 2025, reaching USD 144.90 billion by 2030. These are analyst estimates, not our measurements; we cite them as scale context only. Unchained's addressable slice is the portion of that spend where AI assistance is currently blocked by verifiability requirements. We have not measured that slice and do not claim a number for it.

## 3. Why now

Two lines are crossing.

First, agent autonomy is rising: models are increasingly allowed to select and execute tools against real systems, and the number of actions per human decision keeps growing.

Second, audit and record-keeping expectations for AI systems are tightening. The EU AI Act (Regulation (EU) 2024/1689, Article 12) requires high-risk AI systems to technically allow automatic recording of events (logs) over the system's lifetime, with deployer retention obligations. We do not claim Unchained is an EU AI Act compliance product, and we have not had its receipts assessed against any regulation. The point is direction of travel: the regulatory default is moving toward "show the log," and most agent stacks cannot produce a log that an outside party can verify.

Unchained is built for exactly that intersection: autonomy that is allowed to act because its actions are independently checkable afterward, offline, without trusting the operator's machine state or the model's memory.

## 4. The wedge, then the category

DFIR memory forensics is the beachhead, chosen deliberately, because evidence custody is already a legal requirement there. Nobody in that market needs to be persuaded that provenance matters; they are the one buyer segment for whom "verifiable" is a purchasing criterion today, not a nice-to-have.

The retained live run shows the wedge working on real evidence: GPT-5.6 selected 6 typed Volatility tools against a 2 GiB Windows domain controller memory image from a public known-answer case (dfirmadness.com, The Stolen Szechuan Sauce), all 6 executed successfully (one tool alone retained 3,961,843 output bytes), custody hashes matched before and after, and the run ended as an honest PARTIAL when the cap engine refused a 7th tool before dispatch. Total measured spend: 59,254 provider-reported tokens, a local cost estimate of $0.38789875, 43.702 seconds end to end. That run used the earlier six-tool opening cap; the runtime now allows up to twelve. A second retained run, shipped in the repository (`examples/public-run-partial`), repeats the pattern on current code: 14 typed tool receipts by `gpt-5.6-luna`, custody intact, an honest hard-budget stop, and a bundle any reader can re-verify offline today.

The architecture does not know it is doing forensics. The pattern is: model chooses bounded strategy, code validates and executes typed authority, exact outputs and citations are retained, a monotonic reviewer reduces claims, deterministic code renders and verifies the deliverable. That generalizes to any high-consequence agent: security testing, compliance review, financial operations. The category Unchained is positioned to define is runtime receipts for agent actions: per-run, evidence-bound, offline-verifiable records of what an autonomous system actually did.

Cost discipline is part of the same design. A completed case makes exactly 4 fixed GPT-5.6 requests plus one per adaptive action (minimum five, never an unbounded loop), and depth ceilings are hard stops that fire before dispatch: LIGHT caps a first case at 20 tools, 100,000 tokens, 10 minutes, $2.50 estimated cost; HEAVY at 60 tools, 400,000 tokens, 30 minutes, $10. These are hard ceilings, not price quotes.

## 5. Positioning: architectural differences only

No performance comparisons are made here or anywhere in this submission; no same-evidence benchmark against other models is published yet (see caveats). This table describes what each approach attests to, which is an architectural fact, not a quality ranking.

| Approach | When it operates | What it attests | What it does not give you |
|---|---|---|---|
| Guardrails / policy filters | Runtime | That disallowed inputs/outputs were blocked or rewritten | A retained, independently verifiable record of what the agent executed and cited |
| Evals and benchmarks | Pre-deployment | Aggregate capability on test sets | Anything about the specific run in front of a regulator |
| Build-time attestation (supply-chain provenance) | Build/release | How the software artifact was produced | What an agent did with evidence at runtime |
| Transcripts / session logs | Runtime | The model's self-reported narrative | Custody hashes, typed-call validation, exact citation spans, or offline reconstruction |
| Unchained | Runtime | Per-run receipts: typed tool calls validated all-or-none, SHA-256 custody, exact UTF-8 evidence spans, hash-chained audit log, content-addressed bundle, byte-exact offline verification | Forensic truth. Receipts establish execution and citation support; interpretation stays human. |

These categories are complements more than competitors: a deployment can want guardrails, evals, build attestation, and runtime receipts simultaneously. Unchained occupies the row the other approaches leave empty.

## 6. Business model (sketch)

Labeled plainly: this is a sketch, not a validated pricing model, and no revenue exists.

- Open-core. The engine stays MIT and public. The verifier must remain free forever; a verification tool nobody can freely run defeats its own purpose.
- Paid hosted verification and viewer. A hosted service that ingests sealed bundles, verifies them, and serves the inert report viewer to case stakeholders (counsel, regulators, clients) who will never install a CLI.
- Enterprise custody integrations. Signed and timestamped external anchoring of bundles (explicitly future work in the README), case-management integration, retention policy enforcement, and multi-case evidence lockers, sold per seat or per case to consultancies and MSSPs.

The wedge revenue is the consultancy that needs to attach a verifiable AI work-product to a billable engagement; the expansion revenue is every other team that later needs receipts for a different class of agent.

---

## Honest caveats (read before pricing anything above)

- The retained real-evidence GPT-5.6 bundle proves the live opening/tool/cap/custody path, but it is PARTIAL; no authentic COMPLETE GPT-5.6 vNext bundle is published yet. Public COMPLETE viewer/bundle: pending a COMPLETE run.
- Demo video link: added on upload.
- No frozen same-evidence Qwen latency/cost/accuracy benchmark is published yet; that comparison was deliberately cut rather than claimed without measurement.
- Exact receipts establish execution and citation support, not forensic truth. The offline verifier validates recorded metadata; it does not prove the model's forensic interpretation is true and does not authenticate OpenAI.
- The fresh-context reviewer is a same-family model call, not independent ground truth.
- Private worker containment and process-tree cleanup are not a complete OS sandbox; SHA-256 pre/post checks do not defeat every privileged concurrent pathname race; a privileged actor who can rewrite and reseal the whole local bundle is outside the current trust boundary (external anchoring is future work).
- Linux/macOS/Docker claims are static-only (read and reasoned, not executed on a real host); macOS runs via the Docker lane under emulation, not yet verified on Mac hardware.
- Known live-run friction: new OpenAI accounts cap around 200k TPM while a rich 12-tool serializer packet can be around 270k tokens, which can produce a 429 and an honest PARTIAL; a full lifecycle can exceed the 400k default token cap.
- The market figures above are third-party analyst estimates; the addressable slice for verifiable-agent tooling within them is unmeasured.

## Sources

- Mordor Intelligence, Digital Forensics And Incident Response (DFIR) Solutions Market (2025 figures): https://www.mordorintelligence.com/industry-reports/digital-forensics-and-incident-response-solutions-market
- Mordor Intelligence, Incident Response And Digital Forensics Services Market (2025 figures): https://www.mordorintelligence.com/industry-reports/incident-response-and-digital-forensics-services-market
- Regulation (EU) 2024/1689 (EU AI Act), EUR-Lex: https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- EU AI Act, Article 12 (Record-Keeping) reference: https://artificialintelligenceact.eu/article/12/
- Unchained repository (MIT): https://github.com/3sk1nt4n/Unchained
- Retained live-run receipt: `docs/runs/sol-capped-dc01-opening.json` (repository commit 51662cfb809212af3b58a680c0d9265d91692302)
- Public evidence source (DC01, The Stolen Szechuan Sauce): https://dfirmadness.com/the-stolen-szechuan-sauce/
- Repository documents quoted: `README.md`, `JUDGE-QUICKSTART.md`, `docs/SUBMISSION.md`, `docs/HONEST-WIN-ASSESSMENT.md`, `HACKATHON_HANDOVER.md`
