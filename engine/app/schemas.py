from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Verdict(StrEnum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class CheckerStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class CheckerTier(StrEnum):
    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"


NonEmpty = Annotated[str, Field(min_length=1)]


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checker: NonEmpty
    severity: Severity
    title: NonEmpty
    detail: NonEmpty
    file: NonEmpty
    line: int = Field(ge=1)
    evidence: NonEmpty
    cwe: str | None = None
    remediation: str | None = None

    @field_validator("file")
    @classmethod
    def reject_path_traversal(cls, value: str) -> str:
        if ".." in value.split("/") or ".." in value.split("\\"):
            raise ValueError("file path must not contain '..'")
        return value


class CheckerResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checker: NonEmpty
    tier: CheckerTier
    status: CheckerStatus
    findings: list[Finding] = Field(default_factory=list)
    duration_ms: int = Field(ge=0)
    error: str | None = None

    @field_validator("findings")
    @classmethod
    def no_findings_when_not_ok(cls, value: list[Finding], info) -> list[Finding]:
        status = info.data.get("status")
        if status is not None and status is not CheckerStatus.OK and value:
            raise ValueError("a checker that did not complete ok must not report findings")
        return value

    @property
    def completed(self) -> bool:
        return self.status is CheckerStatus.OK


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: NonEmpty
    base_sha: str = Field(min_length=7)
    head_sha: str = Field(min_length=7)
    diff: str = ""
    workspace: str = "."


class VerdictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    reason: NonEmpty
    degraded: bool
    degraded_checkers: list[str] = Field(default_factory=list)
    findings: list[Finding]
    results: list[CheckerResult]
    input_hash: str
    duration_ms: int = Field(ge=0)
    cost_usd: float | None = None
