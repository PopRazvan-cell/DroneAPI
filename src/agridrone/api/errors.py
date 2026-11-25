"""RFC 9457 problem+json exception handlers."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from agridrone.core.errors import AgriDroneError

PROBLEM_JSON = "application/problem+json"
logger = logging.getLogger(__name__)


def _problem(
    *,
    problem_type: str,
    title: str,
    status: int,
    detail: str,
    instance: str,
    headers: dict[str, str] | None = None,
    **extensions: Any,
) -> JSONResponse:
    content: dict[str, Any] = {
        "type": problem_type,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    content.update(extensions)
    return JSONResponse(
        content=content,
        status_code=status,
        media_type=PROBLEM_JSON,
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers that always emit ``application/problem+json``."""

    @app.exception_handler(AgriDroneError)
    async def _agridrone_error_handler(request: Request, exc: AgriDroneError) -> JSONResponse:
        return JSONResponse(
            content=exc.to_problem(instance=str(request.url)),
            status_code=exc.status_code,
            media_type=PROBLEM_JSON,
            headers=exc.headers or None,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        try:
            title = HTTPStatus(exc.status_code).phrase
        except ValueError:
            title = "HTTP Error"
        detail = exc.detail if isinstance(exc.detail, str) else title
        return _problem(
            problem_type="about:blank",
            title=title,
            status=exc.status_code,
            detail=detail,
            instance=str(request.url),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem(
            problem_type="https://agridrone.dev/problems/validation",
            title="Request Validation Failed",
            status=422,
            detail="The request body or parameters are invalid.",
            instance=str(request.url),
            errors=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error for %s", request.url, exc_info=exc)
        return _problem(
            problem_type="about:blank",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred.",
            instance=str(request.url),
        )
