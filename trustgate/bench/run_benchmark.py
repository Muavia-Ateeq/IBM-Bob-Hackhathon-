"""TrustGate benchmark runner — measures the roster against a labelled corpus.

Reuses the shipped CLI end to end. It invents no analysis path of its own: each
case is diffed against ``demo_target/base``, handed to ``app/main.py`` exactly as
the Actions gate would, and the verdict is read back off disk with the same
``compute_verdict`` call ``main.py:18`` makes. A number this script prints is a
number the product produced.

The contract that matters: **a checker that did not run gets no rate.** Three of
the four checkers need ``GROQ_API_KEY`` (K12) and the fourth needs the gitleaks
binary (K14), so a default run today is INCOMPLETE and reports no precision or
recall at all. A benchmark that printed a score with most of the roster missing
would be the exact fail-open this project exists to not ship.

    python bench/run_benchmark.py --dry-run     # case table, no key, no binary
    python bench/run_benchmark.py                # measure what can be measured
    python bench/run_benchmark.py --only issue-09-weak-hash
"""

from __future__ import annotations

import argparse
import difflib
import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "backend"
BENCH_DIR = REPO_ROOT / "bench"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from app.runlog import compute_verdict  # noqa: E402
from app.schemas import CheckerStatus, VerdictRecord  # noqa: E402

CHECKERS = ("secrets", "authz", "injection", "business")


# --------------------------------------------------------------------------
# Ground truth, validated at the boundary. cases.json is an external input, so a
# typo in it must fail here rather than silently become ground truth.
# --------------------------------------------------------------------------


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    expected_checker: Optional[str] = None
    expected_file: Optional[str] = None
    expected_line: Optional[int] = Field(default=None, ge=1)
    expected_severity: Optional[str] = None
    disputed: bool = False
    rationale: Optional[str] = None
    caveat: Optional[str] = None
    no_checker_reason: Optional[str] = None

    @property
    def is_planted(self) -> bool:
        """A case is measurable only once its defect actually exists on disk."""
        return self.expected_line is not None

    @property
    def expects_clean(self) -> bool:
        """No checker owns this defect, so the ground truth is zero findings."""
        return self.expected_checker is None


class Corpus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpus: str
    version: int = Field(ge=1)
    base: str
    line_tolerance: int = Field(default=5, ge=0)
    notes: list[str] = Field(default_factory=list)
    cases: list[Case] = Field(min_length=1)


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------


@dataclass
class Tally:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    disputed_misses: int = 0
    ran: bool = False
    error: Optional[str] = None

    @property
    def measured(self) -> bool:
        return self.ran and self.error is None

    @property
    def precision(self) -> Optional[float]:
        denominator = self.true_positives + self.false_positives
        return None if denominator == 0 else self.true_positives / denominator

    @property
    def recall(self) -> Optional[float]:
        denominator = self.true_positives + self.false_negatives
        return None if denominator == 0 else self.true_positives / denominator


@dataclass
class CaseResult:
    case: Case
    verdict: str = "-"
    record: Optional[VerdictRecord] = None
    outcome: Literal["tp", "fp", "fn", "clean", "degraded", "skipped"] = "skipped"
    note: str = ""

    @property
    def findings(self) -> list[dict]:
        if self.record is None:
            return []
        return [f.model_dump() for f in self.record.findings]


# --------------------------------------------------------------------------
# Corpus mechanics
# --------------------------------------------------------------------------


def load_corpus(path: Path) -> Corpus:
    return Corpus.model_validate_json(path.read_text(encoding="utf-8"))


def case_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*") if p.is_file())


def build_diff(base_dir: Path, case_dir: Path, display_prefix: str) -> str:
    """Unified diff from base to one case.

    Nothing in backend/app/ parses diff headers -- the string goes straight to the
    model -- so generating them here is safe, and generating rather than
    hand-writing them means a diff can never drift from its fixture.
    """
    chunks: list[str] = []
    names = {p.relative_to(base_dir).as_posix() for p in case_files(base_dir)}
    names |= {p.relative_to(case_dir).as_posix() for p in case_files(case_dir)}

    for name in sorted(names):
        base_file = base_dir / name
        case_file = case_dir / name
        before = (
            base_file.read_text(encoding="utf-8").splitlines(keepends=True)
            if base_file.is_file()
            else []
        )
        after = (
            case_file.read_text(encoding="utf-8").splitlines(keepends=True)
            if case_file.is_file()
            else []
        )
        if before == after:
            continue
        path = f"{display_prefix}/{name}"
        chunks.extend(
            difflib.unified_diff(
                before, after, fromfile=f"a/{path}", tofile=f"b/{path}", n=3
            )
        )
    return "".join(chunks)


def run_case(corpus: Corpus, case: Case, workdir: Path) -> CaseResult:
    """Diff the case, hand it to the real engine, read the verdict back off disk."""
    # Cases are siblings of the base, not children of it: base is "demo_target/base"
    # and each fixture is "demo_target/<case id>".
    base_dir = REPO_ROOT / corpus.base
    case_dir = base_dir.parent / case.id
    if not case_dir.is_dir():
        raise FileNotFoundError(f"no fixture directory for {case.id}: {case_dir}")

    diff = build_diff(base_dir, case_dir, f"{base_dir.parent.name}/{case.id}")
    if not diff.strip():
        return CaseResult(
            case=case, note="fixture is byte-identical to base, so there is no change to review"
        )

    runs_dir = workdir / case.id / "runs"
    diff_file = workdir / case.id / "change.diff"
    runs_dir.mkdir(parents=True, exist_ok=True)
    diff_file.write_text(diff, encoding="utf-8")

    # backend/ must be the cwd: app/main.py imports `from app.checkers import ...`,
    # so backend/ has to be on sys.path. The workspace is therefore backend-relative.
    #
    # PYTHONIOENCODING is set because main.py's progress logger prints U+2192.
    # Under a pipe on Windows Python falls back to cp1252 and _log raises
    # UnicodeEncodeError, killing the run before any record is written. In an
    # interactive terminal stdout is utf-8 and this never fires, which is why it
    # survived being tested by hand. See the note in bench/README.md.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    completed = subprocess.run(
        [
            sys.executable,
            "app/main.py",
            "--diff",
            str(diff_file),
            "--workspace",
            os.path.relpath(case_dir, ENGINE_DIR),
            "--pr",
            case.id,
            "--runs-dir",
            str(runs_dir),
        ],
        cwd=ENGINE_DIR,
        env=env,
        capture_output=True,
        text=True,
        # The child is told to write utf-8 above, so the parent must read utf-8 too.
        # text=True alone decodes with the locale encoding, which is cp1252 on
        # Windows: the reader thread dies on the first non-cp1252 byte and stdout/
        # stderr come back short — so the Traceback check below can miss a real
        # crash and score it as a verdict.
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    # Exit 1 is BLOCK, but an unhandled traceback also exits 1. Distinguishing
    # them by return code alone would score a crashed run as a verdict.
    if "Traceback (most recent call last)" in completed.stderr:
        raise RuntimeError(f"engine crashed: {completed.stderr.strip()[:400]}")
    if completed.returncode not in (0, 1):
        raise RuntimeError(
            f"engine exited {completed.returncode}: "
            f"{(completed.stderr.strip() or completed.stdout.strip())[:400]}"
        )

    return CaseResult(case=case, record=compute_verdict(case.id, runs_dir))


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def matches(case: Case, finding: dict, tolerance: int) -> bool:
    if case.expected_checker is None or finding["checker"] != case.expected_checker:
        return False
    if case.expected_file and finding["file"] != case.expected_file:
        return False
    if case.expected_line is None:
        return True
    return abs(int(finding["line"]) - case.expected_line) <= tolerance


def _count_fp(tallies: dict[str, Tally], finding: dict) -> None:
    """Charge a finding to its own checker as a false positive.

    Deliberately not called before the match test: a finding that satisfies the
    case is a true positive, and counting it here as well scored a checker that
    found the planted defect exactly right at precision 0.50. The bug was
    invisible while every case was degraded and no case ever reached this code.
    """
    tallies.setdefault(finding["checker"], Tally()).false_positives += 1


def mark_checkers(tallies: dict[str, Tally], results: list[CaseResult]) -> None:
    """A checker is MEASURED only if it completed OK on every case.

    One degraded run disqualifies the rate. A checker that died on case 3 of 10
    has not been measured on the other 9 either -- it has been measured on none
    of them, because we do not know which cases it would have fired on.
    """
    for result in results:
        if result.record is None:
            continue
        for checker_result in result.record.results:
            tally = tallies.setdefault(checker_result.checker, Tally())
            tally.ran = True
            if checker_result.status is not CheckerStatus.OK and tally.error is None:
                tally.error = checker_result.error or checker_result.status.value


def score(corpus: Corpus, results: list[CaseResult], tallies: dict[str, Tally]) -> None:
    for result in results:
        if result.record is None:
            continue
        case = result.case
        result.verdict = result.record.verdict.value

        # A degraded run has not cleared the case, so it cannot have missed it
        # either. Scoring "no findings" from a run where nothing completed as a
        # false negative is the same fail-open one level up from the per-checker
        # rule, and it is worse: it looks like a measurement.
        #
        # Only the checkers that can change THIS case's score disqualify it. A
        # matching finding from the expected checker is a true positive whoever
        # else was down, so three unrelated LLM checkers being unavailable must not
        # cost the one checker that can run today its only measurable result. A
        # case that expects clean is the opposite: any checker at all could have
        # raised the false positive being ruled out, so one degraded checker is
        # enough to disqualify it. Per-checker MEASURED status is decided
        # separately, in mark_checkers, and still refuses a rate for any checker
        # that errored on any case.
        blocking = (
            list(result.record.degraded_checkers)
            if case.expects_clean
            else [n for n in result.record.degraded_checkers if n == case.expected_checker]
        )
        if blocking:
            result.outcome = "degraded"
            missing = ", ".join(blocking) or "unknown"
            result.note = f"run degraded ({missing}) - not scored"
            continue

        if case.expects_clean:
            for finding in result.findings:
                _count_fp(tallies, finding)
            result.outcome = "fp" if result.findings else "clean"
            result.note = (
                f"false positive - {case.no_checker_reason or 'no checker owns this'}"
                if result.findings
                else "clean, as expected"
            )
            continue

        tally = tallies.setdefault(case.expected_checker, Tally())
        matched = False
        for finding in result.findings:
            if not matched and matches(case, finding, corpus.line_tolerance):
                matched = True
            else:
                _count_fp(tallies, finding)
        if matched:
            tally.true_positives += 1
            result.outcome = "tp"
        else:
            tally.false_negatives += 1
            result.outcome = "fn"
            if case.disputed:
                tally.disputed_misses += 1
                result.note = "miss on a case the corpus marks as disputed"


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def rate(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def report(results: list[CaseResult], tallies: dict[str, Tally], dry_run: bool) -> None:
    print()
    print("=" * 78)
    print(f"TrustGate benchmark — {len(results)} cases")
    print("=" * 78)

    if dry_run:
        print("\n--dry-run: nothing was executed. No API key and no gitleaks needed.")

    print(f"\n{'case':<30} {'verdict':<8} {'expected':<11} {'result':<8} title")
    print("-" * 78)
    for result in results:
        case = result.case
        print(
            f"{case.id:<30} {result.verdict:<8} "
            f"{(case.expected_checker or 'none'):<11} {result.outcome:<8} {case.title[:30]}"
        )
        if result.note:
            print(f"{'':<62}{result.note[:60]}")

    print("\nper-checker")
    print("-" * 78)
    for checker in CHECKERS:
        tally = tallies.get(checker)
        if tally is None or not tally.ran:
            print(f"  {checker:<11} SKIPPED    did not run — no rate reported")
            continue
        if tally.error is not None:
            print(f"  {checker:<11} SKIPPED    {tally.error[:40]} — no rate reported")
            continue
        print(
            f"  {checker:<11} MEASURED   TP {tally.true_positives}  "
            f"FP {tally.false_positives}  FN {tally.false_negatives}  "
            f"precision {rate(tally.precision)}  recall {rate(tally.recall)}"
        )
        if tally.disputed_misses:
            print(
                f"{'':<15}{tally.disputed_misses} miss(es) were on cases the corpus "
                f"marks disputed"
            )

    ran = [t for t in tallies.values() if t.ran]
    measured = [t for t in ran if t.measured]
    print()
    if not ran:
        print("OVERALL: INCOMPLETE - no checker completed. Nothing was measured.")
    elif len(measured) < len(ran):
        print(
            f"OVERALL: INCOMPLETE - {len(ran) - len(measured)} of {len(ran)} checkers "
            f"did not complete.\n"
            "         No precision or recall is claimed for them. This is the same\n"
            "         fail-closed contract the engine applies to a degraded run: a\n"
            "         checker that died before it wrote a record has cleared nothing."
        )
    else:
        print(
            f"OVERALL: all {len(ran)} checkers completed. The figures above are measured,\n"
            f"         not estimated."
        )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_benchmark.py",
        description="Measure TrustGate against the labelled corpus.",
    )
    parser.add_argument("--cases", type=Path, default=BENCH_DIR / "cases.json")
    parser.add_argument("--only", action="append", default=[], help="run one case id; repeatable")
    parser.add_argument("--dry-run", action="store_true", help="print the case table and exit 0")
    return parser.parse_args(argv)


def select_cases(corpus: Corpus, only: Sequence[str]) -> list[Case]:
    if not only:
        return list(corpus.cases)
    cases = [c for c in corpus.cases if c.id in set(only)]
    missing = set(only) - {c.id for c in cases}
    if missing:
        raise SystemExit(f"unknown case id(s): {', '.join(sorted(missing))}")
    return cases


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        corpus = load_corpus(args.cases)
        cases = select_cases(corpus, args.only)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"cases.json is not valid: {exc}", file=sys.stderr)
        return 2

    workdir = Path(tempfile.mkdtemp(prefix="trustgate-bench-"))
    tallies: dict[str, Tally] = defaultdict(Tally)
    results: list[CaseResult] = []

    try:
        for case in cases:
            if not case.is_planted:
                results.append(
                    CaseResult(
                        case=case,
                        note=case.caveat or "defect not planted — case skipped",
                    )
                )
                continue
            if args.dry_run:
                results.append(CaseResult(case=case, note="dry run — not executed"))
                continue
            try:
                results.append(run_case(corpus, case, workdir))
            except Exception as exc:
                print(f"  {case.id}: {exc}", file=sys.stderr)
                results.append(CaseResult(case=case, note=f"runner error: {exc}"[:60]))

        mark_checkers(tallies, results)
        score(corpus, results, tallies)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    report(results, tallies, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
