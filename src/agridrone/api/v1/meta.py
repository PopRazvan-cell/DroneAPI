"""Metadata endpoints shared with the frontend."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from agridrone.core.classes import CLASS_DEFINITIONS

router = APIRouter(tags=["meta"])


class ClassInfo(BaseModel):
    code: int
    class_name: str
    color: str | None


@router.get("/meta/classes", response_model=list[ClassInfo])
def list_classes() -> list[ClassInfo]:
    """Return every class code from contracts §5."""
    return [
        ClassInfo(code=int(definition.code), class_name=definition.class_name, color=definition.color)
        for definition in CLASS_DEFINITIONS
    ]
