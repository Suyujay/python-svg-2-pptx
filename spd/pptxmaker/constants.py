"""Constants and mappings for PPTXMaker."""

from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR_TYPE
from pptx.enum.text import PP_ALIGN


# Mapping from schema geometry types to PPTX shape enum types
GEOMETRY_MAP = {
    "RECTANGLE": MSO_SHAPE.RECTANGLE,
    "ROUNDED_RECTANGLE": MSO_SHAPE.ROUNDED_RECTANGLE,
    "ELLIPSE": MSO_SHAPE.OVAL,
    "DIAMOND": MSO_SHAPE.DIAMOND,
    "TRIANGLE": MSO_SHAPE.ISOSCELES_TRIANGLE,
    "CYLINDER": MSO_SHAPE.CAN,
    "DOCUMENT": MSO_SHAPE.FLOWCHART_DOCUMENT,
}

# Mapping from schema text alignment names to PPTX paragraph alignment enums
ALIGN_MAP = {
    "LEFT": PP_ALIGN.LEFT,
    "CENTER": PP_ALIGN.CENTER,
    "RIGHT": PP_ALIGN.RIGHT,
    "JUSTIFY": PP_ALIGN.JUSTIFY,
}

# Mapping from schema vertical anchor alignments to oxml anchor attribute values
VANCHOR_MAP = {"TOP": "t", "MIDDLE": "ctr", "BOTTOM": "b"}

# Mapping from schema line dash styles to PPTX line dash style enums
DASH_MAP = {
    "SOLID": MSO_LINE_DASH_STYLE.SOLID,
    "DASHED": MSO_LINE_DASH_STYLE.DASH,
    "DOTTED": MSO_LINE_DASH_STYLE.ROUND_DOT,
}

# Mapping from schema connector routing modes to PPTX connector type enums
CONNECTOR_MAP = {
    "STRAIGHT": MSO_CONNECTOR_TYPE.STRAIGHT,
    "ORTHOGONAL": MSO_CONNECTOR_TYPE.ELBOW,
    "CURVED": MSO_CONNECTOR_TYPE.CURVE,
}

# Mapping from schema arrow types to oxml arrowhead attribute values
ARROW_MAP = {"NONE": None, "CLASSIC": "triangle", "BLOCK": "triangle", "OPEN": "arrow"}

# Mapping from schema measurement units to PPTX English Metric Units (EMU) conversion factors
EMU_PER_UNIT = {"inches": 914400, "pixels": 9525, "cm": 360000, "points": 12700}

# Mapping from port positions to proportional bounding box offsets (X multiplier, Y multiplier)
PORT_MAP = {
    "TOP": (0.5, 0.0),
    "RIGHT": (1.0, 0.5),
    "BOTTOM": (0.5, 1.0),
    "LEFT": (0.0, 0.5),
    "CENTER": (0.5, 0.5),
}

# Mapping from semantic port positions to internal connection site indices for a rectangle
PORT_IDX_MAP = {
    "TOP": 0,
    "RIGHT": 3,
    "BOTTOM": 2,
    "LEFT": 1,
    "CENTER": 0,
}
