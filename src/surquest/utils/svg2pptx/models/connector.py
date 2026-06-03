from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum
from .base import IRNode
from .canvas import Point
from .color import Color

class ArrowType(str, Enum):
    NONE = "none"
    TRIANGLE = "triangle"

class ConnectorType(str, Enum):
    STRAIGHT = "straight"
    ELBOW = "elbow"

@dataclass
class IRConnector(IRNode):
    connector_type: ConnectorType
    waypoints: Tuple[Point, ...]
    stroke: Color
    stroke_width_emu: int
    dashed: bool = False
    start_arrow: ArrowType = ArrowType.NONE
    end_arrow: ArrowType = ArrowType.NONE
    start_ref: Optional[str] = None
    end_ref: Optional[str] = None
