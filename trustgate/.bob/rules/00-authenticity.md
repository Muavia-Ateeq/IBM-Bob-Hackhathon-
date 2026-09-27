# Rule 00 — Authenticity

Applies to every conversation, in every mode.

## Verifiable or absent

Every technical claim in this repository must be verifiable.

1. **No hallucinated APIs.** Never reference a function, parameter, CLI flag, model ID, or
   HTTP header that you did not read in current documentation during this session. If you
   did not read it, you do not know it.
2. **No invented data.** Every number — latency, precision, recall, false-positive rate,
   cost, test count — must trace to a run that actually happened. Unmeasured numbers are
   omitted, never estimated.
3. **Cite external claims.** Any claim resting on a third party gets a URL: the scanner's
   repository, the model card, the vendor documentation. Academic claims take a DOI or an
   arXiv ID. This build makes no academic claims.
4. **When a fact cannot be confirmed**, write:
   `UNVERIFIED — <what would verify it>`
   An honest gap costs an hour. A fabricated API costs the demo.

## Never fake the system's own success

This is a security product. A gate that hides its own failures reproduces the exact failure
mode it exists to catch.

- If a checker errors, times out, or returns malformed output, the verdict degrades to
  `REVIEW`. It is **never** `PASS`.
- If a measurement failed, report the failure. Do not substitute a plausible number.
- A demo that only shows the happy path is a demo that hides the risk.

## Why this rule exists

During planning, the project name and three alternative names were checked and found to
collide with existing products. A proposed differentiation strategy was checked and found
to be already shipped by a live competitor. All four were caught by verification rather
than assumption.

Assume the next unchecked assumption is the one that costs you.

## Verifying cheaply

Before claiming any tool works, run it and read the output. Before claiming a model ID
exists, read the provider's current model list. Before claiming a CI step passes, push a
branch and read the run.
