# TrustGate

**A pre-merge security gate. One verdict: `PASS`, `REVIEW`, or `BLOCK` — and a broken
checker can never produce a `PASS`.**

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon) ·
online · September 25–27 2026

> **Build status: engine core built and tested, runnable from the CLI. Not a finished
> product — the GitHub gate, the deterministic scanners, SARIF, and the dashboard are not
> built. See [Not built](#not-built) below.**
>
> This README is written to be updated, not to look finished. Numbers appear here only
> after they have been measured.

## Run it

```bash
cd engine
pip install -r requirements.txt          # once

# with GROQ_API_KEY set — real verdicts from the semantic checkers
python app/main.py --diff path/to/change.diff

# with GROQ_API_KEY unset — every semantic checker degrades, verdict is REVIEW
python app/main.py --diff path/to/change.diff

# HTTP surface
python app/main.py --serve               # then: curl localhost:8000/api/health

# the tests
python -m pytest tests/ -v               # 19 passing
```

---

## The problem

A pull request is the cheapest place to catch a security defect and the most expensive
place to discover one after release. Yet the review step is a bottleneck: a human reviewer
holding five things in their head — secrets, dependency CVEs, access control, injection,
business logic — is slow, inconsistent, and quietly unreliable at hour 18.

TrustGate fans the diff out to independent specialists in parallel, then merges their findings
through a deterministic adjudicator into one verdict with cited evidence.

## How it works

```
       diff / pull_request
             │
     ┌───────┴────────┐
     │  3 checkers    │   run concurrently — BUILT
     │  (Tier 2)  authz        LLM             semantic
     │  (Tier 2)  injection    LLM             semantic
     │  (Tier 2)  business     LLM             semantic
     ├────────────────┤
     │  (Tier 1)  secrets      Gitleaks        NOT BUILT
     │  (Tier 1)  deps         OSV-Scanner     NOT BUILT
     └───────┬────────┘
             │  validated findings, each with file + line + quote
     ┌───────┴────────┐
     │  adjudicator   │   pure function, no LLM, no I/O — BUILT
     └───────┬────────┘
             │
   PASS ─────┼───── REVIEW ───── BLOCK
             │
   SARIF 2.1.0 ──► GitHub Code Scanning   NOT BUILT
   status check ──► branch protection     NOT BUILT
```

### Why the roster is mixed

> **Not yet realised.** Only the three Tier 2 LLM checkers are built. The deterministic tier
> described below is the intended design and is **not implemented** — so this project
> currently has no ground-truth scanner, and no measured false-positive rate to defend.

Two of the five checkers are meant to be deterministic scanners, not models. That is deliberate.

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
| All checkers completed clean | `PASS` |
| **Any checker errored, timed out, or returned malformed output** | **`REVIEW`** |

That last row is the most important line in this README, and it is the one thing here that is
**built and tested** — `tests/test_adjudicator.py` asserts it for both the error and timeout
paths, and a failure in those two tests would invalidate the central claim.

A security gate that degrades to `PASS` when it breaks is worse than no gate, because it
launders uncertainty into confidence. TrustGate fails closed toward `REVIEW`. Only a fully
clean, fully completed run is a `PASS`.

TrustGate never merges your code. It renders a verdict; a human decides. That is a product
constraint, not a missing feature.

## Tech

| Layer | Choice | State |
|-------|--------|-------|
| Verdict engine | Python · FastAPI · Pydantic v2 | **built** |
| Inference | Groq (`openai/gpt-oss-120b`, strict JSON-schema mode) | **built**, unverified against a live call — no API key in this environment |
| Dashboard | React · Vite · TypeScript | **not built** |
| Gate | GitHub Actions · SARIF 2.1.0 · Code Scanning | **not built** |
| Scanners | Gitleaks · OSV-Scanner | **not built** |

The model ID was verified against Groq's published strict-mode supported-model list. It has
**not** been verified against a live completion, because no `GROQ_API_KEY` is present in this
environment — so the inference layer is written to spec and exercised only through the
deterministic `StaticProvider` used in tests.

Rationale for each choice, and the model/streaming/tool-use constraints that shape the
checker design, are in [`AI_CONTEXT.md`](AI_CONTEXT.md).

## Repository layout

| Path | Contents |
|------|----------|
| `AI_CONTEXT.md` | The constitution — identity, architecture, rules, model strategy |
| `PROJECT_ROADMAP.md` | Phases, milestones, success metrics |
| `SYSTEM_LEDGER.md` | Session-to-session memory |
| `WEDGE.md` | The positioning, the demo, and the claims that can be falsified |
| `AGENTS.md` | Agent rules, read by every AI tool in the loop |
| `.bob/rules/` | The same rules, in IBM Bob's native format |
| `engine/app/` | Verdict engine — schemas, adjudicator, checkers, LLM client, CLI |
| `engine/tests/` | Adjudicator and schema tests — 19 passing |
| `dashboard/` | React/Vite UI — **not built** |
| `corpus/` | Labelled samples for measuring false positives — **not built** |

## Not built

This is a 48-hour hackathon build that ran out of time. These are the pieces that do not
exist, stated plainly because a gate that overstates its own coverage is the exact failure
mode this project exists to catch.

| Missing | Consequence |
|---|---|
| **GitHub Actions gate** | **No pull request is ever blocked.** TrustGate is a local command, not yet a gate. This is the single largest gap. |
| **Gitleaks** (secrets) | No deterministic secret detection. The roster is LLM-only. |
| **OSV-Scanner** (dependencies) | No CVE detection. |
| **SARIF output** | Findings do not render inline on a diff or in the Code Scanning tab. |
| **React dashboard** | Verdict and evidence are terminal output only. |
| **Labelled corpus** | **No false-positive rate has been measured, and none is claimed.** |
| **Determinism harness** | The same diff has not been run 20× to prove the verdict is stable. |

**The roster is 3 LLM checkers, not the 5 described below.** `authz`, `injection`, and
`business` are implemented. The two deterministic checkers are not. The "why the roster is
mixed" argument describes the intended design; only the LLM half of it is built.

What *is* built and tested: the deterministic adjudicator, the fail-closed contract, the
schema-level evidence guarantees, and a CLI that runs them.

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

**Team of 6 · engine core built, gate not built · submissions close Sun Sep 27 2026, 15:00 UTC**
