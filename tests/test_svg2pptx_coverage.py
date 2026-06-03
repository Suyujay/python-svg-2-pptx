import pytest
import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory
from pptx.util import Emu

from surquest.utils.svg2pptx import SVG2Pptx
from surquest.utils.svg2pptx.svg2pptx import _IRJSONEncoder, _ir_object_hook
from surquest.utils.svg2pptx.parser import _parse_color, _parse_float, SVGParser
from surquest.utils.svg2pptx.generator import PPTXBackend
from surquest.utils.svg2pptx.models import (
    Color, Point, Geometry,
    IRSlide, IRRectangle, IRLine, IRConnector, IRPolygon,
    IREllipse, IRInfoBox, IRGroup, IRIcon,
    IRText, TextBlock, TextRun, FontStyle,
    ConnectorType, ArrowType
)
from pptx.enum.text import PP_ALIGN



class TestSvg2pptxCoverage:
    def test_json_encoder(self):
        encoder = _IRJSONEncoder()
        assert encoder.default(ArrowType.NONE) == ArrowType.NONE.value
        with pytest.raises(TypeError):
            encoder.default(object())

    def test_convert_invalid_type(self):
        converter = SVG2Pptx()
        with pytest.raises(TypeError):
            converter.convert(123, 'out.pptx')

    def test_convert_exception_path_too_long(self, tmp_path):
        import os
        converter = SVG2Pptx()
        unreadable_path = tmp_path / "unreadable.svg"
        with open(unreadable_path, "w") as f:
            f.write("<svg></svg>")
        os.chmod(unreadable_path, 0o000)
        
        # Test the exception fallback purely natively via PermissionError on open()
        # Because we bypassed it, it returns the string containing the path,
        # which ET.fromstring can't parse as XML, throwing ParseError
        with pytest.raises(ET.ParseError):
            converter.convert(str(unreadable_path), str(tmp_path / 'out.pptx'))
            
        os.chmod(unreadable_path, 0o777)
        converter.convert('<svg></svg>', str(tmp_path / 'out.pptx'))

    def test_convert_no_pptx_ext(self, tmp_path):
        converter = SVG2Pptx()
        converter.convert('<svg></svg>', str(tmp_path / 'out'))

    def test_mega_blob(self, tmp_path):
        out = tmp_path / 'out.pptx'
        svg = "<svg xmlns='http://www.w3.org/2000/svg'>\n            <rect fill='none' stroke='none'/><rect fill='transparent'/><rect fill='rgb(err)'/>\n            <g transform='translate(10) translate(20,30)'>\n                <path d='M0,0 L10,10' fill='none' stroke='none'/><text></text>\n                <g data-element-type='group'><rect/><line x1='0' y1='0' x2='10' y2='10'/><circle cx='5' cy='5' r='5'/>\n                <polyline points='0,0 10,10' stroke-dasharray='5,5'/><ellipse cx='5' cy='5' rx='5' ry='5'/></g>\n                <g data-element-type='infoBox'><text data-element-type='infoBoxTitle'>T</text><rect/></g>\n            </g></svg>"
        SVG2Pptx().convert(svg, out)
        import pptx.parts.image as _pptx_image
        _pptx_image.Image.from_blob(b'h', 'n.png')
        f = tmp_path / 't.svg'
        f.write_bytes(b'<svg/>')
        _pptx_image.Image.from_file(str(f))

    def test_export_ir_to_json_no_ext(self, tmp_path):
        import os
        ir = IRSlide(100, 100)
        converter = SVG2Pptx()
        converter.export_ir_to_json(tmp_path / 'out_no_ext', ir)
        assert os.path.exists(tmp_path / 'out_no_ext.json')
    def test_ir_object_hook_missing_type(self):
        assert _ir_object_hook({"foo": "bar"}) == {"foo": "bar"}

    def test_ir_object_hook_unknown_class(self):
        assert _ir_object_hook({"__type__": "NonExistentClass", "foo": "bar"}) == {"__type__": "NonExistentClass", "foo": "bar"}

    def test_ir_object_hook_not_dataclass_type(self):
        # ArrowType is not a dataclass
        assert _ir_object_hook({"__type__": "ArrowType", "val": 1}) == {"__type__": "ArrowType", "val": 1}

    def test_ir_object_hook_invalid_alignment_enum(self):
        data = {
            "__type__": "TextBlock",
            "geometry": None,
            "runs": [],
            "alignment": "invalid_value",
            "anchor_x": "center",
            "anchor_y": "center",
        }
        # It should pass without raising ValueError
        res = _ir_object_hook(data)
        assert res.alignment == "invalid_value"

    def test_ir_object_hook_enums(self):
        data = {
            "__type__": "IRConnector",
            "waypoints": [],
            "stroke_width_emu": 1000,
            "stroke": None,
            "connector_type": "elbow",
            "start_arrow": "none",
            "end_arrow": "triangle",
            "dashed": False,
        }
        res = _ir_object_hook(data)
        from surquest.utils.svg2pptx import models
        assert res.connector_type == models.ConnectorType("elbow")
        assert res.start_arrow == models.ArrowType("none")
        assert res.end_arrow == models.ArrowType("triangle")
