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

DEFAULT_RUNS_DIR = Path("runs")


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


def load_results(runs_dir: Path, pr: str) -> tuple[list[CheckerResult], list[str], str]:
    if not runs_dir.is_dir():
        raise FileNotFoundError(f"no such runs directory: {runs_dir}")

    unreadable: list[str] = []
    by_run: dict[str, list[tuple[Path, bytes, RunRecord]]] = {}

    for path in sorted(runs_dir.glob("*.json")):
        raw = path.read_bytes()
        try:
            record = RunRecord.model_validate_json(raw)
        except ValidationError:
            unreadable.append(path.name)
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
    for _path, raw, record in sorted(by_run.get(max(by_run, default=""), [])):
        digest.update(raw)
        results.append(record.result)

    return results, unreadable, digest.hexdigest()


def compute_verdict(pr: str, runs_dir: Path | str = DEFAULT_RUNS_DIR) -> VerdictRecord:
    results, unreadable, input_hash = load_results(Path(runs_dir), pr)
    verdict, reason, degraded_checkers = adjudicate(results)

    if unreadable:
        reason = f"{reason}; {len(unreadable)} unreadable run file(s): {', '.join(unreadable)}"

    return VerdictRecord(
        verdict=verdict,
        reason=reason,
        degraded=bool(degraded_checkers) or not results,
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
