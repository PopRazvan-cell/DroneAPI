"""Class codes and colours must match contracts §5 exactly."""

from __future__ import annotations

import pytest

from agridrone.core.classes import (
    CLASS_COLORS,
    CLASS_DEFINITIONS,
    CLASS_NAMES,
    ClassCode,
    get_class_definition,
)

EXPECTED = [
    (0, "nodata", "transparent"),
    (1, "soil", "#A1887F"),
    (2, "vegetation", "#43A047"),
    (3, "water", "#1E88E5"),
    (4, "wet_soil", "#5D4037"),
    (5, "weed", "#FDD835"),
    (6, "gap", "#E53935"),
    (7, "other", "#9E9E9E"),
    (255, "ignore", None),
]


def test_codes_names_and_colours() -> None:
    actual = [
        (int(definition.code), definition.class_name, definition.color) for definition in CLASS_DEFINITIONS
    ]
    assert actual == EXPECTED


def test_lookup_tables_are_consistent() -> None:
    assert len(CLASS_NAMES) == len(EXPECTED)
    assert len(CLASS_COLORS) == len(EXPECTED)
    for code, name, color in EXPECTED:
        assert CLASS_NAMES[ClassCode(code)] == name
        assert CLASS_COLORS[ClassCode(code)] == color


def test_get_class_definition() -> None:
    definition = get_class_definition(3)
    assert definition.code is ClassCode.WATER
    assert definition.class_name == "water"
    assert definition.color == "#1E88E5"


def test_unknown_class_code_is_rejected() -> None:
    with pytest.raises(KeyError):
        get_class_definition(42)
