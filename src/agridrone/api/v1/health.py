"""Health endpoint used by Docker and by the deploy checks."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Literal

import redis.asyncio as redis_asyncio
from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from agridrone import __version__
from agridrone.api.deps import SettingsDep
from agridrone.core.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["meta"])

CheckStatus = Literal["ok", "unavailable"]
HealthState = Literal["ok", "degraded"]

_CHECK_TIMEOUT_SECONDS = 3.0


class HealthResponse(BaseModel):
    status: HealthState
    version: str
    db: CheckStatus
    redis: CheckStatus
    storage: CheckStatus


async def _check_db(settings: Settings) -> CheckStatus:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with asyncio.timeout(_CHECK_TIMEOUT_SECONDS):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        logger.warning("Database health check failed", exc_info=True)
        return "unavailable"
    finally:
        await engine.dispose()


async def _check_redis(settings: Settings) -> CheckStatus:
    client = redis_asyncio.Redis.from_url(settings.redis_url)
    try:
        async with asyncio.timeout(_CHECK_TIMEOUT_SECONDS):
            await client.ping()
        return "ok"
    except Exception:
        logger.warning("Redis health check failed", exc_info=True)
        return "unavailable"
    finally:
        await client.aclose()


def _check_storage(settings: Settings) -> CheckStatus:
    try:
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.warning("Storage health check failed: cannot create directory", exc_info=True)
        return "unavailable"
    return "ok" if os.access(settings.storage_dir, os.W_OK) else "unavailable"


@router.get(
    "/healthz",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "One or more dependencies are down"}},
)
async def healthz(settings: SettingsDep, response: Response) -> HealthResponse:
    db_status, redis_status = await asyncio.gather(_check_db(settings), _check_redis(settings))
    storage_status = _check_storage(settings)
    state: HealthState = "ok" if db_status == redis_status == storage_status == "ok" else "degraded"
    if state == "degraded":
        response.status_code = 503
    return HealthResponse(
        status=state,
        version=__version__,
        db=db_status,
        redis=redis_status,
        storage=storage_status,
    )
