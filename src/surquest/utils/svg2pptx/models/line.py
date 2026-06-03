from dataclasses import dataclass
from .base import IRNode
from .canvas import Point
from .color import Color

@dataclass
class IRLine(IRNode):
    """Decorative line (legend swatch, etc.)."""
    start: Point
    end: Point
    stroke: Color
    stroke_width_emu: int
    dashed: bool = False
