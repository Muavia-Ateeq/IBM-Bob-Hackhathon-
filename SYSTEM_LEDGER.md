# SYSTEM_LEDGER.md — The Memory

> This file is the project's memory. Update it at the end of every session and whenever a
> workstream closes. Any AI agent can read it and instantly recover the exact project state.

---

## Current State

| Metric | Value |
|--------|-------|
| **Active Phase** | Phase 0: Foundation & Governance 🔴 — **disputed, see K10** |
| **Phase progress** | Phase 0's 6 exit criteria passed 26/26 checks on 2026-09-25, but `engine/app/**` was added afterwards in a session that did not close out. The phase status is therefore unverified against current disk |
| **Files tracked in git** | 23 — 11 docs/config + 12 Python. Excludes `.git/`, `engine/.venv/`, `__pycache__/` |
| **Application code files** | **12** — 11 under `engine/app/`, 1 under `engine/tests/`. Not greenfield. See K8 for how this count was wrong until 2026-09-25 |
| **Tests** | **1 file, 19 tests, all passing** — `engine/tests/test_adjudicator.py`. Covers the D5 fail-closed contract and the schema evidence guards. No test for the network path, the model client, or the CLI |
| **Build** | Imports verified working from `engine/` on Python 3.14.3. No `pyproject.toml` and no lockfile — see K9 |
| **Dependencies installed** | Present in `engine/.venv/` but **unpinned in any tracked file** — see K9 |
| **Missing from the architecture** | `engine/app/routes/`, `engine/app/store.py`, `engine/app/sarif.py`, `engine/app/checkers/secrets.py`, `engine/app/checkers/deps.py`, `dashboard/`, `.github/` — none exist. `engine/app/main.py` is now built |
| **Checker roster** | **3 semantic, 0 deterministic.** The two Tier 1 scanners named in D3 do not exist. See D3 |
| **Git repository** | Initialized in this directory. Top level is **this folder**, not `E:/` |
| **Last commit** | `61150f0` (baseline, 21 files) + one more adding `main.py` and the tests |
| **Time remaining** | Submissions close **Sun Sep 27 2026, 15:00 UTC** |
| **Team** | 6 |

### Counted how

The 23 figure is `find . -type f` excluding `.git/`, `engine/.venv/`, and `*.pyc`. Stated
explicitly because the previous entry gave a bare number with no basis, and a number without
its counting rule cannot be checked by the next session. `__pycache__` is excluded because it
is build output that `.gitignore` already discards; including it would make the count change
every time Python runs.

### Metrics deliberately absent

There is no latency figure, no false-positive rate, and no cost-per-PR anywhere in this
repository. None of them have been measured. Under the Authenticity Rule they are omitted
rather than estimated. They appear in Phase 4, with the harness that reproduces them, or not
at all.

A test count **does** appear, because it was measured: 19 tests, all passing, from one
`pytest` run on 2026-09-25. It is the only number in this project backed by a recorded run.

---

## File Ledger

### Created — Phase 0

| # | File | Bytes | Purpose and architectural justification |
|---|------|-------|-------------------------------------------|
| 1 | `AI_CONTEXT.md` | 22155 | The constitution. Identity, stack with rationale, architecture and file boundaries, design tokens for light and dark, NEVER/ALWAYS rules, model and tool strategy, i18n, authenticity rule, governance tiers. Declares the name-collision constraints discovered during planning so a later session does not re-derive or violate them. |
| 2 | `PROJECT_ROADMAP.md` | 10605 | The GPS. Seven phases with exactly one 🔴 ACTIVE, per-phase deliverables acting as the Tier 1 manifest, exit criteria, eight milestones, and success metrics that each state their *measurement method*. Records the rejected strategies so nobody rebuilds them at hour 30. |
| 3 | `SYSTEM_LEDGER.md` | — (this file) | The memory. This file. |
| 4 | `AGENTS.md` | 7017 | Portable agent rules. Read by OpenCode, Codex, Cursor, Aider, and IBM Bob. Records the Node 20 CI landmine and the Groq structured-output constraints so they are learned once. |
| 5 | `.bob/rules/00-authenticity.md` | 2015 | Bob-native: rule 1. Loads alphabetically, so the numbering is the ordering. |
| 6 | `.bob/rules/01-planning-governance.md` | 2326 | Bob-native: rule 2. The tiered approval policy. |
| 7 | `.bob/rules/02-session-continuity.md` | 2094 | Bob-native: rule 3. Boot sequences and close-out. |
| 8 | `.bob/rules/03-scope-control.md` | 1852 | Bob-native: rule 4. One active phase, and the scope-cutting order. |
| 9 | `.gitignore` | 887 | Python, Node, secrets, and — deliberately — `*.sarif` and `corpus/output/`, because scan output contains fragments of live credentials. `data/` and `build/` are anchored to the root — see K11 |
| 10 | `README.md` | 8838 | Human-facing; doubles as the lablab submission page. Rewritten 2026-09-25 to state what is built and, in a dedicated *Not built* table, what is not — including the consequence that no PR is ever blocked. Results section is intentionally empty rather than aspirational. |
| 11 | `WEDGE.md` | 7365 | Phase 1 deliverable. The one-sentence wedge, the 90-second demo script, anti-goals, and a falsification table where each claim has a test that can fail. Written without a ledger update — see K8. Corrected 2026-09-25: it claimed a published false-positive rate and a 5-checker fault-injection run, neither of which had happened |

### Created — parallel session, 2026-09-25, no ledger update at the time

These 10 files appeared while a planning session was in progress. They were verified by
reading every one, not inferred from the file listing. They are listed here because their
absence from this table is what allowed the ledger to claim a greenfield repo — see K8.

| # | File | Bytes | Purpose and architectural justification |
|---|------|-------|-------------------------------------------|
| 12 | `engine/app/schemas.py` | 2460 | Pydantic v2 boundary contracts. `extra="forbid"` everywhere, `line >= 1`, path-traversal rejection on `file`, and a validator forbidding a non-OK checker from reporting findings. This is the schema-at-the-boundary rule made mechanical: a malformed finding cannot enter the system |
| 13 | `engine/app/adjudicator.py` | 2030 | The deterministic adjudicator. Pure function, no I/O, no model, no clock. Caps any run containing an incomplete checker at `REVIEW`; only a fully clean, fully completed run reaches `PASS`. **This is D5 implemented** |
| 14 | `engine/app/checkers/base.py` | 1801 | `Checker` Protocol plus `execute`/`run_all`. `asyncio.gather` fan-out with per-checker `asyncio.wait_for` timeout, and every failure mode converted to a `CheckerResult` rather than raised. A sixth checker must not require touching the orchestrator |
| 15 | `engine/app/config.py` | 1619 | Frozen `Settings` dataclass populated from environment variables, with safe int/float parsing that falls back to defaults on malformed input. `GROQ_API_KEY` is optional by construction — its absence is a supported state, not an error |
| 16 | `engine/app/checkers/semantic.py` | 2696 | Shared LLM-checker base. `EVIDENCE_CONTRACT` instructs verbatim quoting and forbids reporting anything that cannot be quoted. Validates model output through `Finding` and raises on failure. **This is the WEDGE's mechanically-enforced evidence, working** |
| 17 | `engine/app/llm/client.py` | 2922 | `Provider` Protocol with three implementations: `GroqProvider` (strict-mode Structured Outputs, `temperature: 0`), `UnavailableProvider` (raises when the key is absent — the fail-closed path), and `StaticProvider` (deterministic, network-free, for tests) |
| 18 | `engine/app/llm/schemas.py` | 1280 | The JSON Schema handed to Groq strict mode. Every field `required`, `additionalProperties: false`, matching the constraints Groq documents for strict mode |
| 19 | `engine/app/checkers/authz.py` | 742 | Broken access control. Focus prompt only — delegates to `SemanticChecker`. Tier 2 |
| 20 | `engine/app/checkers/injection.py` | 763 | SQL/NoSQL/command/template injection, XSS, SSRF, path traversal, unsafe deserialization. Asks the model to judge whether the framework in use actually neutralises the sink. Tier 2 |
| 21 | `engine/app/checkers/business.py` | 841 | Business-logic and crypto defects: validation gaps, race conditions, ECB mode, fixed IV, negative/overflow handling. Explicitly told not to duplicate the injection and access-control checkers — checker independence is a hard rule |

### Created — 2026-09-25, make-it-run-then-prove-it-then-tell-the-truth

| # | File | Bytes | Purpose and architectural justification |
|---|------|-------|----------------------------------------|
| 22 | `engine/app/main.py` | 4313 | The entry point. CLI (`--diff` / `--serve`) and a FastAPI app with CORS. `main.py` owns the only `run_all` call site and the only `adjudicate` call site, so both the roster and the verdict path are reached through one file. It names the degraded checkers in its own output — the fail-closed contract made visible rather than silent. `build_app()` is a factory so uvicorn can be given an app object without a module-level import of FastAPI |
| 23 | `engine/tests/test_adjudicator.py` | 4982 | The proof. 19 tests over `adjudicate()` and the `Finding` schema: both D5 degradation paths, the severity mapping, the "a blocking finding survives a degraded sibling" case, and the evidence guards (`line < 1`, empty evidence, path traversal, a non-OK checker reporting findings). Also asserts purity by calling the function twice and on a reversed list. **A failure in either D5 test invalidates the central claim of the product** |

### Not yet built, and named in `AI_CONTEXT.md`

`engine/app/routes/` · `engine/app/store.py` · `engine/app/sarif.py` ·
`engine/app/checkers/secrets.py` (Gitleaks) · `engine/app/checkers/deps.py` (OSV-Scanner) ·
`dashboard/` · `.github/workflows/`.

The two deterministic tier-1 checkers are absent, so the roster is 3 LLM checkers and 0
scanners — the opposite of the D3 hybrid decision, and the reason no false-positive rate can
be defended. **`main.py` is now the caller of `run_all`**, so the engine has an entry point;
what it does not have is a gate. Nothing blocks a pull request.

### Why `AGENTS.md` *and* `.bob/rules/` both exist

Per IBM Bob's documented behaviour, `.bob/rules/*.md` loads alphabetically into every Bob
conversation and mode, and can be overridden per-mode via `.bob/rules-{mode}/`. But
**OpenCode, Codex, Cursor, and Aider do not read `.bob/`** — they read `AGENTS.md`.

Writing only one of the two would leave half the toolchain silently working without rules.
`AGENTS.md` is the portable spine; `.bob/rules/` is the Bob-specific enforcement layer
whose per-file granularity allows a mode-specific override later.

---

## Key Decisions and Their Reasons

| # | Decision | Reason | Cost if reversed |
|---|----------|--------|-----------------|
| D1 | Groq as primary inference | Team decision. Low latency is what makes a 5-way parallel fan-out feel instant | Loses the IBM/watsonx on-theme signal and IBM indemnification. Granite retained in `AI_CONTEXT.md` as the documented fallback |
| D2 | `openai/gpt-oss-120b` with **strict** JSON-schema mode | Strict mode guarantees schema-valid output via constrained decoding. A checker whose response cannot be parsed is a checker that does not run | Best-effort mode would need validation plus retry on every call, and llama-class models do not support strict mode at all |
| D3 | Hybrid roster: 2 deterministic + 3 LLM | Secrets and CVEs have ground truth. Regex and a CVE database beat a model on both cost and accuracy | 5 LLM checkers would be slower, costlier, and produce the false-positive noise that makes teams disable PR gates |
| D4 | Adjudicator contains no LLM | A pure function is deterministic, network-free, and testable. This is what makes a verdict auditable | An LLM adjudicator makes the verdict irreproducible and untrustworthy — the opposite of the product's purpose |
| D5 | Degraded path is `REVIEW`, never `PASS` | A gate that returns `PASS` when it breaks launders uncertainty into confidence | Fatal for the product's credibility |
| D6 | `TrustGate` name kept | Verified as colliding with 8 existing products, but the field has 31 submissions and a leader at 19 votes — this is decided on execution, not novelty | Not applicable. Constraints are recorded instead: never `pip install trustgate`, never claim the `™` |
| D7 | SQLite, not Postgres | Zero-ops for a 48-hour build; a single file is trivially swappable | Migration cost, later, off the critical path |
| D8 | Tiered governance over strict approval | A 48-hour clock cannot absorb a permission request per file | Governance gets ignored, which is worse than no governance |

---

## Known Issues & Technical Debt

| # | Item | Severity | Status |
|---|------|----------|--------|
| K1 | Groq strict-mode supported-model list is **not fully consistent across the provider's own doc pages** — one lists `qwen/qwen3.8-27b`, another omits it | Medium | **Closed 2026-09-25.** Checked against `https://console.groq.com/docs/structured-outputs#supported-models`: `openai/gpt-oss-120b` **is** on the strict-mode list, alongside `openai/gpt-oss-20b` and `qwen/qwen3.8-27b`. The inconsistency is in the doc pages, not in the model choice. `llm/client.py`'s hardcoded default is therefore correct. Note this verifies *eligibility for strict mode*, not a live completion — see K12 |
| K2 | No dependency versions pinned. The Tech Stack intentionally carries no version numbers | Low | Resolved at Phase 2 into lockfiles. Deliberate, not an oversight — pre-install version claims would be unverified |
| K3 | Six people, one repository, no branching strategy agreed | Medium | **Open.** Team leads to decide at Phase 1. Merge conflicts on `AI_CONTEXT.md` are the symptom to watch for |
| K4 | No owner assigned to any workstream | Medium | **Open.** The Phase 3 table proposes A–F. Needs confirmation from the team |
| K5 | `corpus/` labelled-vulnerable samples do not exist. Without them, Phase 4 cannot produce a false-positive rate | High | **Open.** Blocks M7. Owner F in Phase 3 |
| K6 | Git repository is nested inside an unrelated drive-root repo at `E:\` | Low | Contained. All git commands must be run from this directory. `git init` here makes the top level correct; running git from `E:\` still targets the drive repo |
| K7 | No RTL support | Low | Out of scope by decision. Recorded in `AI_CONTEXT.md` so it reads as a choice, not an oversight |
| K8 | **The ledger claimed 0 application code files while 10 existed on disk.** A session booting on this file would have rebuilt work that was already written — the exact failure this file exists to prevent, and it happened anyway | **High** | **Fixed 2026-09-25.** Current State and File Ledger corrected; the 10 files are now itemised with justification. The counting basis is stated so the next session can reproduce the number. Unresolved process risk: nothing mechanically forces a close-out |
| K9 | `engine/` has **no `__init__.py`**, no `pyproject.toml`, and **no lockfile**. `engine/app/**` imports resolve only because `engine/` happens to be the working directory — running from the repo root fails. `.venv/` holds real packages (fastapi 0.141.1, groq 1.7.0, pydantic 2.46.5, pytest 9.1.1 on Python 3.14.3) with **nothing recording those versions in a tracked file** | Medium | **Open.** The lockfile is an explicit Phase 2 deliverable (`PROJECT_ROADMAP.md:83`). Until it exists, the installed set cannot be reproduced, and `AI_CONTEXT.md`'s deliberate no-version-numbers rule means the versions live nowhere tracked. Owner: whoever takes Phase 2 |
| K10 | **Phase 0 is 🔴 ACTIVE and forbids application code, but `engine/app/**` exists.** Either the phase advanced without a roadmap edit, or the code landed outside approved scope. The record cannot distinguish these, and this ledger will not guess | **High** | **Open — Tier 3, team decision, deliberately not resolved by an agent.** Recorded rather than silently fixed. A phase transition is not an agent's call. Blocks a truthful Phase 0 close-out. **Worse now:** this session added a CLI entry point and a test file on top of the disputed code, so the discrepancy has grown, not closed |
| K11 | **`.gitignore` used unanchored `data/` and `build/`.** An unanchored pattern with a trailing slash matches at *any* depth, so `data/` was silently excluding `engine/app/data/` and `dashboard/src/data/` — a findings store would have vanished with no error and no warning | Medium | **Fixed 2026-09-25.** Both anchored to the root (`/data/`, `/build/`) with the reason written into the file. Verified with `git check-ignore -v engine/app/data/findings.json` — no match, i.e. tracked — while `git check-ignore -v data/x` still matches. Worth knowing: `git check-ignore` is the check, not reading the file, because the failure mode is a *silence* |
| K12 | **No `GROQ_API_KEY` in this environment and no `.env`.** The inference path has therefore never executed against a live model. The `BLOCK` verdict is implemented and unit-tested through a static provider, but **no real model call has happened** — so no latency, no cost-per-PR, and no per-checker precision exist and none are claimed | **High** | **Open.** Not an agent's to solve. Blocks M4 ("first real verdict"), all of Phase 4's numbers, and the `BLOCK` branch of the demo. Every documented alternative path — the degraded run, the schema validators, the HTTP health check — was exercised instead, which is why the product is demonstrable without it. `UNVERIFIED — one `python app/main.py --diff <real diff>` run with a key set` |

---

## Next Actions

**In order. Item 1 is a Tier 3 decision and blocks a truthful close-out.**

1. **Resolve K10 — decide what happened to the phase.** Application code exists under a phase
   that forbids it, and this session added a CLI and a test file on top. Either confirm a
   Phase 0 → 1 → 2 transition happened and update `PROJECT_ROADMAP.md` to say so, or record
   the code as out-of-scope work that needs a decision. **An agent must not make this call**
   — it is a phase transition, which is Tier 3. Until it is resolved, no phase status in
   this repo can be trusted
2. **Get a `GROQ_API_KEY` (K12).** This is now the highest-value unblock in the project. One
   run with a key set produces a real `BLOCK` or a real clean `PASS`, and from there a
   latency figure and a cost figure — the two numbers the roadmap's success metrics ask for.
   Every other path is already exercised. It is also the one thing no amount of coding
   substitutes for
3. **Add the lockfile (K9).** `pip freeze` from `engine/.venv/` into a tracked
   `engine/requirements.txt`. Cheap, unblocks reproducibility, and is already a Phase 2
   deliverable. Decide alongside it whether `engine/` gets an `__init__.py` or a
   `pyproject.toml` — right now imports work only from inside `engine/`
4. **Decide the branching strategy** for 6 people (K3). Six people are now demonstrably
   editing one repo in parallel — this stopped being theoretical when `engine/app/**` landed
   without a ledger update
5. **Confirm workstream owners** A–F (K4). Owner B's three checkers are built; owner C's
   adjudicator, schemas, and tests are built. Nobody has claimed either
6. **Decide the remaining build.** The GitHub gate (`.github/workflows/`), the two
   deterministic tier-1 checkers (`secrets.py`, `deps.py`), `sarif.py`, `routes/`,
   `store.py`, and `dashboard/` are all unbuilt. **`main.py` is done, so the engine has an
   entry point — but nothing blocks a pull request.** With ~1.5 days left, the gate and one
   deterministic checker are worth more than the dashboard: they are the difference between
   a tool and a gate, and the dashboard is the one thing judges will forgive
7. **Test the network path.** `run_all`'s timeout branch and the `GroqProvider` response
   parsing are unexercised. `StaticProvider` covers the schema contract but not a malformed
   or slow real response. This needs a key (item 2) or a hand-rolled fake

### Closed this session

- **K1** — `openai/gpt-oss-120b` confirmed on Groq's live strict-mode list
- **K11** — unanchored `.gitignore` patterns anchored; verified with `git check-ignore`
- **K9** partly — the engine now has a caller of `run_all` and a runnable entry point. The
  lockfile half of it is still open
- **Old item 7 (first test file)** — done. 19 tests, all passing
- **Old items 5 and 6** — 5 closed above; 6 narrowed to the gate and the deterministic tier

### Next session must pick up first

> Read `AI_CONTEXT.md`, `PROJECT_ROADMAP.md`, and `SYSTEM_LEDGER.md`. **Note that application
> code already exists under `engine/app/` — do not rebuild it.** The first action is item 1
> above: the K10 phase-scope decision, which is Tier 3 and belongs to the team, not an agent.
> If a key is available, item 2 is the fastest way to turn a plausible product into a
> demonstrated one.

---

## Verification Log

| Date | Check | Result |
|------|-------|--------|
| 2026-09-25 | Project directory inspected before any write | Empty — 0 items, including hidden. Confirmed greenfield |
| 2026-09-25 | `git rev-parse --show-toplevel` before `git init` | Returned `E:/` — drive-root repo, 3,000+ unrelated paths. Hazard identified |
| 2026-09-25 | Name collision check — `TrustGate` | 8 existing products found. Constraints recorded, not a blocker for a hackathon |
| 2026-09-25 | Differentiation strategy check | Prior recommendation found already shipped by quorum.reviews. Strategy discarded |
| 2026-09-25 | Groq structured-output constraints read from provider docs | Strict mode limited to the `gpt-oss` family; streaming and tool use unsupported. Directly shaped the checker design |
| 2026-09-25 | CI landmines verified | Node 20 removed from GitHub hosted runners Sep 16 2026; SARIF needs `if: always()` and `security-events: write`; Gitleaks needs `fetch-depth: 0` |
| 2026-09-25 | `git init` run in project directory | Top level now resolves to this folder, not `E:/`. No commit at this point; a baseline commit `61150f0` followed later the same day |
| 2026-09-25 | **Phase 0 exit criteria verified** | 26/26 automated checks pass. Sections present, exactly one 🔴 ACTIVE row, ledger counts match disk, tiered policy in all 4 locations, git isolated, zero placeholders |
| 2026-09-25 | Discrepancy found and fixed | Verification caught the ledger claiming 9 files when disk had 10 — `SYSTEM_LEDGER.md` itself was written after the count was taken. Corrected to 10. Three other initial check failures were bugs in the checker itself, not the documents: `.NET` regex needs `\uD83D\uDD34` not `\u{1F534}`; PowerShell 5.1 reads UTF-8 as ANSI without `-Encoding UTF8`; and an over-specified expectation that 🔴 appears exactly twice when 4 uses are correct (1 row, 1 heading, 2 prose) |
| 2026-09-25 | **K1 closed — Groq strict-mode model list** | `https://console.groq.com/docs/structured-outputs#supported-models` confirms `openai/gpt-oss-120b` supports strict mode, alongside `openai/gpt-oss-20b` and `qwen/qwen3.8-27b`. The doc-page inconsistency is real but does not affect the chosen model |
| 2026-09-25 | **K11 found and fixed — `.gitignore` anchoring** | `git check-ignore -v engine/app/data/findings.json` matched the unanchored `data/` rule, confirming nested data directories were being silently excluded. Fixed and re-verified: the nested path no longer matches while root `/data/` still does |
| 2026-09-25 | **Baseline commit `61150f0`** | 21 files. Tree checked for `.venv`, `*.pyc`, `*.sarif`, and `.env` — none present |
| 2026-09-25 | **Adjudicator tests written and run** | 19 tests, 19 passed, Python 3.14.3 / pytest 9.1.1. Both D5 cases pass. Three initial failures were **mine**, not the code's: two over-specified assertions on the `reason` string, and one test that used Pydantic v2's `model_copy(update=...)`, which bypasses validation by design. The real validator was verified directly before that test was rewritten to construct `Finding` properly |
| 2026-09-25 | **End-to-end run with no API key** | `python app/main.py --diff app/schemas.py` → `REVIEW`, "no findings, but 3 of 3 checkers did not complete", all three `ProviderUnavailable: GROQ_API_KEY is not set`. This is wedge claim 1 working. Error paths also verified: empty diff → exit 2, missing file → exit 2 |
| 2026-09-25 | **HTTP surface verified in-process** | `fastapi.testclient.TestClient` against `build_app()`: `/api/health` → 200 `{"ok": true}`, unknown route → 404, CORS headers present. Verified in-process rather than against a live port because `pkill -f "app/main.py"` was denied by the sandbox classifier, and that denial was not worked around |
| 2026-09-25 | **False claims found and corrected in the docs** | `README.md:8` said "No application code exists yet" while 10 files existed. `WEDGE.md:71-73` said the false-positive rate is published "which we do" with no corpus in the repo. `WEDGE.md:94` promised a fault-injection run across 5 checkers; 3 exist. All three corrected. **The `WEDGE.md` findings were found by reading the documents against the disk, not by running a checker** — which is precisely the gap K8 describes |
