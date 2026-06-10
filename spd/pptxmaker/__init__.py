"""
PPTXMaker - A module to generate PowerPoint (.pptx) files from Canvas Document Schema JSON.

This package provides the PPTXMaker class which handles the conversion of 
JSON-based slide definitions (including shapes, text, images, and connectors)
into a structured PowerPoint presentation.
"""

from .pptxmaker import PPTXMaker
from .image_patch import apply_patch

# Automatically apply the SVG image patch to python-pptx when the package is imported.
# This patch enables better SVG support in PPTX files.
apply_patch()

__all__ = ["PPTXMaker"]
