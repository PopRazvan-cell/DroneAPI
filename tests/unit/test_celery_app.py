"""Celery application smoke test (no broker connection)."""

from __future__ import annotations


def test_celery_app_is_configured() -> None:
    from agridrone.workers.celery_app import celery_app

    assert celery_app.main == "agridrone"
    assert celery_app.conf.task_default_queue == "cpu"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.worker_prefetch_multiplier == 1
