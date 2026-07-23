"""Parse dimensions from the unstructured drawing area."""

from drawing_inspector.models import Dimension, PageRegions, TextObject
from drawing_inspector.reassembler import reassemble_dimensions, restore_rotated_text


def parse_dimensions(
    objects: list[TextObject], regions: PageRegions
) -> list[Dimension]:
    """Return dimensions outside the page's structured regions."""

    excluded = (
        regions.table_bbox,
        regions.title_block_bbox,
        regions.tech_requirements_bbox,
    )
    drawing_objects = [
        item
        for item in objects
        if _inside(item, regions.drawing_bbox)
        and not any(
            region is not None and _inside(item, region) for region in excluded
        )
    ]
    return reassemble_dimensions(restore_rotated_text(drawing_objects))


def _inside(
    item: TextObject, bbox: tuple[float, float, float, float]
) -> bool:
    center_x = item.x + item.width / 2
    center_y = item.y + item.height / 2
    return bbox[0] <= center_x <= bbox[2] and bbox[1] <= center_y <= bbox[3]
