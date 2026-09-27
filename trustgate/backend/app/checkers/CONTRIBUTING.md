# Writing a checker

Every checker is an independent expert. The contract below is the whole interface — there is
no registry to update beyond one import line, and no orchestrator to touch.

## The contract

A checker is any object with a `name`, a `tier`, and an async `run`:

```python
class MyChecker:
    name: str
    tier: CheckerTier

    async def run(self, diff: str, workspace: str) -> list[Finding]: ...
```

This is the `Checker` Protocol in `base.py`. It is structural — you do not subclass it, and you
do not register with anything.

- `diff` — the unified diff under review, already truncated to `max_diff_bytes`.
- `workspace` — path to the checked-out PR branch. **Read nothing outside it.**
- Return `Finding` objects. Raise on failure; `execute()` converts any exception into a
  degraded `CheckerResult`.

`execute()` already measures `duration_ms`, applies the per-checker timeout, and converts
errors and timeouts into a `CheckerResult` with `status != ok`. **Do not** catch your own
errors, do not time yourself, and do not invent a duration — returning normally means
`status: ok`, and that is a claim you have to be able to defend.

## Finding fields

Every finding needs `file`, `line`, and `evidence`. This is enforced by `schemas.py`, not by
convention: a finding missing any of them raises `ValidationError` and the whole run fails.
That is intentional — see `WEDGE.md`, wedge claim 2.

| Field | Rule |
|-------|------|
| `file` | Repo-relative. Absolute paths and `..` are rejected. |
| `line` | `>= 1`. A `0` is rejected. |
| `evidence` | The quoted source, verbatim. Not a paraphrase. |
| `severity` | `critical` · `high` · `medium` · `low` · `info` |
| `title` / `detail` | One line each. |
| `cwe` / `remediation` | Optional. |

**If you cannot cite a file, a line, and the quote, do not report the finding.** A finding
without evidence is a guess wearing a severity label, and `adjudicate()` will make it gate
somebody's merge.

## Registering it

Two lines. The `build()` signature is uniform across the roster — a deterministic checker
ignores both arguments.

```python
# app/checkers/my_checker.py
def build(provider: Provider, max_diff_bytes: int) -> MyChecker:
    return MyChecker()
```

```python
# app/main.py
from app.checkers import my_checker
CHECKER_MODULES = (secrets, my_checker, authz, injection, business)
```

`build_roster` calls `module.build(provider, max_diff_bytes)` for each module, and `run_all`
fans out over them with `asyncio.gather`. Adding a checker does not touch either.

## Rules that are not negotiable

- **`checkers/` modules never import each other.** A checker that trusts another checker's
  opinion is no longer an independent signal, and independence is the reason the FP rate is
  defensible.
- **The adjudicator never imports a model.** Keep LLM calls inside your checker.
- **Use `subprocess` with an argument list, never `shell=True`.** Scanner input is never
  interpolated into a command string.
- **Async all the way.** A blocking call in `run()` serialises the whole fan-out — wall-clock
  becomes the sum of the checkers instead of the slowest one.
- **Never emit a credential.** If your scanner returns the secret value, put the redacted
  match in `evidence` and drop the secret. `runs/*.json` and the SARIF upload are both
  places a leaked key would end up in a file someone commits.

## Testing it

```bash
cd trustgate/backend
python -m pytest tests/ -q
python app/main.py --diff <some>.diff --pr test/1
```

A checker that degrades on every run is a checker that does not run. If you cannot exercise
yours here, say so in `trustgate/docs/SYSTEM_LEDGER.md` rather than reporting a number you did
not measure.
