"""Reassemble fragmented engineering-drawing annotations."""

import re
from dataclasses import replace

from drawing_inspector.models import Dimension, TextObject

ROTATION_TOLERANCE_DEGREES = 5.0
ROTATED_X_TOLERANCE = 1.0
ROTATED_GAP_FONT_FACTOR = 2.0
_NOMINAL_PATTERN = re.compile(
    r"^\s*(?P<prefix>[⌀ΦØφRr]?)(?P<value>\d+(?:\.\d+)?)"
    r"(?P<degree>°?)(?:\s+(?P<grade>[A-Za-z]+\d+))?\s*$"
)
_SYMMETRIC_PATTERN = re.compile(
    r"^\s*(?P<nominal>[⌀ΦØφRr]?\d+(?:\.\d+)?°?)"
    r"\s*±\s*(?P<tolerance>\d+(?:\.\d+)?)\s*$"
)
_SYMMETRIC_FRAGMENT_PATTERN = re.compile(r"^\s*±\s*(\d+(?:\.\d+)?)\s*$")
_DEVIATION_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
TOLERANCE_VERTICAL_FONT_FACTOR = 2.0
TOLERANCE_HORIZONTAL_FONT_FACTOR = 1.0
MAX_DEVIATION_ABSOLUTE_FLOOR = 2.0
MAX_DEVIATION_NOMINAL_FACTOR = 0.1


def classify_dimension_type(text: str) -> str:
    """Classify a dimension from its conventional prefix or suffix."""

    stripped = text.strip()
    if stripped.startswith(("⌀", "Φ", "Ø", "φ")):
        return "diameter"
    if stripped.startswith(("R", "r")):
        return "radius"
    if "°" in stripped:
        return "angle"
    return "linear"


def reassemble_dimensions(objects: list[TextObject]) -> list[Dimension]:
    """Parse plain, symmetric, and vertically stacked dimensions."""

    dimensions: list[Dimension] = []
    consumed: set[int] = set()
    for index, item in enumerate(objects):
        if not _is_dimension_rotation(item):
            continue
        symmetric = _SYMMETRIC_PATTERN.fullmatch(item.text)
        if symmetric is None:
            continue
        tolerance = float(symmetric.group("tolerance"))
        dimensions.append(
            _make_dimension(
                item, symmetric.group("nominal"), tolerance, -tolerance
            )
        )
        consumed.add(index)

    nominal_indexes = [
        index
        for index, item in enumerate(objects)
        if index not in consumed
        and _is_dimension_rotation(item)
        and _NOMINAL_PATTERN.fullmatch(item.text) is not None
    ]
    for index in nominal_indexes:
        if index in consumed:
            continue
        nominal = objects[index]
        inline = _find_inline_tolerance(index, nominal, objects, consumed)
        if inline is not None:
            tolerance_index, tolerance = inline
            dimensions.append(
                _make_dimension(nominal, nominal.text, tolerance, -tolerance)
            )
            consumed.update((index, tolerance_index))
            continue
        stacked = _find_stacked_tolerance(index, nominal, objects, consumed)
        if stacked is not None:
            upper, lower, fragment_indexes = stacked
            dimensions.append(_make_dimension(nominal, nominal.text, upper, lower))
            consumed.add(index)
            consumed.update(fragment_indexes)

    for index in nominal_indexes:
        if index not in consumed:
            item = objects[index]
            dimensions.append(_make_dimension(item, item.text, None, None))
    return dimensions


def _make_dimension(
    item: TextObject,
    nominal_text: str,
    upper_deviation: float | None,
    lower_deviation: float | None,
) -> Dimension:
    match = _NOMINAL_PATTERN.fullmatch(nominal_text)
    if match is None:
        raise ValueError(f"Invalid nominal dimension: {nominal_text!r}")
    return Dimension(
        nominal=float(match.group("value")),
        upper_deviation=upper_deviation,
        lower_deviation=lower_deviation,
        tolerance_grade=match.group("grade"),
        dimension_type=classify_dimension_type(nominal_text),
        x=item.x,
        y=item.y,
        bubble_id=None,
    )


def _is_dimension_rotation(item: TextObject) -> bool:
    normalized = item.rotation % 360
    return any(
        _rotation_distance(normalized, allowed) <= ROTATION_TOLERANCE_DEGREES
        for allowed in (0.0, 90.0, 270.0)
    )


def _rotations_match(first: TextObject, second: TextObject) -> bool:
    return (
        _rotation_distance(first.rotation % 360, second.rotation % 360)
        <= ROTATION_TOLERANCE_DEGREES
    )


def _rotation_distance(first: float, second: float) -> float:
    difference = abs(first - second)
    return min(difference, 360 - difference)


def _find_inline_tolerance(
    nominal_index: int,
    nominal: TextObject,
    objects: list[TextObject],
    consumed: set[int],
) -> tuple[int, float] | None:
    nominal_center_y = nominal.y + nominal.height / 2
    for index, item in enumerate(objects):
        if (
            index == nominal_index
            or index in consumed
            or not _rotations_match(nominal, item)
        ):
            continue
        match = _SYMMETRIC_FRAGMENT_PATTERN.fullmatch(item.text)
        if match is None:
            continue
        font_size = max(nominal.font_size, item.font_size)
        item_center_y = item.y + item.height / 2
        horizontal_gap = item.x - (nominal.x + nominal.width)
        if (
            abs(item_center_y - nominal_center_y) <= font_size / 2
            and -font_size
            <= horizontal_gap
            <= TOLERANCE_HORIZONTAL_FONT_FACTOR * font_size
        ):
            return index, float(match.group(1))
    return None


def _find_stacked_tolerance(
    nominal_index: int,
    nominal: TextObject,
    objects: list[TextObject],
    consumed: set[int],
) -> tuple[float, float, set[int]] | None:
    upper: list[tuple[int, TextObject]] = []
    lower: list[tuple[int, TextObject]] = []
    for index, item in enumerate(objects):
        font_size = max(nominal.font_size, item.font_size)
        if (
            index == nominal_index
            or index in consumed
            or not _rotations_match(nominal, item)
            or abs(item.y - nominal.y)
            >= TOLERANCE_VERTICAL_FONT_FACTOR * font_size
        ):
            continue
        if item.y < nominal.y:
            upper.append((index, item))
        elif item.y > nominal.y:
            lower.append((index, item))
    upper = _connected_tolerance_row(nominal, upper)
    lower = _connected_tolerance_row(nominal, lower)
    if not upper or not lower:
        return None
    upper_text = "".join(
        item.text for _, item in sorted(upper, key=lambda pair: pair[1].x)
    )
    lower_text = "".join(
        item.text for _, item in sorted(lower, key=lambda pair: pair[1].x)
    )
    if (
        _DEVIATION_PATTERN.fullmatch(upper_text) is None
        or _DEVIATION_PATTERN.fullmatch(lower_text) is None
    ):
        return None
    nominal_match = _NOMINAL_PATTERN.fullmatch(nominal.text)
    if nominal_match is None:
        return None
    upper_value = float(upper_text)
    lower_value = float(lower_text)
    max_deviation = max(
        MAX_DEVIATION_ABSOLUTE_FLOOR,
        MAX_DEVIATION_NOMINAL_FACTOR * float(nominal_match.group("value")),
    )
    if abs(upper_value) > max_deviation or abs(lower_value) > max_deviation:
        return None
    return (
        upper_value,
        lower_value,
        {index for index, _ in upper + lower},
    )


def _connected_tolerance_row(
    nominal: TextObject,
    candidates: list[tuple[int, TextObject]],
) -> list[tuple[int, TextObject]]:
    ordered = sorted(candidates, key=lambda pair: pair[1].x)
    start = next(
        (
            position
            for position, (_, item) in enumerate(ordered)
            if abs(item.x - nominal.x)
            <= TOLERANCE_HORIZONTAL_FONT_FACTOR
            * max(nominal.font_size, item.font_size)
        ),
        None,
    )
    if start is None:
        return []
    row = [ordered[start]]
    for candidate in ordered[start + 1 :]:
        previous = row[-1][1]
        item = candidate[1]
        gap = item.x - (previous.x + previous.width)
        if gap > TOLERANCE_HORIZONTAL_FONT_FACTOR * max(
            previous.font_size, item.font_size
        ):
            break
        row.append(candidate)
    return row


def restore_rotated_text(objects: list[TextObject]) -> list[TextObject]:
    """Restore axis-aligned vertical text while leaving other angles unchanged."""

    clusters: list[list[tuple[int, TextObject]]] = []
    untouched: list[tuple[int, TextObject]] = []

    for index, item in enumerate(objects):
        orientation = _axis_orientation(item.rotation)
        if orientation is None:
            untouched.append((index, item))
            continue

        for cluster in clusters:
            first = cluster[0][1]
            if (
                _axis_orientation(first.rotation) == orientation
                and abs(first.rotation - item.rotation) <= ROTATION_TOLERANCE_DEGREES
                and abs(first.x - item.x) <= ROTATED_X_TOLERANCE
            ):
                cluster.append((index, item))
                break
        else:
            clusters.append([(index, item)])

    restored: list[tuple[int, TextObject]] = untouched
    for same_axis in clusters:
        for cluster in _split_at_vertical_gaps(same_axis):
            restored.append(
                (min(index for index, _ in cluster), _merge_rotated_cluster(cluster))
            )

    return [item for _, item in sorted(restored, key=lambda pair: pair[0])]


def _axis_orientation(rotation: float) -> int | None:
    normalized = rotation % 360
    if abs(normalized - 90.0) <= ROTATION_TOLERANCE_DEGREES:
        return 90
    if abs(normalized - 270.0) <= ROTATION_TOLERANCE_DEGREES:
        return 270
    return None


def _split_at_vertical_gaps(
    items: list[tuple[int, TextObject]],
) -> list[list[tuple[int, TextObject]]]:
    ordered = sorted(items, key=lambda pair: pair[1].y)
    result: list[list[tuple[int, TextObject]]] = []
    for indexed_item in ordered:
        if not result:
            result.append([indexed_item])
            continue
        previous = result[-1][-1][1]
        current = indexed_item[1]
        gap = current.y - (previous.y + previous.height)
        maximum_gap = ROTATED_GAP_FONT_FACTOR * max(
            previous.font_size, current.font_size
        )
        if gap <= maximum_gap:
            result[-1].append(indexed_item)
        else:
            result.append([indexed_item])
    return result


def _merge_rotated_cluster(
    cluster: list[tuple[int, TextObject]],
) -> TextObject:
    items = [item for _, item in cluster]
    orientation = _axis_orientation(items[0].rotation)
    ordered = sorted(items, key=lambda item: item.y, reverse=orientation == 270)
    merged_text = "".join(item.text for item in ordered)[::-1]
    left = min(item.x for item in items)
    top = min(item.y for item in items)
    right = max(item.x + item.width for item in items)
    bottom = max(item.y + item.height for item in items)
    return replace(
        items[0],
        text=merged_text,
        x=left,
        y=top,
        width=right - left,
        height=bottom - top,
        font_size=max(item.font_size for item in items),
    )
