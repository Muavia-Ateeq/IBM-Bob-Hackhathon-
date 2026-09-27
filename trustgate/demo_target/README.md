# `demo_target/` — the TrustGate benchmark corpus

A small order service with **exactly one planted defect per case**. `base/` is
clean; every `issue-NN-*` directory is `base/` with one thing changed. That is
what makes the corpus a measurement instrument rather than a folder of
vulnerable-looking code: a finding the ground truth does not list is a false
positive *by construction*, not by judgement.

Ground truth lives in [`../bench/cases.json`](../bench/cases.json). The runner is
[`../bench/run_benchmark.py`](../bench/run_benchmark.py).

```
python bench/run_benchmark.py --dry-run    # case table; no key, no gitleaks
python bench/run_benchmark.py               # measure what can be measured
```

## Why these cases and not the ones the prompts asked for

The case-to-checker assignment was made by reading the `FOCUS` string in each
checker (`backend/app/checkers/*.py`), not by matching case names. Three cases
have **no checker at all**, and that is the corpus doing its job rather than
failing to:

| Case | Expected | Why |
|---|---|---|
| `issue-01-fake-package` | none | `deps.py` is unbuilt and blocked on K13 — OSV-Scanner's JSON carries no line number |
| `issue-07-license-violation` | none | No `FOCUS` mentions licensing. A license checker was specified in a pasted prompt and declined (`SYSTEM_LEDGER.md`, decline 10) |
| `issue-06-prompt-injection` | `injection`, **disputed** | `injection`'s FOCUS says "template injection", and a string-built prompt is a template. Equally, no FOCUS mentions prompt injection. Recorded as disputed rather than quietly resolved |

Two more are marked `disputed`: `issue-08-no-rate-limit` (`business` vs `authz`)
and `issue-10-debug-enabled` (`authz` vs `business`). A disputed case is one the
corpus does not get to declare a clean miss on, and it is the most useful kind of
row in a false-positive benchmark.

## `issue-02-hardcoded-key` and the gate's allowlist

`issue-02-hardcoded-key/config.py` carries a high-entropy secret literal, because
that is the only way the deterministic `secrets` checker has anything to find.
TrustGate's gate runs gitleaks over the whole repository, and `secrets` maps every
gitleaks finding to `Severity.HIGH`, so **without a suppression the gate BLOCKed
every pull request** on a fixture we planted on purpose.

Suppression now exists, and it is scoped so that suppressing the gate's false
positive does not also blind the measurement:

- **`.gitleaksignore` still cannot do this.** Per the vendor README it holds
  finding *fingerprints*, not paths. A path line would be silently ignored —
  the failure mode this repository keeps trying to design out.
- **[`.github/gitleaks.toml`](../../.github/gitleaks.toml) does it, scoped to the
  gate alone.** It carries `[extend] useDefault = true`, so gitleaks' full default
  ruleset stays active and only two anchored paths are allowlisted.

An earlier version of this file claimed a root `.gitleaks.toml` carrying only an
`[[allowlists]]` block "would disable the gate", because gitleaks' config is
replacement, not merge. **That was wrong, and running the binary is what proved
it** — it is true only for a config *without* `[extend] useDefault`. Verified
against the pinned `backend/.tools/gitleaks.exe` v8.30.1:

| Config | Result |
|---|---|
| `[extend] useDefault = true` alone | finding still reported, exit 1 — rules stay active |
| plus an allowlist naming this file | no leaks, exit 0 |
| plus an allowlist naming a *different* file | finding still reported, exit 1 — the allowlist is narrow |

The config lives in `.github/`, **not** at the repo root, and that placement is
load-bearing. `--config`'s precedence list ends in `(target path)/.gitleaks.toml`,
and the target path is `--workspace` — the repo root for the gate *and* for
`bench/run_benchmark.py`. A root config would therefore be auto-discovered by the
benchmark too, and would silence this very fixture: `cases.json` records it as
`expected_checker: secrets`, `expected_line: 5`, `disputed: false`, so removing the
finding would turn a true positive into a guaranteed false negative against ground
truth. Only `trustgate.yml` sets `GITLEAKS_CONFIG`, so `bench/` keeps detecting it.

**VERIFIED 2026-09-26** — this also settles the K14 caveat recorded in
`bench/cases.json`. Executing the binary, gitleaks' default ruleset *does* flag the
literal: `generic-api-key`, entropy 4.0, `config.py` line 5 — exactly the file and
line the ground truth predicts.

UNVERIFIED — whether `issue-05-unsafe-deserialize` gets planted, which is a human
decision recorded below and unrelated to secret scanning.

## `issue-05-unsafe-deserialize` is not planted

The defect — a reachable `pickle.loads` on client-controlled bytes — was
**declined by the sandbox classifier as an RCE surface** and needs an explicit
human decision. `cases.json` marks the case `expected_line: null`, and the
runner skips it and says so rather than reporting a false negative for a fixture
that does not exist.
