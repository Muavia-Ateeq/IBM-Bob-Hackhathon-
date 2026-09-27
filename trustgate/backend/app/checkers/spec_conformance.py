"""Spec Conformance — implemented by M. Muavia (IBM Bob subagent prompts).

Prompts: docs/muavia_prompts/prompt_agent02_step_A_spec_conformance.md and
prompt_agent02_step_B_spec_conformance.md
"""

from __future__ import annotations

from app.checkers.semantic import SemanticChecker
from app.llm.client import Provider

FOCUS = """
Spec conformance. You will review code against these product requirements:
- Passwords must be hashed with a strong algorithm (bcrypt or PBKDF2). MD5, SHA1, or any
  unsalted hash is a violation.
- All login and sensitive endpoints must implement rate limiting. An endpoint with no
  throttling or failed-attempt counting is a violation.
- API keys and secrets must not be hardcoded in source. They must be loaded from environment
  variables or a secrets manager.
- Debug mode must not be enabled in production configuration files.

For each violation, report the exact file and line where the requirement is broken, quote
the offending line verbatim as evidence, and state which requirement is violated.
Only report clear, unambiguous violations — not missing features or aspirational requirements.
""".strip()


def build(provider: Provider, max_diff_bytes: int) -> SemanticChecker:
    return SemanticChecker("spec_conformance", FOCUS, provider, max_diff_bytes)
