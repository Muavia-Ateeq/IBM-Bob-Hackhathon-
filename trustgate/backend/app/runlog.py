from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.adjudicator import adjudicate
from app.schemas import CheckerResult, RunRecord, Verdict, VerdictRecord

# Anchored to this file, not the working directory. `Path("runs")` resolved against the CWD,
# which made the records invisible to anything started from a different directory than the
# one that wrote them -- the served app and the integration check then read two different
# folders and could never agree. CI passes `--runs-dir runs` explicitly after `cd
# trustgate/backend`, so it lands on this same path.
DEFAULT_RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"


def write_run_records(
    results: Sequence[CheckerResult],
    pr: str,
    run_id: str,
    runs_dir: Path = DEFAULT_RUNS_DIR,
) -> list[Path]:
    runs_dir.mkdir(parents=True, exist_ok=True)
    written_at = datetime.now(timezone.utc).isoformat()
    paths = []
    for result in results:
        record = RunRecord(run_id=run_id, pr=pr, written_at=written_at, result=result)
        path = runs_dir / f"{run_id}_{result.checker}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        paths.append(path)
    return paths


def load_all_records(runs_dir: Path) -> tuple[list[RunRecord], list[str]]:
    """Every valid record in ``runs_dir``, plus the names of the ones that would not parse.

    Unreadable files are skipped rather than raised, mirroring `load_results`: one corrupt
    file on disk must not take down the whole listing. The unreadable names are returned so
    a caller can report them — a silently dropped record is a silently dropped finding.
    """
    if not runs_dir.is_dir():
        return [], []

    records: list[RunRecord] = []
    unreadable: list[str] = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            records.append(RunRecord.model_validate_json(path.read_bytes()))
        except ValidationError:
            unreadable.append(path.name)
    return records, unreadable


def load_results(runs_dir: Path, pr: str) -> tuple[list[CheckerResult], int, str]:
    """Results for one PR, the number of unreadable files in the directory, and a digest.

    A file that fails to parse has no readable `pr`, so it cannot be attributed to this PR or
    to any other. Only the count is returned, never the names: this function feeds the verdict
    reason, which the gate writes into the PR job summary, and `runs/*.json` filenames embed
    another PR's run_id and checker name. Counting is the honest answer — we can say how many
    files we could not read, and cannot say whose they were.
    """
    if not runs_dir.is_dir():
        raise FileNotFoundError(f"no such runs directory: {runs_dir}")

    unreadable = 0
    by_run: dict[str, list[tuple[Path, bytes, RunRecord]]] = {}

    for path in sorted(runs_dir.glob("*.json")):
        raw = path.read_bytes()
        try:
            record = RunRecord.model_validate_json(raw)
        except ValidationError:
            unreadable += 1
            continue
        if record.pr != pr:
            continue
        by_run.setdefault(record.run_id, []).append((path, raw, record))

    # Only the newest run for this PR is adjudicated. Aggregating every run ever recorded
    # meant a CRITICAL finding stayed in the verdict forever: the gate re-runs on
    # `synchronize`, so a fixed vulnerability could never be cleared. run_id embeds
    # `run_%Y%m%d_%H%M%S`, so the max is the newest run lexicographically.
    results: list[CheckerResult] = []
    digest = hashlib.sha256()
    for _, raw, record in sorted(by_run.get(max(by_run, default=""), [])):
        digest.update(raw)
        results.append(record.result)

    return results, unreadable, digest.hexdigest()


def compute_verdict(pr: str, runs_dir: Path | str = DEFAULT_RUNS_DIR) -> VerdictRecord:
    results, unreadable, input_hash = load_results(Path(runs_dir), pr)
    verdict, reason, degraded_checkers = adjudicate(results)

    if unreadable:
        reason = f"{reason}; {unreadable} unattributable unreadable run file(s)"
        if verdict is Verdict.PASS:
            # Fail-closed. A file we cannot parse is a checker whose result is unaccounted
            # for, which is the same condition adjudicate() refuses to PASS on. This is not
            # hypothetical: `write_run_records` writes one file per checker with no atomic
            # rename, so a killed process leaves a truncated record, and the readable ones
            # still look perfectly clean. Reporting the count in the reason is not enough --
            # the gate's final step greps for BLOCK, so a PASS merges the PR. The file stays
            # unnamed above: a corrupt record cannot say which PR it was, and its filename
            # would republish another PR's run_id and checker name into the job summary.
            verdict = Verdict.REVIEW
            reason = f"a checker result could not be read, so the run is not verified; {reason}"

    return VerdictRecord(
        verdict=verdict,
        reason=reason,
        degraded=bool(degraded_checkers) or bool(unreadable) or not results,
        degraded_checkers=degraded_checkers,
        findings=[finding for result in results for finding in result.findings],
        results=results,
        input_hash=input_hash,
        duration_ms=max((result.duration_ms for result in results), default=0),
        cost_usd=None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.runlog", description="Verdict from stored runs")
    parser.add_argument("--pr", required=True, help="PR identifier to match, e.g. repo#42")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    args = parser.parse_args(argv)

    try:
        record = compute_verdict(args.pr, args.runs_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(record.model_dump_json(indent=2))
    return 0 if record.verdict is not Verdict.BLOCK else 1


if __name__ == "__main__":
    raise SystemExit(main())
