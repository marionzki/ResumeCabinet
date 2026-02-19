
import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.cv_data import CVData
from utils.pdf_generator import PDFGenerator
from model.modules import ExperienceModule

def test_summary_logic():
    print("Testing summary logic...")
    
    cv = CVData()
    cv.experience.modules = []
    
    mod = ExperienceModule(title="Test", company="Test Co", date_range="2022")
    mod.text_extended = "Extended Text"
    mod.text_summary = "Summary Text"
    mod.use_summary = True
    
    cv.experience.modules.append(mod)
    
    gen = PDFGenerator(cv)
    
    # Mock _get_text to track calls
    gen._get_text = MagicMock(return_value="Mocked Text")
    gen._draw_paragraph = MagicMock(return_value=100)
    gen._draw_section = PDFGenerator._draw_section.__get__(gen, PDFGenerator) # Bind original method
    # But wait, _draw_section calls _get_text.
    # We need to run generate or _draw_section.
    
    # Let's run _draw_section directly to test the loop
    gen.styles = MagicMock()
    c = MagicMock()
    
    print("Running _draw_section with use_summary=True...")
    gen._draw_section(c, cv.experience, 0, 0, 100)
    
    # Check calls
    print(f"All calls: {gen._get_text.call_args_list}")
    calls = [args[1] for args, _ in gen._get_text.call_args_list if args[0] == mod]
    print(f"Calls for module: {calls}")
    
    if "text_summary" in calls and "text_extended" not in calls:
        print("PASS: Only text_summary was fetched.")
    else:
        print("FAIL: Unexpected calls.")

    # Loop 2: use_summary = False
    mod.use_summary = False
    gen._get_text.reset_mock()
    
    print(f"Modules in section: {cv.experience.modules}")
    print("\nRunning _draw_section with use_summary=False...")
    try:
        gen._draw_section(c, cv.experience, 0, 0, 100)
    except Exception as e:
        print(f"Exception: {e}")
    
    print(f"All calls (pass 2): {gen._get_text.call_args_list}")
    calls = [args[1] for args, _ in gen._get_text.call_args_list if args[0] == mod]
    print(f"Calls for module: {calls}")
    
    if "text_extended" in calls and "text_summary" not in calls:
        print("PASS: Only text_extended was fetched.")
    else:
        print("FAIL: Unexpected calls.")

if __name__ == "__main__":
    test_summary_logic()
