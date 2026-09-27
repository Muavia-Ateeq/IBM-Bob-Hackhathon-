# SYSTEM_LEDGER.md — The Memory

> This file is the project's memory. Update it at the end of every session and whenever a
> workstream closes. Any AI agent can read it and instantly recover the exact project state.

---

## Current State

| Metric | Value |
|--------|-------|
| **Active Phase** | Phase 0: Foundation & Governance 🔴 — **disputed, see K10** |
| **Phase progress** | Phase 0's 6 exit criteria passed 26/26 checks on 2026-09-25. **Three sessions have since worked under it** — the second added application code, the third renamed `backend/` → `backend/`, moved the governance docs into `docs/`, and deployed to Render. The phase status is therefore unverified against current disk |
| **Files in the working tree** | **84** — 49 Python + 15 Markdown + 20 config/deploy/CI. Excludes `.git/`, `backend/.venv/`, `__pycache__/`, `backend/runs/`, `.pytest_cache/`, `backend/.tools/`. **All 84 are committed and tracked**; `git status --porcelain` returns empty. The jump from 81 is `docs/` (6) and `screenshots/` (1) landing 2026-09-26 |
| **Application code files** | **24** — 15 under `backend/app/`, 1 at `backend/` root (`integration_test.py`), 8 under `backend/tests/`. Not greenfield. See K8 for how this count was wrong until 2026-09-25 |
| **Tests** | **8 files, 81 tests, all passing** — `test_adjudicator.py` (22), `test_runs.py` (13), `test_sarif.py` (12), `test_semantic.py` (11), `test_comment.py` (9), `test_secrets.py` (6), `test_integration.py` (4), `test_gate.py` (4). Re-derived by `pytest --collect-only` on 2026-09-26 after the rename; the 22 + 13 + 12 + 11 + 9 + 6 + 4 + 4 sum is the 81. **This file has carried a wrong test count six times** — it previously said 79 here, 76 in "Metrics deliberately absent" two sections below, and 74 in the Verification Log, all three disagreeing with each other. `test_runs.py` was recorded as 11 when it holds 13. Still no test that exercises the HTTP surface over a real socket |
| **Corpus** | `demo_target/` + `bench/` — **built 2026-09-26, never measured.** 9 of 10 fixtures planted; 3 cases have no checker by design, 2 are marked disputed. The runner reports `INCOMPLETE` and prints no rate, because K12 and K14 are both open |
| **Build** | Imports verified working from `backend/` on Python 3.14.3. `backend/requirements.txt` pins the installed set — K9 half closed. Still no `pyproject.toml` or `__init__.py`. **`uvicorn app.main:app` was verified by booting it**, after `app = build_app()` was added to `backend/app/main.py` — the module previously exposed only the factory, so that target raised `AttributeError` |
| **Dependencies installed** | Pinned in `backend/requirements.txt`, from `pip freeze` in `backend/.venv/` |
| **Missing from the architecture** | `backend/app/routes/`, `backend/app/store.py`, `backend/app/checkers/deps.py`, `dashboard/` — none exist. `secrets.py`, `runlog.py`, `sarif.py`, and `.github/workflows/trustgate.yml` are now built |
| **Checker roster** | **3 semantic, 1 deterministic.** `secrets` (Gitleaks) landed 2026-09-25; `deps` (OSV-Scanner) is blocked — see K13. D3 is still incomplete |
| **On-disk run records** | `backend/runs/*.json`, one `RunRecord` per checker per run. Written by `runlog.write_run_records` from one call site; read back by `app.runlog`. Gitignored, so a fresh deploy starts empty |
| **SARIF** | `backend/app/sarif.py` converts a `VerdictRecord` to SARIF 2.1.0. Produced end-to-end locally and validated against both the OASIS schema and GitHub's stricter required table. **Never uploaded** — that requires the workflow to run on GitHub |
| **The gate** | `.github/workflows/trustgate.yml`. YAML parses, all three actions SHA-pinned, every runtime read from each `action.yml`. **Never executed — and this is now a measured fact, not an assumption**: `GET api.github.com/repos/ammarzia124/TrustGate-IBM-BOB-Hackathon/actions/runs` returns `total_count: 0` as of 2026-09-26. The workflow only triggers on `pull_request` and `workflow_dispatch`, and no PR has been opened. Opening one is what verifies it |
| **Live deployment** | **`https://trustgate-api-ehib.onrender.com` — LIVE on Render's Free plan.** `/api/health` returns `{"ok":true}` and `/api/runs` returns `{"count":0,...}`, both confirmed in the browser. Built from the root `render.yaml` blueprint. `GROQ_API_KEY` is `sync: false` there, so it must be added by hand in the Render dashboard. The API is **read-only** — it surfaces run records, it does not create verdicts. Free plan spins down after ~15 min idle, so a cold start can take 30–60 s |
| **Git repository** | Initialized in this directory. Top level is **this folder**, not `E:/`. Public, default branch `main`, remote `origin` |
| **Last commit** | **`2fab917`** (ledger close-out). Working tree **clean** — 0 uncommitted, 0 unpushed; local `HEAD` matches `origin/main`. This row previously read `0eda72d` with "39 untracked + 3 modified uncommitted", which was true when written and false for the rest of 2026-09-26 |
| **Time remaining** | Submissions close **Sun Sep 27 2026, 15:00 UTC** |
| **Team** | 6 |

### Counted how

The **84** figure is `find . -type f` excluding `.git/`, `backend/.venv/`, `*.pyc`,
`backend/runs/`, `.pytest_cache/`, and `backend/.tools/`. Stated explicitly because an earlier
entry gave a bare number with no basis, and a number without its counting rule cannot be checked
by the next session. `__pycache__` and `.pytest_cache/` are excluded because they are build and
test output that `.gitignore` already discards; including them would make the count change every
time Python runs. `backend/runs/` is excluded because it is run output, not source — it grows
every time the engine is invoked. `backend/.tools/` is excluded because it holds a downloaded
third-party binary, not source (K14). **Re-run the `find` rather than adjusting this number by
hand** — it has been wrong four times, each time because a session wrote the ledger before
finishing its own edits.

The committed/untracked split that used to stand here is **gone, and its absence is the
result**: `git status --porcelain` now returns **empty**, and `git ls-files | wc -l` returns
**84**, which equals the filesystem count exactly. Those two independent methods agreeing is
the cross-check that makes both numbers trustworthy. `git rev-parse HEAD` equals
`git rev-parse origin/main` at `2fab917` — nothing is unpushed.

### Metrics deliberately absent

There is no latency figure, no false-positive rate, and no cost-per-PR anywhere in this
repository. None of them have been measured. Under the Authenticity Rule they are omitted
rather than estimated. They appear in Phase 4, with the harness that reproduces them, or not
at all.

A test count **does** appear, because it was measured: **81 tests, all passing**, from
`pytest --collect-only` and a full run on 2026-09-26, after the `backend/` → `backend/` rename.
It is the only number in this project backed by a recorded run. This line previously said 76
while the Current State table above it said 79 — **two sections of one file disagreeing about
the same measured quantity is the exact defect this ledger keeps recording**, and it survived
because each section was edited in a different session. Both now read 81.


---

## File Ledger

> **Reading the entries below: the directory was renamed.** `engine/` became `backend/` and
> the six governance docs moved into `docs/` on 2026-09-26. Entries written before that date
> were swept to the current names so that no path in this file dangles — `backend/app/main.py`
> in a 2026-09-25 entry means the file that was then called `engine/app/main.py`. This is the
> one place where the log is deliberately **not** a literal transcript: the alternative was
> ~70 references to a directory that no longer exists, which is worse for a file whose whole
> job is letting a session recover state. The `git mv` history preserves the original paths.

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
| 12 | `backend/app/schemas.py` | 2460 | Pydantic v2 boundary contracts. `extra="forbid"` everywhere, `line >= 1`, path-traversal rejection on `file`, and a validator forbidding a non-OK checker from reporting findings. This is the schema-at-the-boundary rule made mechanical: a malformed finding cannot enter the system |
| 13 | `backend/app/adjudicator.py` | 2030 | The deterministic adjudicator. Pure function, no I/O, no model, no clock. Caps any run containing an incomplete checker at `REVIEW`; only a fully clean, fully completed run reaches `PASS`. **This is D5 implemented** |
| 14 | `backend/app/checkers/base.py` | 1801 | `Checker` Protocol plus `execute`/`run_all`. `asyncio.gather` fan-out with per-checker `asyncio.wait_for` timeout, and every failure mode converted to a `CheckerResult` rather than raised. A sixth checker must not require touching the orchestrator |
| 15 | `backend/app/config.py` | 1619 | Frozen `Settings` dataclass populated from environment variables, with safe int/float parsing that falls back to defaults on malformed input. `GROQ_API_KEY` is optional by construction — its absence is a supported state, not an error |
| 16 | `backend/app/checkers/semantic.py` | 2696 | Shared LLM-checker base. `EVIDENCE_CONTRACT` instructs verbatim quoting and forbids reporting anything that cannot be quoted. Validates model output through `Finding` and raises on failure. **This is the WEDGE's mechanically-enforced evidence, working** |
| 17 | `backend/app/llm/client.py` | 2922 | `Provider` Protocol with three implementations: `GroqProvider` (strict-mode Structured Outputs, `temperature: 0`), `UnavailableProvider` (raises when the key is absent — the fail-closed path), and `StaticProvider` (deterministic, network-free, for tests) |
| 18 | `backend/app/llm/schemas.py` | 1280 | The JSON Schema handed to Groq strict mode. Every field `required`, `additionalProperties: false`, matching the constraints Groq documents for strict mode |
| 19 | `backend/app/checkers/authz.py` | 742 | Broken access control. Focus prompt only — delegates to `SemanticChecker`. Tier 2 |
| 20 | `backend/app/checkers/injection.py` | 763 | SQL/NoSQL/command/template injection, XSS, SSRF, path traversal, unsafe deserialization. Asks the model to judge whether the framework in use actually neutralises the sink. Tier 2 |
| 21 | `backend/app/checkers/business.py` | 841 | Business-logic and crypto defects: validation gaps, race conditions, ECB mode, fixed IV, negative/overflow handling. Explicitly told not to duplicate the injection and access-control checkers — checker independence is a hard rule |

### Created — 2026-09-25, make-it-run-then-prove-it-then-tell-the-truth

| # | File | Bytes | Purpose and architectural justification |
|---|------|-------|----------------------------------------|
| 22 | `backend/app/main.py` | 4313 | The entry point. CLI (`--diff` / `--serve`) and a FastAPI app with CORS. `main.py` owns the only `run_all` call site and the only `adjudicate` call site, so both the roster and the verdict path are reached through one file. It names the degraded checkers in its own output — the fail-closed contract made visible rather than silent. `build_app()` is a factory so uvicorn can be given an app object without a module-level import of FastAPI |
| 23 | `backend/tests/test_adjudicator.py` | 4982 | The proof. 19 tests over `adjudicate()` and the `Finding` schema: both D5 degradation paths, the severity mapping, the "a blocking finding survives a degraded sibling" case, and the evidence guards (`line < 1`, empty evidence, path traversal, a non-OK checker reporting findings). Also asserts purity by calling the function twice and on a reversed list. **A failure in either D5 test invalidates the central claim of the product** |

### Created — 2026-09-25, runlog + the first deterministic checker

Nine files from three pasted task prompts, mapped onto `backend/` rather than the `backend/`
tree the prompts assumed. The prompts' scoring algorithm was **not** adopted; see K13 and the
rejected-alternatives note below.

| # | File | Purpose and architectural justification |
|---|------|--------|
| 24 | `backend/app/checkers/secrets.py` | The `secrets` half of D3, and the first non-LLM checker. Wraps Gitleaks via `asyncio.create_subprocess_exec` — **not** `subprocess.run`, which would block the event loop and serialise the five-way fan-out, turning wall-clock into the sum of the checkers. JSON field names were read from `gitleaks/gitleaks` `report/finding.go` rather than guessed, and `Line` is `json:"-"` there so it is absent from the built-in report. **`Match` is redacted against `Secret` before use** — see the correction below; the first implementation quoted `Match` verbatim on the assumption it excluded the credential, and the tests proved otherwise |
| 25 | `backend/app/runlog.py` | Persists and re-reads verdicts. One `RunRecord` per checker per run, written from **one** call site in `main.analyze()` — not from each checker, which is what stops five checkers inventing five on-disk formats. `compute_verdict()` returns the tested `VerdictRecord` and delegates to `adjudicate()` rather than reimplementing the thresholds. Named `runlog`, not `runs`, so the module does not shadow the `runs/` directory |
| 26 | `backend/app/checkers/CONTRIBUTING.md` | The "same interface for every checker owner" deliverable, as a contract document rather than five copies of a stub template. The interface already existed in `base.py`; what was missing was the evidence rules and the register-your-checker procedure |
| 27 | `backend/tests/test_runs.py` | 9 tests. The load-bearing one is `test_no_runs_never_passes`. **This file caught a real bug**: `adjudicate([])` returns an empty degraded list (no checkers existed to be incomplete), which mapped to `degraded: false` beside a `REVIEW` verdict — a dashboard would have rendered a clean badge next to "no checkers ran". Fixed in `runlog.py`, not in the adjudicator, because the adjudicator's third return value means "names of checkers that did not complete" and that list is correctly empty |
| 28 | `backend/requirements.txt` | `pip freeze` output. Closes the lockfile half of K9 and unblocks `render.yaml`, which cannot build without it. Includes dev tools (`pytest`, `colorama`) — one file rather than a split runtime/dev pair, for a 48h build |
| 29 | `render.yaml` | Render service. **Corrected 2026-09-26: this row previously said `rootDir: engine`, which the committed file had already stopped carrying** — see the decision recorded under *Modified* below. Uses a module-level `app` (a later one-line fix) so `uvicorn app.main:app` resolves. **Restructured 2026-09-26: `rootDir: trustgate`**, which leaves `buildCommand`, `startCommand` and `PYTHONPATH` byte-identical |
| 30 | `Procfile` | The same command, for any host that reads a Procfile. Not a backup for Render — `render.yaml` already carries `startCommand`. Restructured 2026-09-26 to `cd trustgate/backend`, since this file sits at the repo root and gets no `rootDir` treatment |
| 31 | `vercel.json` | SPA build config. **Inert** — no frontend exists. Written because it was asked for and costs nothing, not because a deploy is planned |
| 32 | `backend/tests/test_secrets.py` | 6 tests over the gitleaks report parser, using an entry shaped exactly as `report/finding.go` emits. **This file caught two real defects** — see the correction below. Testing a private `_to_finding` is normally a smell; here it is the only way to exercise the parser without the binary, and the parser is where the credential-handling risk lives |

### Modified — 2026-09-25

| File | Change |
|------|--------|
| `backend/app/schemas.py` | Added `RunRecord`. Separate from `VerdictRecord` rather than a subclass, because `extra="forbid"` makes a subclass impossible and the two have different lifecycles: a run record is written by one checker, a verdict record is derived from all of them. Its timestamp field is `written_at`, not `started_at` — the writer has no start time, only `duration_ms`, and naming it `started_at` would have been a small lie in a file an auditor reads |
| `backend/app/main.py` | `--host` flag (default `127.0.0.1`, unchanged locally) and one `write_run_records()` call. `secrets` added to `CHECKER_MODULES` |
| `README.md` | **Corrected a false claim.** The verdict table said any `high` finding yields `REVIEW`. `adjudicator.py:10` puts `HIGH` in `_BLOCKING` and `test_high_finding_is_block` asserts `BLOCK`. The table also omitted `info` entirely. It now matches the code and states the row order, since `BLOCK` outranks a degraded sibling |
| `.gitignore` | `/backend/runs/`, anchored, with the reason written in. Run records carry `Finding.evidence` verbatim, and for `secrets` that quote is a matched credential fragment — the same hazard as the `*.sarif` rule two lines above. Unanchored would have been the K11 mistake in a different costume |

### Modified — 2026-09-26

| File | Change |
|------|--------|
| `backend/app/checkers/semantic.py` | The two fail-opens closed. `run` now **raises** on an over-budget diff rather than truncating silently, and `_to_finding` takes the diff `body` and rejects any finding whose `evidence` is not a quote from it. `body` is stored with `\r` stripped so a Windows checkout and LF evidence compare equal. A new module-level `_quote_present` carries the reasoning rather than burying it in the loop |
| `backend/app/main.py` | `--sarif` and `--workspace`. `analyze` now takes the workspace and passes it to `run_all` instead of hardcoding `"."` — the workflow `cd engine`, so gitleaks was scanning `backend/` rather than the PR. The SARIF is generated from `compute_verdict` reading the records **back off disk** rather than from the in-memory results |
| `README.md` | Build status, the Tech table, the repository-layout table, and the *Not built* table all updated for the gate and SARIF. Test counts 45 → 61. A new "Failing closed is not one rule, it is everywhere" table records the two closed bypasses, and a "The gate" section documents the two load-bearing decisions in the workflow |
| `AI_CONTEXT.md` | `sarif.py` and `trustgate.yml` marked built-and-never-run rather than NOT BUILT; the gate section gained an explicit state line; the Gitleaks row no longer claims `gitleaks-action@v3`, which the workflow does not use |
| `AGENTS.md` §7 | Rewritten with the precise dead-version data, the `pull_request_target` RCE warning, the working OASIS schema URL, and the fact that GitHub's layer requires more than OASIS |
| `.gitignore` | `/backend/.tools/` — a pinned scanner binary fetched and checksum-verified locally, never committed |

### Restructured — 2026-09-26, project files under `trustgate/`

The checkout directory is named `IBM BOB Hackathon` and the root mixed source with deploy config.
`.bob/`, `backend/`, `bench/`, `demo_target/`, `docs/`, `screenshots/` and `README.md` moved
into `trustgate/`. **Six files did not, and could not** — they are read *by path from the repo
root*, so moving them removes the thing they configure rather than relocating it:

| Stayed at the root | Because |
|---|---|
| `.github/` | GitHub reads workflows only from `<repo root>/.github/workflows/`. One level down, the gate stops existing — no error, no run, no SARIF upload, PRs merge unblocked |
| `render.yaml` | Render reads the blueprint from the repo root ([spec](https://render.com/docs/blueprint-spec)) |
| `vercel.json` | Vercel reads project config from the project root |
| `Procfile`, `.gitignore` | Convention, not a hard platform constraint — but both need editing anyway |
| `AGENTS.md` | Its stated purpose is *"so agent tools which load `AGENTS.md` from the repository root still find the rules"*. Moving it defeats the file |

| File | Change |
|------|--------|
| `render.yaml` | `rootDir: trustgate` added — **one line**, and it is what makes the other three lines unnecessary. Render runs both commands with cwd = `rootDir`, so `pip install -r backend/requirements.txt` and `cd backend` resolve to `trustgate/backend/` unchanged. This is *not* the `rootDir: engine` mistake recorded below: that paired a `rootDir` with a `cd` into the **same** directory. `rootDir: trustgate` + `cd backend` is one level of nesting. `PYTHONPATH` stays `backend` — no dashboard edit needed |
| `trustgate.yml` | `cd backend` → `cd trustgate/backend`, the requirements path gains the `trustgate/` prefix, and the four `../` artifact paths become `../../` because the engine now sits two levels below the repo root where the later steps read `verdict.txt` and `trustgate.sarif`. `GITLEAKS_CONFIG` is absolute and unchanged; the allowlist patterns needed no edit (3a) |
| `backend/integration_test.py` | `REPO_ROOT` → `parents[2]`. It exists solely to find `.github/workflows/trustgate.yml`, which is at the **repo** root, not under `trustgate/` |
| `backend/tests/test_integration.py` | `REAL_WORKFLOW` → `parents[3]`, same reason. The `sys.path` insert on line 6 needed no change — it resolves to `backend/`, which did not move relative to `tests/` |
| `.gitignore` | The four anchored rules re-anchored to `/trustgate/…`. Two of them protect real files on disk — `backend/runs/` (20+ run records, each carrying verbatim evidence) and `backend/.tools/` (a 22 MB `gitleaks.exe`) — so a stale anchor would have committed a credential fragment and a binary, or lost the binary |
| `AGENTS.md` | Pointer retargeted to `trustgate/docs/AGENTS.md` |
| `AI_CONTEXT.md`, `demo_target/README.md` | Directory diagram shows the new two-level shape; one `../.github/gitleaks.toml` link needed a second `../` |

`bench/run_benchmark.py` and `backend/app/main.py` needed **no** edit, and that was verified
rather than assumed — see the verification row below.

**Verified after the move, on the real tree:** 81 tests pass (the 74 in the ledger below is
stale — more landed since); `REPO_ROOT` resolves to the repo root and `trustgate.yml` exists
at the computed path; `--dry-run` prints the 4-checker roster; a real run on
`samples/example.diff` writes 4 run records and returns `REVIEW` with 4 degraded checkers, which
is K12/K14's known state rather than anything the move caused; `bench/run_benchmark.py --dry-run`
resolves all 10 corpus cases; and `uvicorn app.main:app` booted **from `trustgate/backend`** —
the exact cwd `rootDir: trustgate` produces — answered `/api/health` `{"ok":true}` and
`/api/runs` `{"count":23}`.

**Not verified:** that the edited `trustgate.yml` runs green on GitHub. It triggers on
`pull_request` and `workflow_dispatch` only, so a direct push to `main` does not execute it, and
K20 records 0 runs to date. `UNVERIFIED — workflow_dispatch it by hand, or open a throwaway PR`.
The four `../` → `../../` edits are the risk: the test suite proves the file parses and its
invariants hold, but nothing local proves the artifacts land where the later steps read them.

### Two defects the tests caught, recorded because the reasoning was wrong first

Both were found by `test_secrets.py` on its first run, against a report entry shaped from
gitleaks' own source. Neither would have been visible in a demo, and the second would have
leaked a credential.

1. **Gitleaks' `Match` contains the secret.** The first implementation quoted `Match` verbatim
   as the finding's `evidence`, on the reasoning that `Match` was the surrounding context and
   `Secret` the credential. That is backwards: `Match` is the matched text and the secret sits
   inside it. The test asserted the secret value appears nowhere in `model_dump_json()` and
   failed. Fixed by redacting the `Secret` value out of `Match`. The quote is no longer
   verbatim, and that is the deliberate trade — a redacted quote still points at the line, and
   the credential would otherwise land in `runs/*.json` and then in a SARIF upload.
2. **Path relativisation never ran on Windows.** The original code used
   `Path(raw).is_absolute()`, but on Windows `Path("/home/runner/...").is_absolute()` is
   `False` — a POSIX-leading path is not absolute there. Every reported path therefore stayed
   absolute on the platform this team develops on, and would have been written into findings as
   machine-specific strings. Replaced with explicit separator normalisation, which is also why
   the module carries a docstring saying why it does not use `Path`.

The general lesson is the one this repository keeps re-learning: **the reason a line of code
looks right is not evidence that it is right.** Both defects were in code that read
correctly.

### Rejected from the pasted prompts, and why

The first three prompts specified a `backend/` tree, a numeric score, and a `forced_block`
rule. All three were declined on evidence, not taste:

1. **The 5/2/1 score.** `SEVERITY_ORDER` has five levels, and the score has no slot for
   `info`. Five `low` findings would score 5 and `BLOCK` a PR where the current rule reviews —
   the "annoying, users disable it" failure `WEDGE.md:41` names. `adjudicate()` is reused
   instead, and the score is dropped entirely.
2. **`forced_block` on a substring match.** Grepping evidence for `"secret"`/`"password"` fires
   on any comment reading `# no password here`, and puts one checker's domain inside the
   adjudicator, which `AI_CONTEXT.md:157` forbids.
3. **`PASS` when no run files match.** The prompt returned `PASS`. `adjudicate([])` returns
   `REVIEW, "no checkers ran"`. A PR whose checkers all died before writing a record must not
   read as clean — that inverts wedge claim 1, the project's most load-bearing claim.

### Rejected from the second batch of four prompts, and why

Prompts 7–10 repeated the `backend/` tree, assumed five checkers, and specified a run-record
schema, a verdict score, two live-demo URLs, and a README section list. Seven declines, each
recorded so the next session does not relitigate them:

4. **The `backend/` tree.** No `backend/`, `verdict_engine.py`, or `orchestrator.py` exists.
   `compute_verdict` is `app/runlog.py:58`; the orchestrator is `main.analyze()` calling
   `base.run_all()`. Mapped onto `backend/`, as the first batch was.
5. **`requests`.** Not in `requirements.txt`. `urllib.request` is stdlib and the prompt permits
   stdlib, so this was never a reason to add a dependency.
6. **The invented run-record schema** (`run_id, agent, member, pr, findings, status`).
   `RunRecord` is `run_id, pr, written_at, result`. Validating against a second, invented
   schema proves only that the invention is self-consistent — `RunRecord` is the contract.
7. **The read-modify-write of `duration_sec`.** `base.execute` already times all three of its
   exit paths and `write_run_records` persists the result. A second writer that re-reads and
   rewrites the audit trail adds a torn-write failure mode and no data.
8. **The 5/2/1 score, again.** Re-specified in the PR-comment format as `(Score: 12)`. Still
   declined, for the reason above.
9. **The live-demo URLs.** `https://trustgate.vercel.app` and `https://trustgate.onrender.com`
   were requested as "placeholders" for a README that doubles as the lablab submission page.
   Nothing is deployed and the API had one route. Shipping them means a judge who clicks gets
   a dead link and a README that lied to them. Omitted rather than marked, because a marked
   placeholder still reads as an intention.
10. **The five invented checker names** — Security Reviewer, Spec-Conformance, Injection
    Scanner, Dependency Verifier, License Checker. Three of the five do not exist in this
    project and a license checker was never in the design. The Checkers table carries the real
    roster with its real status column instead.
11. **The `orchestrator.py` and `GITHUB_TOKEN` keyword check.** Prompt 7 required the gate to
    contain both. There is no `orchestrator.py`, and the gate posts nothing to the PR. Checking
    for them would report a failure that means nothing. Replaced, with the user's agreement, by
    the six invariants that actually protect the gate — including the *absence* of
    `pull_request_target`, which the old check would never have tested for.


### Not yet built, and named in `AI_CONTEXT.md`

`backend/app/store.py` · `backend/app/checkers/deps.py` (OSV-Scanner — blocked, see K13) ·
`dashboard/`. **`routes/` is no longer on this list**: the two routes the API needs
(`/api/health` and `/api/pr/{pr}/verdict`) are declared inline in `main.build_app()`. There is
still no `POST /analyze` and no HTTP analysis entry point, so `schemas.AnalyzeRequest` remains
referenced by nothing.

**The `secrets` checker is now built** (item 24 below), so the roster is 1 deterministic and 3
semantic. D3's "2 deterministic + 3 LLM" is still incomplete. `runlog.py` (item 25) means the
engine now persists and re-reads verdicts; `sarif.py` and `.github/workflows/trustgate.yml`
(items 33–34) mean a pull request can be blocked — but the workflow has never run on GitHub, so
in practice nothing blocks one yet.

### Created — 2026-09-26, close the fail-opens then build the gate

The audit in §0 of the plan file found a fail-open in the code the project's central claim is
about: `semantic.py` truncated an over-budget diff and told the model nothing, so a large PR
was reviewed *less* thoroughly than a small one and returned `PASS`. Reproduced before fixing —
a 450,075-character diff against the 120,000 budget gave `status: ok`, 0 findings, `PASS`, with
73% of the change silently discarded including a planted credential. After the fix the same input
gives `status: error`, `REVIEW`, `degraded: ["authz"]`.

| # | File | Purpose and architectural justification |
|---|------|--------|
| 33 | `backend/app/sarif.py` | `VerdictRecord` → SARIF 2.1.0. A separate module because no existing file emits one and the format has a second consumer. Two details are load-bearing: `rules[]` always describes the **whole** roster rather than only the checkers that fired today (a catalogue that appeared and disappeared with the findings would make GitHub's dedup unreliable), and `partialFingerprints.primaryLocationLineHash` is a SHA-256 over checker/file/line/evidence — keyed on location and quote, not title, so a reworded title does not orphan an existing alert. `security-severity` maps onto GitHub's published buckets; `precision` is `very-high` for `secrets` and `medium` for the model-derived checkers, which is the one place the heterogeneous roster buys something concrete |
| 34 | `.github/workflows/trustgate.yml` | The gate. Runs on `pull_request`, builds the diff from the merge base, installs gitleaks from a pinned release tarball with a SHA-256 check, runs the engine, writes the verdict to `$GITHUB_STEP_SUMMARY`, uploads SARIF under `if: always()`, then fails the run on `BLOCK` by grepping the captured text. Two decisions are load-bearing and are documented in the file's own header: **`pull_request`, never `pull_request_target`** (the latter runs with a writable token and repository secrets, so executing fork-authored code under it is RCE with the Groq key in reach), and **every action pinned to a commit SHA** (a floating tag in a security gate is remote code execution). It greps the verdict text rather than trusting the exit code because the engine's exit code is 1 on `BLOCK` only, and a `BLOCK` must never skip its own SARIF upload |
| 35 | `backend/tests/test_sarif.py` | 12 tests. `REQUIRED_PATHS` mirrors GitHub's documented required table, so a field GitHub needs and OASIS does not cannot be dropped silently. Also pins fingerprint stability across re-runs, movement on a line change, non-orphaning on a title reword, and `executionSuccessful is False` when the run was degraded |
| 36 | `backend/tests/test_gate.py` | 4 tests. One assertion, four ways: the workflow's `^VERDICT[ \t]+BLOCK` pattern is compiled here and matched against real `render()` output for all three verdicts. A format change that broke the match would silently stop the gate blocking — a fail-open in CI — and nothing else would notice |
| 37 | `backend/samples/example.diff` | A runnable PR carrying a SQL injection, a missing-authorization gap, and a hardcoded key, so the README quickstart is copy-pasteable and every checker has something to say about it |

### Created — 2026-09-26, four pasted prompts mapped onto `backend/`

Four prompts arrived describing a `backend/` tree with a `verdict_engine.py`, a ThreadPoolExecutor
`orchestrator.py`, a run-record schema, and a 5-checker roster. None of that exists here. The
mapping and the four declines are recorded below, because the next session will meet the same
prompts and should not re-derive them.

| # | File | Purpose and architectural justification |
|---|------|--------|
| 38 | `backend/app/comment.py` | `VerdictRecord` → markdown → `POST /repos/{owner}/{repo}/issues/{n}/comments`. `render_comment` is a pure function and is what the tests cover; the network call is three lines. Evidence is escaped and truncated because it is verbatim source — a raw `|` silently adds a table column and a raw newline splits the row, so a comment can be structurally broken by the very content it exists to quote. **Deliberately not wired into `trustgate.yml`**, and the file header says why: under `pull_request` the token is read-only and forks get none, so posting from the gate needs `pull_request_target` (documented in that workflow as RCE with the Groq key in reach) or a GitHub App. Neither exists |
| 39 | `backend/integration_test.py` | A four-check smoke test: API health, run records, the verdict endpoint, and the gate's invariants. Run records are validated with `RunRecord.model_validate_json` — the Pydantic model *is* the contract, so validating against the prompt's invented field list would only have proved the invention self-consistent. The gate check parses the workflow as YAML instead of grepping it, because the file names `pull_request_target` in its own header comment and a substring check reports a working gate as broken. One HTTP call reported 3226 ms against a 5 ms real cost; see K21 |
| 40 | `backend/tests/test_comment.py` | 9 tests over the pure render function: all five severities map, a `|` in evidence does not add a column, a newline does not split the row, backticks in evidence do not end the code span early, long evidence truncates, the checker count comes from the run rather than a constant, and a degraded run names what did not complete. **Severity has five levels, not the three the prompt specified**, and a test asserts every one of them has a glyph |
| 41 | `backend/tests/test_integration.py` | 4 tests over `check_gate`. The load-bearing one asserts that `pull_request_target` *does* appear in the real workflow's prose while `check_gate` still passes — that is the case a naive substring check gets backwards in both directions. A parser change that made the gate check always return true would look exactly like a passing run, which is the same fail-open class `test_gate.py` exists to prevent |

### Modified — 2026-09-26, second pass

| File | Change |
|------|--------|
| `backend/app/checkers/base.py` | `run_all` takes an optional `on_result` callback, fired as each future settles rather than when the gather completes. This is the only way to get true parallel progress out of `asyncio.gather`: a run that takes as long as its slowest checker otherwise prints nothing until the end. Results still return in roster order. One call site, no test call sites, so the signature change is safe |
| `backend/app/main.py` | Live per-checker progress lines, a severity-breakdown summary, a `--dry-run` that prints the roster and needs no credentials, and the `GET /api/pr/{pr}/verdict` route. **The `VERDICT  {verdict}` line is byte-identical** because `test_gate.py` pins the workflow's `^VERDICT[ \t]+BLOCK` pattern against `render()` output — a format change there silently stops the gate blocking. The new summary deliberately does *not* reuse that prefix |
| `README.md` | A Checkers table on the real roster, a setup block, and a Team table. Test count 61 → 74 in all three places it appears |

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
| K9 | `backend/` has **no `__init__.py`**, no `pyproject.toml`, and **no lockfile**. `backend/app/**` imports resolve only because `backend/` happens to be the working directory — running from the repo root fails. `.venv/` holds real packages with **nothing recording those versions in a tracked file** | Medium | **Half closed 2026-09-25.** `backend/requirements.txt` now pins the full installed set from `pip freeze`, so the environment is reproducible and `render.yaml` can build. **Still open:** no `__init__.py` and no `pyproject.toml`, so imports stay cwd-dependent — which is why `render.yaml` needs `rootDir: engine`. That is a workaround for a missing package declaration, not a fix. **Correction:** the earlier text of this entry recorded "pydantic 2.46.5"; that is `pydantic_core`'s version. `pydantic` is **2.13.5** |
| K10 | **Phase 0 is 🔴 ACTIVE and forbids application code, but `backend/app/**` exists.** Either the phase advanced without a roadmap edit, or the code landed outside approved scope. The record cannot distinguish these, and this ledger will not guess | **High** | **Open — Tier 3, team decision, deliberately not resolved by an agent.** Recorded rather than silently fixed. A phase transition is not an agent's call. Blocks a truthful Phase 0 close-out. **Grown again 2026-09-25:** a second session added 3 application files, a schema model, and 3 deploy configs on top of the disputed code. The user approved that batch explicitly, so the edits were authorised — but approval of a batch is not a phase transition, and this entry stays open until the team says which phase this is. **Grown a third time 2026-09-26:** a third session renamed `engine/` → `backend/`, moved six governance docs into `docs/`, rewrote `render.yaml` and `Procfile`, and **deployed to Render** — all under a plan the user approved, and all still under a phase that forbids application code and any git commit. The 🔴 ACTIVE marker has not moved and this agent did not move it |
| K11 | **`.gitignore` used unanchored `data/` and `build/`.** An unanchored pattern with a trailing slash matches at *any* depth, so `data/` was silently excluding `backend/app/data/` and `dashboard/src/data/` — a findings store would have vanished with no error and no warning | Medium | **Fixed 2026-09-25.** Both anchored to the root (`/data/`, `/build/`) with the reason written into the file. Verified with `git check-ignore -v backend/app/data/findings.json` — no match, i.e. tracked — while `git check-ignore -v data/x` still matches. Worth knowing: `git check-ignore` is the check, not reading the file, because the failure mode is a *silence* |
| K12 | **No `GROQ_API_KEY` in this environment and no `.env`.** The inference path has therefore never executed against a live model. The `BLOCK` verdict is implemented and unit-tested through a static provider, but **no real model call has happened** — so no latency, no cost-per-PR, and no per-checker precision exist and none are claimed | **High** | **Status changed 2026-09-26: provisioned, still never exercised.** A `GROQ_API_KEY` is now set in the Render dashboard for `trustgate-api`, and `load_settings()` reads `GROQ_API_KEY` from the environment, so a run on that service *would* reach Groq. **No such run has been made**, so this stays open — the blocker moved from *obtaining a key* to *making a run through the deployed service*. A key existing is not a key having been used. Locally there is still no key and no `.env`. Blocks M4 ("first real verdict"), all of Phase 4's numbers, and the `BLOCK` branch of the demo. `UNVERIFIED — one run through https://trustgate-api-ehib.onrender.com with the key set, or one local run with GROQ_API_KEY exported` |
| K13 | **`deps.py` (OSV-Scanner) is blocked, not merely unbuilt.** OSV-Scanner's JSON gives `id`, `package.{name,version,ecosystem}`, and `source.path` — but **no line number**. `Finding.line` is `Field(ge=1)`, so a package-level CVE has no truthful value for it. Two ways out, both team decisions: (a) allow `line: 0` to mean "package-level, not line-level", which changes a stated success metric — `PROJECT_ROADMAP.md:171` requires 100% of findings to have file + line + quote — and would require rewriting the `line < 1` test; (b) search the manifest for the package name to synthesise a line, which is a heuristic whose accuracy cannot be measured without a corpus | Medium | **Open, deliberately.** Not started rather than shipped wrong. A CVE finding pointing at the wrong line is exactly the "hallucination with a severity label" the constitution forbids, and option (a) weakens a metric the project is scored on. `UNVERIFIED — nothing; the blocker is a schema decision, not a missing fact` |
| K14 | **`secrets.py` has never executed.** The checker has only been exercised through its failure path — where it correctly degrades to `REVIEW` with a named error, which is the behaviour that matters most and is the one thing testable without the binary. Its JSON field names were read from `gitleaks/gitleaks` `report/finding.go` rather than guessed, but no real report has been parsed | **High** | **Partly closed 2026-09-26; still open.** Gitleaks **v8.30.1** `gitleaks_8.30.1_windows_x64.zip` was downloaded to `backend/.tools/` and its SHA-256 verified against the release's own `gitleaks_8.30.1_checksums.txt`: `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`. **The binary was executed on 2026-09-26, later in the same day** — authorised by the user, which is what the earlier denial was waiting on. `./backend/.tools/gitleaks.exe version` → `8.30.1`, matching the workflow's pin. A full working-tree scan returned **3** findings, all `generic-api-key`: `backend/tests/test_secrets.py:18` (entropy 3.66), `demo_target/issue-02-hardcoded-key/config.py:5` (entropy 4.00), and a local `__pycache__/*.pyc` build artifact. The second **matches `cases.json` ground truth exactly** — the same file and line the corpus predicts — so the `UNVERIFIED` caveat recorded in that file is now satisfied. The `.gitleaksignore`-holds-fingerprints claim was re-confirmed against the vendor README, and the contradicting "a `.gitleaks.toml` allowlist would disable the gate" claim was **disproved** by experiment. **Still open:** the checker has still not been driven end-to-end through `python app/main.py` with `GITLEAKS_BIN` pointed at it, so a parsed real report through `checkers/secrets.py` is still untested. `UNVERIFIED — one run of python app/main.py --diff samples/example.diff with GITLEAKS_BIN=./backend/.tools/gitleaks.exe`. The same blocker class as K12: a missing authorisation, not missing code |
| K15 | **A silent-truncation fail-open in `checkers/semantic.py`, live until 2026-09-26.** `body = diff[: self._max_diff_bytes]` dropped everything past 120,000 characters **with nothing in the prompt saying so**. The model obeyed `EVIDENCE_CONTRACT`'s "return an empty findings array" and returned no findings, three checkers reported `status=OK`, and the adjudicator returned **`PASS`** — having reviewed 27% of the diff. Reproduced before the fix: a 450,075-character diff with a planted credential past the cut produced `all checkers completed with no findings`. A large PR was reviewed *less* thoroughly than a small one, invisibly. It was masked only because `secrets` errors without gitleaks (K14), forcing `REVIEW` for an unrelated reason — **installing gitleaks would have made it live** | **Critical** | **Fixed 2026-09-26.** `SemanticChecker.run` now refuses a diff over budget and names `TRUSTGATE_MAX_DIFF_BYTES`; `base.execute` converts the raise to `CheckerResult(ERROR)` and the existing, already-tested fail-closed path yields `REVIEW`. Same input, re-run: `status=error` → `REVIEW`, degraded `['authz']`. Deliberately **refuses rather than chunks** — chunking with the evidence check re-run per chunk is the upgrade if real PRs exceed the budget. `ponytail:` comment in the source names that ceiling. 11 tests in `test_semantic.py` |
| K16 | **Evidence was never checked against the diff.** `EVIDENCE_CONTRACT` *asked* the model for a verbatim quote; nothing verified one. `Finding` enforces only `evidence: NonEmpty`. A model returning `evidence="potential SQL injection here"` passed every gate in the codebase and, at `critical`, reached `adjudicator.py:32` and **`BLOCK`**. Wedge claim 2 was enforced by asking nicely | **Critical** | **Fixed 2026-09-26.** `_quote_present` requires the quote to occur in the body the model was shown; `_to_finding` takes `body` and raises otherwise. A failure discards the **whole batch**, deliberately — the same model produced every quote in it, so the ones that happen to match carry no more assurance than the one that does not. `\r` is stripped from the diff first, so a Windows checkout and LF evidence compare equal. Tested for accept, reject, CRLF, and non-reachability of a fabricated `critical` |
| K17 | **Five `Settings` fields and `VerdictRecord.cost_usd` are pure scaffolding.** `run_budget_s`, `osv_scanner_bin`, `database_path`, `price_per_1k_input_usd`, `price_per_1k_output_usd` are read by nothing. `cost_usd` has exactly one assignment, `runlog.py` → `None`. The token counts that would feed it **are** gathered in `llm/client.py:84-87` and discarded in `semantic.py:40`, which takes only `.payload` | Medium | **Open, recorded.** Cost tracking is not partially implemented; it is not implemented. `AI_CONTEXT.md` now says so. No cost number may be published. `UNVERIFIED — a run with a live key and a `Completion` that reaches `VerdictRecord` |
| K18 | **The constitution had drifted the same way the README did.** `AI_CONTEXT.md:19` read "Greenfield. No application code exists yet" — byte-for-byte the claim already corrected in `README.md` and logged as fixed at `SYSTEM_LEDGER.md:308`, living one file over. Also: a 3-service monorepo of which 1 exists, a directory tree listing 9 phantom files (`routes/`, `sarif.py`, `store.py`, `corpus/`, `dashboard/`, `.github/`) while omitting 7 real ones, and 5 unimplemented promises stated as design — the 4-step fallback chain (step 1 only), the 90s budget, cache-by-input-hash, a shared `httpx.AsyncClient` that is never imported, and "five checkers" | **High** | **Fixed 2026-09-26.** Every one corrected in place and marked built/not-built rather than deleted — the design intent is worth keeping, the false assertion is not. `README.md`'s two contradictory test counts (19 and 28, truth 45) and its orphaned blockquote fragment at 79-81 also fixed. **Root cause is K8, not carelessness:** nothing mechanically forces a close-out, so a document that was true at commit time has no tripwire when the next session lands |
| K19 | **`StaticProvider` is unreachable from the CLI.** `build_provider` returns only `UnavailableProvider` or `GroqProvider`, so with no key and no gitleaks **every run a reviewer can perform today returns `REVIEW` — `BLOCK` and a clean `PASS` are not demonstrable at all.** `WEDGE.md` demo steps 1–3 are therefore not merely unverified, they are unreachable. It is also the only test double for the LLM path, and until 2026-09-26 nothing used it | **High** | **Half closed 2026-09-26.** `test_semantic.py` now uses it, so the LLM path has coverage for the first time. **Still open:** no opt-in path from the CLI. Deliberately **deferred**, not skipped — K12 and K14 are the real unlock, and a fixture path layered on top of two missing credentials would be a demo affordance pretending to be evidence. Rule 00 also requires any verdict a fixture path produces to be labelled unmistakably, because a fabricated `BLOCK` presented as real is the exact failure this project exists to prevent. Not built; flagged rather than quietly done |
| K20 | **The gate has never been executed on GitHub.** `trustgate.yml` parses as YAML, all three actions are SHA-pinned, and each action's `runs.using` was read from its `action.yml` at that tag — `setup-python@v5` and `codeql-action@v3` are both node20 and would fail today, since Node 20 left hosted runners on 2026-09-16. The BLOCK-grep pattern is pinned by `test_gate.py` against real `render()` output. None of that is a run | Medium | **Open, unavoidable — but now measured rather than assumed.** The repository is public, so the absence is checkable, and on 2026-09-26 `GET api.github.com/repos/ammarzia124/TrustGate-IBM-BOB-Hackathon/actions/runs` returned **`total_count: 0`**. That is stronger than `UNVERIFIED`: it is a confirmed zero, and it also explains itself — the workflow triggers on `pull_request` and `workflow_dispatch` only, every commit so far went straight to `main`, and no pull request has ever been opened. `UNVERIFIED — the first run itself; open a pull request against main and read the Actions tab`. Until then, "a gate" is a claim about a file, not about a product |
| K21 | **The smoke test's own health check reported 3226 ms for a request whose real cost is tens of milliseconds.** Not a server problem — `curl` against the same route returned 7–67 ms. Two separate client-side costs, each measured on its own: `urllib.request.urlopen` builds a fresh opener per call and on Windows that construction calls `getproxies()`, which reads the registry (644 ms on the first call, ~5 ms after); and `localhost` resolves to `::1` before `127.0.0.1` while the server binds IPv4 only, so **every** request through the name `localhost` pays a refused connection first — 2054–2292 ms across four runs, consistently | Medium | **Fixed 2026-09-26.** A module-level `ProxyHandler({})` opener is built once, and `--base-url` now defaults to `http://127.0.0.1:8000`. After the fix, five fresh runs of the same check against the same server reported **22, 34, 35, 42, and 60 ms** — so call it ~20–60 ms, not a single number. The 3226 ms figure was a genuine reading *and* a cold first request; both component costs above were what made it large. Both facts are in the source, because a future session that restores the `localhost` default would otherwise have no way to know why it mattered. The general rule: **a latency number is only worth printing if it was measured against a known baseline, and a first measurement is a hypothesis, not a result** |


---

## Next Actions

**In order. Item 1 is a Tier 3 decision and blocks a truthful close-out.**

1. **Resolve K10 — decide what happened to the phase.** Application code exists under a phase
   that forbids it, and **three** sessions have now added to it — the third renamed the
   directory, moved the governance docs, and deployed to Render. Either confirm a
   Phase 0 → 1 → 2 transition happened and update `PROJECT_ROADMAP.md` to say so, or record
   the code as out-of-scope work that needs a decision. **An agent must not make this call** —
   it is a phase transition, which is Tier 3. Until it is resolved, no phase status in
   this repo can be trusted
2. **Make one real run — the two remaining credentials (K12, K14).** A `GROQ_API_KEY` is now
   set in the Render dashboard, so K12 has moved from *blocked* to *provisioned but never
   exercised*; nothing has yet been run through `https://trustgate-api-ehib.onrender.com`.
   `gitleaks` (K14) is absent both locally and on Render's image. One run of each produces a
   real `BLOCK` or a real clean `PASS`, and from the first a latency figure and a cost figure
   — the two numbers the roadmap's success metrics ask for. No amount of coding substitutes
   for either. **A key being set is not a key having been used**
3. **Open a pull request to prove the gate exists (K20).** The GitHub API returns
   `total_count: 0` for workflow runs — the gate has never executed, because every commit so
   far went straight to `main` and the workflow only fires on `pull_request` or
   `workflow_dispatch`. A throwaway PR is a five-minute task that converts the project's
   central claim from *a claim about a file* into *a claim about a product*. Cheapest
   high-value item on this list
4. **Decide K13 — the `deps.py` line-number question.** Either allow `line: 0` for
   package-level findings, which weakens a stated success metric and breaks a test, or accept
   a heuristic line lookup whose accuracy cannot be measured without a corpus. This is a
   schema decision, so it is the team's, and it is the only thing between D3 and completion
5. **Decide the branching strategy** for 6 people (K3). Six people are demonstrably editing one
   repo in parallel. **Superseded in practice 2026-09-26:** all three commits this session went
   straight to `main`, so the risk this entry describes is no longer hypothetical — it happened
   — but nothing was lost, because the restructure was a rename that `git mv` records cleanly
   and the team had no concurrent work in flight. The strategy is still undecided for whoever
   works in parallel next
6. ~~**Commit the uncommitted files.**~~ **Done 2026-09-26.** The working tree is clean:
   `git status --porcelain` returns nothing, all 84 files are tracked, and local `HEAD` equals
   `origin/main` at `2fab917`. `demo_target/` and `bench/` are committed
7. **Confirm workstream owners** A–F (K4). Owner B has three semantic checkers built and one
   deterministic one; owner C has the adjudicator, schemas, and all eight test files. Nobody has
   claimed either
8. **Test the network path.** `run_all`'s timeout branch and the `GroqProvider` response
   parsing are unexercised. `StaticProvider` covers `SemanticChecker` end to end
   (`test_semantic.py`) but not a malformed or slow real response. This needs a key (item 2)
9. **`store.py`, `deps.py`, and `dashboard/` stay unbuilt.** `deps.py` is blocked on K13 above.
   The dashboard is the one thing judges will forgive, and it is the most expensive thing on
   the list

### Closed — 2026-09-26 session

- **K15** — the silent-truncation fail-open. Reproduced before fixing, re-verified after
- **K16** — evidence was never checked against the diff. Now it is, and a bad quote discards
  its whole batch
- **K18** — the constitution had drifted the same way the README had
- **K19, half** — `StaticProvider` now covers the LLM path, closing the "no test exercises the
  model boundary" gap
- **The gate** — `sarif.py` and `.github/workflows/trustgate.yml` written, tested, and
  documented. **Not run** (K20)
- **The gate would have scanned the wrong directory**, and three more workflow bugs, all found
  by reading the workflow against the code rather than by running it
- **A fabricated URL in my own new code**, and a `$schema` URL copied from GitHub's docs that
  404s. Both removed or replaced
- **Old item 9 (build the gate)** — done, in the sense that it is written. The unverified part
  is tracked as K20

### Closed — 2026-09-25 session

- **K1** — `openai/gpt-oss-120b` confirmed on Groq's live strict-mode list
- **K11** — unanchored `.gitignore` patterns anchored; verified with `git check-ignore`
- **K9 half** — `backend/requirements.txt` now pins the installed set. The `__init__.py` /
  `pyproject.toml` half is still open
- **A false claim in `README.md`** — the verdict table said `high` yields `REVIEW`. The code
  blocks on `high` and a test asserts it. Corrected, and the omitted `info` level added
- **A latent `degraded` bug in `runlog.py`** — an empty run reported `degraded: false` beside a
  `REVIEW` verdict, which a dashboard would render as a clean badge. Caught by
  `test_no_runs_never_passes`, fixed in `runlog.py` rather than in the adjudicator
- **An unignored `backend/runs/`** — run records carry `Finding.evidence` verbatim, which for
  `secrets` is a matched credential fragment. Now anchored in `.gitignore`
- **Old item 3 (lockfile)** — done
- **Old item 7 (first test file)** — done, and extended to 28 tests across 2 files
- **Old items 5 and 6** — 5 closed above; 6 narrowed to the gate

### Created — 2026-09-26, the labelled corpus (wedge claim 3, workstream F)

`WEDGE.md` claim 3 — "publish the false-positive rate" — was the largest honest
gap in the repository: the harness did not exist, so the number could not be
produced. It still cannot be, because K12 and K14 are open. What landed is the
harness, and a runner that refuses to fake the number.

| # | File | Purpose and architectural justification |
|---|------|---------|
| 42 | `demo_target/base/` + 10 `issue-NN-*/` | One clean order service and ten copies with **exactly one** planted defect each. One file differs per case, verified by `filecmp` — which is what makes "a finding the ground truth does not list is a false positive" a structural property rather than a claim. A separate `base/` also gives the diff something to be a diff *against* |
| 43 | `bench/cases.json` | Ground truth, `extra="forbid"` and Pydantic-validated at load. `expected_checker` is **`null` for three cases** and `disputed: true` for two. The assignments were made by reading each checker's `FOCUS` string, not by matching case names — which is how `issue-01` (typosquat, no checker: `deps` is unbuilt) and `issue-07` (licensing, never designed) came out with no owner. Those rows are the corpus half of wedge claim 1 |
| 44 | `bench/run_benchmark.py` | Generates each diff with `difflib`, invokes the **shipped CLI** exactly as the gate does, reads the verdict back with the same `compute_verdict` call `main.py:18` makes. No analysis path of its own. Enforces one rule at three levels: an incomplete checker gets no rate, a **degraded case is not scored at all**, and the run ends `INCOMPLETE` rather than `PASS` |
| 45 | `bench/README.md`, `demo_target/README.md` | The `PYTHONIOENCODING` engine bug below, and the self-reference problem the corpus creates for the gate |
| 46 | `.github/gitleaks.toml` | A two-path allowlist that stops the gate blocking every PR on our own planted fixtures. `[extend] useDefault = true` keeps gitleaks' full default ruleset active — without it the file would carry no `[[rules]]` and the secrets gate would silently detect nothing, which is the failure mode this repo treats as worse than a false positive. Both patterns are anchored `^…$` and use `'''` literal strings, because `\.` inside a TOML `"""` string is an invalid escape and gitleaks refuses to start. **Placed in `.github/`, not the repo root, and that placement is load-bearing** — see decision 3a |
| 3a | *Decision — gate-only scoping* | `--config`'s precedence list ends in `(target path)/.gitleaks.toml`, and the target path is `--workspace`, which is `trustgate/` for the gate **and** for `bench/run_benchmark.py`. A config inside that directory would therefore be auto-discovered by the benchmark too, and would silence `demo_target/issue-02-hardcoded-key` — recorded in `cases.json` as `expected_checker: secrets`, `expected_line: 5`, `disputed: false`, i.e. the corpus's **one** deterministic-detection case. Suppressing the gate's false positive that way would turn a true positive into a guaranteed false negative and corrupt the headline false-positive rate. So the config sits outside the scan target path and only `trustgate.yml` opts in, via `GITLEAKS_CONFIG`. Verified both directions on the real tree: with the env var the two fixtures are suppressed, without it all three findings return. **2026-09-26 restructure: the target path stopped being the repo root and became `trustgate/`, which puts `.github/gitleaks.toml` *further* outside it. The decision holds and gets stronger, and the two allowlist patterns need no edit — they are relative to the scan target, so `^demo_target/…` still matches from inside `trustgate/`** |

#### Four things found while building it

1. **The engine crashes when its output is piped on Windows — a real defect, not
   a harness quirk.** `app/main.py:26`'s `_log` prints `→` (U+2192). Under
   `subprocess(capture_output=True)`, Python falls back to cp1252 and raises
   `UnicodeEncodeError: 'charmap' codec can't encode character '→'`, killing
   the run before a single record is written. The Verification Log's "Emoji
   survive stdout on this platform — checked, not assumed" is therefore **true
   but narrower than it reads**: it holds for an interactive terminal and not for
   a pipe. `python app/main.py … | tee` fails today. The one-line fix
   (`sys.stdout.reconfigure(encoding="utf-8")` in `main()`) is **not applied** —
   it is outside the scope the corpus was built under. The runner works around it
   with `PYTHONIOENCODING` in the child env and says so.
2. **A crash and a `BLOCK` are indistinguishable by exit code.** The engine exits
   1 on `BLOCK`; an unhandled traceback also exits 1. The runner's first version
   read `returncode not in (0, 1)` and silently scored a crashed run as a
   verdict. It now scans stderr for `Traceback` first. Caught only because the
   first real run produced *no run records at all* and the empty result looked
   like a clean miss.
3. **`.gitleaksignore` cannot suppress the corpus's own secret — but a
   `.gitleaks.toml` can, if it carries `[extend] useDefault`.** The vendor README
   is explicit that `.gitleaksignore` holds finding **fingerprints**, not paths,
   so a path line would have been silently inert — the exact failure mode Rule 00
   exists to prevent. That half of the finding stands and was re-verified this
   session. The other half — that a config carrying only an `[[allowlists]]`
   block "would disable the gate" — **was wrong, and executing the binary is what
   proved it.** gitleaks' config is replacement rather than merge *only* when the
   replacement carries no rules of its own; `[extend] useDefault = true` keeps the
   entire default ruleset live while appending an allowlist. Verified against
   v8.30.1: `useDefault` alone still reports the finding; an allowlist naming the
   file suppresses it; an allowlist naming a *different* file does not. A third
   option existed that this entry never considered — vendoring the whole default
   config — and it is now unnecessary, because `useDefault` gets the same result
   without pinning the ruleset against gitleaks upgrades. `.github/gitleaks.toml`
   now exists. See decision 3a for why it is scoped to the gate.
4. **`issue-05-unsafe-deserialize` is not planted.** A reachable
   `pickle.loads` on client-controlled bytes was **declined by the sandbox
   classifier as an RCE surface** and was not worked around. `cases.json` marks
   it `expected_line: null` and the runner skips it and says why, rather than
   reporting a false negative for a fixture that does not exist.

#### Declined again on 2026-09-26, same reasons

A tenth pasted prompt repeated the `backend/` tree, the five invented checker
names, the 5/2/1 score, a `ThreadPoolExecutor` orchestrator, a `frontend/` with
five named components, and instructions to move `AGENTS.md`, `AI_CONTEXT.md`,
`PROJECT_ROADMAP.md`, and `SYSTEM_LEDGER.md` into `docs/`. All declined:

- **The renames.** `secrets.py` → `dependency_verifier.py` asserts a checker
  that does not exist (`deps` is unbuilt, K13); a `license_checker.py` was never
  designed. Renaming working, tested code to describe capabilities the repo lacks
  is the failure this project exists to catch, pointed the other way.
- **`AGENTS.md` → `docs/BOB_USAGE.md`.** `AGENTS.md` is the portable agent-rules
  spine read by Bob, Cursor, Codex, and Aider — it is not a Bob usage log, and
  nothing has ever been written to it. `.bob/rules/` reference the other three
  governance files by bare name in 15 places, and
  `01-planning-governance.md:17` defines the **Tier 1 approval boundary** by
  pointer into `PROJECT_ROADMAP.md`'s deliverables table. Moving them makes
  every boot-sequence step open a file that is not there, and if the Tier 1
  boundary silently resolves to nothing, every edit reclassifies from no-approval
  to one-line confirm.
- **The 5/2/1 score, fourth time.** Unchanged: five `low` findings would score 5
  and `BLOCK` a PR the current rule reviews.
- **The `frontend/`.** It does not exist — zero `.jsx`/`.tsx`/`package.json` in
  the repository. `vercel.json` declares `npm run build` at a root with no
  `package.json` and has never been deployable; `README.md` already says so.



### Next session must pick up first

> Read `AI_CONTEXT.md`, `PROJECT_ROADMAP.md`, and `SYSTEM_LEDGER.md`. **Note that application
> code already exists under `backend/app/` — do not rebuild it.** The first action is item 1
> above: the K10 phase-scope decision, which is Tier 3 and belongs to the team, not an agent.
> **19 files are untracked and 10 modified — review them before anything else.** Then item 2:
> a `GROQ_API_KEY` and a gitleaks binary are the two missing credentials, and either one turns
> a plausible product into a demonstrated one. The gitleaks binary is already downloaded and
> checksum-verified at `backend/.tools/gitleaks.exe`; **it has never been run**, because
> executing it was denied. Authorising that one command is cheaper than any remaining build
> task. Item 3 (the K13 `deps.py` schema decision) is the cheapest thing on the list that only
> the team can unblock.
>
> **`backend/app/comment.py` has never posted anything.** It has been run with `--dry-run`
> against real run records and its markdown was inspected, but no API call has been made, so
> the GitHub request itself is unverified. Point it at a throwaway PR before a real one.
>
> **Do not reintroduce** the 5/2/1 score, the `forced_block` substring rule, a `PASS` on an
> empty `runs/` directory, the two live-demo URLs, or the five invented checker names. All were
> specified in the pasted prompts and all were declined on the record, above.

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
| 2026-09-25 | **K11 found and fixed — `.gitignore` anchoring** | `git check-ignore -v backend/app/data/findings.json` matched the unanchored `data/` rule, confirming nested data directories were being silently excluded. Fixed and re-verified: the nested path no longer matches while root `/data/` still does |
| 2026-09-25 | **Baseline commit `61150f0`** | 21 files. Tree checked for `.venv`, `*.pyc`, `*.sarif`, and `.env` — none present |
| 2026-09-25 | **Adjudicator tests written and run** | 19 tests, 19 passed, Python 3.14.3 / pytest 9.1.1. Both D5 cases pass. Three initial failures were **mine**, not the code's: two over-specified assertions on the `reason` string, and one test that used Pydantic v2's `model_copy(update=...)`, which bypasses validation by design. The real validator was verified directly before that test was rewritten to construct `Finding` properly |
| 2026-09-25 | **End-to-end run with no API key** | `python app/main.py --diff app/schemas.py` → `REVIEW`, "no findings, but 3 of 3 checkers did not complete", all three `ProviderUnavailable: GROQ_API_KEY is not set`. This is wedge claim 1 working. Error paths also verified: empty diff → exit 2, missing file → exit 2 |
| 2026-09-25 | **HTTP surface verified in-process** | `fastapi.testclient.TestClient` against `build_app()`: `/api/health` → 200 `{"ok": true}`, unknown route → 404, CORS headers present. Verified in-process rather than against a live port because `pkill -f "app/main.py"` was denied by the sandbox classifier, and that denial was not worked around |
| 2026-09-25 | **False claims found and corrected in the docs** | `README.md:8` said "No application code exists yet" while 10 files existed. `WEDGE.md:71-73` said the false-positive rate is published "which we do" with no corpus in the repo. `WEDGE.md:94` promised a fault-injection run across 5 checkers; 3 exist. All three corrected. **The `WEDGE.md` findings were found by reading the documents against the disk, not by running a checker** — which is precisely the gap K8 describes |
| 2026-09-25 | **Gitleaks CLI and JSON schema read from vendor docs, not memory** | `gitleaks dir --report-format json --report-path <file> <dir>` confirmed from the project README. The `Finding` struct read from `report/finding.go`: `RuleID`, `StartLine`, `Match`, `Secret`, `File` confirmed; `Line` carries `json:"-"` and is **absent** from the built-in report. Exit codes: 0 clean, 1 leaks *or error* (so exit code alone cannot distinguish them — the implementation keys on whether the report file exists) |
| 2026-09-25 | **OSV-Scanner v2 CLI and JSON schema read from vendor docs** | `osv-scanner scan --format json <dir>`, JSON to stdout, confirmed. Result shape confirmed: `results[].source.{path,type}`, `results[].packages[].package.{name,version,ecosystem}`, `.vulnerabilities[].{id,aliases}`. **`summary` and `severity` are inside the abbreviated "Full OSV" record and are NOT confirmed** — so no parser was written against them. This reading is what produced the K13 blocker: the schema carries no line number |
| 2026-09-25 | **34 tests pass** (19 adjudicator + 9 runlog + 6 secrets), Python 3.14.3 / pytest 9.1.1. The 19 pre-existing tests were re-run after every change and never modified |
| 2026-09-25 | **Run-log round trip verified end to end** | `python app/main.py --diff app/schemas.py --pr trustgate#42` wrote 3 records; `python -m app.runlog --pr trustgate#42` returned the identical verdict and reason from disk. An unmatched PR returned `REVIEW` / "no checkers ran" — **not** the `PASS` the pasted prompt specified. A missing `--runs-dir` returned exit 2 with the exact path in the message |
| 2026-09-25 | **4-checker roster run; `secrets` degrades correctly** | `secrets` reported `FileNotFoundError: [WinError 2]` and the run read `REVIEW`, "no findings, but 4 of 4 checkers did not complete". This is a **fourth distinct failure mode** — a missing binary on disk, as opposed to K12's missing key — and the fail-closed contract held for it without being designed for it |
| 2026-09-25 | **Two defects in `secrets.py` found by its own tests** | gitleaks' `Match` **contains the secret**, so quoting it verbatim would have written credentials into `runs/*.json` and SARIF; and `Path.is_absolute()` returns False for POSIX-leading paths on Windows, so path relativisation silently never ran on the team's own platform. Both fixed, both covered. Recorded because in both cases the original code *read* correctly — see the correction section above |
| 2026-09-25 | **`/backend/runs/` gitignore rule verified with `git check-ignore`** | `git check-ignore -v backend/runs/run_x_secrets.json` matches the new anchored rule, while `backend/app/runs/note.py` does not. The K11 method — check the matcher, don't read the file — because the failure mode is a silence |
| 2026-09-25 | **Deploy config parses** | `render.yaml` loads under `yaml.safe_load`, `vercel.json` under `json.load`. Neither has been deployed; `vercel.json` has no frontend to build and the FastAPI app exposes one route |
| 2026-09-26 | **A-to-Z audit run** — two agents, one over unread engine code, one over every document checked against disk. At audit time: 32 files, 16 Python, 34 tests confirmed by `pytest --collect-only`; Python 3.14.3, pydantic 2.13.5. `GROQ_API_KEY` unset, `gitleaks` off PATH — re-confirming K12 and K14. **The tree is 34 files and 45 tests after this session's fixes; see Current State** |
| 2026-09-26 | **K15 reproduced BEFORE the fix** | A 450,075-character diff against a 120,000 budget: `body = diff[:max]` dropped 330,075 characters with no marker in the prompt. The model returned no findings, three checkers reported `status=ok`, and the adjudicator returned **`PASS`** — "all checkers completed with no findings" — having reviewed 27% of the change. **This is the central claim failing, caught by reading the code against the constitution rather than by any test** |
| 2026-09-26 | **K15 fixed and re-verified on the same input** | `status=error`, `ValueError: diff is 450075 characters, over the 120000 budget; raise TRUSTGATE_MAX_DIFF_BYTES…`, verdict `REVIEW`, degraded `['authz']`. No new fail-closed path was added — `base.execute` and the adjudicator already did this |
| 2026-09-26 | **K16 fixed** — a fabricated `critical` can no longer reach the adjudicator | Evidence must now occur in the body the model was shown. Covered for accept, reject, one-bad-quote-discards-the-batch, CRLF-vs-LF, and non-reachability as a `BLOCK` |
| 2026-09-26 | **45 tests pass** (19 adjudicator + 9 runlog + 6 secrets + 11 semantic), Python 3.14.3 / pytest 9.1.1. The 34 pre-existing tests were re-run after every change and never modified |
| 2026-09-26 | **One new test was wrong and was corrected** | `test_an_over_budget_diff_degrades_to_review_and_never_passes` asserted the adjudicator's `reason` contains "budget". It does not — the reason carries the degraded count and the budget text lives in the checker's `error`. The code was right and the assertion was not; split so each layer is asserted against what it actually guarantees |
| 2026-09-26 | **End-to-end CLI run against a new `samples/example.diff`** | `python app/main.py --diff samples/example.diff --pr 42` → `REVIEW`, "no findings, but 4 of 4 checkers did not complete", 27 ms, 4 records written. `secrets` failed with `FileNotFoundError: [WinError 2]` — a fourth confirmation of K14 |
| 2026-09-26 | **Run-log round trip re-verified, including the no-records case** | `python -m app.runlog --pr 42` returned the identical verdict from disk. `--pr 999` returned `REVIEW` / "no checkers ran" with **`degraded: true`** — the empty-`degraded_checkers` bug found earlier stays fixed |
| 2026-09-26 | **K18 — constitution drift corrected** | `AI_CONTEXT.md:19` read "Greenfield. No application code exists yet" — the claim already corrected in `README.md` and logged as fixed at line 308 above, living one file over. Also corrected: a 3-service monorepo of which 1 exists; a tree listing 9 phantom files while omitting 7 real ones; 5 unimplemented promises stated as design. `README.md`'s two contradictory test counts (19 and 28, truth 45) and its orphaned blockquote fragment also fixed. **Root cause is K8, not carelessness** |
| 2026-09-26 | **SARIF validated against BOTH required layers, not one** | The OASIS schema was downloaded from `https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json` (HTTP 200, 115,632 bytes) and its constraints extracted programmatically rather than from memory. **The `$schema` URL in GitHub's own docs example 404s** — 14 bytes of `404: Not Found` — so the file was not the one to copy. Validating against OASIS alone would have missed three of GitHub's requirements: `rules[]` on the driver, `partialFingerprints`, and `shortDescription`/`fullDescription`/`help` per rule. Result: `FAILURES: none — satisfies both layers` |
| 2026-09-26 | **A URL invented inside my own new code, caught before shipping** | The first draft of `sarif.py` carried `TOOL_URI = "https://github.com/gitleaks/gitleaks"` with a comment that did not justify it. `informationUri` is optional, so the field was deleted rather than the URL invented. Same class as the `$schema` 404: the temptation is to write a plausible link because a link looks like rigor |
| 2026-09-26 | **A design flaw in my own SARIF code, caught by my own test** | `rules[]` was emitted only for checkers that had findings, so a run with no `secrets` finding produced a report with no `secrets` rule. That contradicts the schema's meaning — a rule catalogue describes what the tool *can* find — and it makes GitHub's dedup unreliable. Fixed to always emit the full roster. The test (`KeyError: 'secrets'`) was right and the code was wrong; a follow-on test break was then fixed in the *test*, because indexing `rules[0]` is not a contract |
| 2026-09-26 | **The gate would have scanned the wrong directory — caught by self-review** | `main.py` hardcoded `workspace="."`, and the workflow does `cd engine`, so gitleaks would have scanned `backend/` rather than the checked-out PR. Found by reading the workflow against the code, not by running either. Fixed with a `--workspace` flag, defaulting to `"."` for local use, passed as `--workspace ..` in CI. **Three more workflow bugs found in the same pass**: an `echo` referencing a step output that was never set; a `continue-on-error: true` on the gitleaks step that would have swallowed the checksum-mismatch `exit 1` and thereby **contradicted its own comment**; and a malformed `pip install --require-hashes=false` |
| 2026-09-26 | **A wrong env var name, found by grepping rather than assuming** | The workflow set `TRUSTGATE_GITLEAKS_BIN`. `config.py` reads `GITLEAKS_BIN`. The wrong name was a silent no-op that happened to work because gitleaks was also on `PATH` — a bug that would have surfaced only in the environment where PATH lookup failed, which is exactly the environment the flag exists for |
| 2026-09-26 | **Every action's runtime read from its own `action.yml`, not from a tutorial** | `actions/checkout@v7` → node24, `actions/setup-python@v7` → node24, `github/codeql-action/upload-sarif@v4` → node24. Meanwhile `@v5` setup-python and `@v3` codeql-action are both node20 and **fail today**, and nearly every SARIF example on the internet still names the broken v3. The `v4` tag is *annotated*, so `git/ref/tags/v4` returns an object of type `tag` that must be dereferenced once more to reach the commit — a detail that silently yields a non-SHA and defeats the pin |
| 2026-09-26 | **Gitleaks v8.30.1 downloaded and checksum-verified, never executed** | `gitleaks_8.30.1_windows_x64.zip` SHA-256 `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`, matched against the release's own `gitleaks_8.30.1_checksums.txt`. Stored at `backend/.tools/`, gitignored. **The run was denied** by the sandbox classifier as executing an unauthorised third-party binary, and was not worked around or re-attempted. K14 stays open |
| 2026-09-26 | **Two shell commands denied, and not worked around** | `rm -rf /tmp/tg-sarif` (irreversible local destruction — unnecessary, a fresh directory did the job) and `./.tools/gitleaks.exe version` (see the row above). Both denials are recorded here because a session that quietly retries a denial is worse than one that stops |
| 2026-09-26 | **The CLI's SARIF is read back off disk, not rebuilt in memory** | `analyze()` calls `compute_verdict(pr, runs_dir)` and hands *that* to `write_sarif`, rather than rebuilding from the in-memory `results`. Two code paths producing two verdicts from one run is a disagreement waiting to be discovered by a judge reading the run log and the Code Scanning tab side by side |
| 2026-09-26 | **61 tests pass** (19 adjudicator + 9 runlog + 6 secrets + 11 semantic + 12 sarif + 4 gate), Python 3.14.3 / pytest 9.1.1 | The 34 pre-existing tests were re-run after every change and never modified. `pytest` re-run once more at the end of the documentation pass to confirm the count before it was written down — the count is now stated as measured, not as remembered |
| 2026-09-26 | **SARIF produced end to end and inspected** | 4 rules, 0 results, `executionSuccessful: false` — correct, since that run was degraded. The zero results are the honest outcome of a run where no checker completed, not a silent success |
| 2026-09-26 | **Ledger file count derived, not adjusted** | `find . -type f` with the exclusions now written into the file gives **38** (was written as 34 an hour earlier, when `sarif.py`, the workflow, two test files, and the sample diff did not yet exist). `git status --porcelain` gives 24 lines = 8 modified + 15 untracked files, because `.github/` and `backend/samples/` are each one untracked *directory* holding one file. **Fourth time this number has been wrong, every time because the ledger was written before the session's own edits finished** |
| 2026-09-26 | **Four pasted prompts (7–10) mapped onto `backend/`, and seven requirements declined on the record** | Every mismatch verified by reading the file, not inferred: no `backend/`, no `verdict_engine.py`, no `orchestrator.py`, `requests` absent from `requirements.txt`, `RunRecord` is `{run_id, pr, written_at, result}` and not the prompt's five fields, `duration_ms` already measured on all three `base.execute` exit paths, four checkers not five, and `trustgate.yml` contains neither `orchestrator.py` nor `GITHUB_TOKEN`. The 5/2/1 score, the two live-demo URLs, the five invented checker names, the invented schema, and the read-modify-write are all declined above with reasons |
| 2026-09-26 | **Emoji survive stdout on this platform — checked, not assumed** | `sys.stdout.encoding` is `utf-8` and `✅` round-trips, so the progress logger needs no `reconfigure`. The PowerShell *console* display strips the glyph, which looks identical to a failure and is not one. Worth knowing before a teammate "fixes" a rendering bug that does not exist |
| 2026-09-26 | **Live progress and `--dry-run` verified against a real run** | `python app/main.py --diff samples/example.diff --pr 42` printed 4 starting lines and 4 completion lines with per-checker wall time, then the summary. `--dry-run` printed the roster and exited 0 **with no API key and no gitleaks** — which is the point, since K12 and K14 mean a real run cannot get past `REVIEW` today |
| 2026-09-26 | **The four smoke checks pass against a live server, and all three failure paths were proven to fail** | `python integration_test.py --pr 42` → all four ✅, verdict `REVIEW` with the degraded note, 6 gate invariants, 3 actions SHA-pinned. Then, deliberately: server down → ❌ with the exact `WinError 10061`; missing runs dir → ❌; and a hand-written workflow using `pull_request_target` and two floating tags → ❌ on all five of its real defects. **A smoke test that has only ever printed ✅ has not been tested** |
| 2026-09-26 | **K21 — a 3226 ms health check that really costs tens of milliseconds** | `curl` on the same route: 7–67 ms. `socket.create_connection` to `127.0.0.1`: 27 ms. `urllib` to `127.0.0.1`: 743 ms. `urllib` to `localhost`: 2226 ms. Bisected to a per-call `getproxies()` registry read (one-off 644 ms) and IPv6 `::1` fallback on the name `localhost` (recurring 2054–2292 ms over four runs). **After the fix, five fresh runs of the whole check reported 22, 34, 35, 42, 60 ms** — the honest claim is a range, and the earlier single "24 ms" was one draw from it, not the value. An intermediate reading of 355 ms on a later run is why the range is stated rather than a figure. This number would have been read aloud in a demo |
| 2026-09-26 | **74 tests pass** (19 adjudicator + 9 runlog + 6 secrets + 11 semantic + 12 sarif + 4 gate + 9 comment + 4 integration), Python 3.14.3 / pytest 9.1.1 | The 61 pre-existing tests were re-run after every change and never modified. `test_gate.py` matters most here: `render()` gained a summary line, and the `^VERDICT[ \t]+BLOCK` pattern the workflow greps for still matches — which is why the summary deliberately does not reuse the `VERDICT  ` prefix |
| 2026-09-26 | **`python -m pytest` from `backend/` collects cleanly** | `integration_test.py` matches pytest's `*_test.py` default glob. Checked rather than assumed: 74 tests collected, no import collision, no error. A name that looks like a test file but is not one is worth confirming rather than renaming on suspicion |
| 2026-09-26 | **Ledger counts derived, not adjusted** | 42 files (24 `.py` + 11 `.md` + 7 config) by the documented `find` rule. `git ls-files --others --exclude-standard` returns 19 untracked; `git status --porcelain` gives 29 lines = 10 modified + 19 untracked, because `.github/` and `backend/samples/` are each one untracked *directory*. **23 committed + 19 untracked = 42, reconciling with the filesystem count** — the two independent methods agreeing is what makes both numbers trustworthy, and it is the check the previous four wrong counts lacked |
| 2026-09-26 | **The engine crashes when its stdout is piped on Windows — a real defect, not a harness quirk** | `app/main.py:26`'s `_log` prints `→` (U+2192). Under `subprocess(capture_output=True)` Python falls back to cp1252 and raises `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' at position 11`, exiting before any record is written. **This narrows an earlier entry in this same log**: "Emoji survive stdout on this platform — checked, not assumed" is true for an interactive terminal and false for a pipe. `python app/main.py … \| tee` fails today. The one-line fix (`sys.stdout.reconfigure(encoding="utf-8")`) is **not applied** — out of the corpus build's scope. Found by the corpus, not by reading the code |
| 2026-09-26 | **A crash and a `BLOCK` are indistinguishable by exit code** | The engine exits 1 on `BLOCK`; an unhandled traceback also exits 1. The benchmark runner's first version tested `returncode not in (0, 1)` and would have scored a crashed run as a verdict. It now scans stderr for `Traceback` before trusting the code. Caught only because the first real run produced **no run records at all** and the empty result read as a clean miss — the same shape as the K15 fail-open, one layer up |
| 2026-09-26 | **A degraded case was being scored as a false negative** | With all four checkers degraded, every expected-checker case reported `fn`. True arithmetic, false meaning: nothing had run, so nothing had been missed. The runner now refuses to score any case whose `VerdictRecord.degraded` is true, and reports it as `degraded - not scored`. The per-checker rule (no rate without a clean run) already existed; this extends it to the case level |
| 2026-09-26 | **`.gitleaksignore` cannot do what it was going to be used for** | Read from the vendor README rather than assumed: it holds finding **fingerprints**, not paths, so the path-based ignore this session set out to write would have been silently inert. The alternative — a root `.gitleaks.toml` with only an `[[allowlists]]` block — is worse, because gitleaks' config is **replacement, not merge**: no `[[rules]]` means nothing is detected and the secrets gate becomes a silent no-op. **Neither was added.** A visible false positive on one fixture beats an invisible dead gate; the real fix is the team's |
| 2026-09-26 | **K12 and K14 reproduced through an independent code path** | The benchmark drove the real CLI across 9 planted cases. `secrets` → `FileNotFoundError: [WinError 2]` (gitleaks absent, K14); `authz`/`injection`/`business` → `ProviderUnavailable: GROQ_API_KEY is not set` (K12). Both blockers confirmed by a second, unrelated harness, and the run correctly ends `INCOMPLETE` with **no rate printed for any checker** |
| 2026-09-26 | **This ledger's own test count was wrong twice** | Current State said 76, the log's last entry said 74, and disk says **79** — `test_adjudicator.py` holds 22 tests and was recorded as 19. Derived from `pytest --collect-only` per file this session, not adjusted to match a remembered total. Sixth time this file has carried a wrong count |
| 2026-09-26 | **`issue-05-unsafe-deserialize` left unplanted, on purpose** | Writing a reachable `pickle.loads` fixture was **declined by the sandbox classifier as an RCE surface** and was not re-attempted through another tool. `cases.json` carries `expected_line: null` and the runner skips the case with the reason printed, so the corpus reports 9 of 10 rather than a fabricated 10 |
| 2026-09-26 | **Tenth pasted prompt mapped, five requirements declined again** | The `backend/` rename, the five invented checker names, the 5/2/1 score, the `frontend/`, and moving the four governance files into `docs/`. Each declined on evidence and each recorded with its reason, so the next session does not re-derive them. The `docs/` move is the one with a silent cost: `01-planning-governance.md:17` defines the Tier 1 approval boundary by pointer into `PROJECT_ROADMAP.md`, so relocating that table breaks the approval model rather than just a path |
| 2026-09-26 | **`backend/` → `backend/` and the governance docs → `docs/` are DONE, by approval, superseding the entry above** | `git mv` throughout, so all 28 backend files and all 6 docs carry history (`R100`/`R09x` on every one). Root `AGENTS.md` became a 561-byte pointer to `docs/AGENTS.md` rather than disappearing, because Claude Code, Cursor, Codex, Aider and Bob all load that filename from the **repo root** — a bare move would have silently disabled the rules for all six people. `SYSTEM_LEDGER.md` history is deliberately NOT swept for `backend/`; the old entries describe runs that happened under that name | |
| 2026-09-26 | **`uvicorn app.main:app` did not exist, and would have failed on the first Render deploy** | `backend/app/main.py` had only `build_app()` (line 126) — no module-level `app`. The deploy command requested in the prompt would have raised `AttributeError: module 'app.main' has no attribute 'app'`. Fixed with one line, `app = build_app()`; `build_app()` is pure (constructs a `FastAPI`, registers routes, no I/O) so import-time is safe. **Verified, not assumed:** `from app.main import app` resolves, and `uvicorn app.main:app` was actually booted and `GET /api/health` returned HTTP 200 `{"ok":true}` | |
| 2026-09-26 | **`rootDir: backend` and `cd backend` are mutually exclusive** | Render runs the start command with cwd = `rootDir`, so the requested pair — `buildCommand: pip install -r backend/requirements.txt` and `startCommand: cd backend && …` — only works with **no** `rootDir` key, i.e. repo root. The `rootDir: engine` that was in the committed `render.yaml` was removed rather than re-pointed. | |
| 2026-09-26 | **`RUNS_DIR` in the committed `render.yaml` was dead config** | `load_settings()` in `backend/app/config.py` reads only `GROQ_API_KEY`, `TRUSTGATE_*`, `GITLEAKS_BIN`, `OSV_SCANNER_BIN`, `TRUSTGATE_DB`. The runs directory is `Path("runs")` relative to cwd (`runlog.py:15`) and was never configurable. Dropped from the blueprint rather than carried forward as a setting that does nothing. | |
| 2026-09-26 | **The first path sweep missed the two references that actually execute** | Replacing the token `backend/` left `cd engine` (`.github/workflows/trustgate.yml:115`) and `REPO_ROOT / "engine"` (`bench/run_benchmark.py:37`) untouched, because neither has a trailing slash. Both are load-bearing: the first would have broken the gate on every PR, the second would have put the bench harness on a directory that no longer exists. Caught by a follow-up `git grep` for the bare word, not by the sweep. **81 tests pass before and after the move**, and the harness reports `INCOMPLETE` for the expected reasons (K12 `GROQ_API_KEY` unset, K14 gitleaks absent) | |
| 2026-09-26 | **`trustgate-api` is LIVE on Render — `https://trustgate-api-ehib.onrender.com`** | Deployed from the `render.yaml` blueprint at commit `3ae53f3`. `/api/health` returned `{"ok":true}` and `/api/runs` returned `{"count":0,"unreadable":[],"runs":[]}`, both confirmed in the browser, not inferred from the deploy log. **`count: 0` is the correct answer, not a failure**: `runs/` is gitignored, so a fresh deploy starts with an empty directory and stays empty until an engine run writes records. Two facts that do NOT live in the repo and cost a future session time to rediscover — the `-ehib` suffix is generated by Render, not a name anyone chose, and `GROQ_API_KEY` is `sync: false` in the blueprint so Render creates the service **without** it and it must be added by hand in the dashboard. Without that key three of the four checkers degrade to `REVIEW` | |
| 2026-09-26 | **The HTTP API is read-only over run records — it cannot produce a verdict** | All three routes (`/api/health`, `/api/runs`, `/api/pr/{pr}/verdict`) read. Nothing is written over HTTP: a verdict comes from the engine CLI (`python app/main.py --diff … --pr N`), which today runs in GitHub Actions on a pull request. Worth stating plainly so "the live URL shows no findings" is not read as a broken deployment | |
| 2026-09-26 | **The free plan spins down after ~15 min idle** | Render's own banner on the Logs page, and the reason the first request after an idle period can take 30–60 s. A cold start in a timed demo is a real failure mode, so the health URL should be opened once immediately before demoing. Measured only as Render's documented behaviour — no cold-start timing was measured in this session, so none is claimed | |
| 2026-09-26 | **The gate has never run, and that is now a measured zero rather than an assumption** | `GET api.github.com/repos/ammarzia124/TrustGate-IBM-BOB-Hackathon/actions/runs` returns **`total_count: 0`**. K20 recorded this as `UNVERIFIED`; the repository is public, so the absence was checkable and simply had not been checked. It also explains itself: the workflow triggers on `pull_request` and `workflow_dispatch` only, every commit this project has made went straight to `main`, and no pull request has ever been opened. **Opening one throwaway PR is now the cheapest high-value item on the list** and would move the project's central claim from *a claim about a file* to *a claim about a product* | |
| 2026-09-26 | **Seventh wrong test count, and the file is now self-consistent** | Re-derived per-file with `pytest --collect-only` after the rename: adjudicator 22, **runs 13**, sarif 12, semantic 11, comment 9, secrets 6, integration 4, gate 4 = **81**. The Current State table said 79, "Metrics deliberately absent" two sections below said 76, and the Verification Log said 74 — **three sections of one file disagreeing about the same measured quantity.** `test_runs.py` was recorded as 11 when it holds 13. All now read 81. The root cause is unchanged and is K8, not carelessness: nothing mechanically forces a document to be re-read after the work it describes, so a number that was true at commit time has no tripwire when the next session lands | |
| 2026-09-26 | **The ledger's own history was swept, and the one place that is deliberately not a transcript is marked** | Renaming `engine/` → `backend/` left ~70 historical references pointing at a directory that no longer exists. For a file whose entire job is letting a session recover state, a dangling path is worse than a rewritten one, so the sweep was applied to the history as well as the live sections. A note at the head of the File Ledger now says so explicitly, so nobody reads a 2026-09-25 entry as evidence the path was always `backend/`. The `git mv` renames preserve the original paths in history | |
