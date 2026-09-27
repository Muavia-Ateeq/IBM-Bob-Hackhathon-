from __future__ import annotations

from app.checkers.semantic import SemanticChecker
from app.llm.client import Provider
from app.schemas import CheckerTier

FOCUS = """
Broken access control. Look for: missing or incorrect authorization checks, IDOR where a
resource is addressed by an id taken straight from the request, privilege escalation through
role or scope handling, missing tenant isolation in multi-tenant code, authentication flows
that can be bypassed, and endpoints that trust a client-supplied identity field.
""".strip()


def build(provider: Provider, max_diff_bytes: int) -> SemanticChecker:
    checker = SemanticChecker("authz", FOCUS, provider, max_diff_bytes)
    checker.tier = CheckerTier.SEMANTIC
    return checker
