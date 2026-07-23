from pathlib import Path

from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import TextObject

FIXTURE = Path(__file__).parent / "fixtures" / "HJMZ01-01-01.pdf"


def test_extracts_words_with_geometry_font_and_rotation() -> None:
    objects = extract_text_objects(FIXTURE)

    assert objects
    assert all(isinstance(item, TextObject) for item in objects)
    assert all(item.width > 0 and item.height > 0 for item in objects)
    assert all(item.font_name and item.font_size > 0 for item in objects)
    assert any(item.rotation != 0 for item in objects)

    extracted_text = " ".join(item.text for item in objects)
    assert "920" in extracted_text
    assert "M3 - 6H" in extracted_text
    assert "技术要求" in extracted_text
