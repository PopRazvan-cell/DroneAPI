"""Logging setup: JSON in production, readable text in development."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from agridrone.core.config import Settings, get_settings

_HANDLER_MARKER = "_agridrone_handler"


class JsonFormatter(logging.Formatter):
    """One JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False)


def _text_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def configure_logging(settings: Settings | None = None, *, force: bool = False) -> None:
    """Configure the root logger once per process.

    ``force=True`` replaces the handler installed by a previous call, which is
    useful in tests.
    """
    resolved = settings or get_settings()
    root = logging.getLogger()
    existing = [handler for handler in root.handlers if getattr(handler, _HANDLER_MARKER, False)]
    if existing and not force:
        return

    for handler in existing:
        root.removeHandler(handler)

    level = logging.getLevelName(resolved.log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if resolved.is_prod else _text_formatter())
    setattr(handler, _HANDLER_MARKER, True)
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger; callers should pass ``__name__``."""
    return logging.getLogger(name or "agridrone")
