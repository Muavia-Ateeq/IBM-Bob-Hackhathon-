from __future__ import annotations

from typing import Any

from app.llm.client import Provider
from app.llm.schemas import FINDING_SCHEMA
from app.schemas import CheckerTier, Finding
from pydantic import ValidationError

EVIDENCE_CONTRACT = """
Every finding you report MUST be grounded in a line that is present in the diff below.

Rules you must not break:
- `file` must be a path exactly as it appears in the diff, and `line` must be a positive
  integer line number.
- `evidence` must be a verbatim quote of the offending line copied from the diff. Never
  paraphrase it. Never describe what the code does instead of quoting it.
- If you cannot quote a specific line, do not report the finding. Report nothing.
- Do not report style, naming, formatting, or architecture opinions.
- Do not report the absence of a test.
- If the diff contains no problem in your focus area, return an empty findings array.
""".strip()


class SemanticChecker:
    def __init__(self, name: str, focus: str, provider: Provider, max_diff_bytes: int) -> None:
        self.name = name
        self.tier = CheckerTier.SEMANTIC
        self._focus = focus
        self._provider = provider
        self._max_diff_bytes = max_diff_bytes

    async def run(self, diff: str, workspace: str) -> list[Finding]:
        if not diff.strip():
            return []
        body = diff[: self._max_diff_bytes]
        system = f"You are a security reviewer. Your focus: {self._focus}\n\n{EVIDENCE_CONTRACT}"
        user = f"Review this unified diff.\n\n```diff\n{body}\n```"
        completion = await self._provider.complete_json(system, user, FINDING_SCHEMA)
        raw: Any = completion.payload
        if not isinstance(raw, dict) or "findings" not in raw:
            raise ValueError("model response did not contain a 'findings' key")
        items = raw["findings"]
        if not isinstance(items, list):
            raise ValueError("model response 'findings' was not a list")
        try:
            return [self._to_finding(item) for item in items]
        except ValidationError as exc:
            raise ValueError(f"model returned {len(items)} finding(s) that failed evidence validation: {exc}") from exc

    def _to_finding(self, item: Any) -> Finding:
        if not isinstance(item, dict):
            raise ValueError("finding was not an object")
        return Finding(
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
