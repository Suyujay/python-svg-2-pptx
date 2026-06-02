# Python SVG to PPTX Compiler

A high-fidelity, two-pass compiler that translates structured SVG metadata into native PowerPoint (`.pptx`) presentations. It uses a strictly decoupled Intermediate Representation (IR) layer to bridge SVG semantics with PowerPoint's DrawingML.

## Features

- **Decoupled Architecture**: Separate Frontend (Parser), IR Layer, and Backend (Generator).
- **Geometric Mapping**: Translates SVG shapes (`<rect>`, etc.) into native PowerPoint shapes.
- **Smart Text Handling**: Maps nested `<text>` and `<tspan>` elements to native text frames with custom styling (font-family, size, weight, color).
- **Intelligent Connectors**: Support for `straight`, `elbow`, and `curve` routing with automatic shape anchoring (`begin_connect` / `end_connect`).
- **Arrowhead Support**: Recognizes standard SVG markers and maps them to PowerPoint's `arrow`, `diamond`, and `stealth` line-end types.
- **Complex Icons**: Supports embedding nested `<svg>` fragments as high-quality pictures.
- **Hierarchical Grouping**: Reconstructs SVG group structures (`<g>`) as native PowerPoint GroupShapes, supporting nested hierarchies.
- **Styling Preservation**: Handles hex colors, stroke widths, corner radii, and translucency (alpha).

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

### Simple Conversion

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

### Advanced Usage (Low-level API)

```python
from surquest.utils.svg2pptx import SVGParser, PPTXBackend

# 1. Parse SVG into Intermediate Representation
parser = SVGParser(svg_source, slide_width=12192000, slide_height=6858000, svg_ns="{http://www.w3.org/2000/svg}")
ir_slide = parser.parse()

# 2. Render IR to PPTX
prs = PPTXBackend(ir_slide).render()
prs.save("output.pptx")
```

## Development & Testing

### Running the Example

You can use the provided run script to process SVG files in the `data/` directory:

```bash
python scripts/run.py
```

### SVG Metadata Schema

The compiler expects SVG files with specific `data-` attributes to guide the transformation:
- `data-element-type`: `infoBox`, `icon`, or `connector`.
- `data-start` / `data-end`: Tracking IDs for connectors.
- `data-connector-type`: Routing strategy (`straight`, `elbow`, `curve`).

## License

This project is licensed under the MIT License.

