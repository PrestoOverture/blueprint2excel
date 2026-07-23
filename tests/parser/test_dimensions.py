from collections import Counter
from pathlib import Path

import pdfplumber

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import TextObject
from drawing_inspector.parser.dimensions import parse_dimensions
from drawing_inspector.parser.regions import classify_regions
from drawing_inspector.reassembler import reassemble_dimensions

FIXTURE = Path(__file__).parents[1] / "fixtures" / "HJMZ01-01-01.pdf"


def test_parses_only_drawing_area_dimensions_from_real_drawing() -> None:
    objects = extract_text_objects(FIXTURE)
    with pdfplumber.open(FIXTURE) as document:
        page = document.pages[0]
        regions = classify_regions(objects, page.width, page.height)

    dimensions = parse_dimensions(objects, regions)

    dimension_values = Counter(
        (
            dimension.nominal,
            dimension.upper_deviation,
            dimension.lower_deviation,
        )
        for dimension in dimensions
    )
    assert dimension_values[(20.0, None, None)] >= 1
    assert dimension_values[(50.0, None, None)] == 2
    assert dimension_values[(60.0, 0.05, -0.05)] == 2
    assert dimension_values[(440.0, None, None)] == 1
    assert dimension_values[(880.0, None, None)] == 1
    assert dimension_values[(920.0, None, None)] == 1
    assert dimension_values[(12.0, None, None)] == 1
    assert Counter(dimension.nominal for dimension in dimensions) == Counter(
        [
            20.0,
            50.0,
            60.0,
            440.0,
            880.0,
            920.0,
            60.0,
            50.0,
            12.0,
            448.0,
            448.0,
            410.0,
            205.0,
            20.0,
            190.0,
            190.0,
            160.0,
            160.0,
        ]
    )
    assert not any(
        dimension.nominal == 12.0
        and dimension.upper_deviation == 9.0
        and dimension.lower_deviation == 0.0
        for dimension in dimensions
    )
    assert len(dimensions) == 18
    diagonal_numeric_positions = {
        (item.x, item.y)
        for item in objects
        if item.text.replace(".", "", 1).isdigit()
        and all(
            min(
                abs(item.rotation % 360 - allowed),
                360 - abs(item.rotation % 360 - allowed),
            )
            > 5.0
            for allowed in (0.0, 90.0, 270.0)
        )
    }
    assert diagonal_numeric_positions.isdisjoint(
        (dimension.x, dimension.y) for dimension in dimensions
    )


def test_rotated_nominal_only_matches_same_rotation_tolerance() -> None:
    nominal = _text("60", x=10.0, rotation=90.0)
    matching = _text("±0.05", x=15.0, rotation=90.0)
    mismatched = _text("±0.10", x=15.0, rotation=0.0)

    dimensions = reassemble_dimensions([nominal, mismatched, matching])

    assert len(dimensions) == 1
    assert dimensions[0].nominal == 60.0
    assert dimensions[0].upper_deviation == 0.05
    assert dimensions[0].lower_deviation == -0.05


def _text(value: str, x: float, rotation: float) -> TextObject:
    return TextObject(
        text=value,
        x=x,
        y=10.0,
        width=5.0,
        height=5.0,
        rotation=rotation,
        font_name="Arial",
        font_size=5.0,
    )
