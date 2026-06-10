import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any, Tuple
from .utils import strip_default_namespace, localname, f, IDGenerator
from .geometry import GeometryParser
from .styles import StyleParser
from .text import TextParser
from .connectors import ConnectorParser
from .groups import GroupParser

class SVGParser:
    """
    Main parser class for converting SVG files into the Canvas Document JSON schema.
    
    This parser handles standard SVG shapes, paths, text, and connectors,
    translating them into a format used by PPTXMaker.
    """
    
    def __init__(self, title: str = "Untitled", base_unit: str = "pixels"):
        """
        Initialize the parser.
        
        Args:
            title: Title of the document.
            base_unit: Unit system (e.g., 'pixels').
        """
        self.title = title
        self.base_unit = base_unit
        self.id_gen = IDGenerator()

    def parse_file(self, path: str) -> Dict[str, Any]:
        """
        Load an SVG file from disk and parse it.
        
        Args:
            path: Path to the .svg file.
            
        Returns:
            A dictionary following the Canvas Document Schema.
        """
        with open(path, "r", encoding="utf-8") as f:
            return self.parse_string(f.read())

    def parse_string(self, svg_text: str) -> Dict[str, Any]:
        """
        Parse an SVG string and convert it to JSON format.
        
        Args:
            svg_text: Complete SVG XML source as a string.
            
        Returns:
            The parsed document dictionary.
        """
        # Remove default namespaces to simplify XPath/tag lookups
        svg_text = strip_default_namespace(svg_text)
        root = ET.fromstring(svg_text)

        width, height = self._parse_root_dimensions(root)
        elements: List[Dict[str, Any]] = []
        global_texts = []

        # Iterate through top-level elements
        for child in list(root):
            tag = localname(child.tag)
            
            # Skip architectural tags
            if tag == "defs":
                continue
            
            # Lines and polylines might be "connectors" or "simple shapes"
            elif tag in ("line", "polyline"):
                if ConnectorParser.is_connector(child):
                    elements.append(ConnectorParser.parse_connector(child, self.id_gen))
                else:
                    node = self._parse_shape_like(child)
                    if node:
                        elements.append(node)
            
            elif tag == "text":
                global_texts.append(child)
            
            elif tag == "g":
                # Groups return both visual elements and texts for later association
                grp_elems, grp_texts = GroupParser.parse_group(child, self.id_gen, self._parse_shape_like)
                elements.extend(grp_elems)
                global_texts.extend(grp_texts)
            
            elif tag in ("rect", "ellipse", "circle", "polygon", "path"):
                node = self._parse_shape_like(child)
                if node:
                    elements.append(node)

        # Post-processing: associate un-attached text nodes with the nearest shape
        all_shapes = [e for e in elements if e.get("type") in ("shape", "svg_polygon", "svg_path", "svg_line")]
        leftover_standalone = TextParser.associate_text(all_shapes, global_texts, self.id_gen, fallback_to_standalone=True)
        elements.extend(leftover_standalone)

        # Reorder: Non-connectors first, then connectors (to ensure they draw on top)
        non_conn = [e for e in elements if e and e.get("type") != "connector"]
        conn = [e for e in elements if e and e.get("type") == "connector"]
        elements = non_conn + conn
        
        # Merge overlapping ports for clean PPTX results
        ConnectorParser.optimize_connector_ports(elements)

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "document_metadata": {
                "title": self.title,
                "base_unit": self.base_unit,
                "dimensions": {"width": width, "height": height},
            },
            "pages": [
                {
                    "page_id": "page_1",
                    "name": self.title,
                    "background": {"type": "none"},
                    # Remove any temporary internal processing keys
                    "elements": [self._strip_internal(e) for e in elements if e],
                }
            ],
        }

    def _parse_root_dimensions(self, root) -> Tuple[float, float]:
        """Extract canvas dimensions from <svg> attributes or viewBox."""
        vb = root.get("viewBox")
        if vb:
            import re
            parts = re.split(r"[ ,]+", vb.strip())
            if len(parts) == 4:
                return float(parts[2]), float(parts[3])
        return f(root.get("width"), 0), f(root.get("height"), 0)

    def _parse_shape_like(self, el, suffix: str = "") -> Optional[Dict[str, Any]]:
        """
        Intermediate parser for elements that look like shapes (rect, path, polygon, etc.).
        
        Maps SVG geometry to schema geometry and calculates initial bounding boxes.
        """
        tag = localname(el.tag)
        bbox = GeometryParser.shape_bbox(el)
        if bbox is None:
            return None
        x, y, w, h = bbox

        _id = el.get("id")
        if not _id:
            _id = self.id_gen.gen_id(f"shape{suffix}")
        self.id_gen.register_id(_id)

        position = {
            "x": round(x, 3), "y": round(y, 3),
            "width": round(w, 3), "height": round(h, 3),
            "rotation_degrees": 0,
        }

        # Handle SVG-only formats that don't map to standard PPTX shapes directly
        if tag == "polygon":
            node = {"id": _id, "type": "svg_polygon", "svg_points": el.get("points", "").strip(), "position": position}
        elif tag == "path":
            node = {"id": _id, "type": "svg_path", "svg_path": el.get("d", "").strip(), "position": position}
        elif tag in ("polyline", "line"):
            if tag == "line":
                pts = f'{f(el.get("x1"))},{f(el.get("y1"))} {f(el.get("x2"))},{f(el.get("y2"))}'
            else:
                pts = el.get("points", "").strip()
            node = {"id": _id, "type": "svg_line", "svg_points": pts, "position": position}
        else:
            # Traditional shapes (rectangle, ellipse)
            geometry = GeometryParser.map_geometry(el)
            node = {"id": _id, "type": "shape", "geometry": geometry, "position": position}
            if geometry == "ROUNDED_RECTANGLE":
                rx = f(el.get("rx"), 0)
                if rx and w and h:
                    # Map rx to the ratio required by PPTX
                    node["corner_radius_ratio"] = round(rx / (min(w, h) / 2), 3)

        style = StyleParser.parse_style(el)
        if style:
            node["style"] = style
        
        # Keep bbox for internal association logic, will be stripped in final output
        node["_bbox"] = bbox
        return node

    @staticmethod
    def _strip_internal(node: Dict[str, Any]) -> Dict[str, Any]:
        """Strip internal keys (those starting with '_') from the final JSON output."""
        if not isinstance(node, dict):
            return node
        return {k: v for k, v in node.items() if not k.startswith("_")}
