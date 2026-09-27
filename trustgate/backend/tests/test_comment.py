from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.comment import SEVERITY_EMOJI, render_comment
from app.schemas import (
    CheckerResult,
    CheckerStatus,
    CheckerTier,
    Finding,
    Severity,
    Verdict,
    VerdictRecord,
)


def _record(
    verdict: Verdict = Verdict.BLOCK,
    findings: list[Finding] | None = None,
    degraded: bool = False,
    degraded_checkers: list[str] | None = None,
    results: list[CheckerResult] | None = None,
    reason: str = "critical finding reported",
) -> VerdictRecord:
    return VerdictRecord(
        verdict=verdict,
        reason=reason,
        degraded=degraded,
        degraded_checkers=degraded_checkers or [],
        findings=findings or [],
        results=results if results is not None else [_ok("injection"), _ok("authz")],
        input_hash="0" * 64,
        duration_ms=120,
    )


def _ok(checker: str) -> CheckerResult:
    return CheckerResult(
        checker=checker,
        tier=CheckerTier.SEMANTIC,
        status=CheckerStatus.OK,
        findings=[],
        duration_ms=5,
    )


def _finding(severity: Severity, evidence: str = 'cur.execute("SELECT 1")') -> Finding:
    return Finding(
        checker="injection",
        severity=severity,
        title="SQL injection",
        detail="user input concatenated into a query",
        file="app/orders.py",
        line=42,
        evidence=evidence,
    )


def test_every_severity_has_a_glyph_and_a_text_label() -> None:
    for severity in Severity:
        assert severity in SEVERITY_EMOJI
    body = render_comment(
        _record(findings=[_finding(s) for s in Severity])
    )
    for severity in Severity:
        assert severity.value.upper() in body


def test_a_pipe_in_evidence_does_not_add_a_column() -> None:
    body = render_comment(_record(findings=[_finding(Severity.CRITICAL, "a | b | c")]))
    row = next(line for line in body.splitlines() if line.startswith("| `injection`"))
    assert row.count("|") - row.count("\\|") == 6


def test_a_newline_in_evidence_does_not_split_the_table_row() -> None:
    body = render_comment(_record(findings=[_finding(Severity.HIGH, "line one\nline two")]))
    assert "line one line two" in body
    assert "line one\nline two" not in body


def test_backticks_in_evidence_do_not_end_the_code_span_early() -> None:
    body = render_comment(_record(findings=[_finding(Severity.HIGH, "use ``x`` here")]))
    row = next(line for line in body.splitlines() if line.startswith("| `injection`"))
    assert row.rstrip().endswith("|")


def test_long_evidence_is_truncated() -> None:
    body = render_comment(_record(findings=[_finding(Severity.LOW, "y" * 400)]))
    assert "y" * 400 not in body
    assert "…" in body


def test_a_clean_pass_says_pass_and_has_no_findings_table() -> None:
    body = render_comment(
        _record(verdict=Verdict.PASS, reason="all checkers completed with no findings")
    )
    assert "Verdict: PASS" in body
    assert "None reported." in body


def test_a_degraded_review_names_the_checkers_that_did_not_run() -> None:
    body = render_comment(
        _record(verdict=Verdict.REVIEW, degraded=True, degraded_checkers=["authz"])
    )
    assert "`authz`" in body
    assert "did not complete" in body


def test_the_checker_count_comes_from_the_run_not_a_constant() -> None:
    body = render_comment(_record(results=[_ok("a"), _ok("b"), _ok("c")]))
    assert "3 automated checkers ran" in body
    assert "2 automated checkers ran" in render_comment(_record())


def test_a_single_checker_is_not_pluralised() -> None:
    body = render_comment(_record(results=[_ok("a")]))
    assert "1 automated checker ran" in body
