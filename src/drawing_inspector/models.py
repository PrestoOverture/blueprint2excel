from dataclasses import dataclass


@dataclass
class TextObject:
    """PDF中的一个文字对象"""

    text: str
    x: float
    y: float
    width: float
    height: float
    rotation: float
    font_name: str
    font_size: float


@dataclass
class Dimension:
    """A complete dimension annotation."""

    nominal: float
    upper_deviation: float | None
    lower_deviation: float | None
    tolerance_grade: str | None
    dimension_type: str
    x: float
    y: float
    bubble_id: int | None


@dataclass
class PageRegions:
    table_bbox: tuple[float, float, float, float] | None
    title_block_bbox: tuple[float, float, float, float] | None
    tech_requirements_bbox: tuple[float, float, float, float] | None
    drawing_bbox: tuple[float, float, float, float]


@dataclass
class TitleBlock:
    drawing_number: str
    part_name: str
    material: str
    scale: str
    date: str


@dataclass
class TechRequirements:
    items: list[str]
    tolerance_standard: str | None
