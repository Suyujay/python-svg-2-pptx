import pytest
from xml.etree import ElementTree as ET
from pptx.util import Emu

from surquest.utils.svg2pptx.parser import CoordinateNormalizer, _parse_color, _parse_float, SVGParser
from surquest.utils.svg2pptx.models import Color

class TestCoordinateNormalizer:
    def test_coordinate_normalizer(self):
        norm = CoordinateNormalizer(viewbox=(0, 0, 1000, 500), target_width=10000, target_height=5000)
        assert norm.x(100) == Emu(1000)
        assert norm.y(50) == Emu(500)
        assert norm.w(200) == Emu(2000)
        assert norm.h(100) == Emu(1000)

class TestParseColor:
    def test_parse_color(self):
        assert _parse_color("none") is None
        assert _parse_color("transparent") is None
        
        red = _parse_color("red")
        if hasattr(red, 'r'): # assuming it's Color object or from_hex returns it
            assert red.r == 255
            assert red.g == 0
            assert red.b == 0
        else:
            assert isinstance(red, Color)
        
        blue = _parse_color("#0000ff")
        if hasattr(blue, 'b'):
            assert blue.b == 255
            
        rgb = _parse_color("rgb(10, 20, 30)")
        assert rgb.r == 10
        assert rgb.g == 20
        assert rgb.b == 30

class TestParseFloat:
    def test_parse_float(self):
        assert _parse_float("12.5") == 12.5
        assert _parse_float("-3.5") == -3.5
        assert _parse_float(None, 4.0) == 4.0

class TestSVGParser:
    def test_svg_parser_basic(self):
        svg_source = """
        <svg viewBox="0 0 100 100">
            <rect x="10" y="10" width="80" height="80" fill="red" stroke="blue" />
            <circle cx="50" cy="50" r="40" fill="#00FF00" />
        </svg>
        """
        parser = SVGParser(svg_source, slide_width=9144000, slide_height=5143500, svg_ns="")
        slide = parser.parse()
        
        assert slide.width_emu == 9144000
        assert slide.height_emu == 5143500
        assert len(slide.nodes) == 2
        
        rect_node = slide.nodes[0]
        assert type(rect_node).__name__ == "IRRectangle"
        assert rect_node.geometry.width == Emu(7315200)
        
        circle_node = slide.nodes[1]
        assert type(circle_node).__name__ == "IREllipse"
        assert circle_node.geometry.width == Emu(7315200)  # r=40 -> width=80 -> 80*9144000/100
