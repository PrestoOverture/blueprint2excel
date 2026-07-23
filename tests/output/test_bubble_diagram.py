from pathlib import Path

import pymupdf
import pytest

from drawing_inspector.output.bubble_diagram import render_bubble_diagram
from drawing_inspector.pipeline import assemble_drawing_data

FIXTURE = Path("tests/fixtures/HJMZ01-01-01.pdf")
RED = (1.0, 0.0, 0.0)
WHITE = (1.0, 1.0, 1.0)


def test_render_bubble_diagram_overlays_fixture_dimensions(
    tmp_path: Path,
) -> None:
    drawing_data = assemble_drawing_data(FIXTURE)
    for bubble_id, dimension in enumerate(drawing_data.dimensions, start=1):
        dimension.bubble_id = bubble_id
    output_path = tmp_path / "bubble-diagram.pdf"

    render_bubble_diagram(drawing_data, FIXTURE, output_path)

    with (
        pymupdf.open(FIXTURE) as source,
        pymupdf.open(output_path) as output,
    ):
        assert output.page_count == source.page_count

        bubble_drawings = [
            drawing
            for drawing in output[0].get_drawings()
            if drawing["type"] == "fs"
            and drawing["color"] == RED
            and drawing["fill"] == WHITE
        ]
        assigned_dimensions = [
            dimension
            for dimension in drawing_data.dimensions
            if dimension.bubble_id is not None
        ]
        assert len(bubble_drawings) == len(assigned_dimensions) == 18

        dimension_920 = next(
            dimension
            for dimension in drawing_data.dimensions
            if dimension.nominal == 920.0
        )
        expected_center = pymupdf.Point(dimension_920.x, dimension_920.y)
        matching_bubbles = [
            drawing
            for drawing in bubble_drawings
            if pymupdf.Point(
                (drawing["rect"].x0 + drawing["rect"].x1) / 2,
                (drawing["rect"].y0 + drawing["rect"].y1) / 2,
            ).distance_to(expected_center)
            < 0.5
        ]
        assert len(matching_bubbles) == 1
        assert expected_center.x == pytest.approx(252.5, abs=0.1)
        assert expected_center.y == pytest.approx(204.6, abs=0.1)


def test_render_bubble_diagram_skips_dimensions_without_bubble_ids(
    tmp_path: Path,
) -> None:
    drawing_data = assemble_drawing_data(FIXTURE)
    drawing_data.dimensions[0].bubble_id = 42
    output_path = tmp_path / "one-bubble.pdf"

    render_bubble_diagram(drawing_data, FIXTURE, output_path)

    with pymupdf.open(output_path) as output:
        bubble_drawings = [
            drawing
            for drawing in output[0].get_drawings()
            if drawing["type"] == "fs"
            and drawing["color"] == RED
            and drawing["fill"] == WHITE
        ]
        assert len(bubble_drawings) == 1


def test_render_bubble_diagram_rejects_overwriting_source() -> None:
    drawing_data = assemble_drawing_data(FIXTURE)

    with pytest.raises(ValueError, match="output_path must differ"):
        render_bubble_diagram(drawing_data, FIXTURE, FIXTURE)
