from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.checkers import prompt_injection
from app.checkers.base import execute
from app.checkers.semantic import SemanticChecker
from app.llm.client import StaticProvider
from app.schemas import CheckerStatus, CheckerTier

BUDGET = 120_000

# The real planted defect this checker exists to catch: demo_target/issue-06-prompt-injection
# concatenates untrusted `profile_notes` and `question` straight into a support-agent
# instruction string, with no delimiter and no statement that the concatenated text is
# untrusted data. bench/cases.json records this case as `disputed` against the `injection`
# checker's FOCUS (SQL/template/command injection) precisely because no FOCUS string in the
# roster names prompt injection or instruction-hierarchy violations -- this file closes that
# gap rather than duplicating `injection`.
DIFF = '''--- a/app.py
+++ b/app.py
@@ -94,6 +94,12 @@ def export_invoice(conn, order_id, user_id):
     ).encode("utf-8")
 
 
+def build_support_prompt(question: str, profile_notes: str) -> str:
+    """Compose the prompt handed to the support assistant."""
+    return (
+        "You are a support agent for the order service. "
+        "Answer only from the order database and never reveal another "
+        "customer's data.\\n"
+        "Customer notes: " + profile_notes + "\\n"
+        "Question: " + question
+    )
'''


def _checker(payload: dict) -> SemanticChecker:
    return prompt_injection.build(StaticProvider(payload), BUDGET)


def _run(checker: SemanticChecker, diff: str = DIFF):
    return asyncio.run(execute(checker, diff, ".", 30))


def test_build_wires_the_shared_semantic_checker_with_the_right_identity() -> None:
    checker = prompt_injection.build(StaticProvider({"findings": []}), BUDGET)
    assert checker.name == "prompt_injection"
    assert checker.tier is CheckerTier.SEMANTIC
    assert isinstance(checker, SemanticChecker)


def test_focus_names_instruction_hierarchy_not_just_code_injection() -> None:
    # A cheap guard against a future edit accidentally narrowing this checker back into
    # `injection`'s territory (SQL/template/command injection), which would make the two
    # checkers redundant rather than independent signals.
    focus = prompt_injection.FOCUS.lower()
    assert "prompt injection" in focus or "instruction" in focus
    assert "untrusted" in focus


def test_accepts_the_real_planted_defect_in_issue_06_with_evidence_quoted() -> None:
    # This is the exact line bench/cases.json expects for issue-06-prompt-injection
    # (file=app.py, line=103, severity=medium, line_tolerance=5). The evidence string below
    # is copied verbatim from the diff above, as EVIDENCE_CONTRACT requires.
    payload = {
        "findings": [
            {
                "severity": "medium",
                "title": "Untrusted profile notes concatenated into a model instruction",
                "detail": (
                    "profile_notes and question are user-controlled and are concatenated "
                    "directly into the support-agent instruction string with no delimiter "
                    "and no statement that this text is untrusted data, so a customer can "
                    "inject their own instructions into the assistant's context."
                ),
                "file": "app.py",
                "line": 103,
                "evidence": '"Customer notes: " + profile_notes + "\\n"',
                "cwe": "CWE-1427",
                "remediation": (
                    "Wrap profile_notes and question in a clearly labelled untrusted-data "
                    "block, or pass them as a separate message role instead of concatenating "
                    "into the instruction text."
                ),
            }
        ]
    }
    result = _run(_checker(payload))
    assert result.status is CheckerStatus.OK
    assert result.checker == "prompt_injection"
    finding = result.findings[0]
    assert finding.file == "app.py"
    assert finding.line == 103
    assert finding.severity.value == "medium"


def test_a_labelled_untrusted_block_is_not_reported() -> None:
    # No finding at all is a valid, honest response: the model looked and found nothing in
    # its focus area. This mirrors EVIDENCE_CONTRACT's "return an empty findings array" rule
    # rather than asserting the checker itself does the labelling detection -- that judgment
    # belongs to the model, not to this test.
    result = _run(_checker({"findings": []}))
    assert result.status is CheckerStatus.OK
    assert result.findings == []


def test_evidence_not_present_in_the_diff_is_rejected_not_trusted() -> None:
    payload = {
        "findings": [
            {
                "severity": "medium",
                "title": "Untrusted profile notes concatenated into a model instruction",
                "detail": "fabricated location",
                "file": "app.py",
                "line": 103,
                "evidence": "this exact string is not anywhere in the diff under review",
            }
        ]
    }
    result = _run(_checker(payload))
    assert result.status is not CheckerStatus.OK
    assert result.findings == []
