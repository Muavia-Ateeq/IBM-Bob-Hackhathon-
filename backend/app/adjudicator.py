from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.schemas import CheckerResult, CheckerStatus, Severity, Verdict

SEVERITY_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]

_BLOCKING = {Severity.CRITICAL, Severity.HIGH}
_REVIEW_TRIGGER = {Severity.MEDIUM, Severity.LOW, Severity.INFO}


def _worst(findings: Sequence[Any]) -> Severity | None:
    for severity in SEVERITY_ORDER:
        for finding in findings:
            if finding.severity is severity:
                return severity
    return None


def adjudicate(results: Sequence[CheckerResult]) -> tuple[Verdict, str, list[str]]:
    """Reduce checker results to one verdict. Pure function: no I/O, no model, no clock."""
    if not results:
        return Verdict.REVIEW, "no checkers ran", []

    by_name = {result.checker: result for result in results}
    incomplete = [name for name, result in by_name.items() if not result.completed]
    findings = [finding for result in results for finding in result.findings]
    worst = _worst(findings)

    if worst in _BLOCKING:
        reason = f"{worst.value} finding reported"
        if incomplete:
            reason += f"; {len(incomplete)} of {len(results)} checkers did not complete"
        return Verdict.BLOCK, reason, sorted(incomplete)

    if worst in _REVIEW_TRIGGER:
        reason = f"{worst.value} finding reported"
        if incomplete:
            reason += f"; {len(incomplete)} of {len(results)} checkers did not complete"
        return Verdict.REVIEW, reason, sorted(incomplete)

    if incomplete:
        return (
            Verdict.REVIEW,
            f"no findings, but {len(incomplete)} of {len(results)} checkers did not complete",
            sorted(incomplete),
        )

    if any(result.status is CheckerStatus.TIMEOUT for result in results):
        return Verdict.REVIEW, "a checker timed out", sorted(incomplete)

    return Verdict.PASS, "all checkers completed with no findings", []
