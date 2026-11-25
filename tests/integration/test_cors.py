"""CORS must allow the configured web origin and reject others."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agridrone.api.main import create_app
from agridrone.core.config import Settings


def test_preflight_from_allowed_origin(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.options(
            "/api/v1/meta/classes",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_preflight_from_other_origin_is_rejected(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.options(
            "/api/v1/meta/classes",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
