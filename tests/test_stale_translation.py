
# Test for stale translation detection
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.cv_data import CVData
from utils.pdf_generator import PDFGenerator

def test_stale_translation():
    print("Testing stale translation logic...")
    
    cv = CVData()
    cv.settings.language = "Inglés"
    
    mod = cv.experience.modules[0]
    mod.title = "Cámara"
    mod.translations = {
        "Inglés": {
            "title": "Camera",
            "_source_title": "Cámara"
        }
    }
    
    gen = PDFGenerator(cv)
    # Mock translator
    gen.translator.translate_text = MagicMock(side_effect=lambda text, lang: f"Translated: {text}")
    
    # 1. Initial State: Valid
    print("1. Testing valid translation...")
    text = gen._get_text(mod, "title")
    print(f"Result: {text}")
    assert text == "Camera"
    gen.translator.translate_text.assert_not_called()
    
    # 2. Update Source Text
    print("2. Updating source text...")
    mod.title = "Director de Fotografía"
    # Should trigger stale detection
    
    text = gen._get_text(mod, "title")
    print(f"Result: {text}")
    assert text == "Translated: Director de Fotografía"
    
    # Check if _source_ was updated
    new_source = mod.translations["Inglés"]["_source_title"]
    print(f"New stored source: {new_source}")
    assert new_source == "Director de Fotografía"
    
    print("Stale translation verification passed.")

if __name__ == "__main__":
    test_stale_translation()
