from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from app.config import load_settings
from app.llm.client import Provider
from app.schemas import CheckerTier, Finding, Severity


def _repo_relative(raw: str, workspace: str) -> str:
    """Normalise a scanner-supplied path to repo-relative, separator-agnostic.

    String handling rather than ``Path``: gitleaks reports POSIX separators, and on Windows
    ``Path("/srv/app").is_absolute()`` is False, so the obvious implementation silently skips
    relativisation on exactly the platform the team develops on.
    """
    path = raw.replace("\\", "/")
    root = workspace.replace("\\", "/").rstrip("/")
    if root and path.startswith(f"{root}/"):
        path = path[len(root) + 1 :]
    parts = [part for part in path.split("/") if part not in ("", ".", "..")]
    return "/".join(parts) or "unknown"


def _redact(evidence: str, secret: str) -> str:
    """Strip the credential out of the quoted match.

    gitleaks' ``Match`` is the matched text and it *contains* the secret, so quoting it
    verbatim would write the credential into ``runs/*.json`` and then into a SARIF upload.
    Redaction is not verbatim, and that trade is deliberate: a quote with the value masked
    still points at the line, and a leaked key in a committed artifact does not.
    """
    if secret and secret in evidence:
        evidence = evidence.replace(secret, "[redacted]")
    return evidence[:400] or "secret matched"


class GitleaksChecker:
    name = "secrets"
    tier = CheckerTier.DETERMINISTIC

    def __init__(self, binary: str) -> None:
        self.binary = binary

    async def run(self, diff: str, workspace: str) -> list[Finding]:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "gitleaks.json"
            proc = await asyncio.create_subprocess_exec(
                self.binary,
                "dir",
                "--report-format",
                "json",
                "--report-path",
                str(report),
                workspace,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                _, stderr = await proc.communicate()
            finally:
                if proc.returncode is None:
                    proc.kill()

            if proc.returncode == 126:
                raise RuntimeError(
                    f"{self.binary} rejected a flag: {stderr.decode(errors='replace').strip()}"
                )
            if not report.is_file():
                raise RuntimeError(
                    f"{self.binary} wrote no report (exit {proc.returncode}): "
                    f"{stderr.decode(errors='replace').strip()}"
                )

            payload = report.read_text(encoding="utf-8", errors="replace").strip()
            if not payload:
                return []
            entries = json.loads(payload)
            if not isinstance(entries, list):
                raise RuntimeError(f"unexpected gitleaks report shape: {type(entries).__name__}")

        return [self._to_finding(entry, workspace) for entry in entries]

    def _to_finding(self, entry: dict, workspace: str) -> Finding:
        rule = str(entry.get("RuleID", "gitleaks-rule"))
        return Finding(
            checker=self.name,
            severity=Severity.HIGH,
            title=f"Possible secret: {rule}",
            detail=str(entry.get("Description") or rule),
            file=_repo_relative(str(entry.get("File", "")), workspace),
            line=max(1, int(entry.get("StartLine") or 1)),
            evidence=_redact(str(entry.get("Match", "")), str(entry.get("Secret", ""))),
        )


def build(provider: Provider, max_diff_bytes: int) -> GitleaksChecker:
    return GitleaksChecker(load_settings().gitleaks_bin)
