import pytest
import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from pptx.util import Emu

from surquest.utils.svg2pptx import SVG2Pptx
from surquest.utils.svg2pptx.parser import _parse_color, _parse_float, SVGParser, CSS_COLORS
from surquest.utils.svg2pptx.generator import PPTXBackend
from surquest.utils.svg2pptx.models import (
    Color, Point, Geometry,
    IRSlide, IRRectangle, IRLine, IRConnector, IRPolygon,
    IREllipse, IRInfoBox, IRGroup, IRIcon,
    IRText, TextBlock, TextRun, FontStyle,
    ConnectorType, ArrowType
)
from pptx.enum.text import PP_ALIGN


from unittest import mock

class TestParserCoverage:
    def test_parse_color_invalid_format(self):
        assert _parse_color('invalid') is None

    def test_parser_unsupported_tag(self):
        svg_source = '<svg viewBox="0 0 100 100"><unsupportedTag fill="red" /></svg>'
        parser = SVGParser(svg_source, 100, 100, '')
        slide = parser.parse()
        assert len(slide.nodes) == 0

    def test_parse_transform_translate(self):
        svg_source = '<svg viewBox="0 0 100 100"><rect x="10" y="10" width="10" height="10" transform="translate(10, 20)" /></svg>'
        parser = SVGParser(svg_source, 100, 100, '')
        slide = parser.parse()
        assert len(slide.nodes) == 1
        assert slide.nodes[0].geometry.x == Emu(20)

    def test_traverse_infobox_missing_rect(self):
        svg_source = '<svg viewBox="0 0 100 100"><g data-element-type="infoBox" id="test1"><circle cx="50" cy="50" r="10"/></g></svg>'
        parser = SVGParser(svg_source, 100, 100, '')
        slide = parser.parse()
        assert len(slide.nodes) == 1
        ib = slide.nodes[0]
        assert ib.rectangle.shape_id == 'test1'
        assert ib.rectangle.geometry.width == Emu(0)

    def test_parse_color_indirect_none(self):
        old_val = CSS_COLORS.get('testcolor')
        CSS_COLORS['testcolor'] = 'none'
        try:
            assert _parse_color('testcolor') is None
        finally:
            if old_val:
                CSS_COLORS['testcolor'] = old_val
            else:
                del CSS_COLORS['testcolor']

    def test_icon_xmlns_fallback(self):
        svg_source = '<svg viewBox="0 0 100 100"><g data-element-type="icon" id="test2"><svg viewBox="0 0 10 10"><rect/></svg></g></svg>'
        parser = SVGParser(svg_source, 100, 100, '') # Empty svs_ns prevents automatic root namespace ingestion
        with mock.patch('xml.etree.ElementTree.tostring', return_value=b"<svg viewBox='0 0 10 10'><rect/></svg>"):
            slide = parser.parse()
        assert len(slide.nodes) > 0

    def test_tspan_newline(self):
        svg_source = '<svg viewBox="0 0 100 100">\n            <text x="10" y="20">\n                <tspan x="10" y="20">Hello</tspan>\n                <tspan dx="10" y="20">Middle</tspan>\n                <tspan x="10" y="20">World</tspan>\n                <tspan x="50" y="20">NewBlock</tspan>\n            </text>\n        </svg>'
        parser = SVGParser(svg_source, 100, 100, '')
        slide = parser.parse()
        assert any((isinstance(n, IRText) for n in slide.nodes))

    def test_color_hex_short(self):
        c = Color.from_hex('#abc')
        assert c.r == 170 and c.g == 187 and (c.b == 204)

    def test_parser_exact_missing(self):
        svg = '<svg viewBox="0 0 100 100">\n            <defs><linearGradient id="grad1"/></defs>\n            <path d="M0,0 L10,10" /> <!-- no dx, dy for dx=0, dy=0 in path -->\n            <g data-element-type="infoBox">\n                <rect x="0" y="0" width="10" height="10" /> <!-- first rect -->\n                <rect x="10" y="10" width="10" height="10" /> <!-- second rect -->\n                <line x1="0" y1="0" x2="10" y2="10" /> <!-- line -->\n                <polygon points="0,0 10,10" /> <!-- polygon -->\n                <path d="M0,0 L10,10" /> <!-- path -->\n            </g>\n            <text x="10" y="10">\n                <tspan x="10" y="10">Hello</tspan>\n                <tspan x="10" y="20">NewBlock</tspan> <!-- ts_y_str is explicitly set and diff from previous -->\n            </text>\n        </svg>'
        parser = SVGParser(svg, 100, 100, '')
        slide = parser.parse()
        assert len(slide.nodes) > 0