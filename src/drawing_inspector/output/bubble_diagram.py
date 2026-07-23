"""Overlay inspection bubbles on a source drawing PDF."""

from os import PathLike
from pathlib import Path

import pymupdf

from drawing_inspector.models import DrawingData

_BUBBLE_RADIUS = 7.0
_FONT_SIZE = 7.0
_RED = (1.0, 0.0, 0.0)
_WHITE = (1.0, 1.0, 1.0)
_BLACK = (0.0, 0.0, 0.0)


def render_bubble_diagram(
    drawing_data: DrawingData,
    source_pdf_path: str | PathLike[str],
    output_path: str | PathLike[str],
) -> None:
    """Write a copy of a drawing with numbered inspection bubbles."""
    source_path = Path(source_pdf_path)
    destination_path = Path(output_path)
    if source_path.resolve() == destination_path.resolve():
        msg = "output_path must differ from source_pdf_path"
        raise ValueError(msg)

    with pymupdf.open(source_path) as document:  # type: ignore[no-untyped-call]
        page = document[0]
        for dimension in drawing_data.dimensions:
            if dimension.bubble_id is None:
                continue

            center = pymupdf.Point(dimension.x, dimension.y)  # type: ignore[no-untyped-call]
            page.draw_circle(
                center,
                _BUBBLE_RADIUS,
                color=_RED,
                fill=_WHITE,
                width=1.0,
                overlay=True,
            )

            label = str(dimension.bubble_id)
            label_width = pymupdf.get_text_length(
                label, fontname="helv", fontsize=_FONT_SIZE
            )
            page.insert_text(
                pymupdf.Point(  # type: ignore[no-untyped-call]
                    center.x - label_width / 2,
                    center.y + _FONT_SIZE * 0.35,
                ),
                label,
                fontsize=_FONT_SIZE,
                fontname="helv",
                color=_BLACK,
                overlay=True,
            )

        document.save(destination_path)
