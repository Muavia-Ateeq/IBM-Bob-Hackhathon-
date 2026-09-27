from __future__ import annotations

import os
from dataclasses import dataclass

__version__ = "0.1.0"


def _env_optional(name: str) -> str | None:
    raw = os.environ.get(name)
    return raw if raw and raw.strip() else None


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    model_id: str
    watsonx_api_key: str | None
    watsonx_url: str
    watsonx_model_id: str
    watsonx_project_id: str | None
    watsonx_space_id: str | None
    checker_timeout_s: int
    run_budget_s: int
    max_diff_bytes: int
    gitleaks_bin: str
    osv_scanner_bin: str
    database_path: str
    price_per_1k_input_usd: float
    price_per_1k_output_usd: float
    ingest_token: str | None


def load_settings() -> Settings:
    return Settings(
        groq_api_key=_env_optional("GROQ_API_KEY"),
        model_id=os.environ.get("TRUSTGATE_MODEL", "openai/gpt-oss-120b"),
        watsonx_api_key=_env_optional("WATSONX_API_KEY"),
        watsonx_url=os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        watsonx_model_id=os.environ.get("WATSONX_MODEL", "ibm/granite-4-h-small"),
        watsonx_project_id=_env_optional("WATSONX_PROJECT_ID"),
        watsonx_space_id=_env_optional("WATSONX_SPACE_ID"),
        checker_timeout_s=_env_int("TRUSTGATE_CHECKER_TIMEOUT_S", 30),
        run_budget_s=_env_int("TRUSTGATE_RUN_BUDGET_S", 90),
        max_diff_bytes=_env_int("TRUSTGATE_MAX_DIFF_BYTES", 120_000),
        gitleaks_bin=os.environ.get("GITLEAKS_BIN", "gitleaks"),
        osv_scanner_bin=os.environ.get("OSV_SCANNER_BIN", "osv-scanner"),
        database_path=os.environ.get("TRUSTGATE_DB", "trustgate.db"),
        price_per_1k_input_usd=_env_float("TRUSTGATE_PRICE_IN", 0.0),
        price_per_1k_output_usd=_env_float("TRUSTGATE_PRICE_OUT", 0.0),
        ingest_token=_env_optional("TRUSTGATE_INGEST_TOKEN"),
    )
