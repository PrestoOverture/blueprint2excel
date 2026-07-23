"""Parse fields from a classified title block."""

import re

from drawing_inspector.models import PageRegions, TextObject, TitleBlock

_DATE = re.compile(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}")


def parse_title_block(
    objects: list[TextObject], regions: PageRegions
) -> TitleBlock:
    """Extract the stable labelled fields in a drawing title block."""

    region = regions.title_block_bbox
    if region is None:
        return TitleBlock("", "", "", "", "")
    items = [item for item in objects if _inside(item, region)]
    return TitleBlock(
        drawing_number=_value_right_of(items, "图号"),
        part_name=_value_right_of(items, "名称"),
        material=_value_right_of(items, "材料", join_row=True),
        scale=_value_below(items, "比例"),
        date=_first_matching(items, _DATE),
    )


def _value_right_of(
    objects: list[TextObject], label: str, *, join_row: bool = False
) -> str:
    labels = [item for item in objects if label in item.text]
    if not labels:
        return ""
    anchor = labels[0]
    row = [
        item
        for item in objects
        if item is not anchor
        and item.x >= anchor.x + anchor.width - anchor.font_size
        and abs(_center_y(item) - _center_y(anchor))
        <= max(anchor.height, item.height)
    ]
    if not row:
        return ""
    ordered = sorted(row, key=lambda item: item.x)
    if not join_row:
        return ordered[0].text.strip()
    values: list[str] = []
    previous: TextObject | None = None
    for item in ordered:
        if previous is not None:
            gap = item.x - (previous.x + previous.width)
            if gap > max(previous.font_size, item.font_size):
                break
        values.append(item.text.strip())
        previous = item
    return " ".join(values)


def _value_below(objects: list[TextObject], label: str) -> str:
    labels = [item for item in objects if label in item.text]
    if not labels:
        return ""
    anchor = labels[0]
    candidates = [
        item
        for item in objects
        if item.y > anchor.y
        and abs((item.x + item.width / 2) - (anchor.x + anchor.width / 2))
        <= max(anchor.width, item.width)
    ]
    if not candidates:
        return ""
    return min(candidates, key=lambda item: item.y).text.strip()


def _first_matching(objects: list[TextObject], pattern: re.Pattern[str]) -> str:
    for item in objects:
        match = pattern.search(item.text)
        if match is not None:
            return match.group()
    return ""


def _inside(
    item: TextObject, bbox: tuple[float, float, float, float]
) -> bool:
    center_x = item.x + item.width / 2
    center_y = _center_y(item)
    return bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]


def _center_y(item: TextObject) -> float:
    return item.y + item.height / 2
