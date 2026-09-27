# Rule 03 — Scope Control

Applies to every conversation, in every mode.

## One active phase, always

`PROJECT_ROADMAP.md` marks exactly one phase 🔴 ACTIVE. Everything else is ⏳ Pending.

- Work only inside the ACTIVE phase.
- If asked for out-of-scope work, say so and ask to update the roadmap first.
- Changing the active phase is a **Tier 3** action: full plan, then approval.

## Current status: the build phase — `backend/` is in scope

**Rewritten 2026-09-27, on the user's explicit instruction.** This section previously read:

> **Phase 0 — Foundation & Governance** is the only active phase… Out of scope until
> Phase 2: writing application code, installing dependencies, creating `backend/`,
> `dashboard/`, or `.github/workflows/`, any git commit.

That was false against the tree it governs. All of those directories exist, hold the
product, and are deployed. An agent booting on this rule would either refuse to work or
rebuild what already exists — which is exactly the failure **K8** records as having already
happened once. The rule was not protecting the boundary; it was the breach.

**Now in scope, and the ordinary work of this project:**

- `trustgate/backend/` — the engine, its checkers, its tests
- `trustgate/bench/` — the corpus and the benchmark runner
- `trustgate/demo_target/` — the planted fixtures the corpus measures against
- `trustgate/dashboard/` — the React dashboard
- `.github/workflows/` — the gate
- Dependency installs into `backend/.venv/`

**Still requiring explicit approval:**

- `git commit` / `git push`
- Any deletion
- Any new top-level dependency
- Phase transitions (still Tier 3, still `PROJECT_ROADMAP.md`'s call, still open as K10)

`PROJECT_ROADMAP.md` still marks Phase 0 🔴 ACTIVE. That label is now known to be stale
and it is recorded as open in `SYSTEM_LEDGER.md` (K10) — **but nothing in this rule
depends on it any more.** The scope above is the truth about the tree, and it stands
whatever the phase is eventually renamed.

## Do not move a phase boundary

When a task slips, **cut its scope** — do not widen a phase to absorb it.

A phase boundary that moves to accommodate a slipping task stops being a boundary. The
moment it moves, scope control becomes a suggestion, and the 48-hour build starts
absorbing work nobody decided to do.

## Say what you are not doing

If the request is out of scope, the honest answer names the boundary and offers the
legitimate path:

> That is Phase 3 work and Phase 3 is not active. I can add it to the Phase 3 task list, or
> you can approve a phase transition now. Which?

Do not quietly expand scope. Do not refuse without offering the alternative.

## Cutting scope, in the right order

When time runs short, cut in this sequence. Never cut in the reverse.

1. Polish — animations, transitions, visual refinement
2. Dashboard richness — show fewer, but real, findings
3. Checker depth — fewer classes checked, but each one correct
4. Evaluation breadth — smaller corpus, still honestly measured

What is never cut: the degraded `REVIEW` path, the evidence on every finding, and the
authenticity of every published number.
