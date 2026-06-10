"""Handlers for individual slide elements (shapes, images, connectors)."""

import io
import re
from typing import Any
from lxml import etree
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR_TYPE
from pptx.oxml.ns import qn

from .constants import (
    GEOMETRY_MAP, CONNECTOR_MAP, ARROW_MAP, 
    PORT_MAP, PORT_IDX_MAP, DASH_MAP
)
from .utils import ColorUtils
from .style_manager import StyleManager


class ElementHandler:
    """Base class for element handlers providing common functionality."""
    
    @staticmethod
    def _apply_common(shape, elem: dict, unit_converter) -> None:
        """
        Apply common properties like rotation, style, and text to a shape.
        
        Args:
            shape: The pptx shape object.
            elem: The element data dictionary.
            unit_converter: The UnitConverter instance for coordinate conversion.
        """
        pos = elem["position"]
        if pos.get("rotation_degrees"):
            shape.rotation = pos["rotation_degrees"]
        
        # Disable default shadow to follow schema styles
        shape.shadow.inherit = False
        
        StyleManager.apply_style(shape, elem.get("style", {}), unit_converter)
        StyleManager.apply_text(shape, elem.get("text_content", {}), unit_converter)


class ShapeHandler(ElementHandler):
    """Handler for standard PowerPoint shapes and textboxes."""
    
    @classmethod
    def add_shape(cls, slide, elem: dict, unit_converter) -> Any:
        """
        Create and add a standard shape (rect, ellipse, etc.) to a slide.
        
        Args:
            slide: The slide to add the shape to.
            elem: Element data defining the shape.
            unit_converter: Unit converter for EMU conversion.
            
        Returns:
            The created pptx shape.
        """
        geo = GEOMETRY_MAP.get(elem["geometry"], MSO_SHAPE.RECTANGLE)
        pos = elem["position"]
        shape = slide.shapes.add_shape(
            geo,
            unit_converter.to_emu(pos["x"]),
            unit_converter.to_emu(pos["y"]),
            unit_converter.to_emu(pos["width"]),
            unit_converter.to_emu(pos["height"]),
        )
        
        # Apply corner radius for rounded rectangles if available
        if "corner_radius_ratio" in elem and len(shape.adjustments) > 0:
            shape.adjustments[0] = elem["corner_radius_ratio"]
        
        cls._apply_common(shape, elem, unit_converter)
        return shape

    @classmethod
    def add_textbox(cls, slide, elem: dict, unit_converter) -> Any:
        """
        Create and add a textbox to a slide.
        
        Args:
            slide: The slide to add the textbox to.
            elem: Element data defining the textbox.
            unit_converter: Unit converter for EMU conversion.
            
        Returns:
            The created pptx textbox shape.
        """
        pos = elem["position"]
        shape = slide.shapes.add_textbox(
            unit_converter.to_emu(pos["x"]),
            unit_converter.to_emu(pos["y"]),
            unit_converter.to_emu(pos["width"]),
            unit_converter.to_emu(pos["height"]),
        )
        cls._apply_common(shape, elem, unit_converter)
        return shape


class SvgHandler(ElementHandler):
    """
    Handler for SVG-specific elements using PowerPoint's freeform shape builder.
    
    This class converts SVG path data and polygon points into PowerPoint shapes.
    """
    
    @classmethod
    def add_svg_polygon(cls, slide, elem: dict, unit_converter) -> Any:
        """Add a closed SVG polygon."""
        return cls._add_svg_poly(slide, elem, unit_converter, close=True)

    @classmethod
    def add_svg_line(cls, slide, elem: dict, unit_converter) -> Any:
        """Add an open SVG polyline or line."""
        return cls._add_svg_poly(slide, elem, unit_converter, close=False)

    @classmethod
    def _add_svg_poly(cls, slide, elem: dict, unit_converter, close: bool) -> Any:
        """Internal helper to build freeform shapes from SVG-style points."""
        pos = elem["position"]
        ox = unit_converter.to_emu(pos["x"])
        oy = unit_converter.to_emu(pos["y"])
        
        pts_str = elem.get("svg_points", "0,0")
        raw_pts = []
        for pair in re.split(r'\s+', pts_str.strip()):
            if ',' in pair:
                try:
                    px, py = map(float, pair.split(','))
                    raw_pts.append((px, py))
                except ValueError:
                    pass
        
        if not raw_pts:
            raw_pts = [(0, 0), (1, 0), (1, 1), (0, 1)]

        # Calculate local bounding box of raw points for scaling
        min_x = min(p[0] for p in raw_pts)
        max_x = max(p[0] for p in raw_pts)
        min_y = min(p[1] for p in raw_pts)
        max_y = max(p[1] for p in raw_pts)
        
        sw = max(max_x - min_x, 1)
        sh = max(max_y - min_y, 1)
        tgt_w = unit_converter.to_emu(pos["width"])
        tgt_h = unit_converter.to_emu(pos["height"])
        
        # Scale and offset points to fit the target position/size
        def scale_pt(p):
            sx = ox + int(((p[0] - min_x) / sw) * tgt_w)
            sy = oy + int(((p[1] - min_y) / sh) * tgt_h)
            return sx, sy

        start_pt = scale_pt(raw_pts[0])
        ffb = slide.shapes.build_freeform(*start_pt)
        
        scaled_pts = [scale_pt(pt) for pt in raw_pts[1:]]
            
        if scaled_pts:
            ffb.add_line_segments(scaled_pts, close=close)
            
        shape = ffb.convert_to_shape()
        cls._apply_common(shape, elem, unit_converter)
        return shape

    @classmethod
    def add_svg_path(cls, slide, elem: dict, unit_converter) -> Any:
        """
        Add an SVG path element.
        
        Args:
            slide: The slide to add the path to.
            elem: Element data containing the SVG path 'd' attribute.
            unit_converter: Unit converter for EMU conversion.
            
        Returns:
            The created pptx shape.
        """
        pos = elem["position"]
        ox = unit_converter.to_emu(pos["x"])
        oy = unit_converter.to_emu(pos["y"])
        
        raw_pts = cls._parse_path_to_points(elem.get("svg_path", ""))
        if not raw_pts:
            raw_pts = [(0, 0), (1, 0), (1, 1), (0, 1)]

        min_x = min(p[0] for p in raw_pts)
        max_x = max(p[0] for p in raw_pts)
        min_y = min(p[1] for p in raw_pts)
        max_y = max(p[1] for p in raw_pts)
        
        sw = max(max_x - min_x, 1)
        sh = max(max_y - min_y, 1)
        tgt_w = unit_converter.to_emu(pos["width"])
        tgt_h = unit_converter.to_emu(pos["height"])
        
        def scale_pt(p):
            sx = ox + int(((p[0] - min_x) / sw) * tgt_w)
            sy = oy + int(((p[1] - min_y) / sh) * tgt_h)
            return sx, sy

        start_pt = scale_pt(raw_pts[0])
        ffb = slide.shapes.build_freeform(*start_pt)
        
        scaled_pts = [scale_pt(pt) for pt in raw_pts[1:]]
            
        if scaled_pts:
            ffb.add_line_segments(scaled_pts, close=True)
            
        shape = ffb.convert_to_shape()
        cls._apply_common(shape, elem, unit_converter)
        return shape

    @staticmethod
    def _parse_path_to_points(d: str) -> list[tuple[float, float]]:
        """
        Crude parser for SVG path 'd' attribute to extract major points for freeform building.
        Does not support curves (Bezier); they are treated as straight lines to control points.
        """
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

            if cmd in 'Zz':
                x, y = start_x, start_y
                pts.append((x, y))
                continue

            if cmd in 'MmLl':
                if i + 1 >= len(tokens):
                    break
                dx, dy = float(t), float(tokens[i+1])
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

            if cmd in 'Hh':
                if cmd == 'H':
                    x = float(t)
                else:
                    x += float(t)
                pts.append((x, y))
                i += 1
                continue

            if cmd in 'Vv':
                if cmd == 'V':
                    y = float(t)
                else:
                    y += float(t)
                pts.append((x, y))
                i += 1
                continue

            # Skip unsupported commands (curves etc.)
            i += 1

        return pts


class ImageHandler(ElementHandler):
    """Handler for image elements including embedded SVGs."""
    
    @classmethod
    def add_image(cls, slide, elem: dict, unit_converter) -> Any:
        """
        Add an image to the slide. Falls back to a placeholder if image missing.
        """
        pos = elem["position"]
        x, y = unit_converter.to_emu(pos["x"]), unit_converter.to_emu(pos["y"])
        w, h = unit_converter.to_emu(pos["width"]), unit_converter.to_emu(pos["height"])
        
        src_data = elem["source"]
        if "svg_text" in src_data:
            # Handle embedded SVG strings
            src = io.BytesIO(src_data["svg_text"].encode("utf-8"))
        else:
            # Handle local paths or URLs
            src = src_data["url_or_path"]

        try:
            pic = slide.shapes.add_picture(src, x, y, w, h)
        except Exception:
            # Image not found or error – insert a dashed placeholder rectangle
            pic = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
            pic.fill.background()
            pic.line.dash_style = MSO_LINE_DASH_STYLE.DASH
            # Add a small note or just leave as box
            
        if pos.get("rotation_degrees"):
            pic.rotation = pos["rotation_degrees"]
        return pic


class ConnectorHandler:
    """Handler for connectors between shapes."""
    
    @classmethod
    def add_connector(cls, slide, elem: dict, shapes_by_id: dict, unit_converter) -> None:
        """
        Add a connector (line/arrow) linking two shapes.
        
        Args:
            slide: The slide to add the connector to.
            elem: Connector element data.
            shapes_by_id: Map of element IDs to (pptx_shape, position_data).
            unit_converter: Unit converter for EMU conversion.
        """
        conn_data = elem["connection"]
        src_id, tgt_id = conn_data["source_id"], conn_data["target_id"]
        if src_id not in shapes_by_id or tgt_id not in shapes_by_id:
            # Cannot connect if one of the shapes is missing
            return

        _, spos = shapes_by_id[src_id]
        _, tpos = shapes_by_id[tgt_id]
        
        # Calculate start and end coordinates based on ports
        sox, soy = PORT_MAP.get(conn_data.get("source_port", "CENTER"), (0.5, 0.5))
        tox, toy = PORT_MAP.get(conn_data.get("target_port", "CENTER"), (0.5, 0.5))

        bx = unit_converter.to_emu(spos["x"] + spos["width"] * sox)
        by = unit_converter.to_emu(spos["y"] + spos["height"] * soy)
        ex = unit_converter.to_emu(tpos["x"] + tpos["width"] * tox)
        ey = unit_converter.to_emu(tpos["y"] + tpos["height"] * toy)

        ctype = CONNECTOR_MAP.get(
            elem.get("routing", "STRAIGHT"), MSO_CONNECTOR_TYPE.STRAIGHT
        )
        cxn = slide.shapes.add_connector(ctype, bx, by, ex, ey)

        # Formal connection to shapes (allows them to move together in PPTX)
        sshape, _ = shapes_by_id[src_id]
        tshape, _ = shapes_by_id[tgt_id]
        s_idx = PORT_IDX_MAP.get(conn_data.get("source_port", "CENTER"), 0)
        t_idx = PORT_IDX_MAP.get(conn_data.get("target_port", "CENTER"), 0)
        
        try:
            cxn.begin_connect(sshape, s_idx)
            cxn.end_connect(tshape, t_idx)
        except Exception:
            # Some shapes might not support certain port indices; ignore errors here
            pass
            
        cxn.shadow.inherit = False

        style = elem.get("style", {})
        ln = cxn.line
        
        # Apply line styling
        if "line_color_hex" in style:
            ln.color.rgb = ColorUtils.hex_to_rgb(style["line_color_hex"])
        if "width" in style:
            ln.width = unit_converter.to_emu(style["width"])
        if style.get("dash_style") in DASH_MAP:
            ln.dash_style = DASH_MAP[style["dash_style"]]

        cls._set_arrows(cxn, style)

    @staticmethod
    def _set_arrows(cxn, style: dict) -> None:
        sp_pr = cxn._element.find(qn("p:spPr"))
        if sp_pr is None:
            return
        ln = sp_pr.find(qn("a:ln"))
        if ln is None:
            ln = etree.SubElement(sp_pr, qn("a:ln"))

        for attr, tag in (("end_arrow", "a:tailEnd"), ("start_arrow", "a:headEnd")):
            arrow_type = ARROW_MAP.get(style.get(attr, "NONE"))
            if arrow_type:
                el = ln.find(qn(tag))
                if el is None:
                    el = etree.SubElement(ln, qn(tag))
                el.set("type", arrow_type)
