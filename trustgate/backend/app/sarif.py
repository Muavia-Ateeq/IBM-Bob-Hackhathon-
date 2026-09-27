from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.config import __version__
from app.schemas import Finding, Severity, VerdictRecord

SARIF_VERSION = "2.1.0"
# Verified to resolve (HTTP 200) on 2026-09-26. The GitHub docs example carries an
# oasis-tcs GitHub raw URL that 404s, so it is not the one to copy.
SARIF_SCHEMA = "https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json"
TOOL_NAME = "TrustGate"

_LEVEL = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "note",
}

# GitHub's published security-severity buckets: >9.0 critical, 7.0-8.9 high, 4.0-6.9 medium,
# 0.1-3.9 low. These are a mapping onto GitHub's scale, NOT a measurement of anything.
_SECURITY_SEVERITY = {
    Severity.CRITICAL: "9.5",
    Severity.HIGH: "8.0",
    Severity.MEDIUM: "5.0",
    Severity.LOW: "2.0",
    Severity.INFO: "0.5",
}

# The heterogeneous roster buys something concrete here: a deterministic scanner's findings
# have a known precision, a model's do not. GitHub accepts very-high|high|medium|low.
_PRECISION = {
    "secrets": "very-high",
    "authz": "medium",
    "injection": "medium",
    "prompt_injection": "medium",
    "business": "medium",
}

_DESCRIPTIONS = {
    "secrets": (
        "Hardcoded credentials and API keys",
        "A credential is committed in plaintext. Ground truth — a leaked key is a fact, not a judgement.",
    ),
    "authz": (
        "Missing or broken access control",
        "A handler acts on an attacker-controlled identifier without checking ownership. Model-derived.",
    ),
    "injection": (
        "Injection vulnerabilities",
        "Untrusted input reaches an interpreter — SQL, shell, a template, a deserializer. Model-derived.",
    ),
    "prompt_injection": (
        "Prompt injection and instruction-hierarchy violations",
        "Externally-sourced text is concatenated into a model instruction with no delimiter and no "
        "statement that it is untrusted data, so the data can issue instructions. Model-derived.",
    ),
    "business": (
        "Business-logic flaws",
        "The code is syntactically safe and semantically wrong: broken invariants, unsafe ordering, weak crypto.",
    ),
}

_GENERIC = ("Finding reported by {checker}", "No rule catalogue entry exists for this checker yet.")


def _rule_id(checker: str) -> str:
    return f"trustgate/{checker}"


def _rules(checkers: set[str]) -> list[dict[str, Any]]:
    catalogue = []
    for checker in sorted(checkers):
        short, full = _DESCRIPTIONS.get(checker, _GENERIC)
        catalogue.append(
            {
                "id": _rule_id(checker),
                "name": checker,
                "shortDescription": {"text": short.format(checker=checker)},
                "fullDescription": {"text": full},
                "help": {"text": f"TrustGate checker `{checker}`. Evidence and remediation are in the run log."},
                "properties": {
                    "tags": ["security", checker],
                    "precision": _PRECISION.get(checker, "medium"),
                },
            }
        )
    return catalogue


def _fingerprint(finding: Finding) -> dict[str, str]:
    """``primaryLocationLineHash`` is the only fingerprint GitHub reads.

    Keyed on the location and the quote, not on the title, so a reworded title does not
    orphan an existing alert and a genuinely new line does. SHA-256 for a stable, short key.
    """
    digest = hashlib.sha256(
        f"{finding.checker}\0{finding.file}\0{finding.line}\0{finding.evidence}".encode()
    ).hexdigest()
    return {"primaryLocationLineHash": digest}


def _result(finding: Finding) -> dict[str, Any]:
    return {
        "ruleId": _rule_id(finding.checker),
        "level": _LEVEL[finding.severity],
        "message": {"text": f"{finding.title} — {finding.detail}"},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.file, "uriBaseId": "%SRCROOT%"},
                    "region": {"startLine": finding.line},
                }
            }
        ],
        "partialFingerprints": _fingerprint(finding),
        "properties": {"security-severity": _SECURITY_SEVERITY[finding.severity]},
    }


def to_sarif(record: VerdictRecord, pr: str, tool_version: str = __version__) -> dict[str, Any]:
    findings = record.findings
    # rules[] describes what the tool can find, not what it found today, so the whole roster is
    # always emitted. It is also why the catalogue is stable run to run: a rule that appeared
    # and disappeared with the findings would make GitHub's dedup unreliable.
    checkers = set(_PRECISION) | {finding.checker for finding in findings}
    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "version": tool_version,
                        "rules": _rules(checkers),
                    }
                },
                "automationDetails": {"id": f"trustgate/{pr}/"},
                "results": [_result(finding) for finding in findings],
                "invocations": [{"executionSuccessful": not record.degraded}],
            }
        ],
    }


def write_sarif(record: VerdictRecord, pr: str, path: Path, tool_version: str = __version__) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_sarif(record, pr, tool_version), indent=2), encoding="utf-8")
    return path
