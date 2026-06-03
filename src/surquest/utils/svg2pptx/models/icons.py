from dataclasses import dataclass

from .base import IRNode
from .canvas import Geometry

@dataclass
class IRIcon(IRNode):
    geometry: Geometry
    svg_bytes: bytes
