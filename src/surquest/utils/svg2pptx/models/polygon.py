from dataclasses import dataclass
from typing import List, Optional
from .base import IRNode
from .canvas import Point
from .color import Color

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
