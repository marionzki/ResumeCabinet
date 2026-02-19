
from utils.translator import TranslationService
import sys

def debug_translation():
    # Force utf-8 for output if possible, but safer to just repr()
    ts = TranslationService()
    
    # Text from user_data.json causing issues
    text_profile = "uso de lenguajes como Python, C++"
    text_education = "Uso de lenguajes de programación orientados a objetos (C# y Python)"
    
    # Translate
    trans_profile = ts.translate_text(text_profile, "Inglés")
    trans_education = ts.translate_text(text_education, "Inglés")
    
    print(f"Original Profile: {text_profile}")
    # Print repr to see the codes
    print(f"Translated Profile Repr: {repr(trans_profile)}")
    
    print("-" * 20)
    
    print(f"Original Education: {text_education}")
    print(f"Translated Education Repr: {repr(trans_education)}")

if __name__ == "__main__":
    debug_translation()
