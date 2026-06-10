"""SVG Image patching for python-pptx."""

import hashlib
from pptx.parts import image as _pptx_image


class SvgImageHolder:
    """A holder for SVG image data to be inserted into a PPTX."""
    def __init__(self, blob, width, height, filename):
        self.blob = blob
        self.filename = filename
        self.ext = 'svg'
        self.content_type = 'image/svg+xml'
        self._px_width = width
        self._px_height = height

    @property
    def sha1(self):
        return hashlib.sha1(self.blob).hexdigest()
        
    @property
    def size(self):
        return (self._px_width, self._px_height)
        
    @property
    def dpi(self):
        return (72, 72)


def is_svg(blob):
    """Check if the given blob is an SVG image."""
    s = blob[:1024].lower()
    return b'<svg' in s or (b'svg' in s and b'http://www.w3.org' in s)


_orig_from_blob = getattr(_pptx_image.Image, 'from_blob')


@classmethod
def from_blob_patch(cls, blob, filename=None):
    """Patched version of Image.from_blob that handles SVG images."""
    if is_svg(blob):
        return SvgImageHolder(blob, 100, 100, filename or 'image.svg')
    return _orig_from_blob(blob, filename)


def apply_patch():
    """Apply the SVG image patch to python-pptx."""
    _pptx_image.Image.from_blob = from_blob_patch
