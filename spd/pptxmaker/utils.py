"""Utility functions and classes for PPTXMaker."""

from pptx.dml.color import RGBColor
from .constants import EMU_PER_UNIT


class ColorUtils:
    """Utilities for color conversion and manipulation."""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> RGBColor:
        """
        Convert a hex color string (e.g., "#FF0000" or "#F00") to a python-pptx RGBColor object.
        
        Args:
            hex_color: The hex color string.
            
        Returns:
            An RGBColor object. Defaults to black (0, 0, 0) if conversion fails.
        """
        if not hex_color:
            return RGBColor(0, 0, 0)
        h = hex_color.lstrip('#')
        # Handle 3-digit hex codes by doubling each digit
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        try:
            return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except (ValueError, IndexError):
            return RGBColor(0, 0, 0)


class UnitConverter:
    """Handles conversion between various measurement units and EMUs (English Metric Units)."""
    
    def __init__(self, base_unit: str):
        """
        Initialize the converter with a base unit.
        
        Args:
            base_unit: The unit used in the input data (e.g., 'pixels', 'inches').
        """
        self._emu_factor = EMU_PER_UNIT.get(base_unit, EMU_PER_UNIT["pixels"])

    def to_emu(self, value: float) -> int:
        """
        Convert a value from the base unit to EMU.
        
        Args:
            value: The numeric value to convert.
            
        Returns:
            The equivalent value in EMUs.
        """
        return int(value * self._emu_factor)
