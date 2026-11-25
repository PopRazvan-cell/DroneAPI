"""The classes metadata endpoint must expose every code from contracts §5."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agridrone.api.main import create_app
from agridrone.core.config import Settings

EXPECTED = [
    {"code": 0, "class_name": "nodata", "color": "transparent"},
    {"code": 1, "class_name": "soil", "color": "#A1887F"},
    {"code": 2, "class_name": "vegetation", "color": "#43A047"},
    {"code": 3, "class_name": "water", "color": "#1E88E5"},
    {"code": 4, "class_name": "wet_soil", "color": "#5D4037"},
    {"code": 5, "class_name": "weed", "color": "#FDD835"},
    {"code": 6, "class_name": "gap", "color": "#E53935"},
    {"code": 7, "class_name": "other", "color": "#9E9E9E"},
    {"code": 255, "class_name": "ignore", "color": None},
]


def test_meta_classes(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/meta/classes")

    assert response.status_code == 200
    assert response.json() == EXPECTED
