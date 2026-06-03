from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from pptx.util import Emu

from .base import IRNode

@dataclass(frozen=True)
class Geometry:
    """Normalized geometry in EMU."""
    x: Emu
    y: Emu
    width: Emu
    height: Emu

@dataclass(frozen=True)
class Point:
    x: Emu
    y: Emu

@dataclass
class IRSlide:
    width_emu: int
    height_emu: int
    nodes: List[IRNode] = field(default_factory=list)
