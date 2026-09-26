# TrustGate — Data Contract

Every checker writes one JSON file per run into the `runs/` directory. This document
describes what the engine actually writes today. Every claim below is traced to source;
where this document and the code disagree, the code is the contract and this file is the
bug.

- Models: [`engine/app/schemas.py`](engine/app/schemas.py)
- Writer / reader: [`engine/app/runlog.py`](engine/app/runlog.py)
- Verdict rules: [`engine/app/adjudicator.py`](engine/app/adjudicator.py)

---

## Files on disk

One file per checker per run, named `{run_id}_{checker}.json`:

```
runs/run_20260925_222535_authz.json
runs/run_20260925_222535_business.json
runs/run_20260925_222535_injection.json
runs/run_20260925_222535_secrets.json
```

`run_id` is `run_%Y%m%d_%H%M%S` — `main.py:114`. It sorts lexicographically in time order,
which is what lets `load_results` pick the newest run for a pull request without parsing a
timestamp (`runlog.py:73-79`).

## Schema — `RunRecord`

`schemas.py:115-128`. **One checker's result, not a whole run's.**

```json
{
  "run_id": "run_20260925_222535",
  "pr": "repo#42",
  "written_at": "2026-09-25T22:25:35.123456+00:00",
  "result": {
    "checker": "secrets",
    "tier": "deterministic",
    "status": "ok",
    "findings": [
      {
        "checker": "secrets",
        "severity": "high",
        "title": "Hardcoded credential",
        "detail": "A live-format API key is committed in source.",
        "file": "app/config.py",
        "line": 14,
        "evidence": "API_KEY = \"...\"",
        "cwe": "CWE-798",
        "remediation": "Move the key to an environment variable."
      }
    ],
    "duration_ms": 1240,
    "error": null
  }
}
```

`RunRecord` is a separate model from `VerdictRecord`, not a subclass: `extra="forbid"`
means a run record cannot be modelled as an extended verdict, and the two have different
lifecycles — a run record is written by a checker, a verdict is derived from a set of them.

### `Finding` — `schemas.py:38-65`

| Field | Type | Rule |
|---|---|---|
| `checker` | string | non-empty |
| `severity` | enum | one of the five below |
| `title` | string | non-empty, one line |
| `detail` | string | non-empty |
| `file` | string | **repo-relative.** `..`, absolute POSIX paths, Windows drives and UNC paths are all rejected by a validator |
| `line` | int | `>= 1` |
| `evidence` | string | non-empty. The literal source text that triggered the finding |
| `cwe` | string \| null | optional |
| `remediation` | string \| null | optional |

The `file` validator exists because a diff is attacker-influenced text: without it a
checker could point the report at `C:\Windows` or a UNC share (`schemas.py:53-65`).

### `CheckerResult` — `schemas.py:68-88`

| Field | Type | Rule |
|---|---|---|
| `checker` | string | non-empty |
| `tier` | enum | `deterministic` \| `semantic` |
| `status` | enum | `ok` \| `error` \| `timeout` |
| `findings` | `Finding[]` | **must be empty unless `status` is `ok`** |
| `duration_ms` | int | `>= 0` |
| `error` | string \| null | set when `status` is not `ok` |

A checker that failed, timed out, or degraded **must not** report findings. Half a result
from a crashed checker is worse than none, because it reads as coverage that never happened.

---

## Enums

**`Severity` — `schemas.py:10-15`. Five values, not three.**

| Value | Verdict |
|---|---|
| `critical` | BLOCK |
| `high` | BLOCK |
| `medium` | REVIEW |
| `low` | REVIEW |
| `info` | REVIEW |

**`CheckerStatus` — `schemas.py:24-27`.** `ok` \| `error` \| `timeout`. There is no
`success`; `ok` is the only status that can carry findings.

**`CheckerTier` — `schemas.py:29-32`.** `deterministic` \| `semantic`. Deterministic
checkers need no model; semantic ones degrade to `REVIEW` when `GROQ_API_KEY` is absent.

**`Verdict` — `schemas.py:18-21`.** `PASS` \| `REVIEW` \| `BLOCK`.

---

## Verdict rules

`adjudicate()` — `adjudicator.py:22-54`. A pure function: no I/O, no model, no clock, which
is what makes the verdict reproducible.

1. **Worst severity wins.** The highest-severity finding across all checkers decides it.
2. `critical` or `high` → **BLOCK**
3. `medium`, `low`, or `info` → **REVIEW**
4. **Any checker that did not complete → at least REVIEW.** A degraded run can never
   return `PASS`. This is designed behaviour, not a bug: the system that could have found
   the bug did not finish, so silence is not evidence of safety.
5. No checkers ran at all → **REVIEW**, never `PASS`.
6. Only the **newest** run for a given `pr` is adjudicated. The gate re-runs on every push,
   so aggregating every run ever recorded would leave a fixed `CRITICAL` blocking the PR
   forever (`runlog.py:73-79`).

**REVIEW never hard-blocks.** A human decides. This is a product decision, not a technical
limit — see [`WEDGE.md`](WEDGE.md).

---

## Rules for checkers

- `status` must be `ok`, `error`, or `timeout`. Nothing else.
- A `Finding` with no `file`, no `line`, or no `evidence` **must not be written**. The
  models enforce this: all three are non-empty, and `line >= 1`.
- `evidence` is the literal source text. It is what makes a finding checkable by a human.
- `file` is repo-relative and traversal-free.
- A checker that did not complete reports **no findings**.

## Integrity

`VerdictRecord` carries an `input_hash` — a SHA-256 over the raw bytes of exactly the run
records that were adjudicated (`runlog.py:79-83`). The SARIF report is built from the
verdict **read back off disk**, not from the in-memory results (`main.py:118-122`), so the
report and the run log cannot disagree about what happened.

A run file that fails validation is **skipped and named** in `reason` — never silently
dropped. A silently dropped record is a silently dropped finding.

---

## Not implemented

Named here so nobody writes a checker against a field the engine does not have:

- **`bob_session`** — a screenshot path per run. No model field, no reader, no writer.
  There is no code path in this repo that reads or writes it.
- **Multi-agent runs** — one `RunRecord` per checker per run, not per agent. The `agent`
  and `member` fields do not exist.
- **Point-based scoring** — the verdict is severity-ranked, not a score with thresholds.
  There are no points and no numeric cutoffs in `adjudicator.py`.

If any of these are wanted, they need a model change first. Writing a `runs/*.json` file in
one of these shapes today is not a no-op: `extra="forbid"` means it fails validation and
`load_results` drops it as unreadable — the finding disappears from the verdict with no
error.

---

## ⚠️ `runs/` is gitignored, and these files hold credential fragments

`.gitignore:39` excludes `/engine/runs/`. That is deliberate: `Finding.evidence` is the
literal matched text, and for the secrets checker that text **is a fragment of a real
credential**.

The same fact governs `GET /api/runs` (`main.py:149-156`): the endpoint is unauthenticated
and the app allows every origin, so a publicly deployed instance republishes those
fragments to anyone who asks. It is built for a demo instance scanning `demo_target/`
only. Gate it before it points at real code.
