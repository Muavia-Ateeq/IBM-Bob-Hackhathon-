"""Security Reviewer — implemented by M. Muavia (IBM Bob subagent prompts).

Prompt: docs/muavia_prompts/prompt_agent01_security_reviewer.md
"""

from __future__ import annotations

from app.checkers.semantic import SemanticChecker
from app.llm.client import Provider

FOCUS = """
Security review. Look for:
1. HARDCODED SECRETS: API keys, passwords, tokens, or credentials written directly in source
   code instead of loaded from environment variables or a secrets manager.
2. SQL INJECTION: SQL queries built using string concatenation or f-strings with variables
   that come from user input, instead of parameterized queries.
3. MISSING AUTH: An endpoint that performs sensitive actions (admin actions, data modification,
   access to another user's data) with no visible authentication or authorization check.
4. UNSAFE DESERIALIZATION: Use of pickle.loads, yaml.load (without SafeLoader), eval, or exec
   on data that originates from a request or external input.
5. DEBUG MODE IN PRODUCTION: Configuration that leaves debug mode, verbose error pages, or
   development flags enabled in a production config file.

Only report issues that fall into one of these five categories. Do not report style,
naming, or architecture opinions.
""".strip()


def build(provider: Provider, max_diff_bytes: int) -> SemanticChecker:
    return SemanticChecker("security_reviewer", FOCUS, provider, max_diff_bytes)
