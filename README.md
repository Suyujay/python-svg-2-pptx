# Python SVG to PPTX Compiler

A high-fidelity, two-pass compiler that translates structured SVG metadata into native PowerPoint (`.pptx`) presentations. It uses a strictly decoupled Intermediate Representation (IR) layer to bridge SVG semantics with PowerPoint's DrawingML.

## SVG Requirements & Schema

The compiler expects SVG files to conform to specific structural and metadata rules to guide the transformation properly:

### Canvas & Styling
- **Dimensions**: Fixed 16:9 aspect ratio is recommended (e.g., `viewBox="0 0 960 540" width="100%" height="100%"`).
- **Styling**: Use presentation attributes (`fill="#FF5733"`, `stroke="#e0e0e0"`) ONLY. Do **not** use inline CSS (`style="..."`) or `<style>` blocks.
- **Colors & Transparency**: Use 3 or 6-digit hex colors. For opacity, use explicit `fill-opacity="..."` or `stroke-opacity="..."` attributes (0.0 to 1.0) rather than 8-digit hex codes.
- **Typography**: Use standard fonts only (e.g., Arial, Calibri, Segoe UI). Use `<tspan>` for rich text formatting.

### Structural Rules
- **InfoBox (`data-element-type="infoBox"`)**: Wrap logical components in `<g id="[unique_id]" data-element-type="infoBox">`.
- **Connectors (`data-element-type="connector"`)**: Must be kept isolated at the root level (never nested inside other `<g>` groups) as `<line>` or `<polyline>`.
  - **Required attributes**: `data-start="[source_id]"`, `data-end="[target_id]"`, `data-connector-type="straight|elbow|curve"`.
  - **Arrowheads**: Supported via `marker-start` and `marker-end` attributes referencing standard marker defs (`none`, `arrow`, `diamond`, `stealth`).
- **Icons (`data-element-type="icon"`)**: Isolate inside a group and nest a child `<svg>` with explicit `x`, `y`, `width`, `height`, and `viewBox` attributes.

## Features

- **Decoupled Architecture**: Separate Frontend (Parser), IR Layer, and Backend (Generator).
- **Geometric Mapping**: Translates SVG shapes (`<rect>`, `<circle>`, `<ellipse>`, `<polygon>`) into native PowerPoint shapes.
- **Smart Text Handling**: Maps nested `<text>` and `<tspan>` elements to native text frames with custom styling (font-family, size, weight, color).
- **Intelligent Connectors**: Support for `straight`, `elbow`, and `curve` routing with automatic shape anchoring (`begin_connect` / `end_connect`).
- **Arrowhead Support**: Recognizes standard SVG markers and maps them to PowerPoint's `arrow`, `diamond`, and `stealth` line-end types.
- **Complex Icons**: Supports embedding nested `<svg>` fragments as high-quality pictures.
- **Hierarchical Grouping**: Reconstructs SVG group structures (`<g>`) as native PowerPoint GroupShapes, supporting nested hierarchies.
- **Styling Preservation**: Handles hex colors, CSS color names (e.g., `orange`, `blue`), stroke widths, corner radii, and translucency (alpha).
- **Logging Implementation**: Uses standard Python `logging` module for production-ready monitoring.

## Project Structure

```text
src/surquest/utils/svg2pptx/
├── parser.py           # SVG Parser (Frontend)
├── generator.py        # PPTX Generator (Backend)
├── svg2pptx.py         # Main entry point and orchestration
├── models/             # Intermediate Representation (IR) Layer
```

## Installation

Ensure you have the required dependencies:

```bash
pip install python-pptx lxml
```

## Usage

### Simple Conversion (Single Slide)

```python
from surquest.utils.svg2pptx import SVG2Pptx

# Initialize converter
converter = SVG2Pptx()

# Convert SVG file/string to PPTX
converter.convert(
    svg_input="input.svg",
    output_path="output.pptx"
)
```

### Multi-Slide Conversion

You can generate a multi-slide presentation by providing a list of SVG paths. The slides will be generated in the order provided.

```python
from surquest.utils.svg2pptx import SVG2Pptx

converter = SVG2Pptx()
converter.convert(
    svg_input=["slide1.svg", "slide2.svg", "slide3.svg"],
    output_path="multi_slide.pptx"
)
```

### Exporting and Importing Intermediate Representation (JSON)

The compiler allows you to export the Intermediate Representation (IR) to JSON, and recreate presentations directly from the JSON. This is particularly useful for debugging or programmatic manipulation before PPTX generation.

```python
from surquest.utils.svg2pptx import SVG2Pptx

converter = SVG2Pptx()

# 1. Export SVG directly to JSON IR
json_string = converter.to_json("input.svg")

# 2. Convert to PPTX and save the JSON IR simultaneously
converter.convert(
    svg_input="input.svg",
    output_path="output.pptx",
    export_as_json=True # Will also generate output.json
)

# 3. Create a presentation from a saved JSON IR
converter.from_json(
    json_input="output.json",
    output_path="restored_presentation.pptx"
)
```

### Advanced Usage (Low-level API)

```python
from surquest.utils.svg2pptx.parser import SVGParser
from surquest.utils.svg2pptx.generator import PPTXBackend

# 1. Parse SVG into Intermediate Representation
parser = SVGParser(svg_source, slide_width=12192000, slide_height=6858000, svg_ns="{http://www.w3.org/2000/svg}")
ir_slide = parser.parse()

# 2. Render IR to PPTX
prs = PPTXBackend([ir_slide]).render()
prs.save("output.pptx")
```

## Development & Testing

### Running the Example

You can use the provided run script to process SVG files in the `data/` directory:

```bash
python scripts/run.py
```

## License

This project is licensed under the MIT License.
