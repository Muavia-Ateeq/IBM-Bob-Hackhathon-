# Rule 02 — Session Continuity

Applies to every conversation, in every mode.

## Why this rule exists

Language models are stateless. A new conversation knows nothing about the previous one, no
matter which model or provider is in use. Without a written record, the project loses
hours every time context is refreshed, a teammate takes over, or the team swaps tools.

These three files are that record. Treat them as the project's actual memory.

| File | Role |
|------|------|
| `AI_CONTEXT.md` | The constitution — identity, architecture, rules, model strategy |
| `PROJECT_ROADMAP.md` | The GPS — phases, one 🔴 ACTIVE at a time |
| `SYSTEM_LEDGER.md` | The memory — current state, file history, known issues, next actions |

## Full Boot — new session, or after a context reset

```
1. Read AI_CONTEXT.md      — identity, stack, architecture, strict rules, model strategy
2. Read PROJECT_ROADMAP.md — the 🔴 ACTIVE phase and its scope
3. Read SYSTEM_LEDGER.md   — current state, known issues, next actions
4. Confirm understanding before beginning work
```

## Quick Boot — resuming, context still warm

```
1. Read AI_CONTEXT.md and SYSTEM_LEDGER.md
2. Resume work from where we left off
```

## Close-Out — end of session

```
1. Update PROJECT_ROADMAP.md — mark completed tasks, update phase status
2. Update SYSTEM_LEDGER.md — add every file created or modified, update metrics,
                            add known issues, set next actions
3. State what the next session must pick up first
```

A session that ends without a ledger update is a session whose knowledge is lost. This is
the single highest-value habit in the project: it costs two minutes and saves hours.

## What belongs in the ledger

- Every file created or modified, with why
- Every metric, with how it was measured
- Every known issue, however small
- Every decision, with the reason — especially the ones a future reader would otherwise
  re-litigate

## What does not belong

Guesses. Aspirations. Numbers that were not measured. If it was not observed, it is not
in the ledger.
