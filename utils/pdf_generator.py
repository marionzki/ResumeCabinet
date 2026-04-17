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
        return self.trans.get(key.lower(), key)

    def _get_text(self, module, field_name, default_value=""):
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
        is_stale = source_key not in lang_trans or lang_trans[source_key] != original_text
        if not is_stale and field_name in lang_trans and lang_trans[field_name]:
            return lang_trans[field_name]
        if original_text:
            translated = self.translator.translate_text(original_text, self.language)
            lang_trans[field_name] = translated
            lang_trans[source_key] = original_text
            return translated
        return original_text

    def _get_tags(self, module):
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
        if not date_str: return ""
        keywords = ["Actualidad", "Present", "Current", "Hoy", "Today"]
        lower_date = date_str.lower()
        for k in keywords:
            if k.lower() in lower_date:
                return re.sub(k, self._t(k.lower()), date_str, flags=re.IGNORECASE)
        return date_str

    # ------------------------------------------------------------------
    # LEFT COLUMN BLOCK BUILDER
    # ------------------------------------------------------------------

    def _build_left_col_blocks(self, c, col1_x, col1_w):
        """
        Returns a list of blocks: {'height': float, 'draw': callable(c, y)}.
        y = cursor position (PDF coords, moving downward = decreasing y).
        Each draw(c, y) renders its content at the given y and the caller
        decrements y by block['height'] afterwards.
        """
        blocks = []
        logo_size = 40
        gap = 3
        logos_per_row = max(1, int(col1_w / (logo_size + gap)))
        line_height = self.design.left_col.body.size * 1.3
        lc_title_size = self.design.left_col.title.size

        # Helper: plain text line
        def _text_block(text):
            def _draw(c, y, _t=text):
                c.setFont(self.design.left_col.body.family, self.design.left_col.body.size)
                c.setFillColor(HexColor(self.design.left_col.body.color))
                c.drawString(col1_x, y, _t)
            return {'height': line_height, 'draw': _draw}

        # Helper: spacer
        def _spacer(h):
            return {'height': h, 'draw': lambda c, y: None}

        # Helper: sidebar section header (title + underline, cursor moves by 6 after)
        def _header_block(title):
            def _draw(c, y, _title=title):
                self._draw_sidebar_header(c, _title, col1_x, y, col1_w)
            return {'height': lc_title_size + 6, 'draw': _draw}

        # Helper: logo row
        def _logo_row_block(row):
            def _draw(c, y, _row=row):
                for i, m in enumerate(_row):
                    x_off = col1_x + i * (logo_size + gap)
                    if m.image_path and os.path.exists(m.image_path):
                        try:
                            c.drawImage(m.image_path, x_off, y - logo_size,
                                        width=logo_size, height=logo_size,
                                        mask='auto', preserveAspectRatio=True)
                        except Exception:
                            pass
                    else:
                        c.setFont("Helvetica", 8)
                        c.drawString(x_off, y - logo_size / 2, m.name[:4])
            return {'height': logo_size + gap, 'draw': _draw}

        # 1. Avatar
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
                path = avatar_mod.image_path
                def _draw_avatar(c, y, _p=path, _iw=img_w, _ih=img_h):
                    c.drawImage(_p, col1_x, y - _ih + 8, width=_iw, height=_ih,
                                mask='auto', preserveAspectRatio=True)
                blocks.append({'height': img_h + 12, 'draw': _draw_avatar})
            except Exception:
                pass

        # 2. Contact info
        info = self.cv_data.header_info
        if info.city or info.country:
            blocks.append(_text_block(f"{info.city}, {info.country}".strip(", ")))
        if info.phone:
            blocks.append(_text_block(info.phone))
        if info.email:
            blocks.append(_text_block(info.email))
        if hasattr(info, 'others') and info.others:
            blocks.append(_text_block(info.others))
        if info.linkedin:
            style_link = ParagraphStyle('Link', parent=self.style_left_body,
                                        fontSize=self.design.left_col.body.size,
                                        textColor=HexColor(self.design.left_col.body.color))
            p_m = Paragraph(self._process_text_formatting(info.linkedin), style_link)
            _, _lh = p_m.wrap(col1_w, 50)
            linkedin_text = info.linkedin
            def _draw_linkedin(c, y, _text=linkedin_text):
                _style = ParagraphStyle('Link2', parent=self.style_left_body,
                                        fontSize=self.design.left_col.body.size,
                                        textColor=HexColor(self.design.left_col.body.color))
                _p = Paragraph(self._process_text_formatting(_text), _style)
                _, _h = _p.wrap(col1_w, 50)
                _p.drawOn(c, col1_x, y - _h + 2)
            blocks.append({'height': line_height, 'draw': _draw_linkedin})

        blocks.append(_spacer(12))

        # 3. Profile section
        blocks.append(_header_block(self._t(self.cv_data.personal_info.id)))
        for m in self.cv_data.personal_info.modules:
            if m.is_active and not isinstance(m, AvatarModule):
                field = "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended"
                text = self._get_text(m, field)
                if text:
                    formatted = self._process_text_formatting(text).replace('\n', '<br/>')
                    p_m = Paragraph(formatted, self.style_left_body)
                    _, ph = p_m.wrap(col1_w, PAGE_HEIGHT_A4)
                    def _draw_para(c, y, _text=text):
                        _fmt = self._process_text_formatting(_text).replace('\n', '<br/>')
                        _p = Paragraph(_fmt, self.style_left_body)
                        _, _h = _p.wrap(col1_w, PAGE_HEIGHT_A4)
                        _p.drawOn(c, col1_x, y - _h)
                    blocks.append({'height': ph + 5, 'draw': _draw_para})

        blocks.append(_spacer(10))

        # 4. Knowledge (competencias) section
        has_text_knowledge = any(
            not isinstance(m, ImageModule)
            for m in self.cv_data.knowledge.modules if m.is_active
        )
        if has_text_knowledge:
            blocks.append(_header_block(self._t(self.cv_data.knowledge.id)))
            k_tags = []
            for m in self.cv_data.knowledge.modules:
                if m.is_active and not isinstance(m, ImageModule):
                    raw_title = self._get_text(m, "title")
                    if raw_title:
                        k_tags.append(raw_title)
            if k_tags:
                blocks.append(_spacer(5))
                t_font = self.design.tags.font
                row_h = t_font.size + 6
                cur_x = 0
                rows = 1
                for tag in k_tags:
                    tw = c.stringWidth(tag, t_font.family, t_font.size) + 10
                    if cur_x + tw > col1_w:
                        cur_x = 0
                        rows += 1
                    cur_x += tw + 5
                tags_h = rows * row_h
                def _draw_k_tags(c, y, _tags=k_tags):
                    self._draw_tags(c, _tags, col1_x, y, col1_w)
                blocks.append({'height': tags_h + 5, 'draw': _draw_k_tags})

            blocks.append(_spacer(10))

        # 5. Software section
        blocks.append(_header_block(self._t(self.cv_data.software.id)))
        sw_modules = [m for m in self.cv_data.software.modules if m.is_active]
        sw_rows = [sw_modules[i:i + logos_per_row] for i in range(0, len(sw_modules), logos_per_row)]
        for row in sw_rows:
            blocks.append(_logo_row_block(row))
        blocks.append(_spacer(15))

        # 6. Languages section
        blocks.append(_header_block(self._t(self.cv_data.languages.id)))
        lang_modules = [m for m in self.cv_data.languages.modules if m.is_active]
        lang_rows = [lang_modules[i:i + logos_per_row] for i in range(0, len(lang_modules), logos_per_row)]
        for row in lang_rows:
            blocks.append(_logo_row_block(row))
        blocks.append(_spacer(15))

        return blocks

    # ------------------------------------------------------------------
    # MAIN GENERATE
    # ------------------------------------------------------------------

    def generate(self, filepath):
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        sidebar_width = width * 0.34
        col_gap = 20
        col1_x = MARGIN
        col1_w = sidebar_width - MARGIN - col_gap / 2
        col2_x = sidebar_width + col_gap / 2
        col2_w = width - sidebar_width - MARGIN

        # Pre-build left column blocks
        left_blocks = self._build_left_col_blocks(c, col1_x, col1_w)
        left_state = {'idx': 0}

        # ---- Page infrastructure ----

        def _draw_sidebar_bg():
            c.setFillColor(HexColor(self.design.left_col.bg_color))
            c.rect(0, 0, sidebar_width, height, fill=1, stroke=0)
            c.setStrokeColor(COLOR_SECONDARY)
            c.line(sidebar_width, MARGIN, sidebar_width, height - MARGIN)

        def _draw_left_for_page():
            y = height - MARGIN
            while left_state['idx'] < len(left_blocks):
                blk = left_blocks[left_state['idx']]
                if y - blk['height'] < MARGIN / 2:
                    break
                blk['draw'](c, y)
                y -= blk['height']
                left_state['idx'] += 1

        def _new_page():
            c.showPage()
            _draw_sidebar_bg()
            _draw_left_for_page()
            return height - MARGIN

        # Draw page 1
        _draw_sidebar_bg()
        _draw_left_for_page()

        # ---- RIGHT COLUMN ----
        h_name = self.design.header.name
        name = self.cv_data.header_info.name if self.cv_data.header_info.name else "NOMBRE APELLIDO"
        has_job = hasattr(self.cv_data.header_info, 'job_position') and self.cv_data.header_info.job_position
        has_certs = hasattr(self.cv_data.header_info, 'certifications') and self.cv_data.header_info.certifications

        name_lines = self._wrap_text(c, name.upper(), col2_w, h_name.family, h_name.size)
        name_block_h = len(name_lines) * (h_name.size + 2) + 5

        job_block_h = 0
        if has_job:
            h_job = self.design.header.job
            job_val = self._get_text(self.cv_data.header_info, "job_position")
            job_lines = self._wrap_text(c, job_val.upper(), col2_w, h_job.family, h_job.size)
            job_block_h = len(job_lines) * (h_job.size + 4) - (h_name.size / 2 - 3) - 18
        else:
            job_block_h = 5

        certs_block_h = 0
        if has_certs:
            h_cert = self.design.header.certification
            cert_val = self._get_text(self.cv_data.header_info, "certifications")
            certs_text = self._process_text_formatting(cert_val.replace('\n', '<br/>'))
            style_certs_m = ParagraphStyle('CM', parent=self.style_body,
                                           fontName=h_cert.family, fontSize=h_cert.size,
                                           textColor=HexColor(h_cert.color),
                                           alignment=TA_CENTER, leading=h_cert.size * 1.2)
            p_m = Paragraph(certs_text, style_certs_m)
            _, ch = p_m.wrap(col2_w, PAGE_HEIGHT_A4)
            certs_block_h = ch + 15

        header_bottom_gap = 20
        exp_h = self._measure_section(c, self.cv_data.experience, col2_w)
        edu_h = self._measure_section(c, self.cv_data.education, col2_w)

        total_h = (20 + name_block_h + job_block_h + certs_block_h
                   + header_bottom_gap + exp_h + 10 + edu_h)
        available_h = height - 2 * MARGIN
        leftover = max(0, available_h - total_h)
        extra_after_separator = leftover

        # Draw header elements
        y_right = height - MARGIN - 20

        c.setFont(h_name.family, h_name.size)
        c.setFillColor(HexColor(h_name.color))
        for line in name_lines:
            w = c.stringWidth(line, h_name.family, h_name.size)
            c.drawString(col2_x + (col2_w - w) / 2, y_right, line)
            y_right -= (h_name.size + 2)
        y_right -= 5

        if has_job:
            h_job = self.design.header.job
            y_right += (h_name.size / 2) - 3
            c.setFont(h_job.family, h_job.size)
            c.setFillColor(HexColor(h_job.color))
            job_val = self._get_text(self.cv_data.header_info, "job_position")
            for line in self._wrap_text(c, job_val.upper(), col2_w, h_job.family, h_job.size):
                w = c.stringWidth(line, h_job.family, h_job.size)
                c.drawString(col2_x + (col2_w - w) / 2, y_right, line)
                y_right -= (h_job.size + 4)
            y_right += 18
        else:
            y_right -= 5

        if has_certs:
            h_cert = self.design.header.certification
            cert_val = self._get_text(self.cv_data.header_info, "certifications")
            certs_text = self._process_text_formatting(cert_val.replace('\n', '<br/>'))
            style_certs = ParagraphStyle('Certs', parent=self.style_body,
                                         fontName=h_cert.family, fontSize=h_cert.size,
                                         textColor=HexColor(h_cert.color),
                                         alignment=TA_CENTER, leading=h_cert.size * 1.2)
            p = Paragraph(certs_text, style_certs)
            _, h = p.wrap(col2_w, PAGE_HEIGHT_A4)
            p.drawOn(c, col2_x, y_right - h)
            y_right -= (h + 15)

        y_right -= (header_bottom_gap + extra_after_separator)

        y_right = self._draw_section(c, self.cv_data.experience, col2_x, y_right, col2_w, _new_page)
        y_right -= 10
        y_right = self._draw_section(c, self.cv_data.education, col2_x, y_right, col2_w, _new_page)

        c.save()

    # ------------------------------------------------------------------
    # MEASURE HELPERS
    # ------------------------------------------------------------------

    def _measure_module(self, c, m, width):
        """Height consumed by a single active module in the right column."""
        gt_title = self.design.global_text.title
        gt_subtitle = self.design.global_text.subtitle
        h = gt_title.size + 1  # title

        sub_parts = []
        if self._get_text(m, "company"):
            sub_parts.append(self._get_text(m, "company"))
        if self._get_text(m, "date_range"):
            sub_parts.append(self._get_text(m, "date_range"))
        if sub_parts:
            h += gt_subtitle.size + 2

        if hasattr(m, 'hide_text') and getattr(m, 'hide_text', False):
            h += 5
        else:
            text = self._get_text(m, "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended")
            if text:
                formatted = self._process_text_formatting(text).replace('\n', '<br/>')
                p = Paragraph(formatted, self.style_body)
                _, ph = p.wrap(width, PAGE_HEIGHT_A4)
                h += ph
            h += 12

        if hasattr(m, 'tags') and m.tags:
            tags = self._get_tags(m)
            t_font = self.design.tags.font
            row_h = t_font.size + 6
            cur_x = 0
            rows = 1
            for tag in tags:
                tw = c.stringWidth(tag, t_font.family, t_font.size) + 10
                if cur_x + tw > width:
                    cur_x = 0
                    rows += 1
                cur_x += tw + 5
            h += rows * row_h + 5

        h += 8  # bottom padding
        return h

    def _measure_section(self, c, section, width):
        rc_title = self.design.right_col.title
        header_height = rc_title.size + 10
        h = header_height + 11
        for m in section.modules:
            if m.is_active:
                h += self._measure_module(c, m, width)
        return h

    # ------------------------------------------------------------------
    # DRAW HELPERS
    # ------------------------------------------------------------------

    def _draw_sidebar_header(self, c, title, x, y, width):
        lc_title = self.design.left_col.title
        c.setFont(lc_title.family, lc_title.size)
        c.setFillColor(HexColor(lc_title.color))
        c.drawString(x, y, title.upper())
        c.setStrokeColor(HexColor(lc_title.color))
        c.line(x, y - 2, x + width, y - 2)

    def _draw_section(self, c, section, x, y, width, new_page_fn=None):
        rc_title = self.design.right_col.title
        header_height = rc_title.size + 10
        section_header_h = header_height + 11

        # Check if section header fits; if not, new page
        if new_page_fn and y - section_header_h < MARGIN / 2:
            y = new_page_fn()

        c.setFillColor(HexColor(self.design.right_col.separator_bg_color))
        c.rect(x - 5, y - 8, width + 10, header_height, fill=1, stroke=0)
        c.setFont(rc_title.family, rc_title.size)
        c.setFillColor(HexColor(rc_title.color))

        title = self._t(section.id)
        if title == section.id:
            title = section.title

        c.drawString(x, y, title.upper())
        y -= section_header_h

        gt_title = self.design.global_text.title
        gt_subtitle = self.design.global_text.subtitle

        for m in section.modules:
            if not m.is_active:
                continue

            # Measure module BEFORE drawing
            module_h = self._measure_module(c, m, width)

            # If module doesn't fit on current page, start a new page
            if new_page_fn and y - module_h < MARGIN / 2:
                y = new_page_fn()

            # Draw title
            raw_title = self._get_text(m, "title")
            c.setFont(gt_title.family, gt_title.size)
            c.setFillColor(HexColor(gt_title.color))
            title_text = ""
            if raw_title:
                title_text = raw_title if section.type == "education" else raw_title.upper()
            c.drawString(x, y, title_text)
            y -= (gt_title.size + 1)

            # Draw subtitle
            sub_line = []
            company = self._get_text(m, "company")
            if company:
                sub_line.append(company)
            date_range = self._get_text(m, "date_range")
            if date_range:
                sub_line.append(self._translate_date(date_range))
            if sub_line:
                c.setFont(gt_subtitle.family, gt_subtitle.size)
                c.setFillColor(HexColor(gt_subtitle.color))
                c.drawString(x, y, " | ".join(sub_line))
                y -= (gt_subtitle.size + 2)

            # Draw body text
            if hasattr(m, 'hide_text') and getattr(m, 'hide_text', False):
                y -= 5
            else:
                text = self._get_text(m, "text_summary" if (hasattr(m, 'use_summary') and m.use_summary) else "text_extended")
                y = self._draw_paragraph(c, text, x, y, width, self.style_body)
                y -= 12

            # Draw tags
            if hasattr(m, 'tags') and m.tags:
                y = self._draw_tags(c, self._get_tags(m), x, y, width)
                y -= 5

            y -= 8

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
            c.roundRect(current_x, y - 2, tag_w - 2, t_font.size + 3, 2, fill=1, stroke=0)
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
        if not text:
            return y
        text = self._process_text_formatting(text).replace('\n', '<br/>')
        p = Paragraph(text, style if style else self.style_body)
        _, h = p.wrap(width, PAGE_HEIGHT_A4)
        p.drawOn(c, x, y - h)
        return y - h

    def _process_text_formatting(self, text):
        if not text:
            return ""
        pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'

        def replace_match(match):
            display_text = match.group(1)
            url = match.group(2)
            translated_text = self._t(display_text)
            return f'<a href="{url}"><font color="blue">{translated_text}</font></a>'

        return re.sub(pattern, replace_match, text)
