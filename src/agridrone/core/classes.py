"""Class codes and UI colours (contracts §5).

The codes are defined exactly once here. Masks, ML, DB and frontend all use
these values; the frontend receives them from ``GET /api/v1/meta/classes``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final


class ClassCode(IntEnum):
    """Pixel/analysis class codes."""

    NODATA = 0
    SOIL = 1
    VEGETATION = 2
    WATER = 3
    WET_SOIL = 4
    WEED = 5
    GAP = 6
    OTHER = 7
    IGNORE = 255


@dataclass(frozen=True, slots=True)
class ClassDefinition:
    """A class code with its canonical name and UI colour."""

    code: ClassCode
    class_name: str
    color: str | None


CLASS_DEFINITIONS: Final[tuple[ClassDefinition, ...]] = (
    ClassDefinition(ClassCode.NODATA, "nodata", "transparent"),
    ClassDefinition(ClassCode.SOIL, "soil", "#A1887F"),
    ClassDefinition(ClassCode.VEGETATION, "vegetation", "#43A047"),
    ClassDefinition(ClassCode.WATER, "water", "#1E88E5"),
    ClassDefinition(ClassCode.WET_SOIL, "wet_soil", "#5D4037"),
    ClassDefinition(ClassCode.WEED, "weed", "#FDD835"),
    ClassDefinition(ClassCode.GAP, "gap", "#E53935"),
    ClassDefinition(ClassCode.OTHER, "other", "#9E9E9E"),
    ClassDefinition(ClassCode.IGNORE, "ignore", None),
)

CLASS_BY_CODE: Final[dict[ClassCode, ClassDefinition]] = {
    definition.code: definition for definition in CLASS_DEFINITIONS
}

CLASS_NAMES: Final[dict[ClassCode, str]] = {
    definition.code: definition.class_name for definition in CLASS_DEFINITIONS
}

CLASS_COLORS: Final[dict[ClassCode, str | None]] = {
    definition.code: definition.color for definition in CLASS_DEFINITIONS
}


def get_class_definition(code: int) -> ClassDefinition:
    """Return the definition for a class code.

    Raises:
        KeyError: if the code is not part of contracts §5.
    """
    try:
        class_code = ClassCode(code)
    except ValueError as exc:
        raise KeyError(f"Unknown class code: {code}") from exc
    return CLASS_BY_CODE[class_code]
