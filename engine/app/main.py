from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adjudicator import adjudicate
from app.checkers import authz, business, injection
from app.checkers.base import Checker, run_all
from app.config import Settings, load_settings
from app.llm.client import Provider, UnavailableProvider, build_provider
from app.schemas import CheckerResult, CheckerStatus, Verdict

CHECKER_MODULES = (authz, injection, business)


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
    return "\n".join(lines)


async def analyze(diff: str, settings: Settings, provider: Provider) -> int:
    if not diff.strip():
        print("The diff is empty. There is nothing to review.", file=sys.stderr)
        return 2

    if isinstance(provider, UnavailableProvider):
        print("GROQ_API_KEY is not set. Every semantic checker will degrade to REVIEW.", file=sys.stderr)

    roster = build_roster(provider, settings.max_diff_bytes)
    started = time.perf_counter()
    results = await run_all(lambda: roster, diff, ".", settings.checker_timeout_s)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    verdict, reason, _ = adjudicate(results)
    print(render(results, verdict, reason, elapsed_ms))
    return 0 if verdict is not Verdict.BLOCK else 1


def build_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    application = FastAPI(title="TrustGate", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    return application


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app", description="TrustGate verdict engine")
    parser.add_argument("--diff", type=Path, help="path to a unified diff to review")
    parser.add_argument("--serve", action="store_true", help="run the HTTP server instead")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.serve:
        import uvicorn

        uvicorn.run(build_app(), host="127.0.0.1", port=args.port)
        return 0

    if args.diff is None:
        parser.error("one of --diff or --serve is required")

    settings = load_settings()
    provider = build_provider(settings)
    try:
        diff = read_diff(args.diff)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return asyncio.run(analyze(diff, settings, provider))


if __name__ == "__main__":
    raise SystemExit(main())
