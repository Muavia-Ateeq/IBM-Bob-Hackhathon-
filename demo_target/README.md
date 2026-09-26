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

## ⚠️ `issue-02-hardcoded-key` will be flagged by TrustGate's own gate

`issue-02-hardcoded-key/config.py` carries a high-entropy secret literal, because
that is the only way the deterministic `secrets` checker has anything to find.
TrustGate's gate runs gitleaks over the whole repository, so **the gate will
report this fixture as a leak in our own pull request.**

No suppression has been added, deliberately. The two available mechanisms are
both worse than the problem:

- **`.gitleaksignore` does not work here.** Per the vendor README it holds
  finding *fingerprints*, not paths. A path line would be silently ignored —
  which is the failure mode this repository keeps trying to design out.
- **A root `.gitleaks.toml` with an `[[allowlists]]` block would disable the
  gate.** gitleaks' config is replacement, not merge: a config carrying only an
  allowlist has no `[[rules]]`, so nothing would be detected at all. Trading a
  visible false positive for a silently dead secrets gate is a bad trade.

Real fixes, both team decisions rather than something to paper over here:

1. Narrow the gate's gitleaks `--workspace` so it does not scan `demo_target/`,
   or
2. Vendor gitleaks' full default config and add the fixture path to its
   allowlist — which pins the ruleset and stops it tracking gitleaks upgrades.

UNVERIFIED — which of the two the team prefers, and whether gitleaks' default
ruleset flags this specific literal at all, are both settled only by executing
the binary. That is K14.

## `issue-05-unsafe-deserialize` is not planted

The defect — a reachable `pickle.loads` on client-controlled bytes — was
**declined by the sandbox classifier as an RCE surface** and needs an explicit
human decision. `cases.json` marks the case `expected_line: null`, and the
runner skips it and says so rather than reporting a false negative for a fixture
that does not exist.
