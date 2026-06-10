import re
from typing import Dict, Any, Optional
from .utils import f

class StyleParser:
    """
    Parses SVG styling attributes into the Canvas Document Schema style objects.
    
    Handles fills, strokes, opacity, and dash patterns.
    """

    @staticmethod
    def parse_dash_style(el) -> str:
        """
        Determine the dash style from the SVG stroke-dasharray attribute.
        
        Args:
            el: The XML element to inspect.
            
        Returns:
            One of "SOLID", "DOTTED", or "DASHED".
        """
        dash = el.get("stroke-dasharray")
        if not dash or dash == "none":
            return "SOLID"
        
        # Split by comma or space
        nums = [n for n in re.split(r"[ ,]+", dash) if n]
        if not nums:
            return "SOLID"
            
        try:
            # Simple heuristic: small first value -> DOTTED, large -> DASHED
            first = float(nums[0])
        except ValueError:
            return "SOLID"
            
        return "DOTTED" if first <= 2 else "DASHED"

    @staticmethod
    def parse_style(el) -> Dict[str, Any]:
        """
        Parse common SVG styling attributes (fill, stroke, opacity).
        
        Args:
            el: The XML element to parse.
            
        Returns:
            A dictionary containing style properties mapped to the schema.
        """
        style: Dict[str, Any] = {}
        
        # Handle Fill
        fill = el.get("fill")
        if fill and fill != "none":
            style["fill_color_hex"] = fill

        # Handle Opacity
        opacity = el.get("opacity") or el.get("fill-opacity")
        if opacity is not None:
            try:
                style["opacity"] = float(opacity)
            except ValueError:
                pass

        # Handle Stroke (mapped to 'border')
        stroke = el.get("stroke")
        if stroke and stroke != "none":
            border = {"color_hex": stroke}
            sw = el.get("stroke-width")
            if sw is not None:
                border["width"] = f(sw, 1)
            border["style"] = StyleParser.parse_dash_style(el)
            style["border"] = border

        return style
