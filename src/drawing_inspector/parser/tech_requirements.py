"""Parse numbered technical requirements within their classified region."""

import re

from drawing_inspector.models import PageRegions, TechRequirements, TextObject

_NUMBERED_ITEM = re.compile(r"^\d+\.")
_TOLERANCE = re.compile(r"GB[-\s]?\d+[-\s]?[A-Za-z]+\b", re.IGNORECASE)


def parse_tech_requirements(
    objects: list[TextObject], regions: PageRegions
) -> TechRequirements:
    """Reconstruct numbered rows without relying on PDF stream order."""

    region = regions.tech_requirements_bbox
    if region is None:
        return TechRequirements([], None)
    candidates = [
        item
        for item in objects
        if _inside(item, region) and "技术要求" not in item.text
    ]
    rows = _group_rows(candidates)
    items = [
        "".join(item.text.strip() for item in row)
        for row in rows
        if row and _NUMBERED_ITEM.match(row[0].text.strip())
    ]
    combined = " ".join(items)
    tolerance_match = _TOLERANCE.search(combined)
    return TechRequirements(
        items=items,
        tolerance_standard=tolerance_match.group() if tolerance_match else None,
    )


def _group_rows(objects: list[TextObject]) -> list[list[TextObject]]:
    rows: list[list[TextObject]] = []
    for item in sorted(objects, key=lambda obj: (_center_y(obj), obj.x)):
        for row in rows:
            reference = row[0]
            if abs(_center_y(item) - _center_y(reference)) <= max(
                item.height, reference.height
            ) / 2:
                row.append(item)
                break
        else:
            rows.append([item])
    return [sorted(row, key=lambda item: item.x) for row in rows]


def _inside(
    item: TextObject, bbox: tuple[float, float, float, float]
) -> bool:
    center_x = item.x + item.width / 2
    center_y = _center_y(item)
    return bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]


def _center_y(item: TextObject) -> float:
    return item.y + item.height / 2
