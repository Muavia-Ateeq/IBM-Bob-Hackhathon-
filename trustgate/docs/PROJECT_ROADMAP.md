# PROJECT_ROADMAP.md — The GPS

> Exactly one phase is 🔴 ACTIVE. That constraint is what makes scope control real
> rather than decorative. Do not start work in a ⏳ phase without a phase transition.

---

## Phase Overview

| Phase | Name | Window (from kickoff) | Status |
|-------|------|----------------------|--------|
| 0 | Foundation & Governance | T+0h → T+1h | 🔴 **ACTIVE** |
| 1 | Problem Definition & Wedge Lock | T+1h → T+3h | ⏳ Pending |
| 2 | Stack Lock & Scaffold | T+3h → T+5h | ⏳ Pending |
| 3 | Core Build — checkers, adjudicator, gate | T+5h → T+30h | ⏳ Pending |
| 4 | Evaluation Harness & FP Measurement | T+30h → T+38h | ⏳ Pending |
| 5 | Demo, Docs & Submission Prep | T+38h → T+45h | ⏳ Pending |
| 6 | Submit & Buffer | T+45h → T+48h | ⏳ Pending |

**Absolute deadline: Sun Sep 27 2026, 15:00 UTC.** Phase 6 exists so that a late Phase 5
cannot cost the submission.

---

## Current Active Phase

### Phase 0 — Foundation & Governance 🔴

**Objective.** Make the project recoverable by any agent, in any session, on any model —
before a single line of application code exists. If the team loses its context at hour 20,
the ledger brings it back.

**Deliverables — this table is the Tier 1 manifest.** Files listed here may be edited
without per-file approval once the batch is approved:

| File | Purpose |
|------|---------|
| `docs/AI_CONTEXT.md` | Constitution: identity, stack, architecture, tokens, rules, model strategy |
| `docs/PROJECT_ROADMAP.md` | This file |
| `docs/SYSTEM_LEDGER.md` | Memory: state, file history, issues, next actions |
| `docs/AGENTS.md` | Portable agent rules |
| `AGENTS.md` | Root pointer to `docs/AGENTS.md`, so tools that load that filename from the repo root still find the rules |
| `docs/WEDGE.md` | The positioning, the demo script, and the claims that can be falsified |
| `docs/CONTRACT.md` | The HTTP surface the engine writes and the dashboard reads |
| `.bob/rules/00-authenticity.md` | Bob-native: authenticity |
| `.bob/rules/01-planning-governance.md` | Bob-native: tiered approval |
| `.bob/rules/02-session-continuity.md` | Bob-native: boot / close-out |
| `.bob/rules/03-scope-control.md` | Bob-native: active-phase discipline |
| `.gitignore` | Python, Node, secrets, SARIF artifacts |
| `README.md` | Human-facing; doubles as the lablab submission page |
| `render.yaml` | Render blueprint — service name, build, start, health check, env vars |
| `Procfile` | Same start command, for any Procfile-hosting platform |

**Out of scope for Phase 0 — do not start early:**
- Writing any application code
- Installing dependencies
- Creating `backend/`, `dashboard/`, or `.github/workflows/`
- Any git commit

> ### ⚠️ Scope discrepancy — unresolved, Tier 3 (recorded 2026-09-25, widened twice)
>
> The boundaries above forbid application code. **`backend/app/**` nevertheless contains 15
> Python files** — schemas, the adjudicator, the checker base, three LLM checkers, one
> deterministic checker, the config loader, the Groq client, the run log, and the entry point.
>
> The record cannot say whether a phase transition happened without this file being updated,
> or whether the code landed outside approved scope. **This is deliberately left unresolved**,
> because a phase transition is a Tier 3 decision and not an agent's to make. Tracked as **K10**
> in `docs/SYSTEM_LEDGER.md`; it is the first item in that file's Next Actions.
>
> **The 🔴 ACTIVE marker is deliberately left on Phase 0.** A second session added 3
> application files, one schema model, and 3 deploy configs under a user-approved batch. A
> **third** session (2026-09-26) renamed `engine/` → `backend/`, moved this file and five
> sibling docs into `docs/`, rewrote `render.yaml` and `Procfile`, and **deployed to Render**
> — all under a plan the user approved. That approval authorised the edits; it was not a phase
> transition, and moving this marker is not an agent's call.
>
> Consequence: **no phase status in this repository can be trusted until a human resolves it.**
> Everything else in Phase 0 verified clean (26/26 checks, 2026-09-25). One Phase 0
> deliverable, `README.md`, was corrected: its verdict table contradicted the code.
>
> **Note on the deliverables table above:** the governance files moved into `docs/` on
> 2026-09-26, so their paths changed. This table is the Tier 1 manifest, and a manifest listing
> a path that does not exist is a governance bug rather than a typo — which is why the new
> paths are recorded here and not just in the ledger.

**Exit criteria — all must hold:**
1. All three governance files contain their required sections
2. Exactly one 🔴 ACTIVE in this file
3. `SYSTEM_LEDGER.md` file counts match the real directory listing
4. `AGENTS.md` and all four `.bob/rules/` files carry the tiered approval policy
5. `git rev-parse --show-toplevel` from this directory returns **this directory**, not `E:/`
6. Zero `TBD` or `UNDECIDED` remaining in Tech Stack, Design Tokens, or Model Strategy

---

## Future Phases

### Phase 1 — Problem Definition & Wedge Lock (T+1h → T+3h)

No code. Write, on one page:

- **Problem statement** — the specific PR failure mode, in one sentence
- **Target user** — who feels this pain daily
- **Wedge** — the one thing TrustGate does that the four overlapping submissions do not
- **Demo script** — the 90 seconds the judges will see
- **Anti-goals** — what we are explicitly not building

Deliverable: the wedge statement, agreed by all 6. Everything in Phase 3 must trace to it.

### Phase 2 — Stack Lock & Scaffold (T+3h → T+5h)

- Confirm exact model IDs against live IBM watsonx.ai and Groq docs — **including Groq's
  strict-mode supported list** (watsonx `.chat()` is unconfirmed for strict-mode support)
- Scaffold `backend/`, `dashboard/`, `.github/workflows/`
- Pin dependency versions into lockfiles
- Confirm an IBM watsonx.ai key (with project ID) is present, and a Groq key as fallback
- Green test: the engine boots, the dashboard renders, `/health` returns 200

### Phase 3 — Core Build (T+5h → T+30h)

The long phase. Suggested split across 6 people, adjusted as the team sees fit:

| Owner | Workstream |
|-------|-----------|
| A | `backend/app/llm/` — watsonx.ai primary + Groq fallback client, strict schema enforcement, retry, cache-by-input-hash |
| B | `backend/app/checkers/` — the 7 checkers + `base.py` protocol |
| C | `backend/app/adjudicator.py` + `schemas.py` + `store.py` + `tests/` |
| D | `.github/workflows/trustgate.yml` + `sarif.py` + secrets/permissions plumbing |
| E | `dashboard/` — API client, components, verdict rendering |
| F | `corpus/` — labelled vulnerable samples; integration harness |

Each workstream is independently testable. Integration is C's milestone, not the last hour.

**Definition of done:** a real PR in a real repo gets a real verdict, a SARIF file lands
in the Code Scanning tab, and a failed checker degrades to `REVIEW` rather than `PASS`.

### Phase 4 — Evaluation Harness & FP Measurement (T+30h → T+38h)

Run the full corpus. Produce **measured** precision/recall per checker, false-positive rate,
p50/p95 latency, and cost per PR. This phase is what converts claims into evidence.

A number that was not measured does not get written down. See the Authenticity Rule.

### Phase 5 — Demo, Docs & Submission Prep (T+38h → T+45h)

README with the real architecture, the measured numbers, and an honest limitations section.
Demo video or scripted walkthrough. lablab submission page. Repo public and pushed.

### Phase 6 — Submit & Buffer (T+45h → T+48h)

Submit early, then keep improving. **Submitting at T+45h and letting the last 3 hours be
optional is strictly better than submitting at T+48h and having a broken build.**

---

## Milestones

| # | Milestone | Target | Completion metric |
|---|-----------|--------|-------------------|
| M1 | Foundation complete | T+1h | All 6 Phase 0 exit criteria pass |
| M2 | Wedge agreed | T+3h | One sentence, signed off by all 6 |
| M3 | Stack locked | T+5h | Scaffold boots; model IDs verified against live docs |
| M4 | First real verdict | T+14h | One PR, end to end, verdict rendered |
| M5 | All 7 checkers live | T+24h | Every checker produces findings on the corpus |
| M6 | Gate installed | T+30h | Workflow runs on a real PR; SARIF visible in the Security tab |
| M7 | Numbers measured | T+38h | Every README number traces to a recorded run |
| M8 | Submitted | T+45h | lablab submission live, 3h buffer intact |

> **M5 is not met.** 5 of the 7 checkers produce findings on the corpus; `security_reviewer`
> and `spec_conformance` are named by no case in `bench/cases.json` and are therefore
> unmeasured. The roster is 7 — one deterministic (`secrets`), six semantic.
>
> **M6 is now met, in two halves.** The workflow runs on a real pull request and is green:
> runs `36317034453` (PR #6) and `36311839360` (PR #5) both completed `success` on
> 2026-09-27, and the SARIF upload step succeeded inside `36317931615`. **The second half is
> not verified** — "SARIF visible in the Security tab" means Code Scanning *accepted* the
> report and rendered alerts, which is a different claim from the upload step succeeding.
> `UNVERIFIED — open the Code Scanning tab on the default branch and confirm alerts render`
>
> **M4 is not met.** The gate runs and renders a verdict, but no run has yet reached a live
> provider: the six semantic checkers degrade to `REVIEW` because no `WATSONX_API_KEY` and
> no `GROQ_API_KEY` have been observed in the Actions environment. A verdict has been
> rendered end to end; a *real* one has not. `UNVERIFIED — read a `tests`/gate job summary for
> an `authz ok` line rather than `DEGRADED … ProviderUnavailable``
>
> **M7 is not met** and no number is published that is not traced to a recorded run.

---

## Key Success Metrics

Every metric below states its **measurement method**. A metric without a method is a wish.

| Metric | Target | How it is measured |
|--------|--------|-------------------|
| Gate wall-clock latency | p95 < 60s end to end | Timed over ≥30 corpus runs; p95 from recorded durations |
| Cost per PR verdict | < $0.50 | Sum of token usage from API responses ÷ runs — **Groq-served runs only.** watsonx `.chat()` returns no token usage, so cost is not measurable on watsonx-served runs. Not estimated |
| False-positive rate | < 15% on the corpus | Findings labelled false by 2 reviewers ÷ total findings, disagreements resolved by a 3rd |
| Recall on known-vuln samples | > 80% | Corpus samples with a known planted flaw that produced a finding ÷ total samples |
| Verdict correctness | 100% on error injection | Every fault-injection case (timeout, malformed JSON, HTTP 500, empty diff) yields `REVIEW` or `UNKNOWN`. **Never `PASS`** |
| Determinism | Same input → same verdict, 20/20 runs at `temperature: 0` | 20 repeats of the same diff, verdicts diffed |
| Evidence completeness | 100% of findings have file + line + quote | Automated assertion over every emitted finding |

**Explicit non-goal:** competitive wall-clock against CodeRabbit, Greptile, or SonarQube.
Those are funded products with production SAST engines. We are a 48-hour prototype whose
credibility comes from honest numbers, not from out-scaling a company.

---

## Competitive Advantages

### The field, as measured on Sep 25 2026

31 submissions, leader at 19 community votes. The previous edition of this event had 503
submissions, 2,319 total hearts, and a winner at 47 votes. **This is a community-voted
event decided on execution, documentation, and demo quality — not on being first to an idea.**

Four live submissions overlap the general territory: *Inbin Gate* (merge-approval gating),
*Rehearsal* (pre-rollout testing), *Cutover* (pre-merge correctness), *Smart Developer
Onboarding Assistant*. The previous edition placed *PRISM — Pull Request Intelligent
Semantic Monitor* fourth.

### What that means, honestly

Novelty is not the lever. A sixth "AI reviews your PR" is not a differentiator. The levers,
in order of expected value:

1. **Measured numbers in the README.** The overwhelming majority of competing submissions
   will assert impact. If our README shows a real FP rate, a real p95, and a real cost per
   PR — with the harness in the repo to reproduce them — that is visibly more credible.
2. **A demo that runs live in under 90 seconds.** On a real PR, real verdict, real SARIF.
3. **Honest failure.** Showing the degraded `REVIEW` path when a checker breaks is a
   security product behaving correctly. Most demos only show the happy path.
4. **Heterogeneous checker roster.** Deterministic scanners for what has a ground truth,
   LLMs for what needs judgement. This is *why* the FP rate is defensible — it is a
   mechanism, not a boast.

### Explicitly rejected strategies

- **Shadow-mode calibration as the headline.** Already shipped by a live competitor
  (quorum.reviews). Building it to spec would produce a clone discovered at demo time.
- **Auto-merge.** A gate that merges code is a much larger safety claim than a 48-hour
  prototype can support, and a wrong auto-merge is far more costly than a missed finding.

---

## Team Operating Notes

Six people, one repo, 48 hours.

- `SYSTEM_LEDGER.md` is written by whoever closes a workstream, not deferred to session end.
- Merge conflicts on `AI_CONTEXT.md` are a smell — it means two people changed the
  architecture without a Tier 3 conversation.
- The person running the demo should not also be the person debugging at hour 44.
- If a workstream slips, cut its scope. Do not move a phase boundary.
