You are checking whether a code change violates any of the VERIFIED requirements listed
below. These requirements have already been confirmed to exist in the project PRD, so
treat them as ground truth.

{{VERIFIED_REQUIREMENTS_LIST}}

Check the unified diff below against every requirement. Report a finding ONLY if a
requirement is clearly violated or clearly absent in the diff — not if you are unsure,
and not for requirements the code does not touch at all.

STRICT EVIDENCE RULE:
Every finding must include ALL THREE of:
  (a) the exact file path, exactly as it appears in the diff
  (b) the exact line number as an integer
  (c) a verbatim quote copied EXACTLY from the diff — never paraphrase
If the requirement is entirely absent (nothing to quote), quote the smallest relevant
code block present in the diff and note in your detail that the requirement is missing.
If the evidence quote is not a literal substring of the diff shown to you, DO NOT report
that finding.

SEVERITY:
  - "high":   a security- or data-integrity requirement is violated
               (e.g. weak hashing instead of bcrypt, no rate limiting on a public login endpoint)
  - "medium": a functional requirement is violated with no direct security impact
  - "low":    a minor or cosmetic requirement is violated

EXAMPLE — requirement violated:
Verified requirement req_1: "Passwords must be hashed with bcrypt before storage."
Diff:
```diff
--- a/crypto.py
+++ b/crypto.py
@@ -6,1 +6,1 @@
-    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
+    return hashlib.md5(password.encode()).hexdigest()
```

Correct output:
{
  "findings": [
    {
      "checker": "spec_conformance",
      "file": "crypto.py",
      "line": 7,
      "severity": "high",
      "title": "req_1 violated: MD5 used instead of bcrypt",
      "detail": "PRD requires bcrypt hashing but code uses unsalted MD5, a cryptographically weak algorithm.",
      "evidence": "return hashlib.md5(password.encode()).hexdigest()",
      "cwe": "CWE-916",
      "remediation": "Restore PBKDF2-HMAC-SHA256 with per-user salt and constant-time compare."
    }
  ]
}

EXAMPLE — requirement satisfied (report nothing for it):
If the code correctly uses bcrypt, do not include a finding for that requirement.
Only report violations or clear absences.

OUTPUT FORMAT — return ONLY valid JSON matching this exact shape, nothing else:
{
  "findings": [
    {
      "checker": "spec_conformance",
      "file": "<exact file path as it appears in the diff>",
      "line": <exact line number as integer>,
      "severity": "high" | "medium" | "low",
      "title": "<requirement_id + one-line summary of the violation>",
      "detail": "<one sentence: which PRD requirement is violated and how>",
      "evidence": "<verbatim quoted line copied from the diff>",
      "cwe": "<CWE ID or null>",
      "remediation": "<one sentence fix or null>"
    }
  ]
}

Now check this unified diff:
{{CODE_INPUT}}
