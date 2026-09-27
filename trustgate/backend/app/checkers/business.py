from __future__ import annotations

from app.checkers.semantic import SemanticChecker
from app.llm.client import Provider
from app.schemas import CheckerTier

FOCUS = """
Business-logic and cryptographic defects. Look for: missing validation on values that drive
money, quota, or state transitions; race conditions and check-then-act sequences; incorrect
cryptographic choices such as ECB mode, a fixed IV, or a hand-rolled comparison; secrets
derived from a weak source; and integer or float handling that can be driven negative or
overflowed. Do not report anything the injection or access-control checkers already own.
""".strip()


def build(provider: Provider, max_diff_bytes: int) -> SemanticChecker:
    checker = SemanticChecker("business", FOCUS, provider, max_diff_bytes)
    checker.tier = CheckerTier.SEMANTIC
    return checker
