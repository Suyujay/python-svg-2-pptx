SVG_NS = "http://www.w3.org/2000/svg"

# SVG marker id -> schema arrow enum
MARKER_MAP = {
    "none": "NONE",
    "arrow": "CLASSIC",
    "diamond": "BLOCK",
    "stealth": "OPEN",
}

CONNECTOR_TYPE_MAP = {
    "straight": "STRAIGHT",
    "elbow": "ORTHOGONAL",
    "curve": "CURVED",
}

SIZE_COEFFICIENT = {
    'textbox': {
        'width': 1.2
    }
}
