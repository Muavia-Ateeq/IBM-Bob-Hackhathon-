You are checking whether a code change violates or is missing any of the
following VERIFIED requirements (these have already been confirmed to
exist in the project's PRD, so treat them as ground truth):

{{VERIFIED_REQUIREMENTS_LIST}}

For each requirement, check the given unified diff. Report a finding ONLY if the
requirement is clearly violated or clearly missing — not if you are unsure,
and not for requirements the code doesn't touch at all.

STRICT EVIDENCE RULE:
Every finding must include:
 (a) the exact file path, exactly as it appears in the diff,
 (b) the exact line number,
 (c) a verbatim quote copied EXACTLY from the diff — never paraphrase.
If the requirement is entirely absent from the code (nothing to quote),
quote the smallest relevant code block that is present in the diff and note
in your detail that the requirement is missing outright.
If the evidence quote is not a literal substring of the diff shown to you,
DO NOT report that finding.

SEVERITY:
- "high": a security- or data-integrity-related requirement is violated
  (e.g. weak hashing instead of bcrypt, no rate limiting on a public API)
- "medium": a functional requirement is violated with no direct security impact
- "low": a minor or cosmetic requirement is violated

EXAMPLE — requirement violated:
Requirement req_1: "Passwords must be hashed with bcrypt before storage."
Diff:
```diff
--- a/app/auth.py
+++ b/app/auth.py
@@ -3,1 +3,1 @@
-    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
+    return hashlib.md5(password.encode()).hexdigest()
```

Correct output:
{
  "findings": [
    {
      "checker": "spec_conformance",
      "file": "app/auth.py",
      "line": 4,
      "severity": "high",
      "title": "req_1 violated: MD5 used instead of bcrypt",
      "detail": "PRD requires bcrypt hashing but code uses MD5, a weak hash for passwords.",
      "evidence": "return hashlib.md5(password.encode()).hexdigest()"
    }
  ]
}

EXAMPLE — requirement satisfied (report nothing for it):
If the code correctly uses bcrypt, do not include a finding for that
requirement at all. Only report violations or clear absences.

OUTPUT FORMAT — return ONLY this JSON, nothing else:
{
  "findings": [
    {
      "checker": "spec_conformance",
      "file": "<exact file path as it appears in the diff>",
      "line": <exact line number as integer>,
      "severity": "high" | "medium" | "low",
      "title": "<requirement_id + one-line summary>",
      "detail": "<one sentence explaining which PRD requirement is violated and how>",
      "evidence": "<verbatim quoted line copied from the diff>"
    }
  ]
}

Now check this unified diff:
{{CODE_INPUT}}
