"""Settings smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agridrone.core.config import Settings


def test_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.env == "dev"
    assert settings.is_dev is True
    assert settings.is_prod is False
    assert settings.storage_dir == Path("./data/store")
    assert settings.data_dir == Path("./data")
    assert settings.database_url.startswith("mysql+asyncmy://")
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.photogrammetry_mode == "mock"
    assert settings.log_level == "INFO"


def test_environment_prefix_overrides_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AGRIDRONE_ENV", "prod")
    monkeypatch.setenv("AGRIDRONE_STORAGE_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("AGRIDRONE_LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.env == "prod"
    assert settings.is_prod is True
    assert settings.storage_dir == tmp_path / "store"
    assert settings.log_level == "DEBUG"


def test_cors_origins_accept_comma_separated_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGRIDRONE_CORS_ORIGINS", "http://localhost:5173, https://example.test")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:5173", "https://example.test"]


def test_ensure_dirs_creates_storage_and_uploads(settings: Settings) -> None:
    settings.ensure_dirs()

    assert settings.data_dir.is_dir()
    assert settings.storage_dir.is_dir()
    assert (settings.storage_dir / "_uploads").is_dir()


def test_secret_values_are_not_exposed_in_repr() -> None:
    settings = Settings(_env_file=None)

    assert "dev-token" not in repr(settings)
    assert "dev-only-change-me" not in repr(settings)
