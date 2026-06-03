import json
from pathlib import Path
import pytest
from surquest.utils.svg2pptx import SVG2Pptx
import os

DATA_DIR = Path(__file__).parent / "data"
SVG_FILES = list(DATA_DIR.glob("*.svg"))

@pytest.mark.parametrize("svg_file", SVG_FILES, ids=lambda path: path.name)
class TestDataFiles:

    converter = SVG2Pptx()

    def test_convert_svg_data_files(self, svg_file, tmp_path):
        
        converter = self.converter
        out_pptx = tmp_path / f"{svg_file.stem}.pptx"
        
        # Check that convert doesn't crash on standard test data
        converter.convert(svg_input=str(svg_file), output_path=str(out_pptx), export_as_json=True)
        
        # Check outputs were created
        assert out_pptx.exists()
        
        out_json = tmp_path / f"{svg_file.stem}.json"
        assert out_json.exists()

    def test_to_json_matches_expected(self, svg_file):
        converter = self.converter
        expected_json_path = svg_file.with_suffix(".json")
        
        if not expected_json_path.exists():
            pytest.skip(f"No corresponding JSON file found for {svg_file.name}")
            
        with open(expected_json_path, "r", encoding="utf-8") as f:
            expected_data = json.load(f)
            
        generated_json_str = converter.to_json(svg_input=str(svg_file))
        generated_data = json.loads(generated_json_str)
        
        # Verify length and content are matching
        assert expected_data == generated_data

