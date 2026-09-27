"""
Security Reviewer checker — M. Muavia
Wired to SemanticChecker using the same pattern as the existing checkers.

Prompt focus: docs/muavia_prompts/prompt_agent01_security_reviewer.md
"""
from __future__ import annotations

from app.checkers.semantic import SemanticChecker
from app.llm.client import Provider
from app.schemas import CheckerTier

FOCUS = """
Dangerous runtime configuration left on in production. Look for exactly one class of issue:

DEBUG MODE IN PRODUCTION: A configuration file, settings module, or application factory that
sets a debug flag, verbose error mode, or development-only feature to True (or an equivalent
truthy value) in a context that will run in production — for example Flask DEBUG=True,
Django DEBUG=True, FastAPI reload=True, or a custom DEVELOPMENT=True flag in a config file
that is not gated behind an environment variable check.

Do NOT report any of the following — they are owned by other checkers in this pipeline:
- Hardcoded secrets, API keys, or credentials → owned by the secrets checker
- SQL injection or any other injection → owned by the injection checker
- Missing authentication or authorization → owned by the authz checker
- Unsafe deserialization (pickle, yaml.load) → owned by the injection checker
- Weak cryptography or hash functions → owned by the business checker

If the diff does not contain a production debug/verbose configuration being enabled,
return an empty findings array. Do not invent an issue.
""".strip()


def build(provider: Provider, max_diff_bytes: int) -> SemanticChecker:
    checker = SemanticChecker("security_reviewer", FOCUS, provider, max_diff_bytes)
    checker.tier = CheckerTier.SEMANTIC
    return checker
