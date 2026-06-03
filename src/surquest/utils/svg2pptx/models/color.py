from dataclasses import dataclass
from pptx.dml.color import RGBColor

@dataclass(frozen=True)
class Color:
    """Normalized RGB color."""
    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, value: str) -> "Color":
        v = value.strip().lstrip("#")
        if len(v) == 3:
            v = "".join(c * 2 for c in v)
        return cls(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

    def to_rgb(self) -> RGBColor:
        return RGBColor(self.r, self.g, self.b)
