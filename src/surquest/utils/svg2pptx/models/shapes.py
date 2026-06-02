from dataclasses import dataclass, field
from typing import Optional, List

from .base import IRNode
from .canvas import Geometry, Point
from .color import Color

@dataclass
class IRRectangle(IRNode):
    geometry: Geometry
    fill: Optional[Color]
    stroke: Optional[Color]
    stroke_width_emu: int
    corner_radius_emu: int
    shape_id: Optional[str] = None

@dataclass
class IRInfoBox(IRNode):
    """Composite: a rectangle + child icons/lines/text."""
    rectangle: IRRectangle
    children: List[IRNode] = field(default_factory=list)

@dataclass
class IREllipse(IRNode):
    geometry: Geometry
    fill: Optional[Color]
    stroke: Optional[Color]
    stroke_width_emu: int
    shape_id: Optional[str] = None

@dataclass
class IRPolygon(IRNode):
    """Handles both polygon and polyline."""
    waypoints: List[Point]
    is_closed: bool
    fill: Optional[Color]
    stroke: Optional[Color]
    stroke_width_emu: int
    dashed: bool = False
    shape_id: Optional[str] = None

@dataclass
class IRGroup(IRNode):
    """A generic group of IR nodes."""
    children: List[IRNode] = field(default_factory=list)
    shape_id: Optional[str] = None
