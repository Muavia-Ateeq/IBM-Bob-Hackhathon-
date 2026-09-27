# BOB_USAGE.md

This document records how M. Muavia used IBM Bob during the TrustGate build.

## M. Muavia

### Task 1: PRD requirements extraction — Step A (Spec-Conformance)
- **Bob feature used**: Agent mode + document understanding
- **Files**: `PRD.pdf`
- **Result**: Bob extracted 8 verified requirements from PRD.pdf with exact quotes under 15 words each.
- **Screenshot**: `screenshots/muavia_1.png`

### Task 2: Spec-Conformance check — issue-08-no-rate-limit
- **Bob feature used**: Agent mode (Step B prompt)
- **Branch**: `issue-08-no-rate-limit`
- **Result**: 1 medium finding — login docstring promises throttling, body never performs it.
- **Output**: `runs/spec_001.json`
- **Screenshot**: `screenshots/muavia_2.png`

### Task 3: Spec-Conformance check — issue-09-weak-hash
- **Bob feature used**: Agent mode (Step B prompt)
- **Branch**: `issue-09-weak-hash`
- **Result**: 1 high finding — PBKDF2 replaced with unsalted MD5 in crypto.py line 7.
- **Output**: `runs/spec_002.json`
- **Screenshot**: `screenshots/muavia_3.png`

### Task 4: Security Reviewer — issues 02, 03, 04, 10
- **Bob feature used**: Agent mode (Security Reviewer prompt)
- **Branches**: `issue-02-hardcoded-key`, `issue-03-sql-injection`, `issue-04-missing-auth`, `issue-10-debug-enabled`
- **Result**: 4 high findings — hardcoded key, SQL injection, IDOR, Flask DEBUG=True. **3 of these 4 are now out of scope**: `security_reviewer` was narrowed on 2026-09-27 to production debug/verbose configuration only and explicitly refuses secrets, injection and authz as owned by other checkers. Only `Flask DEBUG=True` (issue-10) survives the narrowing. These transcripts predate it.
- **Output**: `runs/sec_001.json` through `runs/sec_005.json`
- **Screenshot**: `screenshots/muavia_4.png`

### Task 5: False-positive check — clean branches
- **Bob feature used**: Agent mode (both checkers)
- **Branches**: `clean-01`, `clean-02`, `clean-03`
- **Result**: 0 findings on all 3 clean branches. **This is not a false-positive rate** — these are 3 hand-picked clean branches through one Bob session, not the `bench/` corpus, and no command in this repository reproduces them. No FP rate has been measured. See WEDGE.md claim 3.
- **Output**: `runs/sec_clean_*.json`, `runs/spec_clean_*.json`
- **Screenshot**: `screenshots/muavia_5.png`

**Note on document understanding**: Bob's document understanding was used in Step A to ingest PRD.pdf and extract only mechanically-verifiable requirements with exact quotes. If Bob cannot quote it from the document, it is not extracted — this prevents hallucinated requirements.
