from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import render
from app.schemas import CheckerResult, CheckerStatus, CheckerTier, Finding, Severity, Verdict

# The gate's final step decides whether to fail the run with this pattern, against the text the
# CLI printed. If a format change breaks the match, the gate stops blocking and nobody finds
# out until a vulnerable PR merges. That is a fail-open in CI, so the coupling is pinned here.
GATE_MATCHES_BLOCK = re.compile(r"^VERDICT[ \t]+BLOCK", re.MULTILINE)


def _ok(checker: str, *findings: Finding) -> CheckerResult:
    return CheckerResult(
        checker=checker,
        tier=CheckerTier.SEMANTIC,
        status=CheckerStatus.OK,
        findings=list(findings),
        duration_ms=3,
    )


def _critical() -> Finding:
    return Finding(
        checker="injection",
        severity=Severity.CRITICAL,
        title="SQL injection",
        detail="input concatenated into a query",
        file="app/orders.py",
        line=42,
        evidence='cur.execute("SELECT * FROM t WHERE id = " + oid)',
    )


def test_a_block_verdict_is_caught_by_the_gate_pattern() -> None:
    out = render([_ok("injection", _critical())], Verdict.BLOCK, "critical finding reported", 12)
    assert GATE_MATCHES_BLOCK.search(out), "the workflow's final step would not fail the run"


def test_a_review_verdict_is_not_caught_by_the_gate_pattern() -> None:
    out = render([], Verdict.REVIEW, "no checkers ran", 4)
    assert not GATE_MATCHES_BLOCK.search(out)


def test_a_pass_verdict_is_not_caught_by_the_gate_pattern() -> None:
    out = render([_ok("authz")], Verdict.PASS, "all checkers completed with no findings", 9)
    assert not GATE_MATCHES_BLOCK.search(out)


def test_a_degraded_run_never_reports_pass_in_the_text_the_gate_reads() -> None:
    degraded = CheckerResult(
        checker="authz",
        tier=CheckerTier.SEMANTIC,
        status=CheckerStatus.ERROR,
        duration_ms=1,
        error="ProviderUnavailable: GROQ_API_KEY is not set",
    )
    out = render([degraded], Verdict.REVIEW, "no checkers ran", 2)
    assert "VERDICT  PASS" not in out
    assert "A degraded run can never return PASS" in out
