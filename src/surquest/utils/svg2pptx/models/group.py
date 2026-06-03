from dataclasses import dataclass, field
from typing import List, Optional
from .base import IRNode

@dataclass
class IRGroup(IRNode):
    """A generic group of IR nodes."""
    children: List[IRNode] = field(default_factory=list)
    shape_id: Optional[str] = None
