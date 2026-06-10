from typing import List, Dict, Any, Tuple, Optional
from .utils import f, localname, element_to_string
from .geometry import GeometryParser
from .styles import StyleParser
from .connectors import ConnectorParser
from .text import TextParser

class GroupParser:
    """
    Handles parsing of SVG groups (<g>), specialized icons,
    and attribute inheritance within groups.
    """

    @staticmethod
    def serialize_inner_svg(svg_el) -> str:
        """
        Serialize an inner <svg> element for use as an embedded image source.
        Keeps the viewBox and all children.
        """
        viewbox = svg_el.get("viewBox", "")
        # Filter out viewBox from attributes to avoid duplication
        attrs = " ".join(f'{k}="{v}"' for k, v in svg_el.attrib.items() if k != "viewBox")
        inner_parts = [element_to_string(child) for child in list(svg_el)]
        inner = "".join(inner_parts)
        return f'<svg {attrs} viewBox="{viewbox}">{inner}</svg>'

    @staticmethod
    def parse_icon(g, id_gen) -> Optional[Dict[str, Any]]:
        """
        Convert a group marked as an 'icon' (contains an <svg>) into a schema 'image' node.
        """
        _id = g.get("id") or id_gen.gen_id("icon")
        id_gen.register_id(_id)

        # Locate the inner <svg> block
        inner_svg = next((c for c in list(g) if localname(c.tag) == "svg"), None)
        if inner_svg is None:
            return None

        x, y = f(inner_svg.get("x")), f(inner_svg.get("y"))
        w, h = f(inner_svg.get("width")), f(inner_svg.get("height"))

        return {
            "id": _id,
            "type": "image",
            "position": {
                "x": round(x, 3), "y": round(y, 3),
                "width": round(w, 3), "height": round(h, 3),
                "rotation_degrees": 0,
            },
            "source": {
                "svg_text": GroupParser.serialize_inner_svg(inner_svg),
                "format": "svg",
            },
        }

    @staticmethod
    def parse_group(g, id_gen, parse_shape_func) -> Tuple[List[Dict[str, Any]], List[Any]]:
        """
        Recursively traverse an SVG group, collecting shapes and text.
        
        Handles attribute inheritance (e.g., fill color set on a group should
        apply to child shapes if they don't have their own).
        
        Args:
            g: The XML group element.
            id_gen: ID Generator instance.
            parse_shape_func: Reference to SVGParser._parse_shape_like.
            
        Returns:
            A tuple of (parsed_element_list, unassociated_text_list).
        """
        elem_type = g.get("data-element-type")
        results: List[Dict[str, Any]] = []
        shapes: List[Dict[str, Any]] = []
        texts: List = []
        
        # If the group has an ID, the first child shape usually 'claims' it
        first_shape_id = g.get("id") if elem_type != "icon" else None

        if elem_type == "icon":
            node = GroupParser.parse_icon(g, id_gen)
            if node:
                results.append(node)

        def walk(element, current_fallback_id):
            """Recursive visitor to handle nesting and attribute inheritance."""
            inherited = {}
            attrs_to_inherit = [
                "fill", "fill-opacity", "opacity", 
                "stroke", "stroke-width", "stroke-dasharray"
            ]
            
            # Record attributes defined at this level to pass to children
            for k in attrs_to_inherit:
                v = element.get(k)
                if v is not None:
                    inherited[k] = v

            for child in list(element):
                # Apply inherited attributes to child if child doesn't specify them
                for k, v in inherited.items():
                    if child.get(k) is None:
                        child.set(k, v)

                tag = localname(child.tag)
                
                # Check for nested icons
                if tag == "g" and child.get("data-element-type") == "icon":
                    icon = GroupParser.parse_icon(child, id_gen)
                    if icon:
                        results.append(icon)
                    walk(child, None)
                elif tag == "g":
                    walk(child, current_fallback_id)
                elif tag in ("rect", "ellipse", "circle", "polygon", "path", "line", "polyline"):
                    if tag in ("line", "polyline") and ConnectorParser.is_connector(child):
                        results.append(ConnectorParser.parse_connector(child, id_gen))
                    else:
                        # Auto-assign IDs for shapes within groups to ensure they are identifiable
                        if not child.get("id"):
                            valid_main = [s for s in shapes if s.get("type") not in ("svg_line", "svg_path")]
                            if not valid_main and tag not in ("line", "polyline", "path") and current_fallback_id:
                                child.set("id", current_fallback_id)
                            elif current_fallback_id:
                                child.set("id", f"{current_fallback_id}-body-{len(shapes)}")
                        
                        node = parse_shape_func(child)
                        if node:
                            shapes.append(node)
                elif tag == "text":
                    texts.append(child)

        walk(g, first_shape_id)
        
        # Associate collected text nodes with their nearest shapes
        unassoc = TextParser.associate_text(shapes, texts, id_gen)
        return shapes + results, unassoc
