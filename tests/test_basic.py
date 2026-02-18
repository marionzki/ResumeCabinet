import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.cv_data import CVData
from model.modules import ExperienceModule, TextModule, PersonalInfoModule
from utils.pdf_generator import PDFGenerator

def test_pdf_gen():
    print("Initializing CV Data...")
    cv = CVData()
    
    # Add Personal Info
    cv.personal_info.modules.append(PersonalInfoModule(title="Bio", text_extended="This is a bio with a <a href='https://www.google.com' color='blue'>HYPERLINK</a> to test wrapping functionality."))
    
    # Add Experience
    cv.experience.modules.append(ExperienceModule(title="Senior Developer", company="Tech Corp", date_range="2020-Present", text_extended="Worked on things.", tags=["Python", "Leadership"]))
    
    # Add Education
    cv.education.modules.append(TextModule(title="BSc Computer Science", text_extended="University of Somewhere, 2010-2014"))

    print("Generating PDF...")
    gen = PDFGenerator(cv)
    output_path = "test_output.pdf"
    gen.generate(output_path)
    
    if os.path.exists(output_path):
        pass
    else:
        pass

if __name__ == "__main__":
    test_pdf_gen()
