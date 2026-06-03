import io
import logging
from typing import Dict
from lxml import etree as lxml_etree

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt
import pptx.parts.image as _pptx_image

from ..models import (
    IRSlide, IRNode, IRInfoBox, IRText, IRRectangle, IRIcon, IRLine, IRGroup,
    IREllipse, IRPolygon,
    IRConnector, Point, Color, ArrowType, ConnectorType, TextBlock
)

logger = logging.getLogger(__name__)

class _SvgImageHolder:
    def __init__(self, blob, w, h, filename=''):
        self.blob = blob
        self.ext = 'svg'
        self.content_type = 'image/svg+xml'
        self.size = (w, h)
        self.dpi = (72, 72)
        self.filename = filename

    @property
    def sha1(self):
        import hashlib
        return hashlib.sha1(self.blob).hexdigest()

def _is_svg(blob):
    s = blob[:1024].lower()
    return b'<svg' in s or (b'svg' in s and b'http://www.w3.org' in s)

_orig_from_blob = getattr(_pptx_image.Image, 'from_blob')
@classmethod
def _from_blob_patch(cls, blob, filename=None):
    if _is_svg(blob):
        return _SvgImageHolder(blob, 100, 100, filename or 'image.svg')
    return _orig_from_blob(blob, filename)
_pptx_image.Image.from_blob = _from_blob_patch

_orig_from_file = getattr(_pptx_image.Image, 'from_file')
@classmethod
def _from_file_patch(cls, img):
    if hasattr(img, 'endswith') and img.endswith('.svg'):
        with open(img, 'rb') as f:
            b = f.read()
        return _SvgImageHolder(b, 100, 100, img)
    elif hasattr(img, 'read'): # In case a file object is passed directly
        if hasattr(img, 'seek'):
            img.seek(0)
        blob = img.read()
        if hasattr(img, 'seek'):
            img.seek(0)
        if _is_svg(blob):
            return _SvgImageHolder(blob, 100, 100, 'image.svg')
    return _orig_from_file(img)
_pptx_image.Image.from_file = _from_file_patch

