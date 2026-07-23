import math
from os import PathLike
from pathlib import Path
from typing import TypedDict, cast

import pdfplumber
import pymupdf

from drawing_inspector.models import TextObject


class _Word(TypedDict):
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    fontname: str
    size: float


class _Span(TypedDict):
    bbox: tuple[float, float, float, float]


class _Line(TypedDict):
    dir: tuple[float, float]
    spans: list[_Span]


class _Block(TypedDict, total=False):
    lines: list[_Line]


class _PageText(TypedDict):
    blocks: list[_Block]


class _RotationRegion(TypedDict):
    bbox: tuple[float, float, float, float]
    rotation: float


def extract_text_objects(pdf_path: str | PathLike[str]) -> list[TextObject]:
    """Extract positioned PDF words, adding rotation data from PyMuPDF."""

    objects: list[TextObject] = []
    path = Path(pdf_path)
    with (
        pdfplumber.open(path) as plumber_document,
        pymupdf.open(path) as mupdf_document,  # type: ignore[no-untyped-call]
    ):
        for plumber_page, mupdf_page in zip(
            plumber_document.pages, mupdf_document, strict=True
        ):
            words = cast(
                list[_Word],
                plumber_page.extract_words(extra_attrs=["fontname", "size"]),
            )
            rotations = _rotation_regions(mupdf_page)
            objects.extend(_to_text_object(word, rotations) for word in words)
    return objects


def _rotation_regions(page: pymupdf.Page) -> list[_RotationRegion]:
    page_text = cast(
        _PageText,
        page.get_text("dict"),  # type: ignore[no-untyped-call]
    )
    regions: list[_RotationRegion] = []
    for block in page_text["blocks"]:
        for line in block.get("lines", []):
            if not line["spans"]:
                continue
            boxes = [span["bbox"] for span in line["spans"]]
            direction_x, direction_y = line["dir"]
            regions.append(
                {
                    "bbox": (
                        min(box[0] for box in boxes),
                        min(box[1] for box in boxes),
                        max(box[2] for box in boxes),
                        max(box[3] for box in boxes),
                    ),
                    "rotation": (
                        math.degrees(math.atan2(-direction_y, direction_x)) % 360
                    ),
                }
            )
    return regions


def _to_text_object(word: _Word, rotation_regions: list[_RotationRegion]) -> TextObject:
    bbox = (word["x0"], word["top"], word["x1"], word["bottom"])
    rotation = _matching_rotation(bbox, rotation_regions)
    return TextObject(
        text=word["text"],
        x=word["x0"],
        y=word["top"],
        width=word["x1"] - word["x0"],
        height=word["bottom"] - word["top"],
        rotation=rotation,
        font_name=word["fontname"],
        font_size=word["size"],
    )


def _matching_rotation(
    word_bbox: tuple[float, float, float, float],
    regions: list[_RotationRegion],
) -> float:
    best_overlap = 0.0
    rotation = 0.0
    for region in regions:
        overlap = _intersection_area(word_bbox, region["bbox"])
        if overlap > best_overlap:
            best_overlap = overlap
            rotation = region["rotation"]
    return rotation


def _intersection_area(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    return width * height
