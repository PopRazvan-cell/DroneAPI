"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agridrone import __version__
from agridrone.api.errors import register_exception_handlers
from agridrone.api.v1.router import api_router
from agridrone.core.config import Settings, get_settings
from agridrone.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API application.

    Passing ``settings`` explicitly keeps tests and CLI commands independent
    from the process-wide environment.
    """
    resolved = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_logging(resolved)
        resolved.ensure_dirs()
        yield

    app = FastAPI(
        title="AgriDrone API",
        version=__version__,
        description="Detecția zonelor cu băltire și a golurilor din culturi, din imagini de dronă.",
        lifespan=lifespan,
    )
    app.state.settings = resolved

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "Accept-Ranges"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
