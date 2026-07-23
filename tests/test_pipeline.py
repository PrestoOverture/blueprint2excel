from pathlib import Path

import pymupdf
import pytest

from drawing_inspector.models import Dimension
from drawing_inspector.pipeline import (
    NotVectorPDFError,
    _fill_gb1804_tolerances,
    assemble_drawing_data,
)

FIXTURE = Path(__file__).parent / "fixtures" / "HJMZ01-01-01.pdf"


def test_assemble_real_drawing_data_and_apply_general_tolerances() -> None:
    drawing = assemble_drawing_data(FIXTURE)

    assert drawing.drawing_number == "HJMZ01-01-01"
    assert drawing.tolerance_standard == "GB-1804-M"
    assert len(drawing.hole_features) == 11
    assert len(drawing.dimensions) == 18

    explicit = [
        dimension
        for dimension in drawing.dimensions
        if dimension.nominal == 60
    ]
    assert len(explicit) == 2
    assert all(dimension.upper_deviation == 0.05 for dimension in explicit)
    assert all(dimension.tolerance_grade is None for dimension in explicit)

    derived = next(
        dimension
        for dimension in drawing.dimensions
        if dimension.nominal == 920
    )
    assert derived.upper_deviation is not None
    assert derived.lower_deviation is not None
    assert derived.tolerance_grade == "GB-1804-M"


def test_assemble_rejects_image_only_pdf(tmp_path: Path) -> None:
    image_pdf = tmp_path / "image-only.pdf"
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), False)
    image.clear_with(255)
    document = pymupdf.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=image.tobytes("png"))
    document.save(image_pdf)
    document.close()

    with pytest.raises(NotVectorPDFError, match="当前版本不支持扫描件"):
        assemble_drawing_data(image_pdf)


def test_general_tolerance_leaves_out_of_range_dimension_unchanged() -> None:
    dimension = Dimension(
        nominal=5000,
        upper_deviation=None,
        lower_deviation=None,
        tolerance_grade=None,
        dimension_type="linear",
        x=0,
        y=0,
        bubble_id=None,
    )

    _fill_gb1804_tolerances([dimension], "m", "GB-1804-M")

    assert dimension.upper_deviation is None
    assert dimension.lower_deviation is None
    assert dimension.tolerance_grade is None
