from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adjudicator import adjudicate
from app.schemas import CheckerResult, CheckerStatus, CheckerTier, Finding, Severity, Verdict


def finding(checker: str = "authz", severity: Severity = Severity.MEDIUM) -> Finding:
    return Finding(
        checker=checker,
        severity=severity,
        title="Test finding",
        detail="Test detail",
        file="app/example.py",
        line=1,
        evidence='query = "SELECT * FROM users WHERE id = " + user_id',
    )


def result(
    checker: str = "authz",
    status: CheckerStatus = CheckerStatus.OK,
    findings: list[Finding] | None = None,
) -> CheckerResult:
    return CheckerResult(
        checker=checker,
        tier=CheckerTier.SEMANTIC,
        status=status,
        findings=findings or [],
        duration_ms=1,
    )


def test_empty_run_is_never_pass():
    verdict, reason, degraded = adjudicate([])
    assert verdict is Verdict.REVIEW
    assert reason
    assert degraded == []


def test_all_clean_completed_is_pass():
    results = [result("authz"), result("injection"), result("business")]
    verdict, _, degraded = adjudicate(results)
    assert verdict is Verdict.PASS
    assert degraded == []


def test_pass_requires_every_checker_to_have_completed():
    results = [result("authz"), result("injection"), result("business", CheckerStatus.ERROR)]
    verdict, reason, degraded = adjudicate(results)
    assert verdict is Verdict.REVIEW
    assert degraded == ["business"]
    assert "did not complete" in reason


def test_medium_finding_is_review():
    verdict, _, _ = adjudicate([result(findings=[finding(severity=Severity.MEDIUM)])])
    assert verdict is Verdict.REVIEW


def test_high_finding_is_block():
    verdict, _, _ = adjudicate([result(findings=[finding(severity=Severity.HIGH)])])
    assert verdict is Verdict.BLOCK


def test_critical_finding_is_block():
    verdict, _, _ = adjudicate([result(findings=[finding(severity=Severity.CRITICAL)])])
    assert verdict is Verdict.BLOCK


def test_degraded_error_never_yields_pass():
    results = [result("authz"), result("injection", CheckerStatus.ERROR), result("business")]
    verdict, _, degraded = adjudicate(results)
    assert verdict is Verdict.REVIEW
    assert degraded == ["injection"]


def test_degraded_timeout_never_yields_pass():
    results = [result("authz"), result("injection", CheckerStatus.TIMEOUT), result("business")]
    verdict, reason, degraded = adjudicate(results)
    assert verdict is Verdict.REVIEW
    assert degraded == ["injection"]
    assert "did not complete" in reason


def test_blocking_finding_survives_degradation():
    results = [
        result("authz", findings=[finding(severity=Severity.HIGH)]),
        result("injection", CheckerStatus.ERROR),
    ]
    verdict, _, degraded = adjudicate(results)
    assert verdict is Verdict.BLOCK
    assert degraded == ["injection"]


def test_low_finding_does_not_block():
    verdict, _, _ = adjudicate([result(findings=[finding(severity=Severity.LOW)])])
    assert verdict is Verdict.REVIEW


def test_every_verdict_is_one_of_three():
    results = [result(findings=[finding(severity=Severity.INFO)])]
    verdict, _, _ = adjudicate(results)
    assert verdict in (Verdict.PASS, Verdict.REVIEW, Verdict.BLOCK)


def test_non_ok_checker_may_not_report_findings():
    with pytest.raises(ValidationError):
        result("authz", CheckerStatus.ERROR, findings=[finding()])


def test_finding_requires_a_positive_line():
    with pytest.raises(ValidationError):
        Finding(
            checker="authz",
            severity=Severity.HIGH,
            title="t",
            detail="d",
            file="app/example.py",
            line=0,
            evidence="x = 1",
        )


def test_finding_requires_evidence():
    with pytest.raises(ValidationError):
        Finding(
            checker="authz",
            severity=Severity.HIGH,
            title="t",
            detail="d",
            file="app/example.py",
            line=1,
            evidence="",
        )


@pytest.mark.parametrize("path", ["../../etc/passwd", "..\\..\\windows", "app/../../secret.py"])
def test_finding_rejects_path_traversal(path: str):
    with pytest.raises(ValidationError):
        Finding(
            checker="authz",
            severity=Severity.HIGH,
            title="t",
            detail="d",
            file=path,
            line=1,
            evidence="x = 1",
        )


def test_finding_accepts_an_ordinary_path():
    assert finding().file == "app/example.py"


def test_adjudicator_is_pure():
    results = [result("authz"), result("injection", CheckerStatus.ERROR)]
    first = adjudicate(results)
    second = adjudicate(results)
    assert first == second
    assert adjudicate(list(reversed(results)))[0] is first[0]
