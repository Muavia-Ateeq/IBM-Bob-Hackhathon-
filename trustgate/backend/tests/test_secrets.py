from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.checkers.secrets import GitleaksChecker

ENTRY = {
    "RuleID": "generic-api-key",
    "Description": "Detected a Generic API Key",
    "StartLine": 42,
    "EndLine": 42,
    "StartColumn": 12,
    "EndColumn": 40,
    "Match": "api_key = \"sk-live-abc123\"",
    "Secret": "sk-live-abc123",
    "File": "config/settings.py",
    "SymlinkFile": "",
    "Commit": "0" * 40,
    "Entropy": 3.4,
    "Author": "Someone",
    "Email": "someone@example.com",
    "Date": "2026-09-25T00:00:00Z",
    "Message": "add settings",
    "Tags": ["key"],
    "Fingerprint": "config/settings.py:generic-api-key:42",
}


def test_report_entry_becomes_a_valid_finding() -> None:
    finding = GitleaksChecker("gitleaks")._to_finding(ENTRY, ".")
    assert finding.checker == "secrets"
    assert finding.file == "config/settings.py"
    assert finding.line == 42
    assert finding.severity.value == "high"
    assert "generic-api-key" in finding.title


def test_the_secret_itself_never_reaches_the_finding() -> None:
    finding = GitleaksChecker("gitleaks")._to_finding(ENTRY, ".")
    assert ENTRY["Secret"] not in finding.evidence
    assert ENTRY["Secret"] not in finding.model_dump_json()
    assert "[redacted]" in finding.evidence


def test_evidence_still_quotes_the_offending_line() -> None:
    finding = GitleaksChecker("gitleaks")._to_finding(ENTRY, ".")
    assert finding.evidence.startswith("api_key = ")


def test_absolute_posix_paths_are_relativised_to_the_workspace() -> None:
    entry = dict(ENTRY, File="/home/runner/work/repo/repo/app/main.py")
    finding = GitleaksChecker("gitleaks")._to_finding(entry, "/home/runner/work/repo/repo")
    assert finding.file == "app/main.py"


def test_windows_separators_are_normalised() -> None:
    entry = dict(ENTRY, File="app\\checkers\\secrets.py")
    finding = GitleaksChecker("gitleaks")._to_finding(entry, "C:\\checkout")
    assert finding.file == "app/checkers/secrets.py"


def test_traversal_is_stripped_from_the_reported_path() -> None:
    entry = dict(ENTRY, File="../../etc/passwd")
    finding = GitleaksChecker("gitleaks")._to_finding(entry, ".")
    assert ".." not in finding.file
    assert finding.file == "etc/passwd"
