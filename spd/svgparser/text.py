import re
from typing import List, Dict, Any, Optional, Tuple
from .utils import f, localname
from .constants import SIZE_COEFFICIENT

class TextParser:
    """
    Handles the parsing of SVG <text> and <tspan> elements,
    mapping them to the hierarchical paragraph/run format in the schema.
    Also handles the heuristic association of "floating" text elements
    with their nearest enclosing shapes.
    """

    @staticmethod
    def map_alignment(anchor: Optional[str]) -> str:
        """Map SVG text-anchor style to schema horizontal alignment."""
        return {"middle": "CENTER", "end": "RIGHT"}.get(anchor or "start", "LEFT")

    @staticmethod
    def run_from_attrs(text: str, attrs: Dict[str, str], strip_leading: bool = False) -> Optional[Dict[str, Any]]:
        """
        Create a schema text 'run' from a string and a set of inherited attributes.
        
        Args:
            text: Raw text content.
            attrs: Dictionary of styling attributes (font-family, fill, etc.).
            strip_leading: Whether to strip leading whitespace (useful for first run in paragraph).
            
        Returns:
            A run dictionary or None if text is effectively empty.
        """
        if text is None:
            return None
            
        # Standardize whitespace
        cleaned = re.sub(r"\s+", " ", text)
        if strip_leading:
            cleaned = cleaned.lstrip()
            
        if not cleaned or cleaned == " ":
            return None
            
        run: Dict[str, Any] = {"text": cleaned}
        
        # Map SVG font attributes to schema
        if attrs.get("font-family"):
            run["font_name"] = attrs["font-family"]
        if attrs.get("font-size") is not None:
            run["font_size"] = f(attrs.get("font-size"))
            
        fw = attrs.get("font-weight")
        if fw in ("bold", "700", "800", "900"):
            run["bold"] = True
            
        if attrs.get("font-style") == "italic":
            run["italic"] = True
        if attrs.get("text-decoration") == "underline":
            run["underline"] = True
            
        if attrs.get("fill"):
            run["color_hex"] = attrs["fill"]
            
        return run

    @staticmethod
    def collect_runs(node, inherited: Dict[str, str], is_first: bool = False) -> List[Dict[str, Any]]:
        """
        Recursively traverse text nodes (including tspans) to collect all text runs,
        correctly handling SVG style inheritance.
        """
        style_keys = ("font-family", "font-size", "font-weight",
                      "font-style", "text-decoration", "fill")
        
        # Merge local node attributes with inherited ones
        local = dict(inherited)
        for k in style_keys:
            if node.get(k) is not None:
                local[k] = node.get(k)

        runs: List[Dict[Dict[str, Any]]] = []

        # Handle text before any children
        if node.text:
            r = TextParser.run_from_attrs(node.text, local, strip_leading=is_first and not runs)
            if r:
                runs.append(r)

        # Process child elements (typically <tspan>)
        for child in list(node):
            if localname(child.tag) == "tspan":
                child_is_first = is_first and not runs
                runs.extend(TextParser.collect_runs(child, local, is_first=child_is_first))
            
            # Handle text appearing after a child element (tail)
            if child.tail:
                r = TextParser.run_from_attrs(child.tail, local, strip_leading=is_first and not runs)
                if r:
                    runs.append(r)
        return runs

    @staticmethod
    def paragraphs_from_text(text_el) -> List[Dict[str, Any]]:
        """
        Break an SVG <text> element into one or more paragraphs.
        New paragraphs are inferred if children have absolute 'x' or 'y' offsets.
        """
        inherited = {}
        alignment = TextParser.map_alignment(text_el.get("text-anchor"))
        
        # Check if we have multi-line text (via multiple tspans with explicit offsets)
        direct_tspans = [c for c in list(text_el) if localname(c.tag) == "tspan"]
        paragraphs: List[Dict[str, Any]] = []

        if not direct_tspans:
            # Simple single-block text
            runs = TextParser.collect_runs(text_el, inherited, is_first=True)
            if runs:
                paragraphs.append({"alignment": alignment, "runs": runs})
            return paragraphs

        style_keys = ("font-family", "font-size", "font-weight",
                      "font-style", "text-decoration", "fill")
        base = {k: text_el.get(k) for k in style_keys if text_el.get(k) is not None}

        current_runs = []
        if text_el.text:
            r = TextParser.run_from_attrs(text_el.text, base, strip_leading=True)
            if r:
                current_runs.append(r)

        for child in list(text_el):
            tag = localname(child.tag)
            if tag == "tspan":
                # Explicit positioning on a tspan usually indicates a new line/paragraph
                has_pos = any(child.get(k) is not None for k in ("x", "y", "dy"))
                runs = TextParser.collect_runs(child, base, is_first=not current_runs)
                
                if has_pos and current_runs:
                    paragraphs.append({"alignment": alignment, "runs": current_runs})
                    current_runs = runs
                else:
                    current_runs.extend(runs)
            else:
                runs = TextParser.collect_runs(child, base, is_first=not current_runs)
                current_runs.extend(runs)
                
            if child.tail:
                r = TextParser.run_from_attrs(child.tail, base, strip_leading=not current_runs)
                if r:
                    current_runs.append(r)

        if current_runs:
            paragraphs.append({"alignment": alignment, "runs": current_runs})
        return paragraphs

    @staticmethod
    def parse_standalone_text(text_el, id_gen, parent_shape: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Convert a <text> element that isn't inside any shape into a standalone 'textbox' node.
        
        Args:
            text_el: The SVG text element.
            id_gen: ID Generator instance.
            parent_shape: Optional shape this text originates from (used for centering).
            
        Returns:
            A textbox element dictionary.
        """
        paragraphs = TextParser.paragraphs_from_text(text_el)
        if not paragraphs:
            return None

        _id = text_el.get("id") or id_gen.gen_id("text")
        id_gen.register_id(_id)

        # Heuristic calculations for textbox dimensions (SVG text width != PPTX textbox width)
        max_width = 0.0
        total_height = 0.0
        first_fsize = 14.0

        for i, p in enumerate(paragraphs):
            p_width = 0.0
            max_fsize_in_p = 0.0
            for r in p.get("runs", []):
                t = r.get("text", "")
                fsize = r.get("font_size", 14.0)
                bold = r.get("bold", False)
                
                # Crude character width multiplier
                char_factor = 0.75 if bold else 0.6 
                p_width += len(t) * fsize * char_factor
                max_fsize_in_p = max(max_fsize_in_p, fsize)
            
            if max_fsize_in_p == 0:
                max_fsize_in_p = 14.0
            if i == 0:
                first_fsize = max_fsize_in_p

            total_height += max_fsize_in_p * 1.5
            max_width = max(max_width, p_width)

        if max_width < 10:
            max_width = 100
        if total_height < 10:
            total_height = 20

        x = f(text_el.get("x"))
        y = f(text_el.get("y"))
        
        box_width = max_width + 10
        anchor = text_el.get("text-anchor", "start")
        
        # Adjust X coordinate based on SVG anchor (start/middle/end)
        if anchor == "middle" and parent_shape and "position" in parent_shape:
            x = parent_shape["position"]["x"]
            coef = SIZE_COEFFICIENT.get("textbox", {}).get("width", 1.0)
            box_width = parent_shape["position"]["width"] / coef
        elif anchor == "middle":
            x -= (box_width / 2)
        elif anchor == "end":
            x -= box_width

        return {
            "id": _id,
            "type": "textbox",
            "position": {
                "x": round(x, 3),
                "y": round(max(0, y - first_fsize), 3),
                "width": round(box_width * SIZE_COEFFICIENT.get("textbox", {}).get("width", 1.0), 3),
                "height": round(total_height, 3),
                "rotation_degrees": 0,
            },
            "text_content": {
                "word_wrap": True,
                "vertical_alignment": "TOP",
                "paragraphs": paragraphs,
            },
        }

    @staticmethod
    def text_fits_in_shape(text_el, bbox: Tuple[float, float, float, float], font_size: float) -> bool:
        """
        Check if a shape is likely intended to contain a given text element
        based on their respective dimensions.
        """
        _, _, w, h = bbox
        min_h = font_size + 2
        min_w = font_size
        return w >= min_w and h >= min_h

    @staticmethod
    def associate_text(shapes: List[Dict[str, Any]], texts: List, id_gen, fallback_to_standalone: bool = False) -> List[Dict[str, Any]]:
        """
        Attempt to nest text elements into shapes by checking for spatial overlap.
        
        If a text element is 'inside' a shape and fits, it is added to the shape's 
        text_content. Otherwise, it is either returned as unassociated or converted 
        to a standalone textbox.
        
        Args:
            shapes: List of shape element dictionaries.
            texts: List of XML text nodes.
            id_gen: ID Generator instance.
            fallback_to_standalone: If True, unassociated text becomes a separate textbox.
            
        Returns:
            A list of new textbox nodes if fallback is True, else original unassociated XML nodes.
        """
        unassociated_texts = []
        standalone_nodes = []
        shape_text_map = {id(s): [] for s in shapes}
        shape_by_id = {id(s): s for s in shapes}
        unmapped_texts = []

        # Find the best container shape for each text element
        for text_el in texts:
            tx = f(text_el.get("x"))
            ty = f(text_el.get("y"))
            fsize = f(text_el.get("font-size"), 12)
            target = None
            
            # Iterate backwards (top-to-bottom in SVG z-order)
            for shape in reversed(shapes):
                bbox = shape.get("_bbox")
                if not bbox: continue
                sx, sy, sw, sh = bbox
                # Point-in-rect check with a small 2px fudge factor
                inside = (sx - 2 <= tx <= sx + sw + 2) and (sy - 2 <= ty - fsize) and (ty <= sy + sh + 2)
                if inside and TextParser.text_fits_in_shape(text_el, bbox, fsize):
                    target = shape
                    break
            
            if target is not None:
                shape_text_map[id(target)].append(text_el)
            else:
                unmapped_texts.append(text_el)

        # Handle text that didn't land in any shape
        for text_el in unmapped_texts:
            if fallback_to_standalone:
                standalone = TextParser.parse_standalone_text(text_el, id_gen)
                if standalone:
                    standalone_nodes.append(standalone)
            else:
                unassociated_texts.append(text_el)

        # Apply mapped text to their shapes
        for s_id, mapped_texts in shape_text_map.items():
            shape = shape_by_id[s_id]
            
            if len(mapped_texts) == 1:
                # Direct nesting for single text block
                text_el = mapped_texts[0]
                paragraphs = TextParser.paragraphs_from_text(text_el)
                if not paragraphs:
                    continue
                    
                tx, ty = f(text_el.get("x")), f(text_el.get("y"))
                fsize = f(text_el.get("font-size"), 12)
                sx, sy, sw, sh = shape.get("_bbox", (0, 0, 0, 0))
                th = round(fsize * 1.5, 0)
                
                # Heuristic for vertical positioning (TOP vs MIDDLE vs BOTTOM)
                align_v, margins = "MIDDLE", {}
                pt_top, pt_left = (ty - fsize) - sy, tx - sx
                
                if pt_top < (sh / 3) and th < sh / 3:
                    align_v = "TOP"
                    if pt_top > 3:
                        margins["top"] = round(pt_top, 2)
                elif pt_top > (sh * 0.6):
                    align_v = "BOTTOM"
                    
                if 4 < pt_left < (sw / 2):
                    margins["left"] = round(pt_left, 2)
                    
                tc = shape.setdefault("text_content", {
                    "word_wrap": True, 
                    "vertical_alignment": align_v, 
                    "paragraphs": []
                })
                if margins:
                    tc.setdefault("margins", {}).update(margins)
                tc["paragraphs"].extend(paragraphs)
                
            elif len(mapped_texts) > 1:
                # Multiple text blocks in one shape -> better treated as separate textboxes
                # layered on top, since our schema only supports one text_content block per shape.
                for text_el in mapped_texts:
                    if fallback_to_standalone:
                        standalone = TextParser.parse_standalone_text(text_el, id_gen, parent_shape=shape)
                        if standalone:
                            standalone_nodes.append(standalone)
                    else:
                        unassociated_texts.append(text_el)
                        
        return unassociated_texts if not fallback_to_standalone else standalone_nodes
