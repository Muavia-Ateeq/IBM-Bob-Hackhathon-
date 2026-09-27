from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import Protocol

from app.schemas import CheckerResult, CheckerStatus, CheckerTier, Finding


class Checker(Protocol):
    name: str
    tier: CheckerTier

    async def run(self, diff: str, workspace: str) -> list[Finding]: ...


async def execute(checker: Checker, diff: str, workspace: str, timeout_s: int) -> CheckerResult:
    started = time.perf_counter()
    try:
        findings = await asyncio.wait_for(checker.run(diff, workspace), timeout=timeout_s)
    except asyncio.TimeoutError:
        return CheckerResult(
            checker=checker.name,
            tier=checker.tier,
            status=CheckerStatus.TIMEOUT,
            duration_ms=int((time.perf_counter() - started) * 1000),
            error=f"exceeded {timeout_s}s",
        )
    except Exception as exc:
        return CheckerResult(
            checker=checker.name,
            tier=checker.tier,
            status=CheckerStatus.ERROR,
            duration_ms=int((time.perf_counter() - started) * 1000),
            error=f"{type(exc).__name__}: {exc}",
        )
    return CheckerResult(
        checker=checker.name,
        tier=checker.tier,
        status=CheckerStatus.OK,
        findings=list(findings),
        duration_ms=int((time.perf_counter() - started) * 1000),
    )


async def _notified(
    coro: Awaitable[CheckerResult], on_result: Callable[[CheckerResult], None] | None
) -> CheckerResult:
    result = await coro
    if on_result is not None:
        on_result(result)
    return result


async def run_all(
    factory: Callable[[], Sequence[Checker]],
    diff: str,
    workspace: str,
    timeout_s: int,
    on_result: Callable[[CheckerResult], None] | None = None,
) -> list[CheckerResult]:
    """Run every checker concurrently and return their results in roster order.

    ``on_result`` fires the moment each checker settles rather than when the gather
    completes, which is the only way to report true parallel progress: a run that takes as
    long as its slowest checker would otherwise print nothing until the end. Results are
    still returned in roster order regardless of completion order.
    """
    checkers = factory()
    return list(
        await asyncio.gather(
            *(
                _notified(execute(checker, diff, workspace, timeout_s), on_result)
                for checker in checkers
            )
        )
    )
