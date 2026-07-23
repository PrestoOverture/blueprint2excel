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
