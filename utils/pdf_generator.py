from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from .pdf_styles import *
from model.modules import AvatarModule, ImageModule
import os
from .translations import TRANSLATIONS
from .translator import TranslationService

from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

class PDFGenerator:
    def __init__(self, cv_data):
        self.cv_data = cv_data
        self.styles = getSampleStyleSheet()
        self.style_body = ParagraphStyle(
            'Body',
            parent=self.styles['Normal'],
            fontName=FONT_BODY,
            fontSize=9,
            leading=12,
            textColor=COLOR_TEXT_MAIN,
            alignment=TA_LEFT
        )
        self.language = cv_data.settings.language if cv_data.settings.language in TRANSLATIONS else "Español"
        self.trans = TRANSLATIONS.get(self.language, TRANSLATIONS["Español"])
        self.translator = TranslationService()

    def _t(self, key):
        """Translate a key based on current language. If not found, return key (or specific fallback logic)."""
        # Key should be lowercase for lookup
        k = key.lower()
        return self.trans.get(k, key)

    def _get_text(self, module, field_name, default_value=""):
        """Get text from module, preferring translation if available. Auto-translates if missing or stale."""
        # 1. Check if language is default
        is_default = self.language == "Español" 
        
        original_text = getattr(module, field_name, default_value)
        if is_default:
            return original_text
            
        # 2. Check stored translations
        if not hasattr(module, 'translations'):
            module.translations = {} # Ensure dict exists
            
        if self.language not in module.translations:
            module.translations[self.language] = {}
            
        lang_trans = module.translations[self.language]
        
        # Check for Stale Translation
        # logic: if we have a translation, check if the source text it was based on matches current text
        source_key = f"_source_{field_name}"
        stored_source = lang_trans.get(source_key)
        
        # If we have a translation BUT stored_source doesn't match original_text, it's stale.
        # Exception: if stored_source is None (legacy data), we might assume it's valid OR invalid.
        # Let's assume valid to prevent overwriting manual work, BUT update the source now?
        # No, if we assume valid, we lock it. 
        # User request: "Detect if changes happened".
        # So if stored_source is missing, we can't be sure. 
        # Strategy: If missing, set it to current? No, next time it will match.
        # Let's simple comparison: if stored_source is set and != original, INVALIDATE.
        # If stored_source is NOT set, we assume it matches (fallback for legacy), 
        # UNLESS we want to force re-translate? 
        # Use Case: User adds link to Spanish text. Legacy translation has no link.
        # If we don't re-translate, link is missing in English PDF.
        # So maybe if missing, we SHOULD re-translate? 
        # But that overwrites manual edits from before this feature.
        # Compromise: Only invalidate if stored_source IS present and differs. 
        # (This means first time after update, it won't detect. But future edits will).
        # WAIIIT. If I change text now, `_source_` won't be there.
        # So I need to start saving `_source_` when generating.
        
        is_stale = False
        if source_key in lang_trans:
            if lang_trans[source_key] != original_text:
                is_stale = True
                print(f"Translation for '{field_name}' is stale (source changed). Re-translating...")
        else:
            # Source key missing (legacy data or manual edit pre-tracking).
            # We must assume it might be stale to ensure correctness.
            # This might overwrite manual legacy translations, but ensures consistency for the user's workflow.
            is_stale = True
            print(f"Translation for '{field_name}' lacks source tracking. Re-translating...")
        
        # If valid translation exists and not stale, return it
        if not is_stale and field_name in lang_trans and lang_trans[field_name]:
             return lang_trans[field_name]
            
        # 3. Auto-translate if missing or stale
        if original_text:
            if field_name not in lang_trans:
                 print(f"Auto-translating '{field_name}' to {self.language}...")
                 
            print(f"DEBUG: Translating '{original_text}'...")
            translated = self.translator.translate_text(original_text, self.language)
            print(f"DEBUG: Result: '{translated}'")
            # Store it
            lang_trans[field_name] = translated
            lang_trans[source_key] = original_text # Store source for future checks
            return translated
            
        return original_text

    def _translate_date(self, date_str):
        """Translates specific keywords in date string (e.g. 'Actualidad' -> 'Present')."""
        if not date_str: return ""
        
        # Mapping of common terms to the target language term
        # We rely on the dictionary having keys like "actualidad" -> "Present" (in English dict)
        
        # Simple string replacement for known keywords
        keywords = ["Actualidad", "Present", "Current", "Hoy", "Today"]
        
        lower_date = date_str.lower()
        
        for k in keywords:
            if k.lower() in lower_date:
                # If the keyword is found, we want to replace it with the target language equivalent
                # The target equivalent is found by looking up k.lower() in self.trans
                target = self._t(k.lower())
                
                # Reform the string preserving case if possible, or just replace
                # This is a simple replace, might need regex for exact word match
                import re
                return re.sub(k, target, date_str, flags=re.IGNORECASE)
                
        return date_str

    def generate(self, filepath):
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # 1. Sidebar (Left)
        sidebar_width = width * 0.27
        # Draw Sidebar Background
        c.setFillColor(COLOR_HEADER_BG) 
        
        current_y = height - MARGIN
        
        col_gap = 20
        col1_x = MARGIN
        col1_w = sidebar_width - MARGIN - col_gap/2
        
        col2_x = sidebar_width + col_gap/2
        col2_w = width - sidebar_width - MARGIN
        
        # Draw Separator Line
        c.setStrokeColor(COLOR_SECONDARY)
        c.line(sidebar_width, MARGIN, sidebar_width, height - MARGIN)
        
        # --- LEFT COLUMN ---
        y_left = current_y
        
        # 1. Avatar (Optional)
        avatar_mod = None
        for m in self.cv_data.personal_info.modules:
             if isinstance(m, AvatarModule) and m.is_active:
                 avatar_mod = m
                 break
        
        if avatar_mod and os.path.exists(avatar_mod.image_path):
            try:
                img = ImageReader(avatar_mod.image_path)
                img_w = 120
                img_h = 120
                c.drawImage(avatar_mod.image_path, col1_x + (col1_w - img_w)/2, y_left - img_h, width=img_w, height=img_h, mask='auto', preserveAspectRatio=True)
                y_left -= (img_h + 20)
            except:
                pass

        # 2. Name and Contact
        c.setFont(FONT_HEADING, 18)
        c.setFillColor(COLOR_HEADER_BG)
        name = self.cv_data.header_info.name if self.cv_data.header_info.name else "NOMBRE APELLIDO"
        
        # Wrap name if too long for sidebar
        name_lines = self._wrap_text(c, name.upper(), col1_w, FONT_HEADING, 18)
        for line in name_lines:
             c.drawString(col1_x, y_left, line)
             y_left -= 20
        y_left -= 10
        
        # Contact Info
        c.setFont(FONT_BODY, 9)
        c.setFillColor(COLOR_TEXT_MAIN)
        info = self.cv_data.header_info
        
        if info.city or info.country:
            c.drawString(col1_x, y_left, f"{info.city}, {info.country}".strip(", "))
            y_left -= 12
        if info.phone:
            c.drawString(col1_x, y_left, info.phone)
            y_left -= 12
        if info.email:
            c.drawString(col1_x, y_left, info.email)
            y_left -= 12
        if info.linkedin:
            # Check if it's a markdown link or just a url
            link_text = info.linkedin
            # If it looks like a URL but not a markdown link, make it one?
            # Or assume user enters [Link](url) in the field?
            # User request said: "generate link mechanism for any part of the curriculum".
            # For header info, user might just paste URL. 
            # If it detects URL, wrap it?
            # But specific request was "PERFIL LINKEDIN" instead of URL.
            # So user will likely change the input in the field to "[PERFIL LINKEDIN](url)".
            
            # If input is just a URL, autocreate link? No, user wants custom text.
            # If user puts "[Profile](url)", we render it using Paragraph.
            
            processed_link = self._process_text_formatting(link_text)
            
            # Create Paragraph
            style_link = ParagraphStyle(
                'Link',
                parent=self.style_body,
                fontSize=8,
                textColor=COLOR_TEXT_MAIN
            )
            
            # Wrap in paragraph tag if no font tag present (regex added one)
            # Actually _process_text_formatting adds <font color="blue">
            
            p = Paragraph(processed_link, style_link)
            w, h = p.wrap(col1_w, 50)
            p.drawOn(c, col1_x, y_left - h + 2) # Adjust y (Paragraph draws from top-left, string from baseline)
            # String baseline is y_left. Paragraph top is y_left. 
            # If we draw at y_left, text will be below y_left.
            # drawString draws at baseline.
            # Paragraph needs to be drawn so its baseline matches approx?
            # Paragraph height includes ascender/descender.
            # Let's align top.
            
            y_left -= 12
        else:
             y_left -= 0 # No link
            
        y_left -= 20
        
        # 3. Personal Info (Bio)
        # Use a Section Header style
        # "PERFIL" is mapped in translations under "personal" key usually, but let's check
        # We used "personal" as key in TRANSLATIONS for section id "personal" which maps to "PERFIL"/"PROFILE"
        header_title = self._t(self.cv_data.personal_info.id) 
        self._draw_sidebar_header(c, header_title, col1_x, y_left, col1_w)
        y_left -= 10
        
        for m in self.cv_data.personal_info.modules:
            if m.is_active and not isinstance(m, AvatarModule):
                # Resolve text
                if hasattr(m, 'use_summary') and m.use_summary:
                    text = self._get_text(m, "text_summary")
                else:
                    text = self._get_text(m, "text_extended")
                
                y_left = self._draw_paragraph(c, text, col1_x, y_left, col1_w)
                y_left -= 10
        
        y_left -= 20
        
        # 4. Software
        header_title = self._t(self.cv_data.software.id)
        self._draw_sidebar_header(c, header_title, col1_x, y_left, col1_w)
        y_left -= 10
        
        # Grid of logos
        logo_size = 40
        gap = 3
        x_off = 0
        
        for m in self.cv_data.software.modules:
            if m.is_active:
                if x_off + logo_size > col1_w:
                    x_off = 0
                    y_left -= (logo_size + gap)
                
                if m.image_path and os.path.exists(m.image_path):
                    try:
                        c.drawImage(m.image_path, col1_x + x_off, y_left - logo_size, width=logo_size, height=logo_size, mask='auto', preserveAspectRatio=True)
                    except:
                        pass
                else:
                     # Fallback text
                     c.setFont("Helvetica", 8)
                     c.drawString(col1_x + x_off, y_left - logo_size/2, m.name[:4])

                x_off += (logo_size + gap)
        
        y_left -= (logo_size + 30)
        
        # 5. Languages
        header_title = self._t(self.cv_data.languages.id)
        self._draw_sidebar_header(c, header_title, col1_x, y_left, col1_w)
        y_left -= 10
        x_off = 0
        for m in self.cv_data.languages.modules:
            if m.is_active:
                if x_off + logo_size > col1_w:
                    x_off = 0
                    y_left -= (logo_size + gap)
                
                if m.image_path and os.path.exists(m.image_path):
                    try:
                        c.drawImage(m.image_path, col1_x + x_off, y_left - logo_size, width=logo_size, height=logo_size, mask='auto', preserveAspectRatio=True)
                    except:
                        pass
                else:
                     c.setFont("Helvetica", 8)
                     c.drawString(col1_x + x_off, y_left - logo_size/2, m.name[:4])

                x_off += (logo_size + gap)


        # --- RIGHT COLUMN (Main) ---
        y_right = current_y
        
        # Experience
        y_right = self._draw_section(c, self.cv_data.experience, col2_x, y_right, col2_w)
        
        # Knowledge
        # Filter text knowledge
        has_text_knowledge = any(not isinstance(m, ImageModule) for m in self.cv_data.knowledge.modules if m.is_active)
        if has_text_knowledge:
             y_right -= 10
             y_right = self._draw_section(c, self.cv_data.knowledge, col2_x, y_right, col2_w)

        # Education
        y_right -= 10
        y_right = self._draw_section(c, self.cv_data.education, col2_x, y_right, col2_w)
        
        c.save()

    def _draw_sidebar_header(self, c, title, x, y, width):
        c.setFont(FONT_HEADING, 10)
        c.setFillColor(COLOR_HEADER_BG) 
        c.drawString(x, y, title.upper())
        # Optional underline
        c.setStrokeColor(COLOR_HEADER_BG)
        c.line(x, y-2, x+width, y-2)

    def _draw_section(self, c, section, x, y, width):
        # Styled Header: Dark Box with White Text
        header_height = 24
        c.setFillColor(COLOR_HEADER_BG)
        c.rect(x - 5, y - 8, width + 10, header_height, fill=1, stroke=0)
        
        c.setFont(FONT_HEADING, 14)
        c.setFillColor(COLOR_HEADER_TEXT) 
        
        # Translate Title
        # Use section.id to lookup translation
        title = self._t(section.id)
        # If translation returns key (meaning no translation found) and key was section.id (lowercase), 
        # we might want to fallback to section.title if it's a custom section.
        # But section.id is usually internal english-like (experience, education).
        # Implement fallback logic:
        # If the returned title is same as section.id, and section.title is different, maybe prefer section.title?
        # Actually TRANSLATIONS has defaults for our known sections.
        # If it's a custom section unknown to translations, we should use section.title.
        
        if title == section.id: # No translation found
             title = section.title
        
        c.drawString(x, y, title.upper())
        
        c.setFillColor(COLOR_TEXT_MAIN) # Reset
        y -= 35
        
        # Prepare modules (Sort by date descending)
        # We need a helper to extract date from module
        sorted_modules = sorted(section.modules, key=self._get_module_date, reverse=True)

        # Modules
        for m in sorted_modules:
            if not m.is_active: continue
            
            # Title / Role
            # Use translated title if available
            raw_title = self._get_text(m, "title")
            title = ""
            if raw_title: title = raw_title.upper()
            
            # Draw Title
            c.setFont(FONT_HEADING, 11)
            c.setFillColor(COLOR_HEADER_BG)
            c.drawString(x, y, title)
            
            # Let's put Company | Date below
            y -= 10
            sub_line = []
            
            company = self._get_text(m, "company")
            if company: sub_line.append(company)
            
            date_range = self._get_text(m, "date_range")
            if date_range: 
                # Translate date range if it contains keywords
                sub_line.append(self._translate_date(date_range))
            
            if sub_line:
                c.setFont("Helvetica-Oblique", 9)
                c.setFillColor(COLOR_TEXT_SUB)
                c.drawString(x, y, " | ".join(sub_line))
                c.setFillColor(COLOR_TEXT_MAIN)
                y -= 10
            
            # Text
            # Text
            if hasattr(m, 'use_summary') and m.use_summary:
                text = self._get_text(m, "text_summary")
            else:
                text = self._get_text(m, "text_extended")
            
            y = self._draw_paragraph(c, text, x, y, width)
            y -= 12
            
            # Tags (Smart Render)
            if hasattr(m, 'tags') and m.tags:
                y = self._draw_tags(c, m.tags, x, y, width)
                y -= 5
            
            y -= 12
            
            if y < 50: 
                c.showPage()
                y = PAGE_HEIGHT_A4 - MARGIN

        return y

    def _draw_tags(self, c, tags, x, y, max_width):
        c.setFont("Helvetica", 8)
        start_x = x
        current_x = x
        row_height = 14
        
        for tag in tags:
            tag_w = c.stringWidth(tag, "Helvetica", 8) + 10 # padding
            if current_x + tag_w > start_x + max_width:
                current_x = start_x
                y -= row_height
            
            # Draw tag background
            c.setFillColor(COLOR_TAG_BG)
            c.roundRect(current_x, y-2, tag_w-2, 11, 2, fill=1, stroke=0)
            
            # Draw text
            c.setFillColor(COLOR_TAG_BORDER) 
            c.drawString(current_x + 4, y, tag)
            
            current_x += tag_w + 5
            
        return y - row_height

    def _wrap_text(self, c, text, max_width, font, size):
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if c.stringWidth(test_line, font, size) <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def _draw_paragraph(self, c, text, x, y, width):
        if not text: return y
        
        # Process Markdown Links [text](url) -> <a href="url"><font color="blue">text</font></a>
        text = self._process_text_formatting(text)
        
        text = text.replace('\n', '<br/>')
        p = Paragraph(text, self.style_body)
        w, h = p.wrap(width, PAGE_HEIGHT_A4)
        p.drawOn(c, x, y - h)
        return y - h

    def _process_text_formatting(self, text):
        if not text: return ""
        import re
        # Pattern: [text](url)
        # Avoid matching greedy if multiple links on line? [^\]]+ helps.
        pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        
        def replace_match(match):
            display_text = match.group(1)
            url = match.group(2)
            # Translate display text
            translated_text = self._t(display_text)
            
            # Use blue color for link
            return f'<a href="{url}"><font color="blue">{translated_text}</font></a>'
            
        return re.sub(pattern, replace_match, text)

    def _get_module_date(self, module):
        # Extract a comparable date value (End Date) from module
        # Returns tuple (year, month)
        date_str = ""
        source_text = ""
        
        if hasattr(module, 'date_range') and module.date_range:
            source_text = module.date_range
        elif hasattr(module, 'text_extended') and module.text_extended:
            source_text = module.text_extended
            
        if source_text:
            # Try to find date pattern in text (e.g. "(YYYY - YYYY)" or "MM/YYYY")
            import re
            # Look for YYYY or MM/YYYY patterns. 
            # We want the LAST date mentioned (End Date)
            matches = re.findall(r'(\d{1,2}/\d{4}|\d{4}|Present|Actualidad)', source_text, re.IGNORECASE)
            if matches:
                date_str = matches[-1] # Assume last match is end date
        
        if not date_str:
            return (0, 0)
            
        return self._parse_date_string(date_str)

    def _parse_date_string(self, date_str):
        # Handle "Present", "Actualidad", "Current"
        if any(x in date_str.lower() for x in ['present', 'actualidad', 'current', 'hoy']):
            return (9999, 12) # Future date
            
        try:
            # Try MM/YYYY
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 2:
                    return (int(parts[1]), int(parts[0]))
            # Try YYYY
            elif len(date_str) == 4 and date_str.isdigit():
                return (int(date_str), 12) # End of year if only year given
        except:
            pass
            
        return (0, 0)
