import re
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any, Tuple

def strip_default_namespace(svg_text: str) -> str:
    """
    Remove the root xmlns declaration from an SVG string.
    This prevents ElementTree from prefixing every tag with a namespace URI,
    making tag-based lookups simpler.
    """
    return re.sub(r'\sxmlns="[^"]+"', "", svg_text, count=1)

def localname(tag: str) -> str:
    """
    Strip any namespace prefix from an XML tag.
    Example: '{http://www.w3.org/2000/svg}rect' -> 'rect'
    """
    return tag.split("}")[-1] if "}" in tag else tag

def f(value: Optional[str], default: float = 0.0) -> float:
    """
    Safely convert a string (possibly None or malformed) to a float.
    
    Args:
        value: The string to convert.
        default: Fallback value if conversion fails.
    """
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default

def element_to_string(el: ET.Element) -> str:
    """
    Manually serialize an ElementTree element back to an SVG/XML string.
    Used for embedding inner SVG content into schema elements.
    """
    tag = localname(el.tag)
    attrs = " ".join(f'{k}="{v}"' for k, v in el.attrib.items())
    attr_str = (" " + attrs) if attrs else ""
    children = "".join(element_to_string(c) for c in list(el))
    text = el.text or ""
    
    if children or text.strip():
        return f"<{tag}{attr_str}>{text}{children}</{tag}>"
    return f"<{tag}{attr_str}/>"

class IDGenerator:
    """
    Management of unique identifiers within a single parsing session.
    Ensures that auto-generated IDs do not collide with existing SVG IDs.
    """
    
    def __init__(self):
        self._id_counter = 0
        self._used_ids = set()

    def gen_id(self, prefix: str = "elem") -> str:
        """Generate a new unique ID with the given prefix."""
        while True:
            self._id_counter += 1
            new_id = f"{prefix}-{self._id_counter}"
            if new_id not in self._used_ids:
                self._used_ids.add(new_id)
                return new_id

    def register_id(self, _id: str) -> str:
        """Record an existing ID as taken."""
        self._used_ids.add(_id)
        return _id

    def is_used(self, _id: str) -> bool:
        """Check if an ID has already been assigned."""
        return _id in self._used_ids
