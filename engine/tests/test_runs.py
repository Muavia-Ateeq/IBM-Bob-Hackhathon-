from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.runlog import compute_verdict, load_results, write_run_records
from app.schemas import CheckerResult, CheckerStatus, CheckerTier, Finding, Severity, Verdict


def result(
    checker: str = "authz",
    status: CheckerStatus = CheckerStatus.OK,
    findings: list[Finding] | None = None,
    error: str | None = None,
) -> CheckerResult:
    return CheckerResult(
        checker=checker,
        tier=CheckerTier.SEMANTIC,
        status=status,
        findings=findings or [],
        duration_ms=7,
        error=error,
    )


def finding(checker: str = "authz", severity: Severity = Severity.HIGH) -> Finding:
    return Finding(
        checker=checker,
        severity=severity,
        title="Test finding",
        detail="Test detail",
        file="app/example.py",
        line=1,
        evidence='query = "SELECT * FROM users WHERE id = " + user_id',
    )


def test_missing_runs_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        compute_verdict("repo#1", tmp_path / "absent")


def test_no_runs_never_passes(tmp_path: Path) -> None:
    record = compute_verdict("repo#1", tmp_path)
    assert record.verdict is Verdict.REVIEW
    assert "no checkers ran" in record.reason
    assert record.degraded is True
    assert record.degraded_checkers == []


def test_high_finding_blocks(tmp_path: Path) -> None:
    write_run_records([result(findings=[finding()])], "repo#1", "r1", tmp_path)
    record = compute_verdict("repo#1", tmp_path)
    assert record.verdict is Verdict.BLOCK
    assert len(record.findings) == 1


def test_degraded_checker_yields_review_not_pass(tmp_path: Path) -> None:
    write_run_records(
        [result("injection", CheckerStatus.ERROR, error="ProviderUnavailable: no key")],
        "repo#1",
        "r1",
        tmp_path,
    )
    record = compute_verdict("repo#1", tmp_path)
    assert record.verdict is Verdict.REVIEW
    assert record.degraded is True
    assert record.degraded_checkers == ["injection"]


def test_clean_run_passes(tmp_path: Path) -> None:
    write_run_records([result(), result("injection"), result("business")], "repo#1", "r1", tmp_path)
    record = compute_verdict("repo#1", tmp_path)
    assert record.verdict is Verdict.PASS
    assert record.degraded is False
    assert len(record.results) == 3


def test_records_are_scoped_to_their_pr(tmp_path: Path) -> None:
    write_run_records([result(findings=[finding()])], "repo#1", "r1", tmp_path)
    write_run_records([result()], "repo#2", "r2", tmp_path)
    assert compute_verdict("repo#2", tmp_path).verdict is Verdict.PASS
    assert compute_verdict("repo#1", tmp_path).verdict is Verdict.BLOCK


def test_unreadable_file_is_reported_not_dropped(tmp_path: Path) -> None:
    write_run_records([result()], "repo#1", "r1", tmp_path)
    (tmp_path / "corrupt.json").write_text("{not json", encoding="utf-8")
    record = compute_verdict("repo#1", tmp_path)
    assert "corrupt.json" in record.reason
    assert record.verdict is Verdict.PASS


def test_input_hash_tracks_the_matched_records(tmp_path: Path) -> None:
    write_run_records([result(), result("injection")], "repo#1", "r1", tmp_path)
    baseline = compute_verdict("repo#1", tmp_path).input_hash
    assert baseline == compute_verdict("repo#1", tmp_path).input_hash

    write_run_records([result("business")], "repo#1", "r2", tmp_path)
    assert compute_verdict("repo#1", tmp_path).input_hash != baseline


def test_load_results_returns_parsed_results(tmp_path: Path) -> None:
    write_run_records([result()], "repo#1", "r1", tmp_path)
    results, unreadable, digest = load_results(tmp_path, "repo#1")
    assert [r.checker for r in results] == ["authz"]
    assert unreadable == []
    assert digest


def test_a_later_clean_run_clears_an_earlier_block(tmp_path: Path) -> None:
    """The gate re-runs on every push. A stale CRITICAL must not keep a PR blocked forever."""
    write_run_records([result(findings=[finding(severity=Severity.CRITICAL)])], "repo#1", "r1", tmp_path)
    assert compute_verdict("repo#1", tmp_path).verdict is Verdict.BLOCK

    write_run_records([result(), result("injection")], "repo#1", "r2", tmp_path)
    record = compute_verdict("repo#1", tmp_path)
    assert record.verdict is Verdict.PASS
    assert record.findings == []


def test_only_the_newest_run_is_adjudicated(tmp_path: Path) -> None:
    write_run_records([result("authz"), result("injection")], "repo#1", "r1", tmp_path)
    write_run_records([result("authz"), result("injection"), result("business")], "repo#1", "r2", tmp_path)
    results, _unreadable, _digest = load_results(tmp_path, "repo#1")
    assert sorted(r.checker for r in results) == ["authz", "business", "injection"]
