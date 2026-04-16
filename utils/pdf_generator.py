import os
import re
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor

from .pdf_styles import *
from .translations import TRANSLATIONS
from .translator import TranslationService
from model.modules import AvatarModule, ImageModule

class PDFGenerator:
    def __init__(self, cv_data):
        self.cv_data = cv_data
        self.styles = getSampleStyleSheet()
        self.design = self.cv_data.settings.design
        
        self.style_body = ParagraphStyle(
            'Body',
            parent=self.styles['Normal'],
            fontName=self.design.global_text.body.family,
            fontSize=self.design.global_text.body.size,
            leading=self.design.global_text.body.size * 1.3,
            textColor=HexColor(self.design.global_text.body.color),
            alignment=TA_LEFT
        )
        
        self.style_left_body = ParagraphStyle(
            'LeftBody',
            parent=self.styles['Normal'],
            fontName=self.design.left_col.body.family,
            fontSize=self.design.left_col.body.size,
            leading=self.design.left_col.body.size * 1.3,
            textColor=HexColor(self.design.left_col.body.color),
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
        
        source_key = f"_source_{field_name}"
        stored_source = lang_trans.get(source_key)
        
        is_stale = False
        if source_key in lang_trans:
            if lang_trans[source_key] != original_text:
                is_stale = True
        else:
            is_stale = True
        
        if not is_stale and field_name in lang_trans and lang_trans[field_name]:
            return lang_trans[field_name]
            
        if original_text:
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

        sidebar_width = width * 0.34
        current_y = height - MARGIN

        col_gap = 20
        col1_x = MARGIN
        col1_w = sidebar_width - MARGIN - col_gap/2
        col2_x = sidebar_width + col_gap/2
        col2_w = width - sidebar_width - MARGIN

        # Sidebar Area Background
        c.setFillColor(HexColor(self.design.left_col.bg_color))
        c.rect(0, 0, sidebar_width, height, fill=1, stroke=0)

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
                orig_w, orig_h = img.getSize()
                img_w = col1_w
                img_h = img_w * (orig_h / orig_w) if orig_w > 0 else img_w
                c.drawImage(avatar_mod.image_path, col1_x, y_left - img_h + 8, width=img_w, height=img_h, mask='auto', preserveAspectRatio=True)
                y_left -= (img_h + 12)
            except:
                pass

        # Contact info
        c.setFont(self.design.left_col.body.family, self.design.left_col.body.size)
        c.setFillColor(HexColor(self.design.left_col.body.color))
        info = self.cv_data.header_info
        
        line_height = self.design.left_col.body.size * 1.3

        if info.city or info.country:
            c.drawString(col1_x, y_left, f"{info.city}, {info.country}".strip(", "))
            y_left -= line_height
        if info.phone:
            c.drawString(col1_x, y_left, info.phone)
            y_left -= line_height
        if info.email:
            c.drawString(col1_x, y_left, info.email)
            y_left -= line_height
        if hasattr(info, 'others') and info.others:
            c.drawString(col1_x, y_left, info.others)
            y_left -= line_height
        if info.linkedin:
            style_link = ParagraphStyle('Link', parent=self.style_left_body, fontSize=self.design.left_col.body.size, textColor=HexColor(self.design.left_col.body.color))
            p = Paragraph(self._process_text_formatting(info.linkedin), style_link)
            _, h = p.wrap(col1_w, 50)
            p.drawOn(c, col1_x, y_left - h + 2)
            y_left -= line_height

        y_left -= 20
        
        # Profile section
        self._draw_sidebar_header(c, self._t(self.cv_data.personal_info.id), col1_x, y_left, col1_w)
        y_left -= 10
        for m in self.cv_data.personal_info.modules:
            if m.is_active and not isinstance(m, AvatarModule):
                text = self._get_text(m, "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended")
                y_left = self._draw_paragraph(c, text, col1_x, y_left, col1_w, self.style_left_body)
                y_left -= 10
        y_left -= 20

        # Knowledge section (Competencias limitadas a tags)
        has_text_knowledge = any(not isinstance(m, ImageModule) for m in self.cv_data.knowledge.modules if m.is_active)
        if has_text_knowledge:
            header_title_k = self._t(self.cv_data.knowledge.id)
            self._draw_sidebar_header(c, header_title_k, col1_x, y_left, col1_w)
            y_left -= 10
            k_tags = []
            for m in self.cv_data.knowledge.modules:
                if m.is_active and not isinstance(m, ImageModule):
                    raw_title = self._get_text(m, "title")
                    if raw_title:
                        k_tags.append(raw_title)
            if k_tags:
                y_left -= 5
                y_left = self._draw_tags(c, k_tags, col1_x, y_left, col1_w)
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
        y_right = current_y - 20

        # Header Info (Nombre, Puesto, Certificaciones)
        h_name = self.design.header.name
        c.setFont(h_name.family, h_name.size)
        c.setFillColor(HexColor(h_name.color))
        name = self.cv_data.header_info.name if self.cv_data.header_info.name else "NOMBRE APELLIDO"
        for line in self._wrap_text(c, name.upper(), col2_w, h_name.family, h_name.size):
            w = c.stringWidth(line, h_name.family, h_name.size)
            x_pos = col2_x + (col2_w - w) / 2
            c.drawString(x_pos, y_right, line)
            y_right -= (h_name.size + 2)
        y_right -= 5
        
        if hasattr(self.cv_data.header_info, 'job_position') and self.cv_data.header_info.job_position:
            h_job = self.design.header.job
            # Reduce the visual space between Name and Puesto by half, taking off a bit to add 3px gap
            y_right += (h_name.size / 2) - 3
            c.setFont(h_job.family, h_job.size)
            c.setFillColor(HexColor(h_job.color))
            job_val = self._get_text(self.cv_data.header_info, "job_position")
            for line in self._wrap_text(c, job_val.upper(), col2_w, h_job.family, h_job.size):
                w = c.stringWidth(line, h_job.family, h_job.size)
                x_pos = col2_x + (col2_w - w) / 2
                c.drawString(x_pos, y_right, line)
                y_right -= (h_job.size + 4)
            y_right += 18
        else:
            y_right -= 5

        if hasattr(self.cv_data.header_info, 'certifications') and self.cv_data.header_info.certifications:
            h_cert = self.design.header.certification
            cert_val = self._get_text(self.cv_data.header_info, "certifications")
            certs_text = cert_val.replace('\n', '<br/>')
            certs_text = self._process_text_formatting(certs_text)
            
            style_certs = ParagraphStyle(
                'Certs', parent=self.style_body,
                fontName=h_cert.family, fontSize=h_cert.size,
                textColor=HexColor(h_cert.color), alignment=TA_CENTER, leading=h_cert.size * 1.2
            )
            
            p = Paragraph(certs_text, style_certs)
            _, h = p.wrap(col2_w, PAGE_HEIGHT_A4)
            p.drawOn(c, col2_x, y_right - h)
            y_right -= (h + 15)

        y_right -= 20

        y_right = self._draw_section(c, self.cv_data.experience, col2_x, y_right, col2_w)
        y_right -= 10
        y_right = self._draw_section(c, self.cv_data.education, col2_x, y_right, col2_w)

        c.save()

    def _draw_sidebar_header(self, c, title, x, y, width):
        lc_title = self.design.left_col.title
        c.setFont(lc_title.family, lc_title.size)
        c.setFillColor(HexColor(lc_title.color))
        c.drawString(x, y, title.upper())
        c.setStrokeColor(HexColor(lc_title.color))
        c.line(x, y-2, x+width, y-2)

    def _draw_section(self, c, section, x, y, width):
        rc_title = self.design.right_col.title
        header_height = rc_title.size + 10
        
        c.setFillColor(HexColor(self.design.right_col.separator_bg_color))
        c.rect(x - 5, y - 8, width + 10, header_height, fill=1, stroke=0)

        c.setFont(rc_title.family, rc_title.size)
        c.setFillColor(HexColor(rc_title.color))

        title = self._t(section.id)
        if title == section.id:
            title = section.title

        c.drawString(x, y, title.upper())
        y -= (header_height + 11)

        gt_title = self.design.global_text.title
        gt_subtitle = self.design.global_text.subtitle

        for m in section.modules:
            if not m.is_active: continue
            
            raw_title = self._get_text(m, "title")
            c.setFont(gt_title.family, gt_title.size)
            c.setFillColor(HexColor(gt_title.color))

            title_text = ""
            if raw_title:
                if section.type == "education":
                    title_text = raw_title
                else:
                    title_text = raw_title.upper()

            c.drawString(x, y, title_text)

            y -= (gt_title.size + 1)
            sub_line = []

            company = self._get_text(m, "company")
            if company: sub_line.append(company)

            date_range = self._get_text(m, "date_range")
            if date_range:
                sub_line.append(self._translate_date(date_range))

            if sub_line:
                c.setFont(gt_subtitle.family, gt_subtitle.size)
                c.setFillColor(HexColor(gt_subtitle.color))
                c.drawString(x, y, " | ".join(sub_line))
                y -= (gt_subtitle.size + 2)

            if hasattr(m, 'hide_text') and getattr(m, 'hide_text', False):
                y -= 5
            else:
                text = self._get_text(m, "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended")
                y = self._draw_paragraph(c, text, x, y, width, self.style_body)
                y -= 12

            if hasattr(m, 'tags') and m.tags:
                y = self._draw_tags(c, self._get_tags(m), x, y, width)
                y -= 5

            y -= 8

            if y < 30:
                c.showPage()
                y = PAGE_HEIGHT_A4 - MARGIN

        return y

    def _draw_tags(self, c, tags, x, y, max_width):
        t_font = self.design.tags.font
        c.setFont(t_font.family, t_font.size)
        start_x = x
        current_x = x
        row_height = t_font.size + 6
        for tag in tags:
            tag_w = c.stringWidth(tag, t_font.family, t_font.size) + 10
            if current_x + tag_w > start_x + max_width:
                current_x = start_x
                y -= row_height
            c.setFillColor(HexColor(self.design.tags.bg_color))
            c.roundRect(current_x, y-2, tag_w-2, t_font.size + 3, 2, fill=1, stroke=0)
            c.setFillColor(HexColor(t_font.color))
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

    def _draw_paragraph(self, c, text, x, y, width, style=None):
        if not text: return y
        text = self._process_text_formatting(text).replace('\n', '<br/>')
        p = Paragraph(text, style if style else self.style_body)
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
