"""Guards the two scoring rules in bench/run_benchmark.py that produce published numbers.

Both existed and both were wrong in the direction this project exists to prevent: a
number that looks like a measurement and is not one. The first is a precision of 0.50
for a checker that found the planted defect exactly right, caused by charging every
finding as a false positive before testing it for a match. The second unscored every
case whenever any checker degraded, so a checker that did run could never be measured.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
BENCH = BACKEND.parent / "bench"
for entry in (str(BACKEND), str(BENCH)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import run_benchmark as rb
from app.schemas import CheckerResult, CheckerStatus, CheckerTier, Finding, Severity, Verdict, VerdictRecord


def _corpus(*cases: rb.Case) -> rb.Corpus:
    return rb.Corpus(corpus="test", version=1, base="base", line_tolerance=2, cases=list(cases))


def _finding(checker: str, file: str, line: int) -> Finding:
    return Finding(
        checker=checker,
        severity=Severity.HIGH,
        title=f"{checker} finding",
        detail="detail",
        file=file,
        line=line,
        evidence="x = 1",
    )


def _record(findings: list[Finding], degraded: list[str]) -> VerdictRecord:
    return VerdictRecord(
        verdict=Verdict.REVIEW,
        reason="test",
        degraded=bool(degraded),
        degraded_checkers=degraded,
        findings=findings,
        results=[
            CheckerResult(
                checker=f.checker,
                tier=CheckerTier.DETERMINISTIC,
                status=CheckerStatus.OK,
                findings=[],
                duration_ms=1,
            )
            for f in findings
        ],
        input_hash="h",
        duration_ms=1,
    )


def _secret_case() -> rb.Case:
    return rb.Case(
        id="issue-02-hardcoded-key",
        title="hardcoded key",
        expected_checker="secrets",
        expected_file="config.py",
        expected_line=5,
    )


def test_a_matching_finding_is_a_true_positive_and_not_also_a_false_positive():
    case = _secret_case()
    result = rb.CaseResult(
        case=case, record=_record([_finding("secrets", "config.py", 5)], degraded=[])
    )
    tallies: dict[str, rb.Tally] = {}

    rb.score(_corpus(case), [result], tallies)

    tally = tallies["secrets"]
    assert (tally.true_positives, tally.false_positives, tally.false_negatives) == (1, 0, 0)
    assert result.outcome == "tp"


def test_others_degrading_does_not_unscore_the_case_whose_checker_ran():
    """The regression: GITLEAKS_BIN set, no GROQ_API_KEY, and the one measurable
    result in the project scored zero of everything because three unrelated
    checkers were down."""
    case = _secret_case()
    result = rb.CaseResult(
        case=case,
        record=_record(
            [_finding("secrets", "config.py", 5)], degraded=["authz", "injection", "business"]
        ),
    )
    tallies: dict[str, rb.Tally] = {}

    rb.score(_corpus(case), [result], tallies)

    assert result.outcome == "tp"
    assert tallies["secrets"].true_positives == 1


def test_a_second_unmatched_finding_from_the_same_checker_is_a_false_positive():
    case = _secret_case()
    result = rb.CaseResult(
        case=case,
        record=_record(
            [_finding("secrets", "config.py", 5), _finding("secrets", "app.py", 99)],
            degraded=[],
        ),
    )
    tallies: dict[str, rb.Tally] = {}

    rb.score(_corpus(case), [result], tallies)

    tally = tallies["secrets"]
    assert (tally.true_positives, tally.false_positives) == (1, 1)


def test_the_expected_checker_being_down_still_unscores_the_case():
    case = rb.Case(
        id="issue-03-sql-injection",
        title="sql injection",
        expected_checker="injection",
        expected_file="app.py",
        expected_line=42,
    )
    result = rb.CaseResult(case=case, record=_record([], degraded=["injection"]))
    tallies: dict[str, rb.Tally] = {}

    rb.score(_corpus(case), [result], tallies)

    assert result.outcome == "degraded"
    assert tallies.get("injection") is None or tallies["injection"].false_negatives == 0


def test_a_case_expecting_clean_is_unscored_if_any_checker_degraded():
    case = rb.Case(id="issue-07-license-violation", title="license", expected_checker=None)
    result = rb.CaseResult(case=case, record=_record([], degraded=["authz"]))
    tallies: dict[str, rb.Tally] = {}

    rb.score(_corpus(case), [result], tallies)

    assert result.outcome == "degraded"


def test_a_clean_case_is_clean_and_a_dirty_one_is_a_false_positive():
    clean_case = rb.Case(id="c1", title="t1")
    dirty_case = rb.Case(id="c2", title="t2")
    clean = rb.CaseResult(case=clean_case, record=_record([], degraded=[]))
    dirty = rb.CaseResult(
        case=dirty_case, record=_record([_finding("secrets", "app.py", 3)], degraded=[])
    )
    tallies: dict[str, rb.Tally] = {}

    rb.score(_corpus(clean_case, dirty_case), [clean, dirty], tallies)

    assert clean.outcome == "clean"
    assert dirty.outcome == "fp"
    assert tallies["secrets"].false_positives == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
