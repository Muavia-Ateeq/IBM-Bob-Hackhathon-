from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.sarif import SARIF_SCHEMA, to_sarif, write_sarif
from app.schemas import Finding, Severity, Verdict, VerdictRecord

# Marks every field GitHub's "SARIF support for code scanning" page lists as Required (R).
# The page rejects empty strings for required properties, so presence alone is not enough.
REQUIRED_PATHS = [
    ("$schema", lambda d: d["$schema"]),
    ("version", lambda d: d["version"]),
    ("runs[0].tool.driver.name", lambda d: d["runs"][0]["tool"]["driver"]["name"]),
    ("runs[0].tool.driver.rules[0].id", lambda d: d["runs"][0]["tool"]["driver"]["rules"][0]["id"]),
    ("runs[0].tool.driver.rules[0].shortDescription.text", lambda d: d["runs"][0]["tool"]["driver"]["rules"][0]["shortDescription"]["text"]),
    ("runs[0].tool.driver.rules[0].fullDescription.text", lambda d: d["runs"][0]["tool"]["driver"]["rules"][0]["fullDescription"]["text"]),
    ("runs[0].tool.driver.rules[0].help.text", lambda d: d["runs"][0]["tool"]["driver"]["rules"][0]["help"]["text"]),
]


def _finding(**overrides) -> Finding:
    base = {
        "checker": "injection",
        "severity": Severity.CRITICAL,
        "title": "SQL injection",
        "detail": "user input is concatenated into a query",
        "file": "app/orders.py",
        "line": 42,
        "evidence": 'cur.execute("SELECT * FROM t WHERE id = " + order_id)',
    }
    return Finding(**{**base, **overrides})


def _record(*findings: Finding, degraded: bool = False) -> VerdictRecord:
    return VerdictRecord(
        verdict=Verdict.BLOCK if findings else Verdict.PASS,
        reason="test",
        degraded=degraded,
        degraded_checkers=["authz"] if degraded else [],
        findings=list(findings),
        results=[],
        input_hash="0" * 64,
        duration_ms=7,
    )


def _result(doc: dict, index: int = 0) -> dict:
    return doc["runs"][0]["results"][index]


def test_the_schema_url_is_the_oasis_one() -> None:
    assert to_sarif(_record(), "42")["$schema"] == SARIF_SCHEMA
    assert to_sarif(_record(), "42")["version"] == "2.1.0"


def test_every_field_github_marks_required_is_present_and_non_empty() -> None:
    doc = to_sarif(_record(_finding()), "42")
    for name, read in REQUIRED_PATHS:
        value = read(doc)
        assert value, f"required and non-empty, but empty: {name}"


def test_a_clean_run_still_carries_a_populated_rule_catalogue() -> None:
    rules = to_sarif(_record(), "42")["runs"][0]["tool"]["driver"]["rules"]
    assert rules, "GitHub marks rules[] required on the driver; a clean run must not empty it"
    assert {rule["id"] for rule in rules} == {
        f"trustgate/{name}"
        for name in ("authz", "business", "injection", "prompt_injection", "secrets")
    }


def test_results_carry_the_fields_github_marks_required() -> None:
    result = _result(to_sarif(_record(_finding()), "42"))
    assert result["message"]["text"]
    physical = result["locations"][0]["physicalLocation"]
    assert physical["artifactLocation"]["uri"] == "app/orders.py"
    assert physical["region"]["startLine"] == 42
    assert result["partialFingerprints"]["primaryLocationLineHash"]


def test_levels_are_ones_github_renders() -> None:
    doc = to_sarif(
        _record(
            _finding(severity=Severity.CRITICAL),
            _finding(severity=Severity.HIGH, file="b.py"),
            _finding(severity=Severity.MEDIUM, file="c.py"),
            _finding(severity=Severity.LOW, file="d.py"),
            _finding(severity=Severity.INFO, file="e.py"),
        ),
        "42",
    )
    assert [r["level"] for r in doc["runs"][0]["results"]] == ["error", "error", "warning", "note", "note"]


def test_security_severity_lands_in_github_published_buckets() -> None:
    doc = to_sarif(
        _record(
            _finding(severity=Severity.CRITICAL),
            _finding(severity=Severity.HIGH, file="b.py"),
            _finding(severity=Severity.MEDIUM, file="c.py"),
            _finding(severity=Severity.LOW, file="d.py"),
            _finding(severity=Severity.INFO, file="e.py"),
        ),
        "42",
    )
    scores = [float(r["properties"]["security-severity"]) for r in doc["runs"][0]["results"]]
    assert all(0.0 < s <= 10.0 for s in scores), "GitHub treats 0.0 and out-of-range as no severity"
    assert scores[0] > 9.0, "critical must land in the >9.0 bucket"
    assert 7.0 <= scores[1] <= 8.9, "high must land in the 7.0-8.9 bucket"
    assert 4.0 <= scores[2] <= 6.9, "medium must land in the 4.0-6.9 bucket"
    assert 0.1 <= scores[3] <= 3.9, "low must land in the 0.1-3.9 bucket"


def test_a_deterministic_checker_declares_higher_precision_than_a_model() -> None:
    rules = {r["name"]: r["properties"]["precision"] for r in to_sarif(_record(_finding()), "42")["runs"][0]["tool"]["driver"]["rules"]}
    assert rules["secrets"] == "very-high"
    assert rules["injection"] == "medium"


def test_the_fingerprint_is_stable_for_one_finding_and_moves_when_the_line_does() -> None:
    first = _result(to_sarif(_record(_finding()), "42"))["partialFingerprints"]["primaryLocationLineHash"]
    same = _result(to_sarif(_record(_finding()), "42"))["partialFingerprints"]["primaryLocationLineHash"]
    moved = _result(to_sarif(_record(_finding(line=43)), "42"))["partialFingerprints"]["primaryLocationLineHash"]
    assert first == same, "a re-run must not orphan its own alerts"
    assert first != moved, "a different line is a different finding"


def test_a_reworded_title_does_not_orphan_an_existing_alert() -> None:
    before = _result(to_sarif(_record(_finding()), "42"))["partialFingerprints"]["primaryLocationLineHash"]
    after = _result(to_sarif(_record(_finding(title="SQL injection (reworded)")), "42"))["partialFingerprints"]["primaryLocationLineHash"]
    assert before == after


def test_a_degraded_run_is_recorded_as_an_unsuccessful_invocation() -> None:
    doc = to_sarif(_record(_finding(), degraded=True), "42")
    assert doc["runs"][0]["invocations"][0]["executionSuccessful"] is False


def test_an_unknown_checker_still_produces_a_valid_rule() -> None:
    doc = to_sarif(_record(_finding(checker="deps")), "42")
    rules = {r["id"]: r for r in doc["runs"][0]["tool"]["driver"]["rules"]}
    assert "trustgate/deps" in rules
    assert rules["trustgate/deps"]["shortDescription"]["text"]
    assert rules["trustgate/deps"]["help"]["text"]


def test_the_document_is_json_serialisable_and_written_to_disk(tmp_path) -> None:
    path = write_sarif(_record(_finding()), "42", tmp_path / "nested" / "trustgate.sarif")
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert reloaded["version"] == "2.1.0"
    assert len(reloaded["runs"][0]["results"]) == 1
