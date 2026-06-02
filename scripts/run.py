import sys
import os

# Ensure the 'src' directory is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from surquest.utils.svg2pptx import SVG2Pptx

# Find all SVG files in the 'data' directory
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
svg_files = [f for f in os.listdir(data_dir) if f.endswith('.svg')]

svg2pptx = SVG2Pptx()
# Process each SVG file and convert it to PPTX
for svg_file in svg_files:
    print(f"Processing {svg_file}...")
    svg_input_path = os.path.join(data_dir, svg_file)
    output_path = os.path.join(data_dir, f"{os.path.splitext(svg_file)[0]}.slide.pptx")
    svg2pptx.convert(
        svg_input=svg_input_path,
        output_path=output_path
    )
    print(f"Saved PPTX to {output_path}")