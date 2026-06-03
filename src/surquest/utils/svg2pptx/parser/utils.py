import re
from typing import Tuple, List, Optional
from xml.etree import ElementTree as ET
from pptx.util import Emu
from pptx.enum.text import PP_ALIGN

from ..models import (
    IRSlide, IRNode, IRRectangle, IRIcon, IRText, IRLine, IRConnector, IRInfoBox, IRGroup,
    IREllipse, IRPolygon,
    Geometry, Color, FontStyle, TextRun, TextBlock, Point, ArrowType, ConnectorType
)

class CoordinateNormalizer:
    """Converts SVG viewbox units to EMU."""

    def __init__(self, viewbox: Tuple[float, float, float, float],
                 target_width: int, target_height: int):
        _, _, vb_w, vb_h = viewbox
        self.scale_x = target_width / vb_w
        self.scale_y = target_height / vb_h
        self.offset_x = -viewbox[0] * self.scale_x
        self.offset_y = -viewbox[1] * self.scale_y

    def x(self, v: float) -> Emu:
        return Emu(int(v * self.scale_x + self.offset_x))

    def y(self, v: float) -> Emu:
        return Emu(int(v * self.scale_y + self.offset_y))

    def w(self, v: float) -> Emu:
        return Emu(int(v * self.scale_x))

    def h(self, v: float) -> Emu:
        return Emu(int(v * self.scale_y))

    def pt(self, v: float) -> float:
        """Convert SVG font-size (px) to PowerPoint points (approx scale)."""
        avg = (self.scale_x + self.scale_y) / 2
        emu_per_pt = 12700
        return (v * avg) / emu_per_pt

def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag

CSS_COLORS = {
    "black": "#000000", "silver": "#c0c0c0", "gray": "#808080", "white": "#ffffff",
    "maroon": "#800000", "red": "#ff0000", "purple": "#800080", "fuchsia": "#ff00ff",
    "green": "#008000", "lime": "#00ff00", "olive": "#808000", "yellow": "#ffff00",
    "navy": "#000080", "blue": "#0000ff", "teal": "#008080", "aqua": "#00ffff",
    "orange": "#ffa500", "brown": "#a52a2a", "transparent": "none", "none": "none"
}

def _parse_color(value: Optional[str]) -> Optional[Color]:
    if not value:
        return None
    v = value.strip().lower()
    if v in ("none", "transparent"):
        return None
    if v in CSS_COLORS:
        v = CSS_COLORS[v]
        if v == "none":
            return None
    if v.startswith("#"):
        return Color.from_hex(v)
    if v.startswith("rgb("):
        m = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", v)
        if m:
            return Color(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

def _parse_float(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    m = re.match(r"-?\d*\.?\d+", value.strip())
    return float(m.group()) if m else default

def _parse_dash(value: Optional[str]) -> bool:
    return value is not None and value.strip() not in ("", "none")

