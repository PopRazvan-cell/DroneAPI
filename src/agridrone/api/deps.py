"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from agridrone.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    """Return the settings bound to the current application instance."""
    return cast(Settings, request.app.state.settings)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
