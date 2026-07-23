"""Structured parsers for engineering-drawing page regions."""

from drawing_inspector.parser.regions import classify_regions
from drawing_inspector.parser.tech_requirements import parse_tech_requirements
from drawing_inspector.parser.title_block import parse_title_block

__all__ = [
    "classify_regions",
    "parse_tech_requirements",
    "parse_title_block",
]
