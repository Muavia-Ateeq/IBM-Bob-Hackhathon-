from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import Protocol

from app.schemas import CheckerResult, CheckerStatus, CheckerTier, Finding


class CheckerError(RuntimeError):
    pass


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


async def run_all(
    factory: Callable[[], Sequence[Checker]], diff: str, workspace: str, timeout_s: int
) -> list[CheckerResult]:
    checkers = factory()
    return list(
        await asyncio.gather(
            *(execute(checker, diff, workspace, timeout_s) for checker in checkers)
        )
    )


FindingFactory = Callable[..., list[Finding]]
