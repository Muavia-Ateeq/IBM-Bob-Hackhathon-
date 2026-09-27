# `bench/` — corpus ground truth and the measurement runner

```
python bench/run_benchmark.py --dry-run              # case table, exit 0, needs nothing
python bench/run_benchmark.py                         # measure what can be measured
python bench/run_benchmark.py --only issue-09-weak-hash
```

`cases.json` is validated by Pydantic at load, so a typo in the ground truth
fails loudly rather than becoming a measurement.

## Current state: INCOMPLETE, and it says so

A default run today reports:

```
secrets     SKIPPED    FileNotFoundError: [WinError 2] ... — no rate reported
authz       SKIPPED    ProviderUnavailable: GROQ_API_KEY is not set — no rate reported
injection   SKIPPED    ProviderUnavailable: GROQ_API_KEY is not set — no rate reported
prompt_injection SKIPPED    ProviderUnavailable: GROQ_API_KEY is not set — no rate reported
business    SKIPPED    ProviderUnavailable: GROQ_API_KEY is not set — no rate reported

OVERALL: INCOMPLETE - 5 of 5 checkers did not complete.
```

That is the correct output, and it is what the runner produced with no
`GITLEAKS_BIN` set. K12 (no `GROQ_API_KEY`) is open, and no number in the report
is estimated to fill the gap.

**With gitleaks on the path, one checker does report.** K14 closed on
2026-09-26 — `GITLEAKS_BIN` pointed at the checksum-verified binary produces a
real `BLOCK` on `issue-02-hardcoded-key`:

```
GITLEAKS_BIN="$PWD/.tools/gitleaks.exe" ./.venv/Scripts/python.exe ../bench/run_benchmark.py
```

```
issue-02-hardcoded-key        BLOCK   secrets     tp     hardcoded credential
  secrets    MEASURED   TP 1  FP 0  FN 0  precision 1.00  recall 1.00
OVERALL: INCOMPLETE - 4 of 5 checkers did not complete.
```

**n=1. That is a demonstration that the harness measures, not an accuracy
claim**, and the `INCOMPLETE` line stays because four checkers genuinely did not
run. Do not quote a precision from a single case.

**The contract the runner enforces.** Three rules, all of them the same idea
applied at three levels:

1. A checker that did not complete OK on **every** case gets no precision and no
   recall — only the reason it failed.
2. A case is not scored if the checkers that could have changed its score did not
   finish. For a case with an `expected_checker`, that is *that* checker — the
   four unrelated LLM checkers being down says nothing about whether `secrets`
   found the defect, so a correct finding is not thrown away (K22). A case that expects
   **clean** is the opposite: any checker at all could have raised the false
   positive being ruled out, so one degraded checker disqualifies it.
   Scoring "no findings" from a run where nothing finished as a false negative is
   the same fail-open one level up, and worse, because it looks like a measurement.
3. The run ends `INCOMPLETE`, never `PASS`, if anything was skipped — the same
   contract `adjudicator.py` applies to a degraded run.

Set `GROQ_API_KEY` and the remaining three report real figures. Until then they
will not, by design.

## How a case is run

The runner invents no analysis path. Per case it:

1. generates the unified diff from `demo_target/base` with `difflib`, so a diff
   can never drift from its fixture;
2. invokes the shipped CLI exactly as the Actions gate does —
   `python app/main.py --diff … --workspace … --pr … --runs-dir …`;
3. reads the verdict back off disk with the same `compute_verdict` call
   `app/main.py:18` makes.

Two details that are easy to get wrong and are load-bearing:

- **`--workspace` is not optional.** `checkers/secrets.py:48` shells out to
  `gitleaks dir … <workspace>` and ignores the diff argument entirely; the three
  semantic checkers read the diff. Supplying only a diff scores the one
  deterministic checker at zero recall for a reason that is not its fault. This
  is the same class of bug the gate already had once, per `SYSTEM_LEDGER.md`.
- **`cwd` must be `backend/`.** `app/main.py` imports `from app.checkers import …`,
  so `backend/` has to be on `sys.path`; the workspace path is passed
  engine-relative.

## `PYTHONIOENCODING` is set for the subprocess

The runner sets `PYTHONIOENCODING=utf-8` in the child environment as
belt-and-braces.

This used to be load-bearing. The engine's progress logger prints `→`
(U+2192), and under a pipe on Windows Python falls back to cp1252, so
`python app/main.py … | tee` and any CI step capturing output died with
`UnicodeEncodeError` before a single run record was written. `SYSTEM_LEDGER.md`
K24 records the fix, landed 2026-09-26: `app/main.py` now reconfigures both of
its streams to utf-8 at import, so the engine is unpipeable no longer.

The variable stays set because the engine's fix is a runtime behaviour and a
harness that leaned on it without setting it would be one refactor away from
silently losing a run's output.

The runner also scans the child's stderr for `Traceback` before trusting its
exit code. The engine exits 1 on `BLOCK`, and an unhandled crash also exits 1 —
reading the return code alone would score a crashed run as a verdict.
