import re
from typing import Optional, Tuple, List, Dict, Any
from .utils import f, localname
from .constants import MARKER_MAP, CONNECTOR_TYPE_MAP
from .styles import StyleParser
from .geometry import GeometryParser

class ConnectorParser:
    """
    Identifies and parses SVG elements that represent connectors (lines/arrows)
    between shapes. Also optimizes their port attachments.
    """

    @staticmethod
    def is_connector(el) -> bool:
        """Determines if an SVG element is tagged as a 'connector'."""
        return el.get("data-element-type") == "connector"

    @staticmethod
    def extract_marker(raw: Optional[str]) -> Optional[str]:
        """
        Parses an SVG marker reference (e.g., 'url(#arrowhead)') into a schema arrow enum.
        
        Args:
            raw: The marker attribute value.
            
        Returns:
            The corresponding arrow type enum or None.
        """
        if not raw:
            return None
        m = re.search(r"url\(#([^)]+)\)", raw)
        if not m:
            return None
        marker_id = m.group(1).strip().lower()
        return MARKER_MAP.get(marker_id, "CLASSIC")

    @staticmethod
    def infer_port(point: Tuple[float, float], neighbor: Tuple[float, float]) -> str:
        """
        Heuristic to guess which side of a box a line is exiting from,
        based on the vector between the terminal point and its nearest neighbor.
        """
        dx = neighbor[0] - point[0]
        dy = neighbor[1] - point[1]
        
        # Use the dominant axis to determine direction
        if abs(dx) >= abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        else:
            return "BOTTOM" if dy > 0 else "TOP"

    @staticmethod
    def connector_ports(el) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract the start and end port directions from the connector geometry.
        """
        tag = localname(el.tag)
        if tag == "line":
            x1, y1 = f(el.get("x1")), f(el.get("y1"))
            x2, y2 = f(el.get("x2")), f(el.get("y2"))
            pts = [(x1, y1), (x2, y2)]
        else:
            pts = GeometryParser.parse_points(el.get("points", ""))
            
        if len(pts) < 2:
            return None, None
            
        start, end = pts[0], pts[-1]
        return ConnectorParser.infer_port(start, pts[1]), ConnectorParser.infer_port(end, pts[-2])

    @staticmethod
    def parse_connector(el, id_gen) -> Dict[str, Any]:
        """
        Main entry point for parsing an SVG line/polyline into a schema connector.
        
        Args:
            el: The SVG XML element.
            id_gen: ID Generator instance.
            
        Returns:
            A connector element dictionary.
        """
        start_id = el.get("data-start")
        end_id = el.get("data-end")
        ctype = el.get("data-connector-type", "straight").lower()

        # Generate a unique ID if not present
        _id = el.get("id")
        if not _id:
            base = f"conn-{start_id or 'src'}-{end_id or 'tgt'}"
            _id = base if not id_gen.is_used(base) else id_gen.gen_id(base)
        id_gen.register_id(_id)

        # Build style dictionary
        style: Dict[str, Any] = {}
        stroke = el.get("stroke")
        if stroke and stroke != "none":
            style["line_color_hex"] = stroke
            
        sw = el.get("stroke-width")
        if sw is not None:
            style["width"] = f(sw)
            
        dash = StyleParser.parse_dash_style(el)
        if dash != "SOLID":
            style["dash_style"] = dash

        # Resolve arrowheads
        start_arrow = ConnectorParser.extract_marker(el.get("marker-start"))
        end_arrow = ConnectorParser.extract_marker(el.get("marker-end"))
        if start_arrow:
            style["start_arrow"] = start_arrow
        if end_arrow:
            style["end_arrow"] = end_arrow

        # Initial port inference
        src_port, tgt_port = ConnectorParser.connector_ports(el)
        if tgt_port:
            # Flip direction for the target (looking into the shape)
            flip = {"LEFT": "RIGHT", "RIGHT": "LEFT", "TOP": "BOTTOM", "BOTTOM": "TOP"}
            tgt_port = flip.get(tgt_port, tgt_port)

        connection: Dict[str, Any] = {"source_id": start_id, "target_id": end_id}
        if src_port:
            connection["source_port"] = src_port
        if tgt_port:
            connection["target_port"] = tgt_port

        conn_node = {
            "id": _id,
            "type": "connector",
            "routing": CONNECTOR_TYPE_MAP.get(ctype, "STRAIGHT"),
            "style": style,
            "connection": connection,
        }
        
        # Store raw coordinates for the optimization pass
        tag = localname(el.tag)
        if tag == "line":
            conn_node["_conn_pts"] = [(f(el.get("x1")), f(el.get("y1"))), (f(el.get("x2")), f(el.get("y2")))]
        else:
            conn_node["_conn_pts"] = GeometryParser.parse_points(el.get("points", ""))
                
        return conn_node

    @staticmethod
    def optimize_connector_ports(elements: List[Dict[str, Any]]) -> None:
        """
        Final step in parsing: re-evaluate connector ports by checking distance 
        to possible attachment points on connected shapes. 
        This ensures the PPTX 'glue' points are correct.
        """
        import math
        shapes_by_id = {e["id"]: e for e in elements if "position" in e}
        
        for el in elements:
            if el.get("type") == "connector":
                conn = el.get("connection", {})
                src_id = conn.get("source_id")
                tgt_id = conn.get("target_id")
                
                src = shapes_by_id.get(src_id)
                tgt = shapes_by_id.get(tgt_id)
                pts = el.get("_conn_pts", [])
                
                if src and tgt and len(pts) >= 2:
                    start_pt = pts[0]
                    end_pt = pts[-1]
                    
                    def find_best_port(bbox, point):
                        """Find whichever standard port (T, B, L, R) is closest to a given point."""
                        x, y, w, h = bbox
                        ports = {
                            "TOP": (x + w/2, y),
                            "BOTTOM": (x + w/2, y + h),
                            "LEFT": (x, y + h/2),
                            "RIGHT": (x + w, y + h/2),
                        }
                        
                        best_port = "CENTER"
                        min_dist = float('inf')
                        for port_name, port_coord in ports.items():
                            dist = math.hypot(port_coord[0] - point[0], port_coord[1] - point[1])
                            if dist < min_dist:
                                min_dist = dist
                                best_port = port_name
                        return best_port
                        
                    s_pos = src["position"]
                    t_pos = tgt["position"]
                    src_bbox = (s_pos["x"], s_pos["y"], s_pos["width"], s_pos["height"])
                    tgt_bbox = (t_pos["x"], t_pos["y"], t_pos["width"], t_pos["height"])
                    
                    conn["source_port"] = find_best_port(src_bbox, start_pt)
                    conn["target_port"] = find_best_port(tgt_bbox, end_pt)
