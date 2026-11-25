"""Health endpoint tests (dependencies mocked, no Docker required)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import agridrone.api.v1.health as health_module
from agridrone.api.main import create_app
from agridrone.core.config import Settings


async def _ok(_: Settings) -> str:
    return "ok"


async def _unavailable(_: Settings) -> str:
    return "unavailable"


def test_healthz_ok(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "_check_db", _ok)
    monkeypatch.setattr(health_module, "_check_redis", _ok)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.0.1",
        "db": "ok",
        "redis": "ok",
        "storage": "ok",
    }


def test_healthz_degraded_when_db_is_down(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "_check_db", _unavailable)
    monkeypatch.setattr(health_module, "_check_redis", _ok)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/healthz")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "unavailable"
    assert body["redis"] == "ok"
    assert body["storage"] == "ok"
