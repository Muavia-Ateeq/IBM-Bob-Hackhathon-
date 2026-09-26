# AGENTS.md — Agent Rules for TrustGate

> Read `AI_CONTEXT.md`, `PROJECT_ROADMAP.md`, and `SYSTEM_LEDGER.md` before starting work.
> This file is the portable spine. IBM Bob additionally loads `.bob/rules/`.
> `AGENTS.md` is read by Bob, OpenCode, Codex, Cursor, Aider, and most other agents;
> `.bob/rules/` is read **only** by IBM Bob. Neither replaces the other.

---

## 1. Authenticity

Every technical claim in this repository must be verifiable.

- No hallucinated APIs. Do not reference a function, parameter, CLI flag, model ID, or
  header that you did not read in current documentation during this session.
- No invented data. Every number — latency, precision, false-positive rate, cost, test
  count — must trace to a run that actually happened. Unmeasured numbers are omitted,
  never estimated.
- Cite external claims with a URL: the scanner's repo, the model card, the vendor docs.
  Academic claims take a DOI or arXiv ID. This build makes no academic claims.
- When a fact cannot be confirmed, write `UNVERIFIED — <what would verify it>`.
  An honest gap costs an hour. A fabricated API costs the demo.
- Never fake the system's own success. If a checker fails, TrustGate says so.

**Precedent:** during planning, the project name and three alternative names were checked
and found to collide with existing products, and a proposed differentiation strategy was
found to be already shipped by a live competitor. Verification caught all four. Assume the
next unchecked assumption is the one that costs you.

---

## 2. Planning Governance — "Hackathon Mode"

This project runs on a 48-hour clock. A literal "never edit without approval" policy would
consume the build. The tiered equivalent enforces the boundary where it matters.

| Tier | Action | Approval |
|------|--------|----------|
| **0** | Reads, search, `git status`/`log`/`diff`, running builds, tests, scanners | None |
| **1** | Editing a file already in the active phase's deliverables table in `PROJECT_ROADMAP.md` | None, **batched** — one approved plan covers all its Tier 1 edits |
| **2** | New dependency · new top-level directory · config/schema change · **any deletion** · edits to the 3 governance files · `git commit`/`git push` | One-line confirm |
| **3** | Architecture change · phase transition · deploy | Full plan, then approval |

**Plan-once, batch-execute.** One approved plan authorizes every Tier 1 edit inside it. Do
not ask for confirmation file-by-file — that turns governance into busywork and it gets
ignored, which is worse than not having it.

Strict mode (approval before every edit) is available on request for any phase where the
risk warrants it.

### Before any Tier 2 or Tier 3 change

1. Read `AI_CONTEXT.md` for architecture, rules, and the model strategy
2. Read `PROJECT_ROADMAP.md` for the active phase and its scope
3. Read `SYSTEM_LEDGER.md` for known issues and file history
4. State: which files change, what changes, why it is needed
5. Wait for an explicit "proceed" / "approved" / "go"

### Never requires a plan

Reading files · searching · running read-only git commands · running builds and tests ·
running the existing scanners

---

## 3. Session Management

### Full Boot — new session or after a context reset

```
1. Read AI_CONTEXT.md    — identity, stack, architecture, rules, model strategy
2. Read PROJECT_ROADMAP.md — the 🔴 ACTIVE phase and its scope
3. Read SYSTEM_LEDGER.md — current state, known issues, next actions
4. Confirm understanding before beginning work
```

### Quick Boot — context still warm

```
1. Read AI_CONTEXT.md and SYSTEM_LEDGER.md
2. Resume from where we left off
```

### Close-Out — end of session

```
1. Update PROJECT_ROADMAP.md — completed tasks, phase status
2. Update SYSTEM_LEDGER.md — files created/modified, metrics, known issues, next actions
3. State what the next session must pick up first
```

A session that ends without a ledger update is a session whose knowledge is lost.

---

## 4. Scope Control

- Work only inside the 🔴 ACTIVE phase in `PROJECT_ROADMAP.md`.
- If asked for out-of-scope work, say so and ask to update the roadmap first.
- Do not move a phase boundary to absorb a slipping task. Cut scope instead.
- Only Phase 0 is active. Application code, dependency installs, and commits are **out of
  scope** until Phase 2 / explicit approval.

---

## 5. Code Standards

### Python — `engine/`

- Type hints on every function signature. No bare `Any` in new code.
- Pydantic v2 models for every external boundary — LLM responses, HTTP requests, SARIF
  fields. An unvalidated boundary is a bug.
- `async`/`await` throughout the request path; five checkers must run concurrently.
- One shared `httpx.AsyncClient`, not one per checker.
- `subprocess` with an argument list. **Never `shell=True`.**
- No inline comments. The code says what; `AI_CONTEXT.md` says why.

### React — `dashboard/`

- TypeScript. Mirror the engine's Pydantic types in `types.ts`.
- No inline user-facing string literals in JSX — all strings via `strings.ts`.
- Every verdict renders color **and** icon **and** text label. Never color alone;
  red/amber/green is unreadable for ~1 in 12 men with red-green color vision deficiency.
- Respect `prefers-reduced-motion`.

### Layer boundaries — these are architectural, not preferences

- `routes/` never imports `checkers/` internals
- `adjudicator.py` never imports `llm/` — this is what makes the verdict deterministic
- `checkers/` modules never import each other — independence is the signal
- `dashboard/` never holds a Groq key — all inference is server-side

---

## 6. Git

- **Never commit unless explicitly asked.**
- Stage only intended files. Never stage `.env`, keys, SARIF artifacts, or corpora dumps.
- `git init` has been run **in this project directory only**. Your git repository is NOT
  `E:/` — the drive root is a separate, unrelated repository. Always run git from this
  directory.
- Conventional commits: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`.
- Verify the build before proposing a commit.

---

## 7. CI Landmines — verified, do not relearn

- GitHub **removed Node 20 from hosted runners entirely on Sep 16 2026**. Any action pinned
  to Node 20 now fails. Check every action's runtime before adding it.
- SARIF upload needs `if: always()`. A scanner exiting non-zero otherwise skips its own
  upload and the findings vanish silently.
- SARIF upload needs `security-events: write` permission.
- Gitleaks needs `fetch-depth: 0` on checkout — it scans history.
- Groq Structured Outputs support **neither streaming nor tool use**.

---

## 8. Communication

- Concise. Output goes to a terminal or an IDE panel.
- Explain what you are doing and why before doing it.
- Ask when ambiguous rather than guessing.
- On errors, give the exact error message and the `file_path:line_number`.
- Six people are working this repo. Your change is one of several in flight — say which
  files you touched.
