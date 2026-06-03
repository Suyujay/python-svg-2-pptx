from dataclasses import dataclass
from typing import Optional
from .base import IRNode
from .canvas import Geometry
from .color import Color

@dataclass
class IRRectangle(IRNode):
    geometry: Geometry
    fill: Optional[Color]
    stroke: Optional[Color]
    stroke_width_emu: int
    corner_radius_emu: int
    dashed: bool = False
    shape_id: Optional[str] = None
