from pathlib import Path

import pytest

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import Dimension, TextObject
from drawing_inspector.reassembler import (
    classify_dimension_type,
    reassemble_dimensions,
    restore_rotated_text,
)

FIXTURE = Path(__file__).parent / "fixtures" / "HJMZ01-01-01.pdf"


def _text(
    value: str,
    x: float,
    y: float,
    font_size: float,
    *,
    rotation: float = 90.0,
) -> TextObject:
    return TextObject(
        text=value,
        x=x,
        y=y,
        width=font_size,
        height=font_size,
        rotation=rotation,
        font_name="Arial",
        font_size=font_size,
    )


@pytest.mark.parametrize(
    ("fragments", "expected"),
    [
        (
            [
                _text("44", 59.39, 105.70, 4.35),
                _text("8", 59.39, 101.35, 4.34),
            ],
            "448",
        ),
        ([_text("014", 75.18, 101.35, 4.35)], "410"),
        ([_text("502", 89.16, 128.83, 4.35)], "205"),
        ([_text("02", 89.16, 187.70, 4.35)], "20"),
        (
            [
                _text("0", 89.16, 303.50, 4.35),
                _text("9", 89.16, 307.85, 4.34),
                _text("1", 89.16, 312.19, 4.35),
            ],
            "190",
        ),
        (
            [
                _text("0", 89.16, 412.21, 4.35),
                _text("6", 89.16, 416.57, 4.34),
                _text("1", 89.16, 420.91, 4.35),
            ],
            "160",
        ),
        (
            [
                _text("50", 91.10, 387.01, 3.48),
                _text(".", 91.10, 393.97, 3.47),
                _text("0", 91.10, 397.44, 3.48),
                _text("±", 91.10, 400.93, 6.95),
            ],
            "±0.05",
        ),
    ],
)
def test_restores_real_rotation_90_fragment_patterns(
    fragments: list[TextObject], expected: str
) -> None:
    restored = restore_rotated_text(fragments)

    assert [item.text for item in restored] == [expected]


def test_restores_known_values_from_real_pdf_pipeline() -> None:
    restored = restore_rotated_text(extract_text_objects(FIXTURE))

    restored_text = {item.text for item in restored}
    assert {"448", "410"} <= restored_text


def test_leaves_non_axis_aligned_rotation_untouched() -> None:
    diagonal = _text("15", 10.0, 20.0, 4.0, rotation=315.0)

    assert restore_rotated_text([diagonal]) == [diagonal]


def test_restores_rotation_270_as_mirror_of_rotation_90() -> None:
    fragments = [
        _text("44", 10.0, 10.0, 4.0, rotation=270.0),
        _text("8", 10.0, 14.0, 4.0, rotation=270.0),
    ]

    assert [item.text for item in restore_rotated_text(fragments)] == ["448"]


@pytest.mark.parametrize(
    ("text", "nominal", "dimension_type"),
    [
        ("⌀15", 15.0, "diameter"),
        ("R5", 5.0, "radius"),
        ("30°", 30.0, "angle"),
        ("60", 60.0, "linear"),
    ],
)
def test_classifies_and_parses_nominal_dimensions(
    text: str, nominal: float, dimension_type: str
) -> None:
    dimensions = reassemble_dimensions([_text(text, 10.0, 20.0, 5.0, rotation=0)])

    assert classify_dimension_type(text) == dimension_type
    assert dimensions == [
        Dimension(
            nominal=nominal,
            upper_deviation=None,
            lower_deviation=None,
            tolerance_grade=None,
            dimension_type=dimension_type,
            x=10.0,
            y=20.0,
            bubble_id=None,
        )
    ]


def test_reassembles_stacked_tolerance_fragments() -> None:
    fragments = [
        _text("15", 10.0, 20.0, 5.0, rotation=0),
        _text("+0", 14.0, 12.0, 5.0, rotation=0),
        _text(".01", 19.0, 12.0, 5.0, rotation=0),
        _text("8", 24.0, 12.0, 5.0, rotation=0),
        _text("0", 14.0, 28.0, 5.0, rotation=0),
    ]

    assert reassemble_dimensions(fragments) == [
        Dimension(
            nominal=15.0,
            upper_deviation=0.018,
            lower_deviation=0.0,
            tolerance_grade=None,
            dimension_type="linear",
            x=10.0,
            y=20.0,
            bubble_id=None,
        )
    ]


def test_reassembles_single_text_symmetric_tolerance() -> None:
    annotation = _text("60 ±0.05", 10.0, 20.0, 5.0, rotation=0)

    assert reassemble_dimensions([annotation]) == [
        Dimension(
            nominal=60.0,
            upper_deviation=0.05,
            lower_deviation=-0.05,
            tolerance_grade=None,
            dimension_type="linear",
            x=10.0,
            y=20.0,
            bubble_id=None,
        )
    ]


def test_reassembles_real_pdf_symmetric_tolerance() -> None:
    objects = extract_text_objects(FIXTURE)

    assert any(item.text == "60" and item.rotation == 0 for item in objects)
    assert any(item.text == "±0.05" and item.rotation == 0 for item in objects)
    assert any(
        dimension.nominal == 60.0
        and dimension.upper_deviation == 0.05
        and dimension.lower_deviation == -0.05
        for dimension in reassemble_dimensions(objects)
    )
