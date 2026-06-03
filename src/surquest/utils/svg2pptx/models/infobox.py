from dataclasses import dataclass, field
from typing import List
from .base import IRNode
from .rectangle import IRRectangle

@dataclass
class IRInfoBox(IRNode):
    """Composite: a rectangle + child icons/lines/text."""
    rectangle: IRRectangle
    children: List[IRNode] = field(default_factory=list)
