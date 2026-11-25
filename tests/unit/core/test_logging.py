"""Logging format tests."""

from __future__ import annotations

import json
import logging

from agridrone.core.config import Settings
from agridrone.core.logging import JsonFormatter, configure_logging


def _record() -> logging.LogRecord:
    return logging.LogRecord(
        name="agridrone.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )


def test_json_formatter_emits_one_json_object() -> None:
    payload = json.loads(JsonFormatter().format(_record()))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "agridrone.test"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_text_in_dev_and_json_in_prod(settings: Settings) -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    try:
        configure_logging(settings, force=True)
        dev_handler = next(
            handler for handler in root.handlers if getattr(handler, "_agridrone_handler", False)
        )
        assert not isinstance(dev_handler.formatter, JsonFormatter)

        prod_settings = Settings(
            _env_file=None,
            env="prod",
            data_dir=settings.data_dir,
            storage_dir=settings.storage_dir,
        )
        configure_logging(prod_settings, force=True)
        prod_handler = next(
            handler for handler in root.handlers if getattr(handler, "_agridrone_handler", False)
        )
        assert isinstance(prod_handler.formatter, JsonFormatter)
    finally:
        for handler in list(root.handlers):
            if getattr(handler, "_agridrone_handler", False):
                root.removeHandler(handler)
        for handler in original_handlers:
            if handler not in root.handlers:
                root.addHandler(handler)
        root.setLevel(original_level)
