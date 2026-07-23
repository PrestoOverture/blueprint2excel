"""Assemble parsed drawing information from a vector PDF."""

from os import PathLike
from pathlib import Path

import pdfplumber

from drawing_inspector.detector import is_vector_pdf
from drawing_inspector.extractor import extract_text_objects
from drawing_inspector.models import Dimension, DrawingData
from drawing_inspector.parser.dimensions import parse_dimensions
from drawing_inspector.parser.hole_table import parse_hole_table
from drawing_inspector.parser.regions import classify_regions
from drawing_inspector.parser.tech_requirements import parse_tech_requirements
from drawing_inspector.parser.title_block import parse_title_block
from drawing_inspector.tolerance.gb1804 import lookup_gb1804

_GB1804_GRADES = frozenset({"f", "m", "c", "v"})


class NotVectorPDFError(Exception):
    """Raised when a PDF contains no extractable vector text."""


def assemble_drawing_data(pdf_path: str | PathLike[str]) -> DrawingData:
    """Parse one vector PDF into the data needed by downstream consumers."""
    if not is_vector_pdf(pdf_path):
        msg = "当前版本不支持扫描件; 请输入包含矢量文字的 PDF。"
        raise NotVectorPDFError(msg)

    objects = extract_text_objects(pdf_path)
    with pdfplumber.open(Path(pdf_path)) as document:
        page = document.pages[0]
        regions = classify_regions(objects, page.width, page.height)

    title_block = parse_title_block(objects, regions)
    tech_requirements = parse_tech_requirements(objects, regions)
    hole_features = parse_hole_table(objects, regions)
    dimensions = parse_dimensions(objects, regions)

    tolerance_standard = tech_requirements.tolerance_standard
    if tolerance_standard is not None:
        grade = tolerance_standard.rsplit("-", maxsplit=1)[-1].lower()
        if grade in _GB1804_GRADES:
            _fill_gb1804_tolerances(dimensions, grade, tolerance_standard)

    return DrawingData(
        drawing_number=title_block.drawing_number,
        part_name=title_block.part_name,
        material=title_block.material,
        scale=title_block.scale,
        date=title_block.date,
        tech_requirements=tech_requirements.items,
        dimensions=dimensions,
        hole_features=hole_features,
        tolerance_standard=tolerance_standard or "",
    )


def _fill_gb1804_tolerances(
    dimensions: list[Dimension], grade: str, tolerance_standard: str
) -> None:
    for dimension in dimensions:
        if (
            dimension.upper_deviation is not None
            or dimension.lower_deviation is not None
        ):
            continue
        try:
            upper_deviation, lower_deviation = lookup_gb1804(
                dimension.nominal, grade
            )
        except ValueError:
            continue
        dimension.upper_deviation = upper_deviation
        dimension.lower_deviation = lower_deviation
        dimension.tolerance_grade = tolerance_standard
