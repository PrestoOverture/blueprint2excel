from pathlib import Path

import pdfplumber

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import TitleBlock
from drawing_inspector.parser.regions import classify_regions
from drawing_inspector.parser.title_block import parse_title_block

FIXTURE = Path(__file__).parents[1] / "fixtures" / "HJMZ01-01-01.pdf"


def test_parses_real_title_block() -> None:
    objects = extract_text_objects(FIXTURE)
    with pdfplumber.open(FIXTURE) as document:
        page = document.pages[0]
        regions = classify_regions(objects, page.width, page.height)

    assert parse_title_block(objects, regions) == TitleBlock(
        drawing_number="HJMZ01-01-01",
        part_name="板面",
        material="6061 合金",
        scale="1:10",
        date="2025/12/31",
    )
