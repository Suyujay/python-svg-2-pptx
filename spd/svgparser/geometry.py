import re
from typing import List, Tuple, Optional, Dict, Any
from .utils import f, localname

class GeometryParser:
    """
    Handles extraction of geometric data from SVG elements,
    including coordinate parsing and bounding box calculation.
    """

    @staticmethod
    def parse_svg_path(d: str) -> List[Tuple[float, float]]:
        """
        Extract key vertices from an SVG path 'd' attribute string.
        
        This is a lightweight parser that focuses on straight-line segments.
        Curves (C, S, Q, T) are approximated by their control and end points.
        
        Args:
            d: The SVG path data string.
            
        Returns:
            A list of (x, y) point tuples.
        """
        # Tokenize the path string into commands and numeric values
        tokens = re.findall(r'[A-Za-z]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d)
        pts = []
        x, y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0
        i = 0
        cmd = 'M'
        
        while i < len(tokens):
            t = tokens[i]
            if t.isalpha():
                cmd = t
                i += 1
                if i >= len(tokens):
                    break
                t = tokens[i]

            # Handle Closepath
            if cmd in 'Zz':
                x, y = start_x, start_y
                pts.append((x, y))
                continue

            # Handle MoveTo and LineTo
            if cmd in 'MmLl':
                if i + 1 >= len(tokens):
                    break
                try:
                    dx, dy = float(t), float(tokens[i+1])
                except (ValueError, IndexError):
                    break
                i += 2
                if cmd == 'M':
                    x, y = dx, dy
                    start_x, start_y = x, y
                    cmd = 'L'
                elif cmd == 'm':
                    x += dx
                    y += dy
                    start_x, start_y = x, y
                    cmd = 'l'
                elif cmd == 'L':
                    x, y = dx, dy
                elif cmd == 'l':
                    x += dx
                    y += dy
                pts.append((x, y))
                continue

            # Handle Horizontal Line
            if cmd in 'Hh':
                try:
                    val = float(t)
                except ValueError:
                    i += 1
                    continue
                if cmd == 'H':
                    x = val
                else:
                    x += val
                pts.append((x, y))
                i += 1
                continue

            # Handle Vertical Line
            if cmd in 'Vv':
                try:
                    val = float(t)
                except ValueError:
                    i += 1
                    continue
                if cmd == 'V':
                    y = val
                else:
                    y += val
                pts.append((x, y))
                i += 1
                continue

            # Skip unsupported curve parameters
            i += 1
        return pts

    @staticmethod
    def parse_points(points_str: str) -> List[Tuple[float, float]]:
        """
        Parse an SVG points string (e.g., from a <polyline>) into coordinate pairs.
        
        Args:
            points_str: The points attribute string.
            
        Returns:
            A list of (x, y) point tuples.
        """
        nums = [n for n in re.split(r"[ ,]+", points_str.strip()) if n]
        pts = []
        for i in range(0, len(nums) - 1, 2):
            try:
                pts.append((float(nums[i]), float(nums[i + 1])))
            except ValueError:
                continue
        return pts

    @staticmethod
    def shape_bbox(el) -> Optional[Tuple[float, float, float, float]]:
        """
        Calculate the visual bounding box (x, y, width, height) for various SVG tags.
        
        Supports rect, ellipse, circle, line, polygon, polyline, and path.
        
        Returns:
            (x, y, width, height) tuple or None if calculation fails.
        """
        tag = localname(el.tag)
        if tag == "rect":
            return (f(el.get("x")), f(el.get("y")),
                    f(el.get("width")), f(el.get("height")))
        
        if tag == "ellipse":
            cx, cy = f(el.get("cx")), f(el.get("cy"))
            rx, ry = f(el.get("rx")), f(el.get("ry"))
            return (cx - rx, cy - ry, 2 * rx, 2 * ry)
            
        if tag == "circle":
            cx, cy = f(el.get("cx")), f(el.get("cy"))
            r = f(el.get("r"))
            return (cx - r, cy - r, 2 * r, 2 * r)
            
        if tag == "line":
            x1, y1 = f(el.get("x1")), f(el.get("y1"))
            x2, y2 = f(el.get("x2")), f(el.get("y2"))
            return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            
        if tag in ("polygon", "polyline", "path"):
            if tag == "path":
                pts = GeometryParser.parse_svg_path(el.get("d", ""))
            else:
                pts = GeometryParser.parse_points(el.get("points", ""))
            if not pts:
                return None
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            
        return None

    @staticmethod
    def map_geometry(el) -> str:
        """
        Map an SVG tag name to a corresponding enum used in the Canvas Document Schema.
        
        Args:
            el: The XML element.
            
        Returns:
            A string enum like "RECTANGLE", "ROUNDED_RECTANGLE", or "ELLIPSE".
        """
        tag = localname(el.tag)
        if tag == "rect":
            if f(el.get("rx"), 0) > 0 or f(el.get("ry"), 0) > 0:
                return "ROUNDED_RECTANGLE"
            return "RECTANGLE"
        if tag in ("ellipse", "circle"):
            return "ELLIPSE"
        return "RECTANGLE"
