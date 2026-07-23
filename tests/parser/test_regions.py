from pathlib import Path

import pdfplumber

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import TextObject
from drawing_inspector.parser.regions import classify_regions

FIXTURE = Path(__file__).parents[1] / "fixtures" / "HJMZ01-01-01.pdf"


def _contains(
    bbox: tuple[float, float, float, float] | None, item: TextObject
) -> bool:
    assert bbox is not None
    return (
        bbox[0] <= item.x + item.width / 2 <= bbox[2]
        and bbox[1] <= item.y + item.height / 2 <= bbox[3]
    )


def test_classifies_real_drawing_from_semantic_anchors() -> None:
    objects = extract_text_objects(FIXTURE)
    with pdfplumber.open(FIXTURE) as document:
        page = document.pages[0]
        regions = classify_regions(objects, page.width, page.height)

    assert _contains(
        regions.title_block_bbox,
        next(item for item in objects if "图号" in item.text),
    )
    assert _contains(
        regions.tech_requirements_bbox,
        next(item for item in objects if "技术要求" in item.text),
    )
    assert _contains(
        regions.table_bbox,
        next(item for item in objects if item.text == "标签"),
    )
    assert regions.title_block_bbox is not None
    assert regions.tech_requirements_bbox is not None
    assert regions.drawing_bbox[3] <= regions.title_block_bbox[1]
    assert regions.drawing_bbox[3] <= regions.tech_requirements_bbox[1]
