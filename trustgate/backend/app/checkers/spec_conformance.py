"""
Spec-Conformance checker — M. Muavia

Two-step design that mirrors the Bob document-understanding workflow:

  Step A — requirement extraction:
    The LLM reads the PRD text below and returns only the specific,
    mechanically-verifiable requirements it can quote directly from the
    document. Requirements it cannot quote are not returned. This prevents
    hallucinated requirements from reaching Step B.

  Step B — diff check:
    The LLM receives the verified requirements from Step A and the unified
    diff. It reports a finding only for requirements that are clearly
    violated or clearly absent in the diff, with a verbatim evidence quote.

Prompt docs: docs/muavia_prompts/prompt_agent02_step_A_spec_conformance.md
             docs/muavia_prompts/prompt_agent02_step_B_spec_conformance.md
"""
from __future__ import annotations

from typing import Any

from app.llm.client import Provider
from app.llm.schemas import FINDING_SCHEMA, REQUIREMENTS_SCHEMA
from app.schemas import CheckerTier, Finding
from pydantic import ValidationError

PRD_TEXT = """
TrustGate Order Service — Product Requirements

Security requirements:
1. Password hashing: all user passwords must be hashed using PBKDF2-HMAC-SHA256 or bcrypt
   with a per-user salt before being stored. MD5, SHA1, and any unsalted algorithm are
   prohibited.
2. Rate limiting: the login endpoint and any endpoint that modifies user credentials must
   implement per-IP failed-attempt counting and temporary blocking after five consecutive
   failures within sixty seconds.
3. Secret management: API keys, signing keys, database credentials, and tokens must be
   loaded from environment variables or a secrets manager. Hardcoding them in source is
   prohibited.
4. Production configuration: debug mode, the interactive error console, and verbose
   stack-trace pages must be disabled in all production configuration files.
""".strip()

STEP_A_SYSTEM = (
    "You are reading a Product Requirements Document (PRD) to extract specific, "
    "testable engineering requirements — the kind that can be checked directly against "
    "source code. Only extract a requirement if it is specific enough to verify "
    "mechanically and if you can quote the exact phrase from the document under 15 words. "
    "Do NOT extract vague or aspirational statements. "
    "Return ONLY valid JSON matching the schema provided."
)

STEP_B_SYSTEM = (
    "You are checking whether a code change violates any of the VERIFIED requirements "
    "listed below. These requirements have already been confirmed to exist in the project "
    "PRD. Report a finding ONLY if a requirement is clearly violated or clearly absent in "
    "the diff — not if you are unsure, and not for requirements the code does not touch. "
    "Every finding must include the exact file path, line number, and a verbatim evidence "
    "quote copied from the diff. If the evidence quote is not a literal substring of the "
    "diff shown to you, DO NOT report that finding. "
    "Return ONLY valid JSON matching the schema provided."
)


class SpecConformanceChecker:
    name = "spec_conformance"
    tier = CheckerTier.SEMANTIC

    def __init__(self, provider: Provider, max_diff_bytes: int) -> None:
        self._provider = provider
        self._max_diff_bytes = max_diff_bytes

    async def run(self, diff: str, workspace: str) -> list[Finding]:
        if not diff.strip():
            return []
        if len(diff) > self._max_diff_bytes:
            raise ValueError(
                f"diff is {len(diff)} characters, over the {self._max_diff_bytes} budget"
            )

        body = diff.replace("\r", "")

        step_a = await self._provider.complete_json(
            STEP_A_SYSTEM,
            f"Extract requirements from this PRD:\n\n{PRD_TEXT}",
            REQUIREMENTS_SCHEMA,
        )
        raw_a: Any = step_a.payload
        if not isinstance(raw_a, dict) or "requirements" not in raw_a:
            raise ValueError("Step A: model response did not contain a 'requirements' key")
        reqs = raw_a["requirements"]
        if not isinstance(reqs, list) or not reqs:
            return []

        req_block = "\n".join(
            f"- {r['requirement_id']}: \"{r['quote']}\" — {r['plain_description']}"
            for r in reqs
            if isinstance(r, dict)
            and r.get("requirement_id")
            and r.get("quote")
            and r.get("plain_description")
        )
        if not req_block:
            return []

        step_b = await self._provider.complete_json(
            STEP_B_SYSTEM,
            (
                f"VERIFIED REQUIREMENTS:\n{req_block}\n\n"
                f"Review this unified diff:\n\n```diff\n{body}\n```"
            ),
            FINDING_SCHEMA,
        )
        raw_b: Any = step_b.payload
        if not isinstance(raw_b, dict) or "findings" not in raw_b:
            raise ValueError("Step B: model response did not contain a 'findings' key")
        items = raw_b["findings"]
        if not isinstance(items, list):
            raise ValueError("Step B: model response 'findings' was not a list")

        try:
            return [self._to_finding(item, body) for item in items]
        except (ValidationError, KeyError) as exc:
            raise ValueError(
                f"Step B: {len(items)} finding(s) failed validation: {exc}"
            ) from exc

    def _to_finding(self, item: Any, body: str) -> Finding:
        if not isinstance(item, dict):
            raise ValueError("finding was not an object")
        finding = Finding(
            checker=self.name,
            severity=item["severity"],
            title=item["title"],
            detail=item["detail"],
            file=item["file"],
            line=item["line"],
            evidence=item["evidence"],
            cwe=item.get("cwe"),
            remediation=item.get("remediation"),
        )
        if finding.evidence.strip() not in body:
            raise ValueError(
                f"evidence for {finding.file}:{finding.line} is not a quote from the diff: "
                f"{finding.evidence[:120]!r}"
            )
        return finding


def build(provider: Provider, max_diff_bytes: int) -> SpecConformanceChecker:
    return SpecConformanceChecker(provider, max_diff_bytes)
