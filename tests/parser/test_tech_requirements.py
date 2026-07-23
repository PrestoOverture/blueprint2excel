# ruff: noqa: RUF001

from pathlib import Path

import pdfplumber

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import TechRequirements
from drawing_inspector.parser.regions import classify_regions
from drawing_inspector.parser.tech_requirements import parse_tech_requirements

FIXTURE = Path(__file__).parents[1] / "fixtures" / "HJMZ01-01-01.pdf"


def test_parses_real_technical_requirements_in_spatial_order() -> None:
    objects = extract_text_objects(FIXTURE)
    with pdfplumber.open(FIXTURE) as document:
        page = document.pages[0]
        regions = classify_regions(objects, page.width, page.height)

    assert parse_tech_requirements(objects, regions) == TechRequirements(
        items=[
            "1.未注明尺寸按GB-1804-M；阳极氧化",
            "2.零件要求去毛刺0.3×45°；",
            "3.表面不能有划伤等表面缺陷；",
            "4.未注尺寸以实体为准；",
            "5.图中位置尺寸必须保证",
        ],
        tolerance_standard="GB-1804-M",
    )
