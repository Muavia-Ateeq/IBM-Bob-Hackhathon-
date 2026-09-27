from __future__ import annotations

import argparse
import asyncio
import sys
import time
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.adjudicator import SEVERITY_ORDER, adjudicate
from app.checkers import (
    authz,
    business,
    injection,
    prompt_injection,
    secrets,
    security_reviewer,
    spec_conformance,
)
from app.checkers.base import Checker, run_all
from app.config import Settings, __version__, load_settings
from app.llm.client import Provider, UnavailableProvider, build_provider
from app.runlog import DEFAULT_RUNS_DIR, compute_verdict, load_all_records, write_run_records
from app.sarif import write_sarif
from app.schemas import CheckerResult, CheckerStatus, Verdict

CHECKER_MODULES = (
    secrets,
    authz,
    injection,
    prompt_injection,
    business,
    security_reviewer,
    spec_conformance,
)


def _log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def _announce(result: CheckerResult) -> None:
    mark = "✅" if result.completed else "⚠️"
    plural = "finding" if len(result.findings) == 1 else "findings"
    _log(
        f"{mark} {result.checker} {result.status.value} in "
        f"{result.duration_ms / 1000:.1f}s — {len(result.findings)} {plural}"
    )


def build_roster(provider: Provider, max_diff_bytes: int) -> list[Checker]:
    return [module.build(provider, max_diff_bytes) for module in CHECKER_MODULES]


def read_diff(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"no such diff file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def render(results: list[CheckerResult], verdict: Verdict, reason: str, elapsed_ms: int) -> str:
    lines = [
        "",
        f"VERDICT  {verdict.value}",
        f"REASON   {reason}",
        f"WALL     {elapsed_ms} ms",
        "",
        "CHECKERS",
    ]
    for result in results:
        mark = "ok  " if result.status is CheckerStatus.OK else "DEGRADED"
        lines.append(f"  [{mark}] {result.checker:<10} {result.status.value:<8} {result.duration_ms:>6} ms")
        if result.error:
            lines.append(f"             {result.error}")
    findings = [finding for result in results for finding in result.findings]
    lines.append("")
    lines.append(f"FINDINGS {len(findings)}")
    for finding in findings:
        lines.append(f"  {finding.severity.value.upper():<8} {finding.file}:{finding.line}  {finding.title}")
        lines.append(f"           {finding.evidence}")
    degraded = sorted({r.checker for r in results if r.status is not CheckerStatus.OK})
    if degraded:
        lines.append("")
        lines.append(f"DEGRADED CHECKERS: {', '.join(degraded)}")
        lines.append("A degraded run can never return PASS. This is the designed behaviour, not a bug.")

    counts = Counter(finding.severity for finding in findings)
    breakdown = " · ".join(
        f"{counts[severity]} {severity.value}" for severity in SEVERITY_ORDER if counts[severity]
    )
    lines.append("")
    lines.append(
        f"SUMMARY  {len(findings)} finding(s)"
        + (f" — {breakdown}" if breakdown else "")
        + f" · verdict {verdict.value}"
    )
    return "\n".join(lines)


async def analyze(
    diff: str,
    settings: Settings,
    provider: Provider,
    pr: str,
    runs_dir: Path,
    sarif_path: Path | None = None,
    workspace: str = ".",
) -> int:
    if not diff.strip():
        print("The diff is empty. There is nothing to review.", file=sys.stderr)
        return 2

    if isinstance(provider, UnavailableProvider):
        print(
            f"{provider.reason}. Every semantic checker will degrade to REVIEW.",
            file=sys.stderr,
        )

    roster = build_roster(provider, settings.max_diff_bytes)
    _log(f"Starting {len(roster)} checkers in parallel for PR: {pr}")
    for checker in roster:
        _log(f"→ {checker.name} starting...")
    started = time.perf_counter()
    results = await run_all(
        lambda: roster, diff, workspace, settings.checker_timeout_s, on_result=_announce
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    verdict, reason, _ = adjudicate(results)
    print(render(results, verdict, reason, elapsed_ms))
    run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}"
    written = write_run_records(results, pr, run_id, runs_dir)
    print(f"\nRECORDS  {len(written)} written to {runs_dir}")
    if sarif_path is not None:
        # Read the verdict back off disk rather than rebuilding it from `results`, so the SARIF
        # and the run log cannot disagree about what happened.
        record = compute_verdict(pr, runs_dir)
        written_sarif = write_sarif(record, pr, sarif_path)
        print(f"SARIF    {written_sarif} ({len(record.findings)} result(s))")
    return 0 if verdict is not Verdict.BLOCK else 1


def build_app(runs_dir: Path = DEFAULT_RUNS_DIR):
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    runs_dir.mkdir(parents=True, exist_ok=True)

    application = FastAPI(title="TrustGate", version=__version__)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    # Every run record on disk, newest last. `def`, not `async def`, for the same reason as
    # `pr_verdict` below: the glob and the file reads run in the threadpool.
    #
    # These records carry `Finding.evidence` verbatim, and for the secrets checker that is a
    # matched credential fragment — which is why `runs/` is gitignored. This endpoint is
    # unauthenticated and the app allows every origin, so a publicly deployed instance
    # republishes those fragments. Demo-only until it is gated; see SYSTEM_LEDGER.md.
    @application.get("/api/runs")
    def runs() -> dict:
        records, unreadable = load_all_records(runs_dir)
        return {
            "count": len(records),
            "unreadable": unreadable,
            "runs": [record.model_dump(mode="json") for record in records],
        }

    # Declared `def`, not `async def`, so Starlette runs the glob and the file reads in its
    # threadpool. An `async def` here would block the event loop on every dashboard poll.
    #
    # `pr` arrives as a path segment, so an identifier containing `/` or `#` must arrive
    # percent-encoded. The gate writes a bare pull-request number, which needs neither.
    #
    # A pull request with no record on disk has not been scanned, and `adjudicate` turns an
    # empty result set into REVIEW/"no checkers ran" -- a 200 carrying a security verdict for
    # a run that never happened, byte-identical to a real clean scan. The HTTP API cannot
    # produce a verdict, only report one, so "nothing recorded" stays a 404. See
    # SYSTEM_LEDGER.md on why the deployed instance reads an empty directory by design.
    @application.get("/api/pr/{pr}/verdict")
    def pr_verdict(pr: str) -> dict:
        try:
            record = compute_verdict(pr, runs_dir)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not record.results:
            raise HTTPException(
                status_code=404,
                detail=f"no run records for pr {pr!r} in {runs_dir}",
            )
        return {"pr": pr, **record.model_dump(mode="json")}

    return application


# Module-level ASGI app so `uvicorn app.main:app` works from the repo root and from
# Render. build_app() does one I/O call -- it creates the runs directory -- and that is
# the same directory write_run_records already performs, so importing this module cannot
# fail on a machine where the served app would not have started anyway. The `--factory`
# form stays supported.
app = build_app()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app", description="TrustGate verdict engine")
    parser.add_argument("--diff", type=Path, help="path to a unified diff to review")
    parser.add_argument("--pr", default="local", help="PR identifier stored with the run records")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--sarif", type=Path, help="also write a SARIF 2.1.0 report to this path")
    parser.add_argument(
        "--workspace",
        default=".",
        help="root the deterministic scanners scan; the checked-out PR branch, not the CWD",
    )
    parser.add_argument("--serve", action="store_true", help="run the HTTP server instead")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the roster that would run and exit; runs no checker and needs no credentials",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address; 0.0.0.0 in a container")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.serve:
        import uvicorn

        uvicorn.run(build_app(args.runs_dir), host=args.host, port=args.port)
        return 0

    settings = load_settings()

    if args.dry_run:
        roster = build_roster(build_provider(settings), settings.max_diff_bytes)
        print(f"DRY RUN — {len(roster)} checkers would run. Nothing was executed.\n")
        for checker in roster:
            print(f"  {checker.name:<12} {checker.tier.value}")
        return 0

    if args.diff is None:
        parser.error("one of --diff or --serve is required")

    provider = build_provider(settings)
    try:
        diff = read_diff(args.diff)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return asyncio.run(
        analyze(diff, settings, provider, args.pr, args.runs_dir, args.sarif, args.workspace)
    )


if __name__ == "__main__":
    raise SystemExit(main())
