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
| **Type** | Intended three-service monorepo: Python/FastAPI verdict engine + React/Vite dashboard + GitHub Actions gate. The engine and the gate exist; `dashboard/` does not. |
| **Team** | 6 |
| **Domain** | Application security — pre-merge pull request risk gating |
| **Core Purpose** | Run security checkers in parallel against a pull request diff, merge their findings through a deterministic adjudicator, and emit one verdict — `PASS`, `REVIEW`, or `BLOCK` — with cited evidence |
| **Status** | Engine core built and tested, runnable from the CLI. Four of five checkers exist; none has produced a real finding yet. The SARIF converter, the GitHub gate, the PR-comment formatter, and a four-check smoke test are built but **have never run live** — no workflow execution, no accepted upload, no comment posted. The dashboard is **not built**. See `README.md` for the current build state and `SYSTEM_LEDGER.md` for what is unverified. |

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
| Python 3.11+ | Team fluency; native async for 5-way parallel fan-out |
| FastAPI | Async-native HTTP layer; the Actions gate and the dashboard are both HTTP clients |
| Pydantic v2 | Enforces the checker output schema **at the boundary** — an LLM that returns malformed JSON is rejected before it reaches the adjudicator |
| httpx | Async HTTP client for Groq; connection pooling matters at 5 concurrent calls |
| Groq SDK (`groq`) | Primary LLM inference. OpenAI-compatible surface, low latency — the property that makes 5 parallel checkers feel instant |
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
/
├── AI_CONTEXT.md              # This file — constitution
├── PROJECT_ROADMAP.md         # Phases, one ACTIVE at a time
├── SYSTEM_LEDGER.md           # Memory — state, file history, next actions
├── AGENTS.md                  # Portable agent rules (all tools)
├── .bob/rules/                # Bob-native rules (IBM Bob IDE only)
│   ├── 00-authenticity.md
│   ├── 01-planning-governance.md
│   ├── 02-session-continuity.md
│   └── 03-scope-control.md
├── backend/                    # Python/FastAPI verdict engine — BUILT
│   ├── app/
│   │   ├── main.py            # CLI entry point; build_app() is the lazy FastAPI factory
│   │   ├── checkers/          # One module per checker. See roster below.
│   │   │   ├── base.py        # Checker protocol, timeout, asyncio.gather fan-out
│   │   │   ├── semantic.py    # The shared Tier 2 LLM checker
│   │   │   ├── secrets.py     # Tier 1 — Gitleaks wrapper — BUILT, never run
│   │   │   ├── authz.py       # Tier 2 — LLM
│   │   │   ├── injection.py   # Tier 2 — LLM
│   │   │   ├── business.py    # Tier 2 — LLM
│   │   │   ├── deps.py        # Tier 1 — OSV-Scanner — NOT BUILT (blocked, ledger K13)
│   │   │   └── CONTRIBUTING.md # The contract every checker author implements
│   │   ├── adjudicator.py     # Deterministic verdict. No LLM in this path.
│   │   ├── llm/               # Groq client (strict mode), FINDING_SCHEMA
│   │   ├── runlog.py          # runs/*.json — write records, recompute a verdict from disk
│   │   ├── comment.py         # VerdictRecord → PR comment. Local, NOT wired into the gate
│   │   ├── config.py          # Settings, env-overridable
│   │   ├── sarif.py           # Finding → SARIF 2.1.0 — BUILT, never uploaded
│   │   ├── store.py           # SQLite verdict log — NOT BUILT; runlog.py is what exists
│   │   └── schemas.py         # Pydantic request/response contracts
│   ├── integration_test.py    # 4-check smoke test: health, run records, verdict, gate
│   ├── tests/                 # 79 passing across 8 files
│   ├── requirements.txt       # Pinned installed set
│   └── pyproject.toml         — NOT BUILT
├── demo_target/               # Labelled corpus — BUILT, never run against a live checker
│   ├── base/                  # The clean app every fixture is a one-defect copy of
│   └── issue-NN-*/            # One planted defect each; 3 have no checker, 2 are disputed
├── bench/                     # Ground truth + the measurement runner
│   ├── cases.json             # Pydantic-validated; expected_checker is null where none owns it
│   └── run_benchmark.py       # Reuses the shipped CLI. INCOMPLETE until K12 + K14 close
├── dashboard/                 # React/Vite — NOT BUILT
│   └── src/
│       ├── components/        # VerdictBanner, FindingList, CheckerGrid, EvidencePanel
│       ├── lib/               # API client, verdict token mapping
│       └── types.ts           # Mirrors backend/app/schemas.py
├── .github/workflows/
│   └── trustgate.yml          # The gate — BUILT, never executed on GitHub
├── render.yaml · Procfile · vercel.json   # Deploy config, written, never deployed
└── README.md
```

`routes/` was planned and never built as a package. `build_app()` in `main.py` carries the three
routes it needs — `/api/health`, `/api/pr/{pr}/verdict`, and `/api/runs` — declared inline,
because a package for three handlers is a directory with no reason to exist yet. There is no
`POST /analyze` and no HTTP analysis entry point, so `schemas.AnalyzeRequest` is still
referenced by nothing. The verdict and runs routes are `def`, not `async def`, so the run-log
glob runs in Starlette's threadpool rather than blocking the event loop.

`/api/runs` lists every run record on disk. It is unauthenticated and the app allows every
origin, and a run record carries `Finding.evidence` verbatim — for the secrets checker, a
fragment of a real credential. It is demo-only until it is gated. See `CONTRACT.md`.

### The checker roster — five, deliberately heterogeneous

| # | Checker | Tier | Detects | Method |
|---|---------|------|---------|--------|
| 1 | `secrets` | 1 | Hardcoded credentials, API keys, private keys | Gitleaks |
| 2 | `deps` | 1 | Known CVEs in Python + npm dependencies | OSV-Scanner |
| 3 | `authz` | 2 | Missing authorization, IDOR, privilege escalation, broken access control | LLM |
| 4 | `injection` | 2 | SQL/command injection, XSS, SSRF, unsafe deserialization | LLM |
| 5 | `business` | 2 | Business-logic flaws, race conditions, crypto misuse, validation gaps | LLM |

Tiers 1 and 2 fail in different ways, and that is the point. Tier 1 is **precise and dumb** — it cannot reason about intent, so it does not try. Tier 2 is **reasoning and imprecise** — it understands that "this handler reads `user_id` from the query string and never checks ownership" is a vulnerability, but it will sometimes be wrong. The adjudicator must be built for that asymmetry.

### Design patterns

| Pattern | Where | Description |
|---------|-------|-------------|
| Protocol-based checker | `backend/app/checkers/base.py` | Every checker exposes the same async interface. Adding a sixth checker must not touch the orchestrator. |
| Fan-out / fan-in | `backend/app/checkers/base.py` (`run_all`) | Checkers run concurrently via `asyncio.gather`. Wall-clock is the slowest checker, not the sum. **Four exist, not five** — `deps` is not built. |
| Deterministic adjudicator | `backend/app/adjudicator.py` | Pure function, no I/O, no LLM. Given the same findings it always returns the same verdict. Testable without network. |
| Schema-at-the-boundary | `backend/app/llm/` + `checkers/semantic.py` | Pydantic validates every LLM response, and a finding whose evidence is not a verbatim quote from the diff is rejected outright. A malformed response becomes a checker *error*, never a silent finding. |
| Run log | `backend/app/runlog.py` | One JSON record per checker per run under `runs/`, re-readable into a verdict. `input_hash` is a SHA-256 over the **run records**, not over verdict inputs. Append-only SQLite (`store.py`) is **NOT BUILT**, so there is no tamper-evidence. |

### File boundaries — hard rules

- `routes/` **never** imports from `checkers/` internals. It calls the orchestrator. The two
  routes currently live inline in `main.build_app()`; that is where they move if a third
  arrives, not into a package that exists to hold two handlers.
- `adjudicator.py` **never** imports `llm/`. This is what makes it deterministic. If you need a model in the verdict path, the verdict is no longer reproducible — stop and reconsider the design.
- `checkers/` modules **never** import each other. Checkers are independent experts; a checker that trusts another checker's opinion is no longer an independent signal.
- `dashboard/` **never** calls a Groq key. All inference lives server-side in `backend/`.

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
- **NEVER** commit a `GROQ_API_KEY`, a GitHub token, or any `.env` file.
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

### Primary provider: Groq

Endpoint: `POST https://api.groq.com/openai/v1/chat/completions` — OpenAI-compatible.
Python SDK: `pip install groq` → `from groq import Groq` → `client.chat.completions.create(...)`.

### Routing

| Purpose | Model | Why |
|---------|-------|-----|
| Tier 2 checkers (3 LLM checkers) | `openai/gpt-oss-120b` | **Strict** JSON-schema mode is supported by the `gpt-oss` family **and** `qwen/qwen3.8-27b` (see the supported-model list below). Strict mode guarantees a schema-valid object — it does **not** guarantee a non-empty `evidence` or `line >= 1`; those are enforced in `checkers/semantic.py`, because a checker that cannot be parsed is a checker that does not run. |
| Adjudicator input shaping | same | Shares the finding schema, so one Pydantic model serves both. |
| Fallback | `llama-3.3-70b-versatile` | Broader general capability, but **best-effort** JSON only — requires validation + retry. |

### Structured output — the constraint that shapes the design

Groq exposes `response_format={"type": "json_schema", "json_schema": {...}}` in two modes:

- **Strict** (`strict: true`) — constrained decoding, output always matches the schema, never errors. Requires all fields `required` and `additionalProperties: false`. Supported on a limited model set.
- **Best-effort** (`strict: false`, default) — attempts the schema, may occasionally deviate.

**Verified 2026-09-25** against `console.groq.com/docs/structured-outputs#supported-models` (ledger K1, closed): strict mode supports `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `qwen/qwen3.8-27b`. The docs pages are not fully consistent with each other — one omits the Qwen entry. Re-read the page before changing the model; do not hardcode this list from memory.

Hard limitations, both verified:

- **Streaming is not supported** with Structured Outputs. All inference is non-streaming.
- **Tool use is not supported** with Structured Outputs. Checkers are prompted, not tool-equipped.

### Fallback chain — **step 1 only is implemented**

1. `openai/gpt-oss-120b`, strict mode — **implemented**, a single uncaught call
2. `openai/gpt-oss-120b`, best-effort + Pydantic validation + 1 retry — **NOT BUILT**
3. `llama-3.3-70b-versatile`, best-effort + Pydantic validation + 1 retry — **NOT BUILT** (the model ID appears nowhere in the codebase; `config.py` hardcodes one)
4. **Checker records an error → verdict degrades to `REVIEW`.** Never `PASS`. — **implemented and tested**, but via `checkers/base.py`'s blanket exception handler and `adjudicator.py`, not via any designed recovery.

So today the first hiccup on any LLM checker — a 429, a malformed body — permanently degrades that
checker for that run. There is no retry and no recovery. The honest summary is that steps 2 and 3
do not exist and step 4 holds for a different reason than the one intended here.

Documented secondary provider, not implemented in v1: IBM watsonx / Granite (`ibm/granite-4-h-small`). Retained deliberately — it is on-theme for an IBM event and its models carry IBM's indemnification, which third-party models do not. Relevant if this ships beyond the hackathon.

### Concurrency and cost

- Checkers run via `asyncio.gather` — one `GroqProvider` instance is shared across all of them, not one per checker. **Four checkers exist, not five.** There is no `httpx.AsyncClient` in this codebase; the Groq SDK owns its own HTTP client and TrustGate neither creates nor closes it.
- **Cache by input hash.** Identical diff → identical findings. Key on SHA-256 of (repo, base SHA, head SHA, checker version). **NOT BUILT.** `VerdictRecord.input_hash` exists but hashes the run *records* after the model calls were already paid for, and nothing consults it before invoking a checker. Re-running on an unchanged PR still burns full quota.
- Per-checker timeout: 30s — **implemented, not exercised.** `base.execute` wraps each
  checker in `asyncio.wait_for` and converts a `TimeoutError` into a `status=TIMEOUT`
  result. The only test touching timeouts fabricates a `TIMEOUT` `CheckerResult` and asserts
  the adjudicator's reaction; nothing in `tests/` triggers a real one. `SYSTEM_LEDGER.md`
  K-unverified is right and this line was the optimistic one.
- Whole-run budget: 90s — **NOT BUILT.** `Settings.run_budget_s` is read by nothing; `main.py` measures elapsed only to print it. A PR gate that takes longer than a coffee break gets disabled by its users.
- **Cost tracking is NOT BUILT.** `VerdictRecord.cost_usd` has exactly one assignment, `runlog.py` → `None`. The token counts that would feed it are gathered in `llm/client.py` and discarded in `checkers/semantic.py`. No cost number may be published.

### Tool execution boundaries

- The engine executes **only** the two pinned scanner binaries (Gitleaks, OSV-Scanner), via `subprocess` with an argument list — never `shell=True`.
- Scan targets are resolved from the GitHub-provided checkout path and passed as `cwd`. Scanner input is never interpolated into a command string.
- The engine has no outbound network access other than the Groq endpoint.
- No checker may read anything outside the checked-out PR workspace.

---

## i18n & Localization

| Property | Value |
|----------|-------|
| Languages | `en` only for v1 |
| Scripts | Latin |
| Direction | **LTR** |
| String handling | All user-facing strings in the dashboard pass through a single `strings.ts`. No inline literals in JSX. |
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
