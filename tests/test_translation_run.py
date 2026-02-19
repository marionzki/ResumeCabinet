
# Test script to verify PDF generation with English setting
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.cv_data import CVData
from utils.pdf_generator import PDFGenerator
from utils.translations import TRANSLATIONS

def test_translation():
    print("Testing translation logic...")
    
    # 1. Create CV Data with English setting
    cv = CVData()
    cv.settings.language = "Inglés"
    
    # Mock data with "Actualidad"
    cv.experience.modules[0].date_range = "01/2020 - Actualidad"
    
    # 2. Instantiate Generator
    gen = PDFGenerator(cv)
    
    # 3. Test _t method
    print(f"Language: {gen.language}")
    print(f"Translation for 'experience': {gen._t('experience')}")
    assert gen._t('experience') == "WORK EXPERIENCE"
    
    # 4. Test date translation
    print(f"Translation for date '01/2020 - Actualidad': {gen._translate_date('01/2020 - Actualidad')}")
    assert "Present" in gen._translate_date("01/2020 - Actualidad")
    
    # 5. Generate PDF
    output_path = "test_english.pdf"
    try:
        gen.generate(output_path)
        print(f"PDF generated successfully at {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise

if __name__ == "__main__":
    test_translation()
