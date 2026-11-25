"""Aggregate router for ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from agridrone.api.v1 import health, meta

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(meta.router)
