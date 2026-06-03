from dataclasses import dataclass, field
from typing import Tuple, Optional
from pptx.util import Emu
from pptx.enum.text import PP_ALIGN

from .base import IRNode
from .canvas import Geometry
from .color import Color

@dataclass(frozen=True)
class FontStyle:
    family: str = "Calibri"
    size_pt: float = 12.0
    bold: bool = False
    italic: bool = False
    color: Color = field(default_factory=lambda: Color(0, 0, 0))

@dataclass(frozen=True)
class TextRun:
    text: str
    font: FontStyle
    line_break_before: bool = False

@dataclass(frozen=True)
class TextBlock:
    """Resolved hierarchical text element."""
    runs: Tuple[TextRun, ...]
    anchor_x: Emu
    anchor_y: Emu
    alignment: PP_ALIGN = PP_ALIGN.LEFT

@dataclass
class IRText(IRNode):
    block: TextBlock
    container_geometry: Optional[Geometry] = None
