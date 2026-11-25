"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from agridrone.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep tests independent from a developer's .env and shell environment."""
    for key in list(os.environ):
        if key.startswith("AGRIDRONE_"):
            monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        storage_dir=tmp_path / "data" / "store",
        database_url="mysql+asyncmy://user:password@127.0.0.1:1/agridrone",
        redis_url="redis://127.0.0.1:1/0",
        cors_origins=["http://localhost:5173"],
    )
