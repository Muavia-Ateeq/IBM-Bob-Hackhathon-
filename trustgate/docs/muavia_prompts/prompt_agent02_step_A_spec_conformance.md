You are reading a Product Requirements Document (PRD) to extract specific,
testable engineering requirements — the kind that can be checked directly
against source code.

Only extract a requirement if it is:
- specific enough to verify mechanically (e.g. "passwords must be hashed
  with bcrypt", "all API endpoints must be rate-limited")
- stated directly in the document, not implied or inferred by you

Do NOT extract vague, aspirational, or non-technical statements
(e.g. "the system should be secure" is too vague — skip it).

For each requirement you extract, you must quote the exact sentence or
phrase from the PDF that states it, under 15 words. If you cannot point to
an exact quote in the document, do not include that requirement.

OUTPUT FORMAT — return ONLY this JSON, nothing else:
{
  "requirements": [
    {
      "requirement_id": "req_1",
      "quote": "<exact quote from the PDF, under 15 words>",
      "plain_description": "<one sentence describing what this requires>"
    }
  ]
}

Now read this PRD and extract requirements:
{{PRD_TEXT}}
