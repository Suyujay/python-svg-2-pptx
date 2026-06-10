"""
SVGParser - A module to parse SVG files into Canvas Document Schema JSON.

This package provides the SVGParser class and its specialized sub-parsers
to decompose SVG XML into a flat list of visual elements, text content, 
and connectors.
"""

from .core import SVGParser
from .utils import IDGenerator
from .text import TextParser
from .geometry import GeometryParser
from .styles import StyleParser
from .connectors import ConnectorParser
from .groups import GroupParser

__all__ = [
    "SVGParser",
    "IDGenerator",
    "TextParser",
    "GeometryParser",
    "StyleParser",
    "ConnectorParser",
    "GroupParser"
]
