from __future__ import annotations

from app.checkers.semantic import SemanticChecker
from app.llm.client import Provider

FOCUS = """
Injection. Look for: SQL, NoSQL, OS command and template injection; cross-site scripting where
escaping is missing or applied in the wrong order; server-side request forgery; path traversal;
unsafe deserialization of untrusted data; and header or log injection. Judge whether the
framework in use actually neutralises the sink. A parameterised query is not SQL injection.
""".strip()


def build(provider: Provider, max_diff_bytes: int) -> SemanticChecker:
    return SemanticChecker("injection", FOCUS, provider, max_diff_bytes)
