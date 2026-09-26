# TrustGate

**A pre-merge security gate. Five checkers, one verdict: `PASS`, `REVIEW`, or `BLOCK`.**

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon) ·
online · September 25–27 2026

> **Build status: Phase 0 of 7 — foundation only. No application code exists yet.**
> This README is written to be updated, not to look finished. Numbers appear here only
> after they have been measured.

---

## The problem

A pull request is the cheapest place to catch a security defect and the most expensive
place to discover one after release. Yet the review step is a bottleneck: a human reviewer
holding five things in their head — secrets, dependency CVEs, access control, injection,
business logic — is slow, inconsistent, and quietly unreliable at hour 18.

TrustGate fans the diff out to five independent specialists in parallel, then merges their
findings through a deterministic adjudicator into one verdict with cited evidence.

## How it works

```
       pull_request
             │
     ┌───────┴────────┐
     │  5 checkers    │   run concurrently
     │  (Tier 1)  secrets      Gitleaks        deterministic
     │  (Tier 1)  deps         OSV-Scanner     deterministic
     │  (Tier 2)  authz        LLM             semantic
     │  (Tier 2)  injection    LLM             semantic
     │  (Tier 2)  business     LLM             semantic
     └───────┬────────┘
             │  validated findings, each with file + line + quote
     ┌───────┴────────┐
     │  adjudicator   │   pure function, no LLM, no I/O
     └───────┬────────┘
             │
   PASS ─────┼───── REVIEW ───── BLOCK
             │
   SARIF 2.1.0 ──► GitHub Code Scanning (inline on the diff)
   status check ──► branch protection
```

### Why the roster is mixed

Two of the five checkers are deterministic scanners, not models. That is deliberate.

A leaked API key and a known CVE are **facts with answers**. Spending a model call to
rediscover them is slower, costlier, and less accurate than a scanner built for exactly
that job. The model budget goes to the classes of bug that have no lookup table — missing
authorization, injection through a framework's escaping rules, business-logic flaws.

The tiers fail differently, and that asymmetry is the design. Tier 1 is precise and cannot
reason about intent, so it does not try. Tier 2 reasons and is sometimes wrong, so every
one of its outputs is schema-validated and evidence-bearing.

### Why the adjudicator is not a model

The verdict is a pure function over validated findings. Given the same findings it always
returns the same verdict, it is testable without a network, and its decision is auditable.

| Condition | Verdict |
|-----------|---------|
| Any finding at `critical` | `BLOCK` |
| Any finding at `high` | `REVIEW` |
| Any finding at `medium` or `low` | `REVIEW` |
| All five checkers completed clean | `PASS` |
| **Any checker errored, timed out, or returned malformed output** | **`REVIEW`** |

That last row is the most important line in this README. A security gate that degrades to
`PASS` when it breaks is worse than no gate, because it launders uncertainty into
confidence. TrustGate fails closed toward `REVIEW`. Only a fully clean, fully completed run
is a `PASS`.

TrustGate never merges your code. It renders a verdict; a human decides. That is a product
constraint, not a missing feature.

## Tech

| Layer | Choice |
|-------|--------|
| Verdict engine | Python · FastAPI · Pydantic v2 |
| Inference | Groq (`openai/gpt-oss-120b`, strict JSON-schema mode) |
| Dashboard | React · Vite · TypeScript |
| Gate | GitHub Actions · SARIF 2.1.0 · Code Scanning |
| Scanners | Gitleaks · OSV-Scanner |

Rationale for each choice, and the model/streaming/tool-use constraints that shape the
checker design, are in [`AI_CONTEXT.md`](AI_CONTEXT.md).

## Repository layout

| Path | Contents |
|------|----------|
| `AI_CONTEXT.md` | The constitution — identity, architecture, rules, model strategy |
| `PROJECT_ROADMAP.md` | Phases, milestones, success metrics |
| `SYSTEM_LEDGER.md` | Session-to-session memory |
| `AGENTS.md` | Agent rules, read by every AI tool in the loop |
| `.bob/rules/` | The same rules, in IBM Bob's native format |
| `engine/` | Verdict engine — *Phase 2* |
| `dashboard/` | React/Vite UI — *Phase 2* |
| `corpus/` | Labelled samples for measuring false positives — *Phase 2* |

## Results

Intentionally empty until Phase 4.

False-positive rate, per-checker precision and recall, p50/p95 latency, and cost per PR will
appear here once they have been measured, along with the harness that reproduces them. Any
number here without a reproducible run behind it would be fabricated, and this project does
not publish fabricated numbers — see Rule 00 in [`.bob/rules/`](.bob/rules/00-authenticity.md).

## Working with TrustGate

Any AI agent can pick this project up cold:

> Read `AI_CONTEXT.md`, `PROJECT_ROADMAP.md`, and `SYSTEM_LEDGER.md`. Confirm you
> understand the architecture, the strict rules, and the active phase before we begin.

The project is built by six people in 48 hours, and the governance files are maintained
seriously enough that a new agent — or a new human — can recover the exact technical state
in under two minutes.

---

**Team of 6 · Phase 0 of 7 · submissions close Sun Sep 27 2026, 15:00 UTC**
