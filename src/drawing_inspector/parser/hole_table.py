"""Parse hole features from a classified drawing table."""

import re

from drawing_inspector.models import HoleFeature, PageRegions, TextObject

_LABEL = re.compile(r"[A-Z]")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_THREAD = re.compile(r"M\d+")
_THROUGH_MARKERS = {"贯穿", "完全贯穿"}


def parse_hole_table(
    objects: list[TextObject], regions: PageRegions
) -> list[HoleFeature]:
    """Return hole-feature rows found in the classified table region."""

    if regions.table_bbox is None:
        return []

    table_objects = [
        item
        for item in objects
        if _is_unrotated(item) and _contains(regions.table_bbox, item)
    ]
    label_header = _header(table_objects, "标签")
    size_header = _header(table_objects, "大小")
    quantity_header = _header(table_objects, "数量")
    if label_header is None or size_header is None or quantity_header is None:
        return []

    label_size_boundary = (_center_x(label_header) + _center_x(size_header)) / 2
    size_quantity_boundary = (
        _center_x(size_header) + _center_x(quantity_header)
    ) / 2
    labels = sorted(
        (
            item
            for item in table_objects
            if _LABEL.fullmatch(item.text)
            and _center_x(item) < label_size_boundary
            and _center_y(item) > _center_y(label_header)
        ),
        key=_center_y,
    )

    features: list[HoleFeature] = []
    for index, label in enumerate(labels):
        top = (
            (_center_y(labels[index - 1]) + _center_y(label)) / 2
            if index
            else _center_y(label_header)
        )
        bottom = (
            (_center_y(label) + _center_y(labels[index + 1])) / 2
            if index + 1 < len(labels)
            else regions.table_bbox[3]
        )
        row_objects = [
            item
            for item in table_objects
            if top < _center_y(item) < bottom
        ]
        size_objects = [
            item
            for item in row_objects
            if label_size_boundary <= _center_x(item) < size_quantity_boundary
        ]
        quantity_objects = [
            item
            for item in row_objects
            if _center_x(item) >= size_quantity_boundary
        ]
        quantity = _quantity(quantity_objects)
        if size_objects and quantity is not None:
            features.append(
                _parse_row(label.text, size_objects, quantity)
            )
    return features


def _parse_row(
    label: str, objects: list[TextObject], quantity: int
) -> HoleFeature:
    lines = _group_lines(objects)
    thread_line = next(
        (
            line
            for line in lines
            if any(_THREAD.fullmatch(item.text) for item in line)
        ),
        None,
    )
    back_side = any(item.text == "背面" for item in objects)

    if thread_line is not None:
        pilot_line = next(line for line in lines if line is not thread_line)
        pilot_diameter, pilot_depth = _diameter_and_depth(pilot_line)
        thread_parts = [
            item.text
            for item in thread_line
            if _THREAD.fullmatch(item.text)
            or item.text == "-"
            or re.fullmatch(r"\d+H", item.text)
        ]
        return HoleFeature(
            label=label,
            hole_type="threaded",
            primary_diameter=pilot_diameter,
            depth=pilot_depth,
            counterbore_diameter=None,
            counterbore_depth=None,
            thread_spec=" ".join(thread_parts),
            pilot_hole=pilot_diameter,
            quantity=quantity,
            back_side=back_side,
        )

    first_diameter, first_depth = _diameter_and_depth(lines[0])
    if len(lines) == 1:
        return HoleFeature(
            label,
            "through",
            first_diameter,
            first_depth,
            None,
            None,
            None,
            None,
            quantity,
            back_side,
        )

    second_diameter, second_depth = _diameter_and_depth(lines[1])
    return HoleFeature(
        label,
        "counterbore",
        first_diameter,
        first_depth,
        second_diameter,
        _numeric_depth(second_depth),
        None,
        None,
        quantity,
        back_side,
    )


def _group_lines(objects: list[TextObject]) -> list[list[TextObject]]:
    lines: list[list[TextObject]] = []
    for item in sorted(objects, key=lambda obj: (_center_y(obj), obj.x)):
        if not lines or abs(_center_y(item) - _center_y(lines[-1][0])) > 2.0:
            lines.append([item])
        else:
            lines[-1].append(item)
    return lines


def _diameter_and_depth(line: list[TextObject]) -> tuple[float, float | str]:
    values = [
        item.text
        for item in sorted(line, key=lambda obj: obj.x)
        if _NUMBER.fullmatch(item.text) or item.text in _THROUGH_MARKERS
    ]
    diameter = float(values[0])
    depth_text = values[-1]
    depth: float | str = (
        depth_text if depth_text in _THROUGH_MARKERS else float(depth_text)
    )
    return diameter, depth


def _numeric_depth(depth: float | str) -> float:
    if isinstance(depth, str):
        raise ValueError("counterbore depth must be numeric")
    return depth


def _quantity(objects: list[TextObject]) -> int | None:
    for item in objects:
        if item.text.isdigit():
            return int(item.text)
    return None


def _header(objects: list[TextObject], text: str) -> TextObject | None:
    return next((item for item in objects if item.text == text), None)


def _contains(
    bbox: tuple[float, float, float, float], item: TextObject
) -> bool:
    return (
        bbox[0] <= _center_x(item) <= bbox[2]
        and bbox[1] <= _center_y(item) <= bbox[3]
    )


def _is_unrotated(item: TextObject) -> bool:
    return min(item.rotation % 360, 360 - item.rotation % 360) < 1.0


def _center_x(item: TextObject) -> float:
    return item.x + item.width / 2


def _center_y(item: TextObject) -> float:
    return item.y + item.height / 2
