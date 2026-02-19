
from deep_translator import GoogleTranslator
import logging

class TranslationService:
    def __init__(self):
        # Map internal language names to ISO codes
        self.lang_map = {
            "Inglés": "en",
            "Gallego": "gl",
            "Catalán": "ca",
            "Español": "es"
        }

    def translate_text(self, text, target_lang_name):
        """
        Translate text to the target language using deep-translator (Google Translate).
        Returns original text if translation fails or language not supported.
        """
        if not text or not isinstance(text, str):
            return text

        target_code = self.lang_map.get(target_lang_name)
        if not target_code or target_code == "es": 
            # Assuming source is Spanish, so no need to translate if target is Spanish
            return text
            
        try:
            # Use 'auto' for source detection
            translator = GoogleTranslator(source='auto', target=target_code)
            result = translator.translate(text)
            
            # Sanitization: Remove zero-width spaces which cause rendering issues in ReportLab
            if result:
                result = result.replace('\u200b', '')
                
            return result
        except Exception as e:
            logging.error(f"Translation failed for '{text}': {e}")
            return text
