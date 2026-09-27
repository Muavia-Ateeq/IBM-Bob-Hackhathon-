# AI_CONTEXT.md — The Constitution

> Single source of truth for TrustGate. Read this at the start of every session.
> Update it when architecture changes. Never let it drift from the code.

---

## Project Identity

| Field | Value |
|-------|-------|
| **Name** | TrustGate |
| **Event** | IBM Bob 2.0 Hackathon — lablab.ai, online, Sept 25–27 2026 |
| **Deadline** | Submissions close **Sun Sep 27 2026, 15:00 UTC** |
| **Type** | Intended three-service monorepo: Python/FastAPI verdict engine + React/Vite dashboard + GitHub Actions gate. All three exist. |
| **Team** | 6 |
| **Domain** | Application security — pre-merge pull request risk gating |
| **Core Purpose** | Run security checkers in parallel against a pull request diff, merge their findings through a deterministic adjudicator, and emit one verdict — `PASS`, `REVIEW`, or `BLOCK` — with cited evidence |
| **Version** | `__version__ = "0.1.0"` in `backend/app/config.py`, single source of truth. It is what the FastAPI app title reports *and* what `sarif.py` writes to `tool.driver.version`. Previously SARIF emitted a hardcoded `"0.0.0"` on every upload ever made — that is fixed, and a second hardcoded version string is a defect |
| **Status** | Engine core built and tested, runnable from the CLI. All seven checkers exist; none has produced a real finding yet. The SARIF converter, the GitHub gate, the PR-comment formatter, and a four-check smoke test are built but **have never run live** — no workflow execution, no accepted upload, no comment posted. The dashboard is built. See `README.md` for the current build state and `SYSTEM_LEDGER.md` for what is unverified. |

### Naming constraints (verified, not hypothetical)

`TrustGate` is an **existing name in the security space**. Verified prior uses:

- `NeuralTrust/TrustGate` — Apache-2.0 Go AI/LLM gateway
- `trustgate` on PyPI (Cohorte-ai) — AI reliability certification, ships a GitHub Actions deploy gate
- `bytrustgate.com` — identity verification / KYC-AML company
- `TrustGate™ Network` — registered trademark, device-free WiFi security
- `msctrustgate.com` — Malaysian licensed CA, operating since 1999
- `trustgateit.com` — Microsoft security consultancy

Consequences, binding on this project:

1. **NEVER** run `pip install trustgate` or add it as a dependency. The name is taken on PyPI.
2. **NEVER** claim trademark or imply the mark `™`.
3. Acceptable for a hackathon submission. **Revisit naming before any public release.**

---

## Tech Stack

> Version numbers are deliberately absent. Exact versions get pinned into lockfiles at
> Phase 2 (Tier 2 approval). Writing version numbers here before they are installed
> would be an unverified claim.

### Verdict engine — `backend/`

| Technology | Rationale |
|------------|-----------|
| Python 3.11+ | Team fluency; native async for 7-way parallel fan-out |
| FastAPI | Async-native HTTP layer; the Actions gate and the dashboard are both HTTP clients |
| Pydantic v2 | Enforces the checker output schema **at the boundary** — an LLM that returns malformed JSON is rejected before it reaches the adjudicator |
| httpx | Async HTTP client used underneath the Groq SDK; connection pooling matters at 7 concurrent calls. TrustGate does not construct an `AsyncClient` itself |
| IBM watsonx.ai SDK (`ibm-watsonx-ai` 1.7.2) | **Primary LLM inference.** On-theme for an IBM event, and its models carry IBM's indemnification, which third-party models do not |
| Groq SDK (`groq`) | **Fallback inference.** OpenAI-compatible surface, low latency; it is second in the chain, not the default |
| SQLite (stdlib `sqlite3`) | Intended for the verdict log. A single file is swappable for Postgres later; do not add a DB server during a 48h build. **Not built** — `runlog.py` JSON records are what exists. |

### Dashboard — `dashboard/`

| Technology | Rationale |
|------------|-----------|
| React + Vite | Team fluency; fastest scaffold-to-demo path |
| TypeScript | The verdict and finding types are shared conceptually with the engine; types prevent UI drift from the API contract |
| No UI framework | Hand-rolled components against the design tokens below. A component library is a dependency we do not need for one screen. |

### Gate — `.github/workflows/`

| Technology | Rationale |
|------------|-----------|
| GitHub Actions | Runs on `pull_request`; produces the required status check that branch protection keys on |
| SARIF 2.1.0 | Native GitHub Code Scanning format. Findings render inline on the diff |
| `github/codeql-action/upload-sarif` | Uploads findings. Requires `security-events: write` permission |

**State: written and unit-tested, never executed on GitHub.** `tests/test_gate.py` pins the
BLOCK-grep pattern against the CLI's own output so a format change cannot silently disable
blocking, and `tests/test_sarif.py` validates the report against both the OASIS schema and
GitHub's stricter required table. What is *not* verified: that the workflow runs at all, and
that Code Scanning accepts the upload. UNVERIFIED — pushing any branch and reading the Actions
tab is what verifies it.

### Deterministic scanners (checker tier 1)

| Tool | Role | Verified fact |
|------|------|----------------|
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Secret detection | Deterministic regex + entropy. The workflow installs a pinned release tarball and verifies its SHA-256 rather than using an action — the action's runtime was not verified, and an unverified action in a security gate is the same risk as an unverified binary. Requires `fetch-depth: 0`. MIT |
| [OSV-Scanner](https://github.com/google/osv-scanner) v2.x | Dependency vulnerabilities | Apache-2.0. Supports pip and npm. Has call analysis to cut false positives. v2.5.1 published Aug 2026 |

**Why deterministic tools exist in an "AI checker" product:** a leaked API key and a known CVE are *facts with answers*. Spending an LLM call to rediscover them is slower, costlier, and less accurate than a scanner built for exactly that job. The LLM budget goes to the classes of bug that have no lookup table.

---

## Architecture

### Directory hierarchy

```
/                                    # REPO ROOT — read by path from here, so it cannot move:
├── AGENTS.md                  #   pointer to trustgate/docs/AGENTS.md, for root-loading tools
├── .github/workflows/trustgate.yml  # the gate — written, NEVER RUN (ledger K20)
├── .github/gitleaks.toml      #   gate-only allowlist; outside the scan target on purpose (3a)
├── render.yaml                 # Render blueprint — the API is live at https://trustgate-api-ehib.onrender.com; VERIFIED 2026-09-27, /api/health returned {"ok":true}
├── Procfile                    #   same start command, for any Procfile host
├── vercel.json                 # Vercel SPA config for dashboard/ — never deployed
└── trustgate/                  #   everything else lives here
    ├── docs/                     # Governance — all of it, one directory
    │   ├── AI_CONTEXT.md           # This file — constitution
    │   ├── PROJECT_ROADMAP.md      # Phases, one ACTIVE at a time
    │   ├── SYSTEM_LEDGER.md        # Memory — state, file history, next actions
    │   ├── AGENTS.md               # Portable agent rules (all tools)
    │   ├── WEDGE.md                # Positioning, demo script, falsifiable claims
    │   └── CONTRACT.md             # The HTTP surface the engine writes
    ├── .bob/rules/            # Bob-native rules (IBM Bob IDE only)
    │   ├── 00-authenticity.md
    │   ├── 01-planning-governance.md
    │   ├── 02-session-continuity.md
    │   └── 03-scope-control.md
    ├── screenshots/           # Demo images — 10 files
    ├── runs/                      # Run records — gitignored; see the runlog note below
    ├── backend/                    # Python/FastAPI verdict engine — BUILT
    │   ├── app/
    │   │   ├── main.py            # CLI entry point; CHECKER_MODULES, build_app()
    │   │   ├── checkers/          # One module per checker. See roster below.
    │   │   │   ├── base.py        # Checker protocol, timeout, asyncio.gather fan-out
    │   │   │   ├── semantic.py    # The shared Tier 2 LLM checker
    │   │   │   ├── secrets.py     # Tier 1 — Gitleaks wrapper — BUILT, never run
    │   │   │   ├── authz.py       # Tier 2 — LLM
    │   │   │   ├── injection.py   # Tier 2 — LLM
    │   │   │   ├── prompt_injection.py # Tier 2 — LLM
    │   │   │   ├── business.py    # Tier 2 — LLM
    │   │   │   ├── security_reviewer.py # Tier 2 — LLM
    │   │   │   ├── spec_conformance.py  # Tier 2 — LLM
    │   │   │   └── CONTRIBUTING.md # The contract every checker author implements
    │   │   ├── adjudicator.py     # Deterministic verdict. No LLM in this path.
    │   │   ├── llm/               # client.py (Groq, FallbackProvider, build_provider),
    │   │   │                      # watsonx_client.py (WatsonxProvider), schemas.py
    │   │   ├── runlog.py          # runs/*.json — write records, recompute a verdict from disk
    │   │   ├── comment.py         # VerdictRecord → PR comment. Local, NOT wired into the gate
    │   │   ├── config.py          # Settings, env-overridable, and `__version__`
    │   │   ├── sarif.py           # Finding → SARIF 2.1.0 — BUILT, never uploaded
    │   │   └── schemas.py         # Pydantic request/response contracts
    │   ├── integration_test.py    # 4-check smoke test: health, run records, verdict, gate
    │   ├── tests/                 # 108 passing across 11 files
    │   ├── requirements.txt       # Pinned installed set
    │   └── pyproject.toml         — NOT BUILT
    ├── demo_target/           # Labelled corpus — BUILT, never run against a live checker
    │   ├── base/                  # The clean app every fixture is a one-defect copy of
    │   └── issue-NN-*/            # 10 planted defects; 2 have no owning checker, 2 are disputed
    ├── bench/                 # Ground truth + the measurement runner
    │   ├── cases.json             # Pydantic-validated; expected_checker is null where none owns it
    │   └── run_benchmark.py       # Reuses the shipped CLI. INCOMPLETE until K12 + K14 close
```

`dashboard/` sits at the **repo root**, not under `trustgate/`: React/Vite/TypeScript, integrated
from PR #2. It is the one screen plus an approval-override component; `npm ci` reports 0
vulnerabilities and `npm run build` succeeds. UNVERIFIED — it has never been deployed; the
`vercel.json` at the root is a config file, not a deployment.

The root `README.md` is the only README in the repo. There is no `trustgate/AGENTS.md` — the root
`AGENTS.md` is the pointer file and the rules live at `trustgate/docs/AGENTS.md`.

`routes/` was planned and never built as a package. `build_app()` in `main.py` carries the three
routes it needs — `/api/health`, `/api/pr/{pr}/verdict`, and `/api/runs` — declared inline,
because a package for three handlers is a directory with no reason to exist yet. There is no
`POST /analyze` and no HTTP analysis entry point, so `schemas.AnalyzeRequest` — which used to
describe that missing route — has been deleted rather than left as a contract nothing fulfils.
The verdict and runs routes are `def`, not `async def`, so the run-log glob runs in Starlette's
threadpool rather than blocking the event loop.

`/api/runs` lists every run record on disk. It is unauthenticated and the app allows every
origin, and a run record carries `Finding.evidence` verbatim — for the secrets checker, a
fragment of a real credential. It is demo-only until it is gated. See `CONTRACT.md`.

### The checker roster — seven, deliberately heterogeneous

| # | Checker | Tier | Detects | Method |
|---|---------|------|---------|--------|
| 1 | `secrets` | 1 | Hardcoded credentials, API keys, private keys | Gitleaks |
| 2 | `authz` | 2 | Missing authorization, IDOR, privilege escalation, broken access control | LLM |
| 3 | `injection` | 2 | SQL/command injection, XSS, SSRF, unsafe deserialization | LLM |
| 4 | `prompt_injection` | 2 | Untrusted text concatenated into a model instruction; agent-directed repo content | LLM |
| 5 | `business` | 2 | Business-logic flaws, race conditions, crypto misuse, validation gaps | LLM |
| 6 | `security_reviewer` | 2 | Broad security review pass over the diff — secrets, injection, missing auth, unsafe deserialization | LLM |
| 7 | `spec_conformance` | 2 | Code measured against the product requirements themselves (password hashing, rate limiting, no hardcoded keys, no debug mode) | LLM |

`security_reviewer` and `spec_conformance` were implemented by M. Muavia from his IBM Bob
subagent prompts in `trustgate/docs/muavia_prompts/`, and both are wired to the shared
`SemanticChecker` rather than each carrying their own provider plumbing. `app.main.CHECKER_MODULES`
is the single roster tuple; `trustgate/bench/run_benchmark.py` derives its checker list from it
and a parity test in `tests/test_bench_scoring.py` fails if the two ever diverge.

Tiers 1 and 2 fail in different ways, and that is the point. Tier 1 is **precise and dumb** — it cannot reason about intent, so it does not try. Tier 2 is **reasoning and imprecise** — it understands that "this handler reads `user_id` from the query string and never checks ownership" is a vulnerability, but it will sometimes be wrong. The adjudicator must be built for that asymmetry.

**Not in the roster: `deps`.** OSV-Scanner is a planned Tier 1 checker for known CVEs and
`Settings.osv_scanner_bin` names its binary, but no checker module wraps it — it is blocked
because the OSV-Scanner JSON carries no line number, and a finding without one cannot cite
evidence (ledger K13). `bench/cases.json` records the resulting holes as `no_checker_reason`
rather than leaving them unexplained.

### Design patterns

| Pattern | Where | Description |
|---------|-------|-------------|
| Protocol-based checker | `backend/app/checkers/base.py` | Every checker exposes the same async interface. Adding a checker must not touch the orchestrator — `app/main.py` `CHECKER_MODULES` is the only list. |
| Fan-out / fan-in | `backend/app/checkers/base.py` (`run_all`) | Checkers run concurrently via `asyncio.gather`. Wall-clock is the slowest checker, not the sum. **Seven exist.** |
| Deterministic adjudicator | `backend/app/adjudicator.py` | Pure function, no I/O, no LLM. Given the same findings it always returns the same verdict. Testable without network. |
| Schema-at-the-boundary | `backend/app/llm/` + `checkers/semantic.py` | Pydantic validates every LLM response, and a finding whose evidence is not a verbatim quote from the diff is rejected outright. A malformed response becomes a checker *error*, never a silent finding. |
| Run log | `backend/app/runlog.py` | One JSON record per checker per run under `runs/`, re-readable into a verdict. `input_hash` is a SHA-256 over the **run records**, not over verdict inputs. A record that fails to parse has no readable `pr`, so it cannot be attributed to any PR: `load_results` returns a plain count of unreadable files, never their names, and the verdict reason says `"; N unattributable unreadable run file(s)"`. Naming them would leak another PR's run filename — which embeds its run_id and checker name — into this PR's job summary. Append-only SQLite is **NOT BUILT**, so there is no tamper-evidence. `/trustgate/runs/` is gitignored; run records carry verbatim evidence, and for the secrets checker that is a fragment of a real credential. |

### File boundaries — hard rules

- `routes/` **never** imports from `checkers/` internals. It calls the orchestrator. The three
  routes currently live inline in `main.build_app()`; that is where a fourth goes, not into a
  package that exists to hold three handlers.
- `adjudicator.py` **never** imports `llm/`. This is what makes it deterministic. If you need a model in the verdict path, the verdict is no longer reproducible — stop and reconsider the design.
- `checkers/` modules **never** import each other. Checkers are independent experts; a checker that trusts another checker's opinion is no longer an independent signal.
- `dashboard/` **never** holds an LLM key of any kind — no `GROQ_API_KEY`, no `WATSONX_API_KEY`. All inference lives server-side in `backend/`.

---

## Design Tokens

Verdict color is the most important signal in the product. It is also the most common accessibility failure: red/amber/green alone is unreadable for roughly 1 in 12 men with red-green color vision deficiency.

**Rule: every verdict is communicated by color + icon + text label, always together.** Color is never the sole carrier of meaning.

| Token | Light | Dark | Icon | Label |
|-------|-------|------|------|-------|
| `--verdict-block` | `#DC2626` | `#F87171` | `octicon-x-circle-fill` | `BLOCK` |
| `--verdict-review` | `#B45309` | `#FBBF24` | `octicon-alert-fill` | `REVIEW` |
| `--verdict-pass` | `#15803D` | `#4ADE80` | `octicon-check-circle-fill` | `PASS` |
| `--verdict-unknown` | `#475569` | `#94A3B8` | `octicon-question-fill` | `UNKNOWN` |

`UNKNOWN` exists because a checker that errored must never be silently rendered as clean.

**`UNKNOWN` is a dashboard display state, not a fourth verdict.** The engine's verdict enum is
exactly `PASS | REVIEW | BLOCK` (`backend/app/schemas.py`), and a run containing an incomplete
checker yields `REVIEW` — per D5 below and `WEDGE.md`. The dashboard renders `UNKNOWN` when a
`REVIEW` verdict carries degraded checkers, so the operator can see *why* it is not a pass.

The two rules are not in conflict; they operate at different layers. The verdict is what
gates the merge. `UNKNOWN` is what the operator sees. **Do not add `UNKNOWN` to the
`Verdict` enum** — that would change the branch-protection contract mid-build, and the
`adjudicator.py` fail-closed path already implements the stricter reading.

### Surfaces and text

| Token | Light | Dark |
|-------|-------|------|
| `--bg-canvas` | `#F8FAFC` | `#0B1120` |
| `--bg-surface` | `#FFFFFF` | `#111827` |
| `--border` | `#E2E8F0` | `#1F2937` |
| `--text-primary` | `#0F172A` | `#F1F5F9` |
| `--text-secondary` | `#475569` | `#94A3B8` |

### Severity (per finding, orthogonal to verdict)

`critical` → `--verdict-block` · `high` → `#EA580C` / `#FB923C` · `medium` → `--verdict-review` · `low` → `--text-secondary` · `info` → `--text-secondary`

### Typography

| Role | Family | Notes |
|------|--------|-------|
| UI | Inter | Tabular numerals on all metrics — verdict counts must not jitter as they update |
| Code, diffs, evidence | JetBrains Mono | Evidence is quoted source; it must be monospaced and never reflowed |

### Spacing

4px base scale: `4 · 8 · 12 · 16 · 24 · 32 · 48`. Checker cards are separated by 16px; the verdict banner owns 32px.

### Motion

- Verdict banner: 150ms ease-out fade + 4px rise. Fast enough to feel instant.
- Checker grid: staggered 30ms per card, capped at 200ms total. Beyond that it reads as sluggish.
- **Never** animate a verdict change with a bounce or overshoot. A security verdict is not playful.
- Respect `prefers-reduced-motion: reduce` — collapse all durations to 0ms.

---

## Strict Rules

### NEVER

- **NEVER** emit a finding without a citation: `file`, `line`, and the quoted source. An unevidenced finding is a hallucination with a severity label.
- **NEVER** let a checker error, timeout, or malformed response resolve to `PASS`. Fail-closed toward `REVIEW`. Only a fully clean, fully completed run may be `PASS`.
- **NEVER** put a model call in the adjudicator path.
- **NEVER** auto-merge a pull request. TrustGate renders a verdict; a human decides. This is a product constraint, not a missing feature.
- **NEVER** invent a metric. No fabricated latency, FP rate, benchmark, user count, or test count in the README, the UI, or the submission. If a number was not measured, it does not appear.
- **NEVER** pin a GitHub Action to `Node 20`. GitHub removed Node 20 from hosted runners entirely on **Sep 16 2026**. Such actions now fail.
- **NEVER** commit a `GROQ_API_KEY`, a `WATSONX_API_KEY`, a GitHub token, or any `.env` file.
- **NEVER** add a dependency without approval. Tier 2. See governance below.
- **NEVER** reference an API, function, or CLI flag you have not verified against current docs in this session.
- **NEVER** restructure a directory that already exists in the ledger without Tier 3 approval.
- **NEVER** `pip install trustgate`. The name belongs to someone else on PyPI.
- **NEVER** add inline comments to code. The code states what it does; `AI_CONTEXT.md` states why.

### ALWAYS

- **ALWAYS** run every checker even when an early one finds something critical. Partial results are not a verdict.
- **ALWAYS** set `temperature: 0` on every LLM call. Non-determinism in a security verdict is a defect.
- **ALWAYS** validate every LLM response against a Pydantic schema before use.
- **ALWAYS** record raw findings with a SHA-256 alongside them, so any past verdict can be reproduced and audited. Today this is `runlog.py`: one JSON record per checker per run under `runs/`, with `input_hash` a SHA-256 over those records. The append-only SQLite table described below is **not built** — do not assume it exists.
- **ALWAYS** upload SARIF with `if: always()` on the step. A scanner that exits non-zero skips its own upload without it, and the findings are silently lost.
- **ALWAYS** request `security-events: write` permission for the SARIF upload step.
- **ALWAYS** set `fetch-depth: 0` when checking out for Gitleaks — it needs full history.
- **ALWAYS** apply a per-checker timeout. A hung checker must not hang the gate.
- **ALWAYS** report the exact error message and file path when something breaks.
- **ALWAYS** reference code as `file_path:line_number`.
- **ALWAYS** update `SYSTEM_LEDGER.md` when creating or modifying a file.
- **ALWAYS** keep exactly one phase marked 🔴 ACTIVE in `PROJECT_ROADMAP.md`.

---

## Model & Tool Strategy

### Provider order: IBM watsonx.ai PRIMARY, Groq FALLBACK

**This supersedes the earlier decision that recorded Groq as the only provider.** That entry in
`SYSTEM_LEDGER.md` is left intact as history; the chain below is what the code does.

The order is a product decision, not a default: watsonx is on-theme for an IBM event and its
models carry IBM's indemnification, which third-party models do not. Groq stays in the chain
because it was the original provider and remains the fallback. UNVERIFIED — no live inference
call against either provider has been made and recorded in this repo; `tests/test_providers.py`
exercises both against stubs.

`build_provider` in `app/llm/client.py` assembles the chain from whichever credentials are
present and hands it to `FallbackProvider`.

| Order | Provider | Class | Config |
|-------|----------|-------|--------|
| 1 | IBM watsonx.ai, Granite `ibm/granite-4-h-small` | `WatsonxProvider` — `app/llm/watsonx_client.py` | `WATSONX_API_KEY`, `WATSONX_PROJECT_ID` or `WATSONX_SPACE_ID`, `WATSONX_URL`, `WATSONX_MODEL` |
| 2 | Groq `openai/gpt-oss-120b` | `GroqProvider` — `app/llm/client.py` | `GROQ_API_KEY`, `TRUSTGATE_MODEL` |

`WATSONX_PROJECT_ID` / `WATSONX_SPACE_ID` are a **new required config this project did not have
before**: `ModelInference` is keyword-only and takes no positional arguments, and it requires
`project_id` **or** `space_id`. A watsonx call with an API key and neither ID raises
`ProviderUnavailable` at construction and the chain moves to Groq rather than failing the run.

**UNVERIFIED — no IBM watsonx.ai credential has ever existed in this project, so the live call
has never been made. The code is written against the introspected 1.7.2 SDK signature and
unit-tested with stubs; a real key and project ID are required to verify it end to end.**

SDK facts, verified against the installed `ibm-watsonx-ai` 1.7.2:

- `from ibm_watsonx_ai.foundation_models import ModelInference` and `from ibm_watsonx_ai import Credentials`. `ModelInference` is **not** a top-level export of `ibm_watsonx_ai` — importing it from there raises `ImportError`. This bit an earlier draft of `watsonx_client.py`.
- `.chat()` returns no token usage, so `Completion.input_tokens` / `output_tokens` stay `0` for watsonx. Cost tracking is not built either, so nothing is published from those zeros — but a watsonx-served run has no token counts to compute cost from at all.
- `WATSONX_URL` defaults to `https://us-south.ml.cloud.ibm.com`.

`FallbackProvider` prints one stderr line per failure naming the provider and the reason, and
raises `ProviderUnavailable` carrying **all** of the reasons if every provider fails. It never
fabricates a success.

### Routing

| Purpose | Model | Why |
|---------|-------|-----|
| Tier 2 checkers (6 LLM checkers) | `ibm/granite-4-h-small` (primary) · `openai/gpt-oss-120b` (fallback) | Same schema and the same `SemanticChecker` for both — the provider swap is invisible to a checker. Strict mode guarantees a schema-valid object on the Groq side — it does **not** guarantee a non-empty `evidence` or `line >= 1`; those are enforced in `checkers/semantic.py`, because a checker that cannot be parsed is a checker that does not run. |
| Adjudicator input shaping | same | Shares the finding schema, so one Pydantic model serves both. |
| Groq model fallback | `llama-3.3-70b-versatile` | Broader general capability, but **best-effort** JSON only — requires validation + retry. **NOT BUILT** (the model ID appears nowhere in the codebase; `config.py` hardcodes one). |

### Structured output — the constraint that shapes the design

*(This section is about the Groq provider, which is where the structured-output mode flags live.
The watsonx provider is a different SDK surface; its behaviour is covered by the UNVERIFIED note
above.)*

Groq exposes `response_format={"type": "json_schema", "json_schema": {...}}` in two modes:

- **Strict** (`strict: true`) — constrained decoding, output always matches the schema, never errors. Requires all fields `required` and `additionalProperties: false`. Supported on a limited model set.
- **Best-effort** (`strict: false`, default) — attempts the schema, may occasionally deviate.

**Verified 2026-09-25** against `console.groq.com/docs/structured-outputs#supported-models` (ledger K1, closed): strict mode supports `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `qwen/qwen3.8-27b`. The docs pages are not fully consistent with each other — one omits the Qwen entry. Re-read the page before changing the model; do not hardcode this list from memory.

Hard limitations, both verified:

- **Streaming is not supported** with Structured Outputs. All inference is non-streaming.
- **Tool use is not supported** with Structured Outputs. Checkers are prompted, not tool-equipped.

### Within-model fallback — **step 1 only is implemented**

This is a different axis from the provider chain above. The provider chain (watsonx → Groq) is
**implemented**. The chain between *models on the same provider* is not:

1. `openai/gpt-oss-120b`, strict mode — **implemented**, a single uncaught call
2. `openai/gpt-oss-120b`, best-effort + Pydantic validation + 1 retry — **NOT BUILT**
3. `llama-3.3-70b-versatile`, best-effort + Pydantic validation + 1 retry — **NOT BUILT** (the model ID appears nowhere in the codebase; `config.py` hardcodes one)
4. **Checker records an error → verdict degrades to `REVIEW`.** Never `PASS`. — **implemented and tested**, but via `checkers/base.py`'s blanket exception handler and `adjudicator.py`, not via any designed recovery.

So today the first hiccup on any LLM checker that survives the provider chain — a 429, a
malformed body — permanently degrades that checker for that run. There is no retry and no
recovery. The honest summary is that steps 2 and 3 do not exist and step 4 holds for a different
reason than the one intended here.

### Concurrency and cost

- Checkers run via `asyncio.gather` — one provider instance is shared across all of them, not one per checker. **Seven checkers exist.** There is no `httpx.AsyncClient` in this codebase; each SDK owns its own HTTP client and TrustGate neither creates nor closes it.
- **Cache by input hash.** Identical diff → identical findings. Key on SHA-256 of (repo, base SHA, head SHA, checker version). **NOT BUILT.** `VerdictRecord.input_hash` exists but hashes the run *records* after the model calls were already paid for, and nothing consults it before invoking a checker. Re-running on an unchanged PR still burns full quota.
- Per-checker timeout: 30s — **implemented, not exercised.** `base.execute` wraps each
  checker in `asyncio.wait_for` and converts a `TimeoutError` into a `status=TIMEOUT`
  result. The only test touching timeouts fabricates a `TIMEOUT` `CheckerResult` and asserts
  the adjudicator's reaction; nothing in `tests/` triggers a real one. `SYSTEM_LEDGER.md`
  K-unverified is right and this line was the optimistic one.
- Whole-run budget: 90s — **NOT BUILT.** `Settings.run_budget_s` is read by nothing; `main.py` measures elapsed only to print it. A PR gate that takes longer than a coffee break gets disabled by its users.
- **Cost tracking is NOT BUILT.** `VerdictRecord.cost_usd` has exactly one assignment, `runlog.py` → `None`. The token counts that would feed it are gathered in `llm/client.py` and discarded in `checkers/semantic.py`. No cost number may be published.

### Benchmark contract

`bench/run_benchmark.py` reads its roster from `app.main.CHECKER_MODULES` rather than a
hand-copied tuple — the copy silently fell behind the engine once already, scoring a checker
zero without saying so. A parity test in `tests/test_bench_scoring.py` fails if the two diverge.

A checker that did not run gets no rate. A real run today prints
`OVERALL: INCOMPLETE - 7 of 7 checkers did not complete` and claims no precision and no recall
at all. That is the fail-closed contract working, not a failure to fix: a benchmark that printed
a score with the entire roster missing would be the exact fail-open this project exists to not
ship.

### Tool execution boundaries

- The engine executes **only** the pinned Gitleaks binary, via `subprocess` with an argument list — never `shell=True`. OSV-Scanner is not executed: no checker wraps it yet (see the roster note above).
- Scan targets are resolved from the GitHub-provided checkout path and passed as `cwd`. Scanner input is never interpolated into a command string.
- The engine's only outbound network access is to the configured LLM provider endpoints — watsonx.ai and Groq, in that order.
- No checker may read anything outside the checked-out PR workspace.

---

## i18n & Localization

| Property | Value |
|----------|-------|
| Languages | `en` only for v1 |
| Scripts | Latin |
| Direction | **LTR** |
| String handling | Intended: a single `strings.ts` in `dashboard/`, no inline literals in JSX. **NOT BUILT** — the file does not exist and the shipped components use inline literals. Recorded as a known gap, not a description of the code. |
| Dates/times | UTC everywhere, formatted at the edge. A verdict log spanning timezones is unauditable. |
| RTL | Not supported in v1. If a language requiring RTL is added, `dir="auto"` belongs on the finding-evidence container, where quoted source may contain RTL text regardless of UI language. |

Adding a language is **out of scope** for this build. Recorded so it is a known omission, not an oversight.

---

## Global Authenticity Rule

**Every technical claim in this repository must be verifiable.**

1. **No hallucinated APIs.** Do not reference a function, parameter, CLI flag, model ID, or header that was not read in current documentation during this session. If you did not read it, you do not know it.
2. **No invented data.** Every number in the README, dashboard, or submission — latency, precision, recall, false-positive rate, cost, test count — must be traceable to a run that actually happened. Unmeasured numbers are omitted, not estimated.
3. **Cite external claims.** Any claim resting on a third party gets a URL: the scanner's repo, the model card, the IBM docs page. Academic claims get a DOI or arXiv ID. This build makes no academic claims, so that clause is dormant here.
4. **Prefer "unverified" to "probably".** If a fact cannot be confirmed, write `UNVERIFIED — <what would verify it>`. An honest gap costs an hour; a fabricated API costs the demo.
5. **The system must not fake its own success.** If a checker fails, TrustGate says so. A security product that hides its failures is the exact failure mode it exists to catch.

Precedent, recorded so it is not repeated: during planning, the name `TrustGate` and several alternative names were checked and found to collide with existing products. The alternate strategy "differentiate via shadow-mode calibration" was also checked and found to be already shipped by a live competitor. Both were caught by verification instead of by assumption. That is the rule working.

---

## Session Management & Planning Governance

### 1. Planning Governance — "Hackathon Mode"

This project runs on a 48-hour clock. A policy of "never touch a file without approval" would consume the build. The tiered equivalent enforces the same boundary where it matters and stays out of the way where it does not.

| Tier | Action | Required approval |
|------|--------|-------------------|
| **0** | Reads, search, `git status`/`log`/`diff`, running builds, tests, scanners | None |
| **1** | Editing a file already listed in the active phase's deliverables table | None — **but batched**: one approved plan authorizes all its Tier 1 edits. No per-file confirmation |
| **2** | New dependency · new top-level directory · config or schema change · **any deletion** · edits to `AI_CONTEXT.md` / `PROJECT_ROADMAP.md` / `SYSTEM_LEDGER.md` · `git commit` / `git push` | One-line confirm |
| **3** | Architecture change · phase transition · deploy | Full plan, then approval |

Strict mode (every edit needs approval) is available on request for any phase where the risk warrants it.

### 2. Boot Sequences

**Full Boot** — new session, or after a context reset:
> Read `AI_CONTEXT.md`, `PROJECT_ROADMAP.md`, and `SYSTEM_LEDGER.md`. Confirm you understand the architecture, the strict rules, and the active phase before we begin working.

**Quick Boot** — resuming, context still warm:
> Read `AI_CONTEXT.md` and `SYSTEM_LEDGER.md`, then resume from where we left off.

### 3. Close-Out — end of session
> Update `PROJECT_ROADMAP.md` and `SYSTEM_LEDGER.md` to reflect every completed task, file created or modified, and updated metrics. Then state what the next session must pick up first.

A session that ends without a ledger update is a session whose knowledge is lost.
