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


def _quote_present(evidence: str, body: str) -> bool:
    """Whether the model's quote actually occurs in the diff it was shown.

    ``\\r`` is dropped by the caller, so a diff read on Windows and a model echoing LF compare
    equal. A false rejection here costs precision, never safety: the batch is discarded and the
    checker degrades to ``REVIEW``, which is where an unlocatable quote belongs.
    """
    return evidence.strip() in body


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
        # ponytail: refuses an over-budget diff rather than chunking it. Truncation is
        # fail-open — the model is told nothing was cut, returns an empty array, and the run
        # degrades to PASS having reviewed a fraction of the change. Chunking, with the
        # evidence check re-run per chunk, is the upgrade if real PRs exceed this budget.
        if len(diff) > self._max_diff_bytes:
            raise ValueError(
                f"diff is {len(diff)} characters, over the {self._max_diff_bytes} budget; "
                "raise TRUSTGATE_MAX_DIFF_BYTES or review this PR in smaller pieces"
            )
        body = diff.replace("\r", "")
        system = f"You are a security reviewer. Your focus: {self._focus}\n\n{EVIDENCE_CONTRACT}"
        user = f"Review this unified diff.\n\n```diff\n{body}\n```"
        completion = await self._provider.complete_json(system, user, FINDING_SCHEMA)
        raw: Any = completion.payload
        if not isinstance(raw, dict) or "findings" not in raw:
            raise ValueError("model response did not contain a 'findings' key")
        items = raw["findings"]
        if not isinstance(items, list):
            raise ValueError("model response 'findings' was not a list")
        # One unlocatable quote discards the whole batch. The same model produced every quote in
        # it, so the ones that happen to match carry no more assurance than the one that does
        # not. Degrading to REVIEW is honest; acting on the survivors is not.
        try:
            return [self._to_finding(item, body) for item in items]
        except (ValidationError, KeyError) as exc:
            raise ValueError(
                f"model returned {len(items)} finding(s) that failed evidence validation: {exc}"
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
        if not _quote_present(finding.evidence, body):
            raise ValueError(
                f"evidence for {finding.file}:{finding.line} is not a quote from the diff "
                f"under review: {finding.evidence[:120]!r}"
            )
        return finding

