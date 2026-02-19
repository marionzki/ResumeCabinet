
# Link Text Translation Test
from utils.translator import TranslationService
import re

def process_markdown_links(text):
    # Regex for [text](url)
    pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
    
    def replace_match(match):
        text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}"><font color="blue">{text}</font></a>'
        
    return re.sub(pattern, replace_match, text)

def translate_preserving_links(ts, text, target_lang):
    # 1. Extract links to protect them
    # We want to translate "text" inside [text](url) but keep (url) as is.
    # Actually, Google Translate might mess up Markdown syntax if we send it raw.
    # Better approach: 
    # Option A: Replace [text](url) with a placeholder, translate, then put back? No, we want to translate "text".
    # Option B: Use regex to find [text](url), extract "text", translate it, reconstruct string.
    
    # Let's try Option B: Parse, Translate Text parts, Reassemble.
    
    pattern = r'(\[[^\]]+\]\(https?://[^)]+\))'
    parts = re.split(pattern, text)
    
    translated_parts = []
    for part in parts:
        # Check if part is a link
        link_match = re.match(r'\[([^\]]+)\]\((https?://[^)]+)\)', part)
        if link_match:
            # It's a link. Translate the text part.
            original_text = link_match.group(1)
            url = link_match.group(2)
            
            trans_text = ts.translate_text(original_text, target_lang)
            translated_parts.append(f"[{trans_text}]({url})")
        else:
            # Normal text (maybe)
            if part.strip():
                trans_part = ts.translate_text(part, target_lang)
                translated_parts.append(trans_part)
            else:
                translated_parts.append(part)
                
    return "".join(translated_parts)

def test_link_translation():
    ts = TranslationService()
    
    original = "Visita mi [perfil de LinkedIn](https://linkedin.com) para más info."
    print(f"Original: {original}")
    
    translated = translate_preserving_links(ts, original, "Inglés")
    print(f"Translated: {translated}")
    
    # Process for PDF
    final_xml = process_markdown_links(translated)
    print(f"Final XML: {final_xml}")

if __name__ == "__main__":
    test_link_translation()
