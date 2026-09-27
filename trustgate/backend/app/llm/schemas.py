from __future__ import annotations

from typing import Any

FINDING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "severity",
                    "title",
                    "detail",
                    "file",
                    "line",
                    "evidence",
                    "cwe",
                    "remediation",
                ],
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "evidence": {"type": "string"},
                    "cwe": {"type": ["string", "null"]},
                    "remediation": {"type": ["string", "null"]},
                },
            },
        }
    },
}
