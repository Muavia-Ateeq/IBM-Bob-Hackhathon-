# Rule 01 — Planning Governance (Hackathon Mode)

Applies to every conversation, in every mode.

## The situation

This project runs on a 48-hour clock. Submissions close **Sun Sep 27 2026, 15:00 UTC**.
A literal "never edit without approval" policy would consume the entire build in
permission requests. The tiered policy below enforces the same boundary where it
actually matters, and stays out of the way where it does not.

## The tiers

| Tier | Action | Required approval |
|------|--------|-------------------|
| **0** | Reads, search, `git status` / `log` / `diff`, running builds, tests, scanners | None |
| **1** | Editing a file already listed in the active phase's deliverables table in `PROJECT_ROADMAP.md` | None, **batched** |
| **2** | New dependency · new top-level directory · config or schema change · **any deletion** · edits to `AI_CONTEXT.md`, `PROJECT_ROADMAP.md`, `SYSTEM_LEDGER.md` · `git commit` / `git push` | One-line confirm |
| **3** | Architecture change · phase transition · deploy | Full plan, then approval |

## Plan-once, batch-execute

One approved plan authorizes **every** Tier 1 edit inside it.

Do not ask for confirmation file by file. Per-file confirmation turns governance into
busywork, and busywork gets ignored — which is worse than having no governance at all.

## Before any Tier 2 or Tier 3 change

1. Read `AI_CONTEXT.md` — architecture, strict rules, model strategy
2. Read `PROJECT_ROADMAP.md` — the active phase and its scope
3. Read `SYSTEM_LEDGER.md` — known issues and file history
4. State plainly: which files change, what changes, why it is needed
5. Wait for an explicit "proceed" / "approved" / "go"

## Never requires a plan

Reading files · searching · running read-only git commands · running builds and tests ·
running the existing scanners

## Strict mode

Strict mode — approval before every single edit — is available on request for any phase
where the risk warrants it. Ask for it explicitly; do not default to it under time
pressure, and do not abandon it once a phase is deemed risky.

## The 48-hour test

Before asking for approval, ask: *is this a decision a human should make, or a decision I
can make and report?* Six people are working this repository. Your change is one of several
in flight. Say which files you touched.
