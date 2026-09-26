from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adjudicator import adjudicate
from app.checkers.base import execute
from app.checkers.semantic import SemanticChecker
from app.llm.client import StaticProvider
from app.schemas import CheckerStatus, Verdict

DIFF = """--- a/app/orders.py
+++ b/app/orders.py
@@ -38,6 +38,9 @@ def find_order(conn, order_id):
-    cur = conn.cursor()
+    cur = conn.cursor()
+    cur.execute("SELECT * FROM orders WHERE id = " + order_id)
+    return cur.fetchone()
"""

BUDGET = 120_000


def _checker(payload: dict, budget: int = BUDGET) -> SemanticChecker:
    return SemanticChecker("authz", "authorization", StaticProvider(payload), budget)


def _run(checker: SemanticChecker, diff: str = DIFF):
    return asyncio.run(execute(checker, diff, ".", 30))


def test_a_diff_over_budget_is_never_reported_as_clean() -> None:
    result = _run(_checker({"findings": []}), "x" * (BUDGET + 1))
    assert result.status is not CheckerStatus.OK


def test_an_over_budget_diff_degrades_to_review_and_never_passes() -> None:
    result = _run(_checker({"findings": []}), "x" * (BUDGET + 1))
    verdict, _, degraded = adjudicate([result])
    assert verdict is Verdict.REVIEW
    assert degraded == ["authz"]
    assert "budget" in (result.error or "")


def test_a_diff_at_exactly_the_budget_is_still_reviewed() -> None:
    result = _run(_checker({"findings": []}), "x" * BUDGET)
    assert result.status is CheckerStatus.OK


def test_evidence_quoted_from_the_diff_is_accepted() -> None:
    payload = {
        "findings": [
            {
                "severity": "critical",
                "title": "SQL injection",
                "detail": "order_id is concatenated into SQL",
                "file": "app/orders.py",
                "line": 3,
                "evidence": 'cur.execute("SELECT * FROM orders WHERE id = " + order_id)',
                "cwe": "CWE-89",
                "remediation": "parameterise",
            }
        ]
    }
    result = _run(_checker(payload))
    assert result.status is CheckerStatus.OK
    assert result.findings[0].severity.value == "critical"


def test_evidence_absent_from_the_diff_is_rejected_rather_than_trusted() -> None:
    payload = {
        "findings": [
            {
                "severity": "critical",
                "title": "SQL injection",
                "detail": "order_id is concatenated into SQL",
                "file": "app/orders.py",
                "line": 3,
                "evidence": "potential SQL injection here",
                "cwe": "CWE-89",
                "remediation": "parameterise",
            }
        ]
    }
    result = _run(_checker(payload))
    assert result.status is CheckerStatus.ERROR
    assert "not a quote from the diff" in (result.error or "")


def test_one_hallucinated_quote_discards_the_honest_findings_alongside_it() -> None:
    honest = {
        "severity": "medium",
        "title": "Unpinned dependency",
        "detail": "no version constraint",
        "file": "requirements.txt",
        "line": 1,
        "evidence": "+requests",
        "cwe": None,
        "remediation": "pin it",
    }
    invented = dict(honest, severity="critical", file="app/orders.py", line=3,
                    evidence="this line is not in the diff at all")
    result = _run(_checker({"findings": [honest, invented]}))
    assert result.status is CheckerStatus.ERROR
    assert result.findings == []


def test_a_hallucinated_critical_never_reaches_the_adjudicator_as_a_block() -> None:
    payload = {
        "findings": [
            {
                "severity": "critical",
                "title": "Remote code execution",
                "detail": "fabricated",
                "file": "app/orders.py",
                "line": 1,
                "evidence": "eval(user_input)",
                "cwe": None,
                "remediation": None,
            }
        ]
    }
    verdict, _, degraded = adjudicate([_run(_checker(payload))])
    assert verdict is Verdict.REVIEW
    assert degraded == ["authz"]


def test_a_crlf_diff_still_matches_evidence_the_model_echoed_without_carriage_returns() -> None:
    payload = {
        "findings": [
            {
                "severity": "high",
                "title": "SQL injection",
                "detail": "concatenated",
                "file": "app/orders.py",
                "line": 3,
                "evidence": 'cur.execute("SELECT * FROM orders WHERE id = " + order_id)',
                "cwe": None,
                "remediation": None,
            }
        ]
    }
    result = _run(_checker(payload), DIFF.replace("\n", "\r\n"))
    assert result.status is CheckerStatus.OK
    assert result.findings


def test_a_finding_missing_a_field_reports_validation_failure_not_a_keyerror() -> None:
    incomplete = {
        "severity": "high",
        "title": "Missing everything else",
        "detail": "no file, line, or evidence",
    }
    result = _run(_checker({"findings": [incomplete]}))
    assert result.status is CheckerStatus.ERROR
    assert "failed evidence validation" in (result.error or "")


def test_a_clean_diff_with_no_findings_still_completes() -> None:
    result = _run(_checker({"findings": []}))
    assert result.status is CheckerStatus.OK
    assert result.findings == []
    assert adjudicate([result])[0] is Verdict.PASS


def test_an_empty_diff_is_not_sent_to_the_model_at_all() -> None:
    provider = StaticProvider({"findings": []})
    checker = SemanticChecker("authz", "authorization", provider, BUDGET)
    assert asyncio.run(execute(checker, "   \n  ", ".", 30)).findings == []
    assert provider.calls == 0
