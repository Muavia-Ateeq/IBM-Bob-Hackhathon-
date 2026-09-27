from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.runlog import compute_verdict, load_all_records, load_results, write_run_records
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


def test_unreadable_file_is_counted_not_named(tmp_path: Path) -> None:
    """A corrupt file is counted, never named.

    Its filename embeds a run_id and checker name, and the verdict reason is written to the
    PR job summary — so naming it would republish another PR's filenames. See runlog.
    """
    write_run_records([result()], "repo#1", "r1", tmp_path)
    (tmp_path / "corrupt.json").write_text("{not json", encoding="utf-8")
    record = compute_verdict("repo#1", tmp_path)
    assert "1 unattributable unreadable run file(s)" in record.reason
    assert "corrupt.json" not in record.reason
    assert record.verdict is Verdict.REVIEW, "an unreadable checker result is an unaccounted result"
    assert record.degraded is True


def test_a_corrupt_run_file_never_yields_pass(tmp_path: Path) -> None:
    """The fail-closed invariant, on the path that had no test.

    `write_run_records` writes one file per checker with no atomic rename, so a killed
    process leaves a truncated record. The readable records still adjudicate clean, so
    before this was fixed the verdict came back PASS and the gate's `grep -q BLOCK` let the
    PR merge -- with one checker's result silently missing.
    """
    write_run_records([result(), result("injection"), result("business")], "repo#1", "r1", tmp_path)
    assert compute_verdict("repo#1", tmp_path).verdict is Verdict.PASS

    (tmp_path / "r1_authz.json").write_text('{"run_id": "r1", "pr": "repo#1", "res', encoding="utf-8")
    record = compute_verdict("repo#1", tmp_path)

    assert record.verdict is Verdict.REVIEW
    assert record.degraded is True
    assert "could not be read" in record.reason


def test_a_corrupt_run_file_does_not_downgrade_a_block(tmp_path: Path) -> None:
    write_run_records([result(findings=[finding()])], "repo#1", "r1", tmp_path)
    (tmp_path / "corrupt.json").write_text("{not json", encoding="utf-8")
    assert compute_verdict("repo#1", tmp_path).verdict is Verdict.BLOCK


def test_unreadable_files_do_not_disclose_another_pr(tmp_path: Path) -> None:
    """A corrupt file whose name is shaped like another PR's must not surface in this PR's reason."""
    write_run_records([result()], "repo#1", "r1", tmp_path)
    (tmp_path / "run_20990101_000000_secretcheck.json").write_text("{not json", encoding="utf-8")
    record = compute_verdict("repo#1", tmp_path)
    assert "secretcheck" not in record.reason
    assert "1 unattributable unreadable run file(s)" in record.reason


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
    assert unreadable == 0
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


def test_load_all_records_skips_a_corrupt_file_and_says_which(tmp_path: Path) -> None:
    """`/api/runs` backs this. A corrupt file must be skipped, not fatal — but a silently
    dropped record is a silently dropped finding, so the name is returned for reporting."""
    write_run_records([result("authz"), result("injection")], "repo#1", "r1", tmp_path)
    (tmp_path / "corrupt.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "wrongshape.json").write_text('{"run_id": "r9"}', encoding="utf-8")

    records, unreadable = load_all_records(tmp_path)

    assert sorted(record.result.checker for record in records) == ["authz", "injection"]
    assert sorted(unreadable) == ["corrupt.json", "wrongshape.json"]


def test_load_all_records_on_a_missing_directory_is_empty_not_an_error(tmp_path: Path) -> None:
    records, unreadable = load_all_records(tmp_path / "nope")
    assert (records, unreadable) == ([], [])
