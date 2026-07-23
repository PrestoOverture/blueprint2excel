"""Classify drawing regions from positioned semantic anchors."""

import re

from drawing_inspector.models import PageRegions, TextObject

_NUMBERED_ITEM = re.compile(r"^\d+\.")
_TITLE_ANCHORS = ("图号", "材料", "名称")
_TABLE_HEADERS = ("标签", "大小", "数量")


def classify_regions(
    objects: list[TextObject], page_width: float, page_height: float
) -> PageRegions:
    """Locate structured regions and leave the upper page as the drawing area."""

    title_anchors = _matching(objects, _TITLE_ANCHORS)
    tech_heading = [item for item in objects if "技术要求" in item.text]
    tech_items = [item for item in objects if _NUMBERED_ITEM.match(item.text)]
    table_headers = _table_header_anchors(objects)

    title_bbox = _title_bbox(objects, title_anchors, page_width, page_height)
    tech_bbox = _tech_bbox(
        objects, tech_heading, tech_items, page_width, page_height
    )
    table_bbox = _table_bbox(
        table_headers, title_bbox, page_width, page_height
    )

    lower_tops = [
        bbox[1] for bbox in (title_bbox, tech_bbox) if bbox is not None
    ]
    drawing_bottom = min(lower_tops) if lower_tops else page_height
    drawing_bbox = (0.0, 0.0, page_width, drawing_bottom)
    return PageRegions(table_bbox, title_bbox, tech_bbox, drawing_bbox)


def _matching(objects: list[TextObject], anchors: tuple[str, ...]) -> list[TextObject]:
    return [item for item in objects if any(anchor in item.text for anchor in anchors)]


def _table_header_anchors(objects: list[TextObject]) -> list[TextObject]:
    candidates = _matching(objects, _TABLE_HEADERS)
    for quantity in (item for item in candidates if "数量" in item.text):
        same_row = [
            item
            for item in candidates
            if abs(_center_y(item) - _center_y(quantity))
            <= max(item.height, quantity.height)
        ]
        if all(
            any(header in item.text for item in same_row)
            for header in _TABLE_HEADERS
        ):
            return same_row
    return []


def _title_bbox(
    objects: list[TextObject],
    anchors: list[TextObject],
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float] | None:
    if not anchors:
        return None
    top = max(0.0, min(item.y for item in anchors) - _padding(anchors))
    lower_right = [
        item
        for item in objects
        if item.y >= top and item.x >= page_width * 0.35
    ]
    if not lower_right:
        return None
    padding = _padding(lower_right)
    return (
        max(0.0, min(item.x for item in lower_right) - padding),
        top,
        min(page_width, max(_right(item) for item in lower_right) + padding),
        page_height,
    )


def _tech_bbox(
    objects: list[TextObject],
    headings: list[TextObject],
    numbered_items: list[TextObject],
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float] | None:
    if not headings or not numbered_items:
        return None
    heading = min(headings, key=lambda item: item.y)
    numbered_items = [
        item
        for item in numbered_items
        if item.y > heading.y
        and item.x <= heading.x + page_width * 0.25
    ]
    if not numbered_items:
        return None
    last_item_bottom = max(_bottom(item) for item in numbered_items)
    content_right = max(_right(item) for item in numbered_items) + 3 * heading.height
    related = [
        item
        for item in objects
        if item.x <= content_right
        and item.y >= heading.y - heading.height
        and _bottom(item) <= last_item_bottom + item.height
    ]
    padding = _padding(related)
    return (
        max(0.0, min(item.x for item in related) - padding),
        max(0.0, min(item.y for item in related) - padding),
        min(page_width, content_right),
        min(page_height, max(_bottom(item) for item in related) + padding),
    )


def _table_bbox(
    headers: list[TextObject],
    title_bbox: tuple[float, float, float, float] | None,
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float] | None:
    if not headers:
        return None
    padding = _padding(headers)
    bottom = title_bbox[1] if title_bbox is not None else page_height
    return (
        max(0.0, min(item.x for item in headers) - padding),
        max(0.0, min(item.y for item in headers) - padding),
        min(page_width, max(_right(item) for item in headers) + padding),
        bottom,
    )


def _padding(objects: list[TextObject]) -> float:
    return max((item.height for item in objects), default=1.0)


def _right(item: TextObject) -> float:
    return item.x + item.width


def _bottom(item: TextObject) -> float:
    return item.y + item.height


def _center_y(item: TextObject) -> float:
    return item.y + item.height / 2
