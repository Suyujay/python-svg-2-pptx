import os
import json
import dataclasses
from enum import Enum
from pathlib import Path
from typing import Union

from .parser import SVGParser
from .generator import PPTXBackend

class _IRJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            d = dict(obj.__dict__)
            d["__type__"] = obj.__class__.__name__
            return d
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)

class SVG2Pptx:
    """Main class for converting SVG to PowerPoint."""
    
    # Centralized configuration and constants
    SVG_NS: str = "{http://www.w3.org/2000/svg}"
    
    # Standard 16:9 slide dimensions in EMU (13.333" x 7.5")
    SLIDE_WIDTH_EMU: int = 12192000
    SLIDE_HEIGHT_EMU: int = 6858000

    def __init__(self, slide_width_emu: int = None, slide_height_emu: int = None, svg_ns: str = None):
        """
        Initialize the SVG to PPTX converter with optional configuration.
        """
        self.slide_width_emu = slide_width_emu or self.SLIDE_WIDTH_EMU
        self.slide_height_emu = slide_height_emu or self.SLIDE_HEIGHT_EMU
        self.svg_ns = svg_ns or self.SVG_NS
    
    def convert(self, svg_input: Union[str, Path], output_path: Union[str, Path]) -> None:
        """
        Convert an SVG string or file to a PPTX presentation and JSON output.
        
        Args:
            svg_input: Either an SVG string format or a path to an SVG file.
            output_path: Path where the output .pptx should be saved.
                         A corresponding .json file will also be created.
        """
        svg_source = ""
        if isinstance(svg_input, (str, Path)):
            try:
                # Try to check if it's a file path
                if os.path.isfile(svg_input):
                    with open(svg_input, "r", encoding="utf-8") as f:
                        svg_source = f.read()
                else:
                    svg_source = str(svg_input)
            except Exception:
                # If path too long or invalid, treat as string
                svg_source = str(svg_input)
        else:
            raise TypeError("svg_input must be a string containing SVG content or a file path.")

        ir = SVGParser(
            svg_source,
            slide_width=self.slide_width_emu,
            slide_height=self.slide_height_emu,
            svg_ns=self.svg_ns
        ).parse()
        
        output_path_str = str(output_path)
        json_path = output_path_str.replace(".pptx", ".json")
        if json_path == output_path_str:
            json_path += ".json"
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ir, f, cls=_IRJSONEncoder, indent=2)
        print(f"[OK] Wrote JSON IR to {json_path}")

        prs = PPTXBackend(ir).render()
        prs.save(output_path_str)
        print(f"[OK] Wrote PPTX to {output_path_str}")