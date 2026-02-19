
# Test script for markdown links translation and generation
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.cv_data import CVData
from utils.pdf_generator import PDFGenerator

def test_markdown_links():
    print("Testing Markdown links logic...")
    
    cv = CVData()
    cv.settings.language = "Inglés"
    
    # Mock Header Info with Markdown Link
    cv.header_info.linkedin = "[LINKEDIN PROFILE](https://linkedin.com/in/mario)"
    
    # Mock Experience Module with Markdown Link in description
    mod = cv.experience.modules[0]
    mod.text_extended = "Check my [Portfolio](https://portfolio.com) for details."
    mod.translations = {} 
    
    gen = PDFGenerator(cv)
    
    # Mock translator
    # We want to ensure it translates "LINKEDIN PROFILE" -> "MockLink" (simulated)
    # and "Portfolio" -> "MockPort"
    def mock_distinguish(text):
        if "LINKEDIN PROFILE" in text: return "MOCK PROFILE"
        if "Portfolio" in text: return "MOCK PORTFOLIO"
        return f"Translated {text}"
    
    # We need to mock the google translator instance inside the service
    # Because translate_text creates a new instance locally? No, logic is inside translate_text.
    # We can mock the method `translate_text` of the service, but we want to test the SPLITTING logic inside `translate_text`.
    # So we need to mock GoogleTranslator class.
    
    # We can rely on `test_link_translation.py` for the split logic correctness.
    # Here let's test `_process_text_formatting` of PDFGenerator.
    
    print("Testing _process_text_formatting...")
    # 1. Header Link
    processed_header = gen._process_text_formatting(cv.header_info.linkedin)
    print(f"Header: {processed_header}")
    assert '<a href="https://linkedin.com/in/mario"><font color="blue">LINKEDIN PROFILE</font></a>' in processed_header
    
    # 2. Body Link
    processed_body = gen._process_text_formatting(mod.text_extended)
    print(f"Body: {processed_body}")
    assert '<a href="https://portfolio.com"><font color="blue">Portfolio</font></a>' in processed_body
    
    print("Link processing verification passed.")

if __name__ == "__main__":
    test_markdown_links()
