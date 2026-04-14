import os
import re
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

from .pdf_styles import *
from .translations import TRANSLATIONS
from .translator import TranslationService
from model.modules import AvatarModule, ImageModule

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
        """Return the translated string for key in the current language, or key itself as fallback."""
        return self.trans.get(key.lower(), key)

    def _get_text(self, module, field_name, default_value=""):
        """Return the field text from module, auto-translating if necessary."""
        is_default = self.language == "Español"
        original_text = getattr(module, field_name, default_value)
        if is_default:
            return original_text
        if not hasattr(module, 'translations'):
            module.translations = {}
            
        if self.language not in module.translations:
            module.translations[self.language] = {}
            
        lang_trans = module.translations[self.language]
        
        # Check for stale translation: compare stored source text with current text.
        # If source_key is missing (legacy data), assume stale to ensure consistency.
        source_key = f"_source_{field_name}"
        stored_source = lang_trans.get(source_key)
        
        is_stale = False
        if source_key in lang_trans:
            if lang_trans[source_key] != original_text:
                is_stale = True
                logging.debug("Translation for '%s' is stale (source changed). Re-translating...", field_name)
        else:
            is_stale = True
            logging.debug("Translation for '%s' lacks source tracking. Re-translating...", field_name)
        
        # If valid translation exists and not stale, return it
        if not is_stale and field_name in lang_trans and lang_trans[field_name]:
            return lang_trans[field_name]
            
        # Auto-translate if missing or stale
        if original_text:
            logging.debug("Auto-translating '%s' to %s...", field_name, self.language)
            translated = self.translator.translate_text(original_text, self.language)
            lang_trans[field_name] = translated
            lang_trans[source_key] = original_text
            return translated
            
        return original_text

    def _get_tags(self, module):
        """Get translated tags from module."""
        if not hasattr(module, 'tags') or not module.tags:
            return []
            
        is_default = self.language == "Español"
        if is_default:
            return module.tags
            
        if not hasattr(module, 'translations'):
            module.translations = {}
            
        if self.language not in module.translations:
            module.translations[self.language] = {}
            
        lang_trans = module.translations[self.language]
        

        if "tags" not in lang_trans:
            lang_trans["tags"] = {}
            
        translated_tags = []
        tags_dict = lang_trans["tags"]
        
        for tag in module.tags:
            if tag in tags_dict and tags_dict[tag]:
                translated_tags.append(tags_dict[tag])
            else:
                logging.debug("Auto-translating tag '%s' to %s...", tag, self.language)
                translated = self.translator.translate_text(tag, self.language)
                tags_dict[tag] = translated
                translated_tags.append(translated)
                
        return translated_tags

    def _translate_date(self, date_str):
        """Translate date keywords (e.g. 'Actualidad' -> 'Present') to the current language."""
        if not date_str: return ""
        keywords = ["Actualidad", "Present", "Current", "Hoy", "Today"]
        lower_date = date_str.lower()
        for k in keywords:
            if k.lower() in lower_date:
                return re.sub(k, self._t(k.lower()), date_str, flags=re.IGNORECASE)
        return date_str

    def generate(self, filepath):
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        sidebar_width = width * 0.27
        current_y = height - MARGIN

        col_gap = 20
        col1_x = MARGIN
        col1_w = sidebar_width - MARGIN - col_gap/2
        col2_x = sidebar_width + col_gap/2
        col2_w = width - sidebar_width - MARGIN

        # Separator line
        c.setStrokeColor(COLOR_SECONDARY)
        c.line(sidebar_width, MARGIN, sidebar_width, height - MARGIN)

        # --- LEFT COLUMN ---
        y_left = current_y

        avatar_mod = None
        for m in self.cv_data.personal_info.modules:
             if isinstance(m, AvatarModule) and m.is_active:
                 avatar_mod = m
                 break
        
        if avatar_mod and os.path.exists(avatar_mod.image_path):
            try:
                img = ImageReader(avatar_mod.image_path)
                img_w = 145
                img_h = 145
                c.drawImage(avatar_mod.image_path, col1_x + (col1_w - img_w)/2, y_left - img_h + 8, width=img_w, height=img_h, mask='auto', preserveAspectRatio=True)
                y_left -= (img_h + 12)
            except:
                pass

        # Name
        c.setFont(FONT_HEADING, 16)
        c.setFillColor(COLOR_HEADER_BG)
        name = self.cv_data.header_info.name if self.cv_data.header_info.name else "NOMBRE APELLIDO"
        for line in self._wrap_text(c, name.upper(), col1_w, FONT_HEADING, 14):
            c.drawString(col1_x, y_left, line)
            y_left -= 20
        y_left -= 4
        
        if hasattr(self.cv_data.header_info, 'job_position') and self.cv_data.header_info.job_position:
            c.setFont(FONT_HEADING, 16)
            c.setFillColor(COLOR_TAG_BORDER)
            for line in self._wrap_text(c, self.cv_data.header_info.job_position.upper(), col1_w, FONT_HEADING, 16):
                c.drawString(col1_x, y_left, line)
                y_left -= 14
        y_left -= 10
        
        # Contact info
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
        if hasattr(info, 'others') and info.others:
            c.drawString(col1_x, y_left, info.others)
            y_left -= 12
        if info.linkedin:
            # LinkedIn supports markdown links: [PERFIL LINKEDIN](url)
            style_link = ParagraphStyle('Link', parent=self.style_body, fontSize=8, textColor=COLOR_TEXT_MAIN)
            p = Paragraph(self._process_text_formatting(info.linkedin), style_link)
            _, h = p.wrap(col1_w, 50)
            p.drawOn(c, col1_x, y_left - h + 2)
            y_left -= 12

        y_left -= 20
        
        # Profile section
        self._draw_sidebar_header(c, self._t(self.cv_data.personal_info.id), col1_x, y_left, col1_w)
        y_left -= 10
        for m in self.cv_data.personal_info.modules:
            if m.is_active and not isinstance(m, AvatarModule):
                text = self._get_text(m, "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended")
                y_left = self._draw_paragraph(c, text, col1_x, y_left, col1_w)
                y_left -= 10
        y_left -= 20

        # Software section
        header_title = self._t(self.cv_data.software.id)
        self._draw_sidebar_header(c, header_title, col1_x, y_left, col1_w)
        y_left -= 10
        
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
                    c.setFont("Helvetica", 8)
                    c.drawString(col1_x + x_off, y_left - logo_size/2, m.name[:4])
                x_off += (logo_size + gap)
        y_left -= (logo_size + 30)

        # Languages section
        self._draw_sidebar_header(c, self._t(self.cv_data.languages.id), col1_x, y_left, col1_w)
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


        # --- RIGHT COLUMN ---
        y_right = current_y

        y_right = self._draw_section(c, self.cv_data.experience, col2_x, y_right, col2_w)

        has_text_knowledge = any(not isinstance(m, ImageModule) for m in self.cv_data.knowledge.modules if m.is_active)
        if has_text_knowledge:
            y_right -= 10
            y_right = self._draw_section(c, self.cv_data.knowledge, col2_x, y_right, col2_w)

        y_right -= 10
        y_right = self._draw_section(c, self.cv_data.education, col2_x, y_right, col2_w)

        c.save()

    def _draw_sidebar_header(self, c, title, x, y, width):
        c.setFont(FONT_HEADING, 10)
        c.setFillColor(COLOR_HEADER_BG)
        c.drawString(x, y, title.upper())
        c.setStrokeColor(COLOR_HEADER_BG)
        c.line(x, y-2, x+width, y-2)

    def _draw_section(self, c, section, x, y, width):
        header_height = 24
        c.setFillColor(COLOR_HEADER_BG)
        c.rect(x - 5, y - 8, width + 10, header_height, fill=1, stroke=0)

        c.setFont(FONT_HEADING, 14)
        c.setFillColor(COLOR_HEADER_TEXT)

        # Fall back to section.title if no translation found
        title = self._t(section.id)
        if title == section.id:
            title = section.title

        c.drawString(x, y, title.upper())
        c.setFillColor(COLOR_TEXT_MAIN)
        y -= 35

        for m in section.modules:
            if not m.is_active: continue
            
            raw_title = self._get_text(m, "title")
            c.setFont(FONT_HEADING, 11)
            c.setFillColor(COLOR_HEADER_BG)
            c.drawString(x, y, raw_title.upper() if raw_title else "")

            y -= 10
            sub_line = []

            company = self._get_text(m, "company")
            if company: sub_line.append(company)

            date_range = self._get_text(m, "date_range")
            if date_range:
                sub_line.append(self._translate_date(date_range))

            if sub_line:
                c.setFont("Helvetica-Oblique", 9)
                c.setFillColor(COLOR_TEXT_SUB)
                c.drawString(x, y, " | ".join(sub_line))
                c.setFillColor(COLOR_TEXT_MAIN)
                y -= 10

            if hasattr(m, 'hide_text') and getattr(m, 'hide_text', False):
                y -= 5
            else:
                text = self._get_text(m, "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended")
                y = self._draw_paragraph(c, text, x, y, width)
                y -= 12

            if hasattr(m, 'tags') and m.tags:
                y = self._draw_tags(c, self._get_tags(m), x, y, width)
                y -= 5

            y -= 12

            if y < 30:
                c.showPage()
                y = PAGE_HEIGHT_A4 - MARGIN

        return y

    def _draw_tags(self, c, tags, x, y, max_width):
        c.setFont("Helvetica", 8)
        start_x = x
        current_x = x
        row_height = 14
        for tag in tags:
            tag_w = c.stringWidth(tag, "Helvetica", 8) + 10
            if current_x + tag_w > start_x + max_width:
                current_x = start_x
                y -= row_height
            c.setFillColor(COLOR_TAG_BG)
            c.roundRect(current_x, y-2, tag_w-2, 11, 2, fill=1, stroke=0)
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
        text = self._process_text_formatting(text).replace('\n', '<br/>')
        p = Paragraph(text, self.style_body)
        _, h = p.wrap(width, PAGE_HEIGHT_A4)
        p.drawOn(c, x, y - h)
        return y - h

    def _process_text_formatting(self, text):
        if not text: return ""
        pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        
        def replace_match(match):
            display_text = match.group(1)
            url = match.group(2)
            translated_text = self._t(display_text)
            return f'<a href="{url}"><font color="blue">{translated_text}</font></a>'
            
        return re.sub(pattern, replace_match, text)


