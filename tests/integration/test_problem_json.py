"""Errors must use application/problem+json (RFC 9457)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agridrone.api.main import create_app
from agridrone.core.config import Settings


def test_unknown_route_returns_problem_json(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "about:blank"
    assert body["title"] == "Not Found"
    assert body["status"] == 404
    assert "detail" in body
    assert "instance" in body
