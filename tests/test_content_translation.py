
# Test content translation
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.cv_data import CVData
from utils.pdf_generator import PDFGenerator
from utils.translations import TRANSLATIONS

def test_content_translation():
    print("Testing content translation logic...")
    
    # 1. Create CV Data with English setting
    cv = CVData()
    cv.settings.language = "Inglés"
    
    # 2. Add translation to an experience module
    # Assuming first experience module
    mod = cv.experience.modules[0]
    mod.translations = {
        "Inglés": {
            "title": "Senior Camera Operator",
            "text_extended": "Recording audiovisual pieces for documentaries."
        }
    }
    
    # 3. Instantiate Generator
    gen = PDFGenerator(cv)
    
    # 4. Test _get_text method
    print(f"Language: {gen.language}")
    title = gen._get_text(mod, "title")
    print(f"Translated Title: {title}")
    assert title == "Senior Camera Operator"
    
    desc = gen._get_text(mod, "text_extended")
    print(f"Translated Desc: {desc}")
    assert desc == "Recording audiovisual pieces for documentaries."
    
    # 5. Generate PDF
    output_path = "test_english_content.pdf"
    try:
        gen.generate(output_path)
        print(f"PDF generated successfully at {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise

if __name__ == "__main__":
    test_content_translation()
