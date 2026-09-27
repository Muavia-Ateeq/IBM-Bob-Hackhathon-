"""
Security Reviewer checker — M. Muavia
Implements the Checker protocol from backend/app/checkers/base.py

Prompt: docs/prompt_agent01_security_reviewer.md
"""
from __future__ import annotations
from app.schemas import CheckerTier, Finding


class SecurityReviewerChecker:
    name: str = "security_reviewer"
    tier: CheckerTier = CheckerTier.SEMANTIC

    async def run(self, diff: str, workspace: str) -> list[Finding]:
        raise NotImplementedError(
            "Wire Bob subagent call here. "
            "Prompt: docs/prompt_agent01_security_reviewer.md"
        )
