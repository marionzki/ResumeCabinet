
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
        Handles Markdown links [text](url) by translating only the text part.
        """
        if not text or not isinstance(text, str):
            return text

        target_code = self.lang_map.get(target_lang_name)
        if not target_code or target_code == "es": 
            # Assuming source is Spanish, so no need to translate if target is Spanish
            return text
            
        try:
            # Check for markdown links
            import re
            pattern = r'(\[[^\]]+\]\(https?://[^)]+\))'
            parts = re.split(pattern, text)
            
            translated_parts = []
            
            # Use 'auto' for source detection
            translator = GoogleTranslator(source='auto', target=target_code)
            
            for part in parts:
                if not part: continue
                
                # Check if part is a link
                link_match = re.match(r'\[([^\]]+)\]\((https?://[^)]+)\)', part)
                if link_match:
                    # It's a link. Translate the text part.
                    original_text = link_match.group(1)
                    url = link_match.group(2)
                    
                    try:
                        trans_text = translator.translate(original_text)
                        if trans_text:
                            trans_text = trans_text.replace('\u200b', '')
                        else:
                            trans_text = original_text
                    except:
                        trans_text = original_text
                        
                    translated_parts.append(f"[{trans_text}]({url})")
                else:
                    # Normal text
                    if part.strip():
                        # Preserve whitespace
                        l_space = part[:len(part) - len(part.lstrip())]
                        r_space = part[len(part.rstrip()):]
                        stripped_part = part.strip()
                        
                        try:
                            # Sanitize before sending?
                            trans_part = translator.translate(stripped_part)
                            if trans_part:
                                trans_part = trans_part.replace('\u200b', '')
                            else:
                                trans_part = stripped_part
                            
                            translated_parts.append(l_space + trans_part + r_space)
                        except:
                            translated_parts.append(part)
                    else:
                        translated_parts.append(part)
            
            return "".join(translated_parts)
            
        except Exception as e:
            logging.error(f"Translation failed for '{text}': {e}")
            return text
