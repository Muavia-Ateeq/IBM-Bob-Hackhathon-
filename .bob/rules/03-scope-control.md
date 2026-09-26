# Rule 03 — Scope Control

Applies to every conversation, in every mode.

## One active phase, always

`PROJECT_ROADMAP.md` marks exactly one phase 🔴 ACTIVE. Everything else is ⏳ Pending.

- Work only inside the ACTIVE phase.
- If asked for out-of-scope work, say so and ask to update the roadmap first.
- Changing the active phase is a **Tier 3** action: full plan, then approval.

## Current status: Phase 0 only

**Phase 0 — Foundation & Governance** is the only active phase. It is governance
documents only.

Out of scope until Phase 2 and explicit approval:

- Writing application code
- Installing dependencies
- Creating `engine/`, `dashboard/`, or `.github/workflows/`
- Any git commit

## Do not move a phase boundary

When a task slips, **cut its scope** — do not widen a phase to absorb it.

A phase boundary that moves to accommodate a slipping task stops being a boundary. The
moment it moves, scope control becomes a suggestion, and the 48-hour build starts
absorbing work nobody decided to do.

## Say what you are not doing

If the request is out of scope, the honest answer names the boundary and offers the
legitimate path:

> That is Phase 3 work and Phase 0 is active. I can add it to the Phase 3 task list, or
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
