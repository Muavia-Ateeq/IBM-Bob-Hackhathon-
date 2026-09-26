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

Concretely, three things — none of which the four overlapping live submissions show:

1. **The `REVIEW`-on-failure contract.** A checker that crashes, times out, or returns
   malformed output can never produce `PASS`. It produces `REVIEW`, and it says which
   checker failed and why. Every competing gate either fails open (dangerous) or fails
   closed into a hard block (annoying, and users disable it). TrustGate fails to the only
   state that is honest.
2. **Evidence on every finding, mechanically enforced.** File, line, and quoted source,
   asserted by the schema — not a convention. A finding without evidence is a rejected
   finding. An LLM's opinion is not a security finding; an LLM's opinion *with the code it
   is pointing at* is.
3. **A measured false-positive rate with the harness that reproduces it in the repo.** Not
   "high accuracy". A number, the corpus it came from, and the command that regenerates it.

The mechanism behind all three is the same: **separate what has a ground truth from what
needs judgement, and never let the second kind silently stand in for the first.**

## The ninety-second demo

1. Open a pull request that contains one planted SQL injection and one hardcoded API key.
2. The gate runs. Wall-clock appears.
3. Two findings appear inline on the diff, each with the quoted line. The key is caught by
   Gitleaks; the injection by the semantic checker.
4. The verdict reads `BLOCK`, and the reason names the critical finding.
5. **Open a second PR while the Groq key is deliberately unset.** The verdict degrades to
   `REVIEW`, not `PASS`, and the banner says which checker was unavailable.

Step 5 is the demo. It is the part no competitor shows, and it is the part that proves the
product is honest.

## Anti-goals — what we are explicitly not building

- **Auto-merge.** A gate that merges code makes a far larger safety claim than a 48-hour
  prototype can support. A wrong auto-merge costs more than a missed finding.
- **A general-purpose code reviewer.** We do not comment on style, naming, or architecture.
  Comments, not gates.
- **A model that ranks its own findings.** Ranking is the LLM's job. The *verdict* is a
  pure function. Do not blur these.
- **Shadow-mode calibration.** Already shipped by a live competitor (quorum.reviews). We
  would be building their product. The honest version of this idea is "publish the
  false-positive rate", which we do.
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

| Claim | How it is falsified |
|-------|--------------------|
| Fails safe | Inject a fault into each of the 5 checkers. If any yields `PASS`, the claim is false |
| Deterministic | Run the same diff 20×. If any verdict differs, the claim is false |
| Evidence-complete | Emit findings. If any lacks file+line+quote, the claim is false |
| Measurable | Run the corpus. If the false-positive rate cannot be computed, the claim is false |

Each row is a test that can fail, and a failing test means the README says so.
