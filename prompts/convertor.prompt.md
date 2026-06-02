Act as an expert Python Software Engineer. Write a complete, production-grade Python solution that implements a two-pass compiler to parse an SVG file conforming to a specific metadata schema, translate it into an Intermediate Representation (IR) data layer, and finally render it into a native PowerPoint (`.pptx`) presentation.

### Step 1: The Intermediate Representation (IR Layer)
Define Python `dataclasses` that represent the abstract data layer. This schema must completely decouple the SVG structure from the PPTX structure. Include data models for:
- **Color:** Normalizes 3/6-digit hex codes and extracts explicit alpha/opacity (0.0 to 1.0).
- **TextSpan:** Captures plain text, font families, explicit font-sizes, weights (bold/normal), and font colors.
- **ShapeNode:** Captures unique IDs, geometric boundaries (x, y, width, height), background fill colors, and an ordered list of `TextSpan` objects.
- **IconNode:** Captures IDs, positioning, and stores raw nested SVG XML data strings for complex infographic elements.
- **ConnectorNode:** Captures source shape IDs, target shape IDs, line styling, geometric routing definitions (`straight`, `elbow`, `curve`), and arrowhead configurations for both the start and end of the line (e.g., `none`, `arrow`, `diamond`, `stealth`).
- **PresentationCanvas:** The root container holding collections of shapes, icons, and connectors.

### Step 2: The SVG Parser (Frontend)
Create an `SVGParser` class that accepts an SVG string or file, reads the XML tree using standard libraries (like `xml.etree.ElementTree`), and outputs a populated `PresentationCanvas` instance. It must parse according to these structural rules:

#### A. Content Cards & Blocks (Shapes & Text)
- **Tag Pattern:** `<g id="[unique_id]" data-element-type="infoBox">`
- **Logic:** 
  - Parse child geometric elements (like `<rect>`) into an IR `ShapeNode`. If multiple shapes exist, the element with the largest surface area defines the primary PowerPoint shape that receives the text frame.
  - Capture all essential styling (fill, stroke, opacity, and text margins) in the IR layer.
  - Extract nested `<text>` and its `<tspan>` sub-nodes into individual `TextSpan` models, preserving font-family, size, weight, and color. 
  - Use explicit `x` offsets and `dy` line heights for positioning.
  - Standalone text or text not visually contained within the primary shape's bounds should be mapped as independent text-only IR nodes.
- *Example Source:*
 <g id="card-1" data-element-type="infoBox">
  <rect x="100" y="100" width="300" height="150" rx="8" fill="#F0F0F0"/>
  <text x="120" y="140" font-family="Arial" font-size="16" font-weight="bold" fill="#333">
   <tspan x="120" dy="0">Title</tspan>
   <tspan x="120" dy="22" font-size="14" font-weight="normal" fill="#666">Body text.</tspan>
  </text>
 </g>

#### B. Complex Icons & Infographics
- **Tag Pattern:** `<g id="[id]" data-element-type="icon" data-icon-name="[name]">`
- **Logic:** Isolate the complete nested `<svg>` child element as a raw string block. Package this markup string alongside its canvas coordinates into an IR `IconNode`.
- *Example Source:*
 <g id="ico-user" data-element-type="icon" data-icon-name="user">
  <svg x="120" y="110" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" fill="#333"/></svg>
 </g>

#### C. Root-Level Connectors
- **Tag Pattern:** Root-level lines, paths, or polylines featuring `data-element-type="connector"`.
- **Logic:** Extract the routing strategy (`data-connector-type`), mapping nodes (`data-start` and `data-end`), and arrowhead markers by parsing the URL fragment in `marker-start` and `marker-end` attributes (e.g., `url(#arrow)` maps to `arrow`). Use `none` if the attribute is missing or set to `none`.
- *Example Source:*
 <defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
   <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
  </marker>
 </defs>
 <polyline id="conn-1" data-element-type="connector" data-connector-type="elbow" points="400,175 450,175 450,300" stroke="#007BFF" stroke-width="2" fill="none" data-start="card-1" data-end="card-2" marker-start="none" marker-end="url(#arrow)" />

#### Styling Rules:
- **Presentation Attributes Only:** Parse styling via element attributes (`fill`, `stroke`, `stroke-width`, `fill-opacity`, `stroke-opacity`). Ignore CSS `<style>` blocks or inline `style="..."` strings.
- **Color Format:** Accept only 3 or 6-digit hex formats. Ignore color strings or functional wrappers (`rgb()`).

### Step 3: The PowerPoint Generator (Backend)
Create a `PPTXGenerator` class that accepts a `PresentationCanvas` IR object and builds a `.pptx` presentation using `python-pptx`.
- **Execution Order:** 1. Render all standard shapes (`ShapeNode`), generating matching PowerPoint geometric shapes. Build a runtime map linking the IR node ID to the created native PowerPoint shape reference. Convert text spans into distinct native text-frame paragraphs.
 2. Render complex icons (`IconNode`) by dumping their raw SVG to scoped temporary files, embedding them onto slides via `slide.shapes.add_picture()`, and cleaning up the temporary files safely.
 3. Render connectors (`ConnectorNode`) last. Use the shape registry map generated in step 1 to programmatically bind the connectors directly to the source and target PowerPoint shape anchors using `connector.begin_connect()` and `connector.end_connect()`. Apply the specified routing styles and arrowhead start/end markers using native `python-pptx` line formatting properties.

Provide the complete, integrated script including all class definitions, type hints, and a clear execution example.
