from pathlib import Path

import pdfplumber

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import HoleFeature, PageRegions
from drawing_inspector.parser.hole_table import parse_hole_table
from drawing_inspector.parser.regions import classify_regions

FIXTURE = Path(__file__).parents[1] / "fixtures" / "HJMZ01-01-01.pdf"


def test_returns_empty_list_when_table_region_is_missing() -> None:
    regions = PageRegions(
        table_bbox=None,
        title_block_bbox=None,
        tech_requirements_bbox=None,
        drawing_bbox=(0.0, 0.0, 100.0, 100.0),
    )

    assert parse_hole_table([], regions) == []


def test_parses_all_hole_rows_from_real_drawing() -> None:
    objects = extract_text_objects(FIXTURE)
    with pdfplumber.open(FIXTURE) as document:
        page = document.pages[0]
        regions = classify_regions(objects, page.width, page.height)

    assert parse_hole_table(objects, regions) == [
        HoleFeature("A", "counterbore", 11.0, 19.75, 20.0, 9.0, None, None, 8, False),
        HoleFeature("B", "threaded", 2.5, 12.0, None, None, "M3 - 6H", 2.5, 16, False),
        HoleFeature("C", "through", 15.0, "贯穿", None, None, None, None, 8, False),
        HoleFeature("D", "through", 12.0, "贯穿", None, None, None, None, 2, False),
        HoleFeature(
            "E", "threaded", 4.2, "完全贯穿", None, None, "M5 - 6H", 4.2, 4, False
        ),
        HoleFeature("F", "counterbore", 12.0, 19.75, 30.0, 10.0, None, None, 3, True),
        HoleFeature("G", "through", 40.0, "贯穿", None, None, None, None, 2, False),
        HoleFeature("H", "threaded", 6.8, "贯穿", None, None, "M8 - 6H", 6.8, 8, False),
        HoleFeature("J", "counterbore", 22.0, 19.75, 50.0, 9.0, None, None, 6, True),
        HoleFeature(
            "K", "threaded", 5.0, "完全贯穿", None, None, "M6 - 6H", 5.0, 8, False
        ),
        HoleFeature(
            "L", "threaded", 2.5, "完全贯穿", None, None, "M3 - 6H", 2.5, 16, False
        ),
    ]
