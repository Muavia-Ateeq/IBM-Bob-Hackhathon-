# TrustGate

**A pre-merge security gate. One verdict: `PASS`, `REVIEW`, or `BLOCK` — and a broken
checker can never produce a `PASS`.**

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon) ·
online · September 25–27 2026

> **Build status: engine core built and tested, a GitHub gate that has run, runnable from the
> CLI, a live backend, and a dashboard that builds. Not a finished product — the OSV dependency
> scanner is not built, no workflow run has completed green, and no false-positive rate is
> claimed. `secrets` does produce a real `BLOCK` against a real scanner; the six LLM checkers
> have never run against a live model. See [Not built](#not-built) below.**
>
> This README is written to be updated, not to look finished. Numbers appear here only
> after they have been measured.

## Live deployment

**`https://trustgate-api-ehib.onrender.com`** — running on Render's Free plan, built from the
`render.yaml` blueprint at the repo root.

| Endpoint | Returns |
|---|---|
| `/api/health` | `{"ok":true}` |
| `/api/runs` | every run record on disk — `{"count":0,...}` on a fresh deploy, because `runs/` is gitignored |
| `/api/pr/{pr}/verdict` | one pull request's verdict |

Four honest caveats:

- The API is **read-only**. It surfaces run records; it does not create verdicts. Those come
  from the engine CLI, which today runs in GitHub Actions on a pull request.
- `/api/runs` is **unauthenticated with `allow_origins=["*"]`**, and a run record carries
  `Finding.evidence` verbatim. The `secrets` checker redacts the matched credential before it
  becomes evidence, but this endpoint is still an open read of internal analysis on a public
  host. Demo-only until it is authenticated — see the note at `trustgate/backend/app/main.py`.
- `WATSONX_API_KEY` and `GROQ_API_KEY` are `sync: false` in the blueprint, so both must be
  added by hand in the Render dashboard. Without either, the six semantic checkers degrade to
  `REVIEW`. watsonx.ai is the primary provider and Groq the fallback; watsonx additionally needs
  a `WATSONX_PROJECT_ID` (or `WATSONX_SPACE_ID`) to scope a request, and is skipped with a log
  line if neither is set.
- The Free plan spins down after ~15 minutes idle, so the first request after a pause can take
  30–60 seconds. Open `/api/health` once before demoing.

## Setup in 8 commands

```bash
git clone <repo-url>                 # replace with this repository's URL
cd <this repository's folder>   # it is `IBM BOB Hackathon` — spaces, no hyphens
cd trustgate/backend
python -m venv .venv
.venv\Scripts\activate                # source .venv/bin/activate on macOS or Linux
pip install -r requirements.txt
python app/main.py --serve
curl http://127.0.0.1:8000/api/health # {"ok":true}
```

`trustgate/backend/` has no `__init__.py` or `pyproject.toml`, so every command above runs from inside
`trustgate/backend/` — that is a known gap (`trustgate/docs/SYSTEM_LEDGER.md` K9), not a preference. Then read a verdict:

```bash
python app/main.py --diff samples/example.diff --pr 42      # run the engine
python app/comment.py --pr 42 --dry-run                    # format a PR comment, post nothing
python integration_test.py --pr 42                         # four-check smoke test
```

## Run it

```bash
cd trustgate/backend
pip install -r requirements.txt          # once

# with a provider credential set — real verdicts from the semantic checkers
python app/main.py --diff samples/example.diff --pr 42

# with WATSONX_API_KEY and GROQ_API_KEY both unset — every semantic checker
# degrades, verdict is REVIEW
python app/main.py --diff samples/example.diff --pr 42

# HTTP surface
python app/main.py --serve               # then: curl localhost:8000/api/health

# re-derive a verdict from the run records on disk
python -m app.runlog --pr 42 --runs-dir runs

# the tests
python -m pytest tests/ -v               # 108 passing
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
     │  7 checkers    │   run concurrently — BUILT
     │  (Tier 2)  authz        LLM             semantic
     │  (Tier 2)  injection    LLM             semantic
     │  (Tier 2)  prompt_inj   LLM             semantic
     │  (Tier 2)  business     LLM             semantic
     │  (Tier 2)  security_rev LLM             semantic
     │  (Tier 2)  spec_conform LLM             semantic
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

**`REVIEW` does not hard-block.** `trustgate/docs/WEDGE.md` is explicit that a human decides on `REVIEW`. But
it is never silent: the full report is written to the job summary. If the team decides a
degraded run should hold a merge, that is a one-line change in the last step.

Every action is pinned to a commit SHA. A floating tag in a security gate is remote code
execution with a trust boundary attached.

### Why the roster is mixed

> **Half realised.** Six Tier 2 LLM checkers are built and have never run against a live
> model. The Tier 1 deterministic checker, `secrets`, runs the real gitleaks binary and does
> produce real findings. The eighth checker, `deps`, is not started.

Two of the seven checkers are meant to be deterministic scanners, not models. That is deliberate.

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

Eight are planned; seven are built, and **one of the seven has produced a real finding.**

| Checker | What it detects | Tier | Method | Status |
|---------|-----------------|------|--------|--------|
| `secrets` | Hardcoded credentials, API keys, private keys | 1 | Gitleaks 8.30.1, deterministic | built — **runs and finds**. It blocks the `issue-02-hardcoded-key` fixture at `config.py:5` with the match redacted. It needs `GITLEAKS_BIN` pointed at the binary; `config.py` defaults to a bare `gitleaks` on `PATH`, which is why earlier runs died `FileNotFoundError` (K14) |
| `authz` | Missing authorization, IDOR, privilege escalation | 2 | LLM | built — never run, no API key (K12) |
| `injection` | SQL/command injection, XSS, SSRF, unsafe deserialization | 2 | LLM | built — never run, no API key (K12) |
| `prompt_injection` | Untrusted text concatenated into a model instruction; agent-directed repo content | 2 | LLM | built — never run, no API key (K12) |
| `business` | Business-logic flaws, race conditions, crypto misuse | 2 | LLM | built — never run, no API key (K12) |
| `security_reviewer` | General security review of the diff | 2 | LLM | built — never run, no API key (K12) |
| `spec_conformance` | Whether the diff matches the stated requirement | 2 | LLM | built — never run, no API key (K12) |
| `deps` | Known CVEs in Python and npm dependencies | 1 | OSV-Scanner, deterministic | **not built** — blocked, see K13 |

`security_reviewer` and `spec_conformance` were contributed by M. Muavia from his IBM Bob
subagent prompts and wired to the same `SemanticChecker` as the other four. Neither is named by
any case in `trustgate/bench/cases.json`, so **neither is measured** — see [Results](#results).

Every checker implements one interface (`trustgate/backend/app/checkers/base.py`), so adding an
eighth must not require touching the orchestrator. The roster lives in one tuple,
`app.main.CHECKER_MODULES`, and `trustgate/bench/run_benchmark.py` derives its own roster from it
rather than restating it, with `tests/test_bench_scoring.py` asserting the two agree. The contract
each checker author follows is in
[`trustgate/backend/app/checkers/CONTRIBUTING.md`](trustgate/backend/app/checkers/CONTRIBUTING.md).

### See the real bench output

The runner is honest even when it has nothing to report. A run today, with no `GITLEAKS_BIN` and
no provider credential, prints:

```
  secrets     SKIPPED    FileNotFoundError: [WinError 2] The syst — no rate reported
  authz       SKIPPED    ProviderUnavailable: neither WATSONX_API — no rate reported
  injection   SKIPPED    ProviderUnavailable: neither WATSONX_API — no rate reported
  prompt_injection SKIPPED    ProviderUnavailable: neither WATSONX_API — no rate reported
  business    SKIPPED    ProviderUnavailable: neither WATSONX_API — no rate reported
  security_reviewer SKIPPED    ProviderUnavailable: neither WATSONX_API — no rate reported
  spec_conformance SKIPPED    ProviderUnavailable: neither WATSONX_API — no rate reported

OVERALL: INCOMPLETE - 7 of 7 checkers did not complete.
```

The reason the runner prints is `neither WATSONX_API_KEY nor GROQ_API_KEY is set`, truncated in
that column. `OVERALL: INCOMPLETE` is the correct output here, **not a failure** — it is the
same fail-closed contract the adjudicator applies to a degraded run, one level up. No checker
wrote a record, so the runner is not willing to print a rate for any of them.

One real `BLOCK` is on the record, and it needs only gitleaks, no model credential:

```bash
cd trustgate/backend
GITLEAKS_BIN="$PWD/.tools/gitleaks.exe" python ../bench/run_benchmark.py
```

That run blocks the planted `issue-02-hardcoded-key` fixture and measures `secrets` on a single
case — see [Results](#results). It is not quoted here as a transcript because the bench output
above is what this branch produces today, and a transcript that could not be reproduced is not
evidence.

`GITLEAKS_BIN` is why `secrets` needs a second step: `config.py` defaults to a bare `gitleaks` on
`PATH`, and the binary is a gitignored local download (K14). **On CI it is installed and
checksum-verified instead**, so the gate gets it for free. A 1-case sample is not a precision
claim and is not published as one.

The six LLM checkers still have never run against a live model, so a reviewer with no provider
credential will get `REVIEW` from them on every diff. A clean `PASS` is still not
demonstrable — a run in which any checker degraded is `REVIEW` by design, and that is the
point, not a gap in the demo.

## Tech

| Layer | Choice | State |
|-------|--------|-------|
| Verdict engine | Python · FastAPI · Pydantic v2 | **built** |
| Inference | IBM watsonx.ai (`ibm/granite-4-h-small`, primary) → Groq (`openai/gpt-oss-120b`, fallback), strict JSON-schema mode | **built** — **UNVERIFIED: no IBM watsonx.ai credential has ever existed in this project, so the live call has never been made.** Written against the introspected `ibm-watsonx-ai` 1.7.2 SDK signature and unit-tested with stubs; a real key plus a project ID are required to verify end to end. No Groq key is present in this environment either |
| Dashboard | React · Vite · TypeScript | **built** — `dashboard/` merged from PR #2; `npm ci` reports 0 vulnerabilities and `npm run build` succeeds. **Not deployed** |
| Gate | GitHub Actions · SARIF 2.1.0 · Code Scanning | **built and executed** — the last 5 workflow runs all **failed**. A `tests` job was added on this branch and has not executed yet, so CI is **UNVERIFIED** and is not claimed green |
| Secret scanner | Gitleaks (`secrets`) | **built and verified** — runs the real binary (`trustgate/backend/.tools/gitleaks.exe`, v8.30.1) and finds. It is not on `PATH`; set `GITLEAKS_BIN` to its full path |
| Dependency scanner | OSV-Scanner (`deps`) | **not built** — blocked, see `trustgate/docs/SYSTEM_LEDGER.md` K13 |
| Run log | `runs/*.json` + `app.runlog` | **built** — `runs/` is gitignored; the 13 fabricated run records that shipped asserting `status:"ok"` for checkers that raised `NotImplementedError` were removed from git |
| Deploy config | `render.yaml` · `Procfile` · `vercel.json` | `render.yaml` **deployed and live**; `vercel.json` written but inert — no deployment of the dashboard has happened |
| Version | `app/config.py` `__version__` | `0.1.0` — the single source of truth. SARIF `tool.driver.version` reads it; it no longer emits a hardcoded `0.0.0` |
| Data contract | `trustgate/docs/CONTRACT.md` | **built** — the schema the engine actually writes |

The Groq model ID was verified against Groq's published strict-mode supported-model list. It has
**not** been verified against a live completion, because no `GROQ_API_KEY` is present in this
environment. The watsonx.ai path is **UNVERIFIED** for the same reason and one more: no IBM
watsonx.ai credential has ever existed in this project, so the live call has never been made —
the provider is written against the introspected `ibm-watsonx-ai` 1.7.2 SDK signature and
unit-tested with stubs. Both paths are therefore exercised in tests only through the
deterministic `StaticProvider`.

`FallbackProvider` tries watsonx first, then Groq, printing one stderr line per failure that
names the provider and the reason. If every provider fails it raises `ProviderUnavailable`
carrying **all** the reasons — it never fabricates a success, and the `model_id` on a result
names the provider that actually served it, not the first one tried. watsonx additionally needs
`WATSONX_PROJECT_ID` or `WATSONX_SPACE_ID` to scope a request, and is dropped with a logged
reason when neither is set.

Rationale for each choice, and the model/streaming/tool-use constraints that shape the
checker design, are in [`trustgate/docs/AI_CONTEXT.md`](trustgate/docs/AI_CONTEXT.md).

## Repository layout

| Path | Contents |
|------|----------|
| `trustgate/docs/AI_CONTEXT.md` | The constitution — identity, architecture, rules, model strategy |
| `trustgate/docs/PROJECT_ROADMAP.md` | Phases, milestones, success metrics |
| `trustgate/docs/SYSTEM_LEDGER.md` | Session-to-session memory |
| `trustgate/docs/WEDGE.md` | The positioning, the demo, and the claims that can be falsified |
| `trustgate/docs/CONTRACT.md` | The HTTP surface the dashboard and the gate both depend on |
| `trustgate/docs/AGENTS.md` | Agent rules, read by every AI tool in the loop |
| `AGENTS.md` | Root pointer to `trustgate/docs/AGENTS.md`, so tools that load from the root still find the rules |
| `.bob/rules/` | The same rules, in IBM Bob's native format |
| `trustgate/backend/app/` | Verdict engine — schemas, adjudicator, checkers, LLM client, run log, SARIF, CLI |
| `trustgate/backend/app/comment.py` | Renders a verdict as a pull-request comment and posts it. Runs locally, not from the gate — see the note in its header |
| `trustgate/backend/integration_test.py` | Four-check smoke test: API health, run records, verdict endpoint, gate invariants |
| `trustgate/backend/tests/` | Adjudicator, schema, run-log, secrets, semantic, SARIF, gate, comment, integration, prompt-injection, and benchmark-scoring tests — **108 passing** (`cd trustgate/backend && python -m pytest tests/ -q`), and a `tests` job runs them in CI (that job has not executed yet) |
| `dashboard/` | React · Vite · TypeScript UI, merged from PR #2 — **built, not deployed** |
| `trustgate/backend/samples/` | A runnable example diff carrying an injection, an authz gap, and a hardcoded key |
| `trustgate/backend/requirements.txt` | The pinned installed set |
| `.github/workflows/trustgate.yml` | The gate — runs the engine on every PR, uploads SARIF, fails the run on `BLOCK` |
| `render.yaml`, `Procfile` | Deploy config for `trustgate-api` on Render |
| `screenshots/` | Demo images for the README — **empty** |
| `trustgate/demo_target/` | Labelled corpus, one planted defect per case — **built, never run against a live checker** |
| `trustgate/bench/` | Ground truth (`cases.json`) and the measurement runner — **built; reports `INCOMPLETE`** |

## Not built

This is a 48-hour hackathon build that ran out of time. These are the pieces that do not
exist, stated plainly because a gate that overstates its own coverage is the exact failure
mode this project exists to catch.

| Missing | Consequence |
|---|---|
| **A green run of the gate** | The workflow **has executed on GitHub** and the last 5 runs all **failed**. An earlier pair of failures was a config bug, not a finding: `.github/gitleaks.toml` allowlisted the two planted fixtures with `^`-anchored regexes while the engine scans `--workspace ..`, so the paths arrived as `../backend/...` and the allowlist matched nothing. The scanner then found TrustGate's own deliberately planted fakes and the gate blocked them. Fixed in `a04438b`. The SARIF upload step carries `if: always()` and did run, but **no run has yet completed green**, so the Code Scanning path is still unproven end to end. CI is **UNVERIFIED** — a `tests` job running the 108-test suite was added on this branch and has not executed yet. |
| **OSV-Scanner** (dependencies) | No CVE detection. Blocked: OSV emits no line number, and `Finding.line` requires one. See `trustgate/docs/SYSTEM_LEDGER.md` K13. |
| **A deployment of the dashboard** | `dashboard/` is built and merged — `npm ci` reports 0 vulnerabilities and `npm run build` succeeds — but **nothing is deployed**. No Vercel deployment has happened, so `vercel.json` at the root still has nothing to build. |
| **Labelled corpus** | The corpus and its runner are built (`trustgate/demo_target/`, `trustgate/bench/`), 9 of 10 fixtures planted. **No false-positive rate is claimed** — the runner still reports `OVERALL: INCOMPLETE - 7 of 7 checkers did not complete`, because the six LLM checkers cannot run without `WATSONX_API_KEY` or `GROQ_API_KEY`. `secrets` alone is measured, on a **1-case sample**, which is too small to publish as a rate. One case (`issue-05`) is unplanted: a reachable `pickle.loads` fixture was declined by the sandbox classifier and needs a human decision. |
| **Bench coverage for two checkers** | No case in `trustgate/bench/cases.json` names `security_reviewer` or `spec_conformance` as `expected_checker`, so **neither is measured at all** — the corpus cannot yet say whether they work. Recorded explicitly in `tests/test_bench_scoring.py` so the roster and the corpus cannot drift apart unnoticed. |
| **Determinism harness** | The same diff has not been run 20× to prove the verdict is stable. |
| **A clean `PASS`** | `secrets` now runs against the real gitleaks binary and **does** produce a real finding — see the checkers table. A clean `PASS` is still not demonstrable, because a run in which any checker degraded is `REVIEW` by design, and no run has had all seven checkers complete. |
| **A deployment of `vercel.json`** | The backend **is** deployed — see [Live deployment](#live-deployment). `vercel.json` is the only deploy config with nothing behind it. |

**The roster is 7 of 8, and exactly 1 of the 7 has produced a real finding.** `secrets` runs
the real gitleaks binary and blocks a planted credential with a cited `file:line`; `authz`,
`injection`, `prompt_injection`, `business`, `security_reviewer`, and `spec_conformance` have
never run against a live model. The six LLM checkers still degrade to `REVIEW` with no provider
credential, and a degraded run is never a `PASS` — so a clean `PASS` remains undemonstrated, and
that is stated here rather than papered over.

What *is* built and tested (**108 tests**): the deterministic adjudicator, the fail-closed
contract including its two closed bypasses, the schema-level evidence guarantees, the
quote-must-exist-in-the-diff check, a run log that round-trips a verdict through disk, a SARIF
converter validated against both the OASIS schema and GitHub's stricter requirements, the
benchmark's scoring rules including the bench/engine roster parity guard, and a CLI that runs
them. `python integration_test.py` passes: API health, runs directory, verdict endpoint, and the
gate invariants (6 invariants hold, 5 actions pinned) — `Status: ALL CHECKS PASSED`.

## Results

**One measured result, and it is too small to be a rate.**

| Checker | Cases | TP | FP | FN | Verdict |
|---|---|---|---|---|---|
| `secrets` | **1** | 1 | 0 | 0 | `BLOCK` on the planted `issue-02-hardcoded-key` fixture |

Reproduce it with `GITLEAKS_BIN="$PWD/.tools/gitleaks.exe" python ../bench/run_benchmark.py` from
`trustgate/backend`. The runner is the harness; `trustgate/bench/cases.json` is the ground truth.

`n = 1`. One case cannot support a precision or false-positive claim, and the runner says so —
it reports `OVERALL: INCOMPLETE` and refuses to print a rate for the six checkers that never
ran. A single correct detection is evidence that the pipeline works end to end, not evidence
that the checker is accurate. The 9 other planted fixtures are all owned by the LLM checkers,
so they cannot be scored until a `WATSONX_API_KEY` or `GROQ_API_KEY` exists.

`security_reviewer` and `spec_conformance` are **unmeasured**: no case in `cases.json` names
either as `expected_checker`, so the corpus says nothing about whether they work at all. The
other four LLM checkers are measurable-in-principle — cases exist for them, they have simply
never run against a live model.

Two scoring bugs were found and fixed while producing this, both of which had been making the
runner report a plausible-looking wrong figure — a `precision 0.50` for a checker that found the
defect exactly right, and a rule that made every case unscorable whenever any checker degraded.
Both are pinned by `tests/test_bench_scoring.py`. They are recorded here because a measurement
harness that quietly miscounts is worse than one that reports nothing.

False-positive rate, per-checker precision and recall, p50/p95 latency, and cost per PR will
appear here once they have been measured, along with the harness that reproduces them. Any
number here without a reproducible run behind it would be fabricated, and this project does
not publish fabricated numbers — see Rule 00 in [`.bob/rules/`](trustgate/.bob/rules/00-authenticity.md).

## Working with TrustGate

Any AI agent can pick this project up cold:

> Read `trustgate/docs/AI_CONTEXT.md`, `trustgate/docs/PROJECT_ROADMAP.md`, and `trustgate/docs/SYSTEM_LEDGER.md`. Confirm you
> understand the architecture, the strict rules, and the active phase before we begin.

The project is built by six people in 48 hours, and the governance files are maintained
seriously enough that a new agent — or a new human — can recover the exact technical state
in under two minutes.

## Team

Six people, 48 hours. **Rows B and E are filled from git authorship** — the two workstreams with
commits attributable to a named author. The rest stay `_unassigned`: every one of the 14 commits
on `main` is authored by Ammar Zia, so there is no repository evidence naming a separate owner for
them, and a name written here that nobody owns would be a fabrication in the one document judges
read. Replace them with the real names before submitting.

| # | Member | Workstream | Focus |
|---|--------|------------|-------|
| A | _unassigned_ | `trustgate/backend/app/llm/` | Provider client — watsonx.ai primary, Groq fallback, strict schema enforcement, retry, cache-by-input-hash |
| B | Malahil Ghauri | `trustgate/backend/app/checkers/` | The `prompt_injection` checker and its tests |
| C | _unassigned_ | `trustgate/backend/app/adjudicator.py`, `schemas.py`, `tests/` | The verdict path and the proof |
| D | _unassigned_ | `.github/workflows/`, `sarif.py` | The gate and the Code Scanning upload |
| E | Areeba Ghaffar | `dashboard/` | React/Vite UI — **built and merged from PR #2; not deployed** |
| F | _unassigned_ | `trustgate/demo_target/` + `trustgate/bench/` | Labelled corpus and the measurement runner — **built; first measurement blocked on K12** |

The workstream column is real: it is the Phase 3 split in `trustgate/docs/PROJECT_ROADMAP.md`, and
one of the six is unstarted — `deps`.

---

**Team of 6 · engine core and gate built, last 5 gate runs red and no run green yet · submissions close Sun Sep 27 2026, 15:00 UTC**
