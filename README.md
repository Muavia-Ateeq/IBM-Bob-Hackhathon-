# TrustGate

**A pre-merge security gate. One verdict: `PASS`, `REVIEW`, or `BLOCK` — and a broken
checker can never produce a `PASS`.**

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon) ·
online · September 25–27 2026

> **Build status: engine core built and tested, a GitHub gate written, runnable from the CLI.
> Not a finished product — the dashboard, the OSV dependency scanner, and a measured
> false-positive rate are not built; the gate has never run on GitHub, and no checker has yet
> produced a real finding against a live scanner or model. See [Not built](#not-built) below.**
>
> This README is written to be updated, not to look finished. Numbers appear here only
> after they have been measured.

## Setup in 8 commands

```bash
git clone <repo-url>                 # replace with this repository's URL
cd <this repository's folder>   # it is `IBM BOB Hackathon` — spaces, no hyphens
cd engine
python -m venv .venv
.venv\Scripts\activate                # source .venv/bin/activate on macOS or Linux
pip install -r requirements.txt
python app/main.py --serve
curl http://127.0.0.1:8000/api/health # {"ok":true}
```

`engine/` has no `__init__.py` or `pyproject.toml`, so every command above runs from inside
`engine/` — that is a known gap (`SYSTEM_LEDGER.md` K9), not a preference. Then read a verdict:

```bash
python app/main.py --diff samples/example.diff --pr 42      # run the engine
python app/comment.py --pr 42 --dry-run                    # format a PR comment, post nothing
python integration_test.py --pr 42                         # four-check smoke test
```

## Run it

```bash
cd engine
pip install -r requirements.txt          # once

# with GROQ_API_KEY set — real verdicts from the semantic checkers
python app/main.py --diff samples/example.diff --pr 42

# with GROQ_API_KEY unset — every semantic checker degrades, verdict is REVIEW
python app/main.py --diff samples/example.diff --pr 42

# HTTP surface
python app/main.py --serve               # then: curl localhost:8000/api/health

# re-derive a verdict from the run records on disk
python -m app.runlog --pr 42 --runs-dir runs

# the tests
python -m pytest tests/ -v               # 76 passing
```

`samples/example.diff` is a small PR carrying a SQL injection, a missing-authorization gap, and a
hardcoded key — enough to make every checker in the roster have something to say about it.

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
     │  4 checkers    │   run concurrently — BUILT
     │  (Tier 2)  authz        LLM             semantic
     │  (Tier 2)  injection    LLM             semantic
     │  (Tier 2)  business     LLM             semantic
     ├────────────────┤
     │  (Tier 1)  secrets      Gitleaks        BUILT, unrun
     │  (Tier 1)  deps         OSV-Scanner     NOT BUILT
     └───────┬────────┘
             │  validated findings, each with file + line + quote
     ┌───────┴────────┐
     │  adjudicator   │   pure function, no LLM, no I/O — BUILT
     └───────┬────────┘
             │
   PASS ─────┼───── REVIEW ───── BLOCK
             │
   runs/<run_id>_<checker>.json ──► app.runlog   BUILT
   SARIF 2.1.0 ──► GitHub Code Scanning   BUILT
   status check ──► branch protection     BUILT — on BLOCK
```

### The gate

`.github/workflows/trustgate.yml` runs on every pull request, uploads the SARIF to Code
Scanning, and fails the run on `BLOCK`. Two decisions in it are load-bearing:

**`pull_request`, never `pull_request_target`.** The latter gets a writable token and
repository secrets, so checking out and running fork-authored `requirements.txt` under it is
remote code execution with the Groq key in reach. Under `pull_request` a fork gets no secrets
and the semantic checkers degrade to `REVIEW`, which is written to the job summary — **not**
posted as a PR comment, which would need either the `pull_request_target` RCE above or a
GitHub App with its own installation token. Neither exists. Losing the model's opinion is an
acceptable price.

**`REVIEW` does not hard-block.** `WEDGE.md` is explicit that a human decides on `REVIEW`. But
it is never silent: the full report is written to the job summary. If the team decides a
degraded run should hold a merge, that is a one-line change in the last step.

Every action is pinned to a commit SHA. A floating tag in a security gate is remote code
execution with a trust boundary attached.

### Why the roster is mixed

> **Half realised.** Three Tier 2 LLM checkers are built and have never run against a live
> model. One Tier 1 deterministic checker is built and has never run against a real scanner.
> The fifth checker, `deps`, is not started. Nothing here has produced a real finding yet.

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
| Any finding at `critical` or `high` | `BLOCK` |
| Any finding at `medium`, `low`, or `info` | `REVIEW` |
| All checkers completed clean | `PASS` |
| **Any checker errored, timed out, or returned malformed output** | **`REVIEW`** |

Rows are evaluated in that order, so a `BLOCK`-severity finding still blocks even when a
sibling checker degraded. The last row only decides runs that would otherwise have been clean.
There is no numeric score and no weighting: one critical finding decides the verdict, and a
hundred low findings do not outvote it.

That last row is the most important line in this README, and it is the one thing here that is
**built and tested** — `tests/test_adjudicator.py` asserts it for both the error and timeout
paths, and a failure in those two tests would invalidate the central claim.

A security gate that degrades to `PASS` when it breaks is worse than no gate, because it
launders uncertainty into confidence. TrustGate fails closed toward `REVIEW`. Only a fully
clean, fully completed run is a `PASS`.

### Failing closed is not one rule, it is everywhere

The last row is the visible half. The load-bearing half is that there is no path — none — by
which a checker that did less work reports a clean result. Two of those paths were found by
audit and are now closed and tested (`tests/test_semantic.py`):

| Attempted fail-open | What happened | Now |
|---|---|---|
| Send the model a diff larger than the budget, silently | 73% of the diff was discarded with nothing in the prompt saying so. The model returned no findings, three checkers reported clean, and the verdict was **`PASS`**. | The checker **refuses** an over-budget diff. It degrades to `REVIEW` and names the env var to raise. |
| Return an `evidence` string that is not in the diff | `EVIDENCE_CONTRACT` asked the model for a verbatim quote; nothing checked. A fabricated `critical` reached the adjudicator and **`BLOCK`**. | A finding whose quote is not present in the diff is **rejected**, and the whole batch with it. |

The second one discards the honest findings in the same response too, deliberately: the same
model produced every quote in it, so the ones that happen to match carry no more assurance than
the one that does not. Degrading to `REVIEW` is honest; acting on the survivors is not.

TrustGate never merges your code. It renders a verdict; a human decides. That is a product
constraint, not a missing feature.

## Checkers

Five are planned; four are built, and **none of the four has ever produced a real finding.**

| Checker | What it detects | Tier | Method | Status |
|---------|-----------------|------|--------|--------|
| `secrets` | Hardcoded credentials, API keys, private keys | 1 | Gitleaks, deterministic | built — has run, but only ever failed: the binary is at `engine/.tools/gitleaks.exe` and not on `PATH` (K14) |
| `authz` | Missing authorization, IDOR, privilege escalation | 2 | `openai/gpt-oss-120b` | built — never run, no API key (K12) |
| `injection` | SQL/command injection, XSS, SSRF, unsafe deserialization | 2 | `openai/gpt-oss-120b` | built — never run, no API key (K12) |
| `business` | Business-logic flaws, race conditions, crypto misuse | 2 | `openai/gpt-oss-120b` | built — never run, no API key (K12) |
| `deps` | Known CVEs in Python and npm dependencies | 1 | OSV-Scanner, deterministic | **not built** — blocked, see K13 |

Every checker implements one interface (`engine/app/checkers/base.py`), so adding a sixth must
not require touching the orchestrator. The contract each checker author follows is in
[`engine/app/checkers/CONTRIBUTING.md`](engine/app/checkers/CONTRIBUTING.md).

Because no checker has run live, **every verdict a reviewer can produce today is `REVIEW`** —
`BLOCK` and a clean `PASS` are not currently demonstrable. That is a consequence of two
missing credentials, not a design property, and it is why K12 and K14 are the first two items
in the ledger's Next Actions.

## Tech

| Layer | Choice | State |
|-------|--------|-------|
| Verdict engine | Python · FastAPI · Pydantic v2 | **built** |
| Inference | Groq (`openai/gpt-oss-120b`, strict JSON-schema mode) | **built**, unverified against a live call — no API key in this environment |
| Dashboard | React · Vite · TypeScript | **not built** |
| Gate | GitHub Actions · SARIF 2.1.0 · Code Scanning | **built**, never executed — the workflow has not been run on GitHub |
| Secret scanner | Gitleaks (`secrets`) | **built**, unverified — the binary is present and works (`engine/.tools/gitleaks.exe`, v8.30.1) but is not on `PATH`; set `GITLEAKS_BIN` to its full path |
| Dependency scanner | OSV-Scanner (`deps`) | **not built** — blocked, see `SYSTEM_LEDGER.md` K13 |
| Run log | `runs/*.json` + `app.runlog` | **built** |
| Deploy config | `render.yaml` · `Procfile` · `vercel.json` | **written, never deployed** |
| Data contract | `CONTRACT.md` | **built** — the schema the engine actually writes |

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
| `engine/app/` | Verdict engine — schemas, adjudicator, checkers, LLM client, run log, SARIF, CLI |
| `engine/app/comment.py` | Renders a verdict as a pull-request comment and posts it. Runs locally, not from the gate — see the note in its header |
| `engine/integration_test.py` | Four-check smoke test: API health, run records, verdict endpoint, gate invariants |
| `engine/tests/` | Adjudicator, schema, run-log, secrets, semantic, SARIF, gate, comment, and integration tests — 76 passing |
| `engine/samples/` | A runnable example diff carrying an injection, an authz gap, and a hardcoded key |
| `engine/requirements.txt` | The pinned installed set |
| `.github/workflows/trustgate.yml` | The gate — runs the engine on every PR, uploads SARIF, fails the run on `BLOCK` |
| `dashboard/` | React/Vite UI — **not built** |
| `demo_target/` | Labelled corpus, one planted defect per case — **built, never run against a live checker** |
| `bench/` | Ground truth (`cases.json`) and the measurement runner — **built; reports `INCOMPLETE`** |

## Not built

This is a 48-hour hackathon build that ran out of time. These are the pieces that do not
exist, stated plainly because a gate that overstates its own coverage is the exact failure
mode this project exists to catch.

| Missing | Consequence |
|---|---|
| **A real run of the gate** | `.github/workflows/trustgate.yml` and the SARIF converter are written and unit-tested, but the workflow has never executed on GitHub and the SARIF has never been accepted by Code Scanning. Everything about it is verified against the published schemas and action runtimes, not against a live run. |
| **OSV-Scanner** (dependencies) | No CVE detection. Blocked: OSV emits no line number, and `Finding.line` requires one. See `SYSTEM_LEDGER.md` K13. |
| **React dashboard** | Verdict and evidence are terminal output, a PR comment, and the Code Scanning tab — nothing more. `vercel.json` exists but has nothing to build. |
| **Labelled corpus** | The corpus and its runner are built (`demo_target/`, `bench/`), 9 of 10 fixtures planted. **No false-positive rate has been measured, and none is claimed** — the runner reports `INCOMPLETE` and prints no rate while K12 and K14 are open. One case (`issue-05`) is unplanted: a reachable `pickle.loads` fixture was declined by the sandbox classifier and needs a human decision. |
| **Determinism harness** | The same diff has not been run 20× to prove the verdict is stable. |
| **A real scanner run** | `secrets` has run four times and produced nothing. Every run ended `FileNotFoundError` because `config.py` defaults to a bare `gitleaks` and the binary is not on `PATH`, so no secret has ever been detected by it. |
| **A deployment** | `render.yaml`, `Procfile`, and `vercel.json` are written. Nothing has been deployed. The backend exposes three routes: `/api/health`, `/api/pr/{pr}/verdict`, and `/api/runs`. |

**The roster is 4 of 5, and none of the 4 has produced a real finding.** `authz`, `injection`,
and `business` are LLM checkers that have never run against a live model; `secrets` is a
Gitleaks wrapper that has never run against a real binary. Without a `GROQ_API_KEY` or a
`gitleaks` binary, every run a reviewer can perform today degrades to `REVIEW` — **`BLOCK` and
a clean `PASS` are not currently demonstrable**, and that is stated here rather than papered over.

What *is* built and tested (76 tests, 8 files): the deterministic adjudicator, the fail-closed
contract including its two closed bypasses, the schema-level evidence guarantees, the
quote-must-exist-in-the-diff check, a run log that round-trips a verdict through disk, a SARIF
converter validated against both the OASIS schema and GitHub's stricter requirements, and a
CLI that runs them.

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

## Team

Six people, 48 hours. **These rows are unfilled on purpose** — no workstream has been claimed
yet (`SYSTEM_LEDGER.md` K4), and a name written here that nobody owns would be a fabrication
in the one document judges read.

| # | Member | Workstream | Focus |
|---|--------|------------|-------|
| A | _unassigned_ | `engine/app/llm/` | Groq client, strict schema enforcement, retry, cache-by-input-hash |
| B | _unassigned_ | `engine/app/checkers/` | The checkers and `base.py` |
| C | _unassigned_ | `engine/app/adjudicator.py`, `schemas.py`, `tests/` | The verdict path and the proof |
| D | _unassigned_ | `.github/workflows/`, `sarif.py` | The gate and the Code Scanning upload |
| E | _unassigned_ | `dashboard/` | React/Vite UI — **not started** |
| F | _unassigned_ | `demo_target/` + `bench/` | Labelled corpus and the measurement runner — **built; first measurement blocked on K12/K14** |

Replace `_unassigned_` with real names before submitting. The workstream column is real: it is
the Phase 3 split in `PROJECT_ROADMAP.md`, and two of the six are unstarted.

---

**Team of 6 · engine core and gate built, neither has run live · submissions close Sun Sep 27 2026, 15:00 UTC**
