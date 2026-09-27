"""
Spec-Conformance checker — M. Muavia
Implements the Checker protocol from backend/app/checkers/base.py

Step A prompt: docs/prompt_agent02_step_A_spec_conformance.md
Step B prompt: docs/prompt_agent02_step_B_spec_conformance.md
"""
from __future__ import annotations
from app.schemas import CheckerTier, Finding


class SpecConformanceChecker:
    name: str = "spec_conformance"
    tier: CheckerTier = CheckerTier.SEMANTIC

    async def run(self, diff: str, workspace: str) -> list[Finding]:
        raise NotImplementedError(
            "Wire Step A + Step B Bob subagent calls here. "
            "Prompts: docs/prompt_agent02_step_A/B_spec_conformance.md"
        )
