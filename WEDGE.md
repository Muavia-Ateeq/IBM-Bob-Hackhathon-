# The Wedge — TrustGate

> Phase 1 deliverable. One page. Everything in Phase 3 traces back to this document.
> If a proposed feature does not serve the wedge below, it does not ship.

---

## Problem

A pull request is the cheapest place to catch a security defect and the most expensive
place to discover one after release. The review step is where that breaks.

A human reviewer at hour 18 is being asked to hold five unrelated threat classes in their
head at once — leaked secrets, dependency CVEs, access control, injection, business logic.
That is slow, it is inconsistent between reviewers, and it degrades silently under fatigue.
The failure is not that reviewers miss things. The failure is that **nobody can tell whether
they missed things**, because there is no record of what was checked.

## Target user

The engineer or security lead who owns merge policy on a team of 5–50. They are accountable
for what ships, they cannot read every diff carefully, and they have no way to prove to an
auditor what a given merge was checked against.

Secondary: the platform engineer wiring branch protection who needs a status check that is
reliable and cheap.

## The wedge

> **TrustGate is the only gate in the field that publishes what it checked, what it could
> not check, and how often it was wrong.**

> **State of the first two: built and tested.** The third is a commitment, not a claim —
> see the note below. This document is a Phase 1 wedge, so it describes the product. Where
> the product does not yet exist, that is said here rather than left for a reader to
> discover.

Concretely, three things — none of which the four overlapping live submissions show:

1. **The `REVIEW`-on-failure contract.** A checker that crashes, times out, or returns
   malformed output can never produce `PASS`. It produces `REVIEW`, and it says which
   checker failed and why. Every competing gate either fails open (dangerous) or fails
   closed into a hard block (annoying, and users disable it). TrustGate fails to the only
   state that is honest.
   **Built and tested** — `engine/app/adjudicator.py` and `engine/tests/test_adjudicator.py`.
2. **Evidence on every finding, mechanically enforced.** File, line, and quoted source,
   asserted by the schema — not a convention. A finding without evidence is a rejected
   finding. An LLM's opinion is not a security finding; an LLM's opinion *with the code it
   is pointing at* is.
   **Built and tested** — `engine/app/schemas.py` rejects a finding with `line < 1`, empty
   evidence, or a traversing `file` path. Asserted in the same test file.
3. **A measured false-positive rate with the harness that reproduces it in the repo.** Not
   "high accuracy". A number, the corpus it came from, and the command that regenerates it.
   **Not built.** `corpus/` does not exist, no corpus run has happened, and **no
   false-positive rate has been measured or is claimed anywhere in this repository.** The
   `Results` section of the README is deliberately empty for this reason. The number is
   Phase 4 work, and it appears here with the harness that produced it, or not at all.

The mechanism behind all three is the same: **separate what has a ground truth from what
needs judgement, and never let the second kind silently stand in for the first.**

## The ninety-second demo

**This is the demo that runs today.** It is a terminal, not a pull request, because the
GitHub gate is not built — see `README.md` → *Not built*.

1. `python app/main.py --diff change.diff` with `GROQ_API_KEY` set. Wall-clock appears.
2. Findings print, each with its file, line, and quoted source line.
3. The verdict reads `PASS`, `REVIEW`, or `BLOCK`, and the reason names the finding that
   decided it.
4. **Re-run the identical command with the key unset.** All three checkers degrade. The
   verdict reads `REVIEW` — never `PASS` — and the output names each unavailable checker
   and why.
5. **"Most gates print PASS here. This one refuses to, and tells you which of its own
   checkers it could not run."**

Step 4 is the demo. It is the part no competitor shows, and it is the part that proves the
product is honest.

> **Steps 1–3 as a real `BLOCK` are unverified.** No `GROQ_API_KEY` was available in the
> environment where this was written, so the model call has never executed end to end. The
> degradation path in step 4 *was* run and its output is in the session log. `UNVERIFIED —
> one run of this command with a key set.`

## Anti-goals — what we are explicitly not building

- **Auto-merge.** A gate that merges code makes a far larger safety claim than a 48-hour
  prototype can support. A wrong auto-merge costs more than a missed finding.
- **A general-purpose code reviewer.** We do not comment on style, naming, or architecture.
  Comments, not gates.
- **A model that ranks its own findings.** Ranking is the LLM's job. The *verdict* is a
  pure function. Do not blur these.
- **Shadow-mode calibration.** Already shipped by a live competitor (quorum.reviews). We
  would be building their product. The honest version of this idea is "publish the
  false-positive rate" — which is what wedge claim 3 commits to, and which this repository
  has **not** done yet.
- **Multi-language support beyond Python and Node.** The ecosystem CVE data and the scanner
  tooling are mature there. Depth beats breadth in 48 hours.
- **i18n.** English only. Recorded in `AI_CONTEXT.md` so it reads as a decision.

## What we are betting on

The field has 31 submissions and the leader has 19 community votes. The previous edition
had 503 submissions and a winner at 47 votes. **This event is decided on execution,
documentation, and demo quality — not on being first to an idea.**

So the bet is: a smaller, correct, fully honest system that demonstrably fails safe beats a
broader one that cannot say what it checked. If that bet is wrong, the cost is a lower
placing in a field where a broader-but-flakier system would have won. We are taking that
trade because the alternative — shipping something we cannot measure — is the one thing
Rule 00 forbids.

## Success, stated as tests

A row is only a claim if the test has actually been run. The state column is the point of
this table — an unrun test is a promise, and this repository does not report promises as
results.

| Claim | How it is falsified | State |
|-------|---------------------|-------|
| Fails safe | Inject a fault into each checker. If any yields `PASS`, the claim is false | **Run for 3 of 3 checkers** — `test_degraded_error_never_yields_pass`, `test_degraded_timeout_never_yields_pass`. No fault-injection harness for the network path yet |
| Deterministic | Run the same diff 20×. If any verdict differs, the claim is false | **Adjudicator only.** `test_adjudicator_is_pure` proves the verdict function is deterministic. The 20× run against the *model* has not happened — no API key |
| Evidence-complete | Emit findings. If any lacks file+line+quote, the claim is false | **Run** — `line < 1`, empty evidence, and path traversal are all asserted to raise `ValidationError` |
| Measurable | Run the corpus. If the false-positive rate cannot be computed, the claim is false | **Not run.** No corpus exists. No rate is claimed |

Each row is a test that can fail, and a failing test means the README says so.
