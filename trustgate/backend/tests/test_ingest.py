from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TOKEN = "test-token-not-a-real-secret"
RECORD = {
    "run_id": "run_20260927_120000",
    "pr": "7",
    "written_at": "2026-09-27T12:00:00+00:00",
    "result": {
        "checker": "secrets",
        "tier": "deterministic",
        "status": "ok",
        "findings": [
            {
                "checker": "secrets",
                "severity": "high",
                "title": "Hardcoded credential",
                "detail": "A live-format API key is committed in source.",
                "file": "app/config.py",
                "line": 14,
                "evidence": "API_KEY = \"...\"",
            }
        ],
        "duration_ms": 12,
    },
}


def _client(tmp_path: Path, token: str | None) -> TestClient:
    import app.main as main

    importlib.reload(main)
    if token is None:
        import app.config as config

        importlib.reload(config)
    from app.config import Settings

    original = main.load_settings

    def fake() -> Settings:
        settings = original()
        return Settings(**{**settings.__dict__, "ingest_token": token})

    main.load_settings = fake
    return TestClient(main.build_app(tmp_path / "runs"))


def test_ingest_rejects_a_bad_token(tmp_path: Path) -> None:
    with _client(tmp_path, TOKEN) as client:
        response = client.post("/api/runs", json=[RECORD], headers={"X-TrustGate-Token": "wrong"})
    assert response.status_code == 401
    assert not list((tmp_path / "runs").glob("*.json"))


def test_ingest_is_closed_when_unconfigured(tmp_path: Path) -> None:
    with _client(tmp_path, None) as client:
        response = client.post("/api/runs", json=[RECORD], headers={"X-TrustGate-Token": TOKEN})
    assert response.status_code == 503


def test_ingest_writes_a_record_and_it_reads_back(tmp_path: Path) -> None:
    with _client(tmp_path, TOKEN) as client:
        response = client.post("/api/runs", json=[RECORD], headers={"X-TrustGate-Token": TOKEN})
        assert response.status_code == 200
        assert response.json() == {"received": 1, "written": 1}
        listing = client.get("/api/runs").json()
        verdict = client.get("/api/pr/7/verdict").json()
    assert listing["count"] == 1
    assert listing["unreadable"] == []
    assert verdict["verdict"] == "BLOCK"


def test_ingest_refuses_to_escape_the_runs_directory(tmp_path: Path) -> None:
    hostile = json.loads(json.dumps(RECORD))
    hostile["run_id"] = "../../../escaped"
    with _client(tmp_path, TOKEN) as client:
        response = client.post(
            "/api/runs", json=[hostile], headers={"X-TrustGate-Token": TOKEN}
        )
    assert response.status_code == 422
    assert not (tmp_path.parent / "escaped_secrets.json").exists()


def test_ingest_rejects_a_record_that_does_not_validate(tmp_path: Path) -> None:
    bad = json.loads(json.dumps(RECORD))
    del bad["result"]["status"]
    with _client(tmp_path, TOKEN) as client:
        response = client.post("/api/runs", json=[bad], headers={"X-TrustGate-Token": TOKEN})
    assert response.status_code == 422
    assert not list((tmp_path / "runs").glob("*.json"))
