from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from .pdf_styles import *
from model.modules import AvatarModule, ImageModule
import os

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

    def generate(self, filepath):
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # 1. Sidebar (Left)
        sidebar_width = width * 0.30
        # Draw Sidebar Background
        c.setFillColor(COLOR_HEADER_BG) 
        # Actually standard design often has dark sidebar, but let's stick to user request "headers like CVPrevia".
        # If "CVPrevia" had dark headers, maybe sidebar is light? 
        # User said "contact info and name on left".
        # Let's keep sidebar distinct.
        
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
            c.setFont(FONT_BODY, 8)
            c.setFillColor(COLOR_LINK)
            # Basic wrap for link
            link = info.linkedin
            if c.stringWidth(link, FONT_BODY, 8) > col1_w:
                link = link.replace("https://www.", "").replace("http://www.", "")
            c.drawString(col1_x, y_left, link)
            c.setFillColor(COLOR_TEXT_MAIN)
            y_left -= 12
            
        y_left -= 20
        
        # 3. Personal Info (Bio)
        # Use a Section Header style
        self._draw_sidebar_header(c, "PERFIL", col1_x, y_left, col1_w)
        y_left -= 20
        
        for m in self.cv_data.personal_info.modules:
            if m.is_active and not isinstance(m, AvatarModule):
                text = m.text_summary if m.use_summary else m.text_extended
                y_left = self._draw_paragraph(c, text, col1_x, y_left, col1_w)
                y_left -= 10
        
        y_left -= 20
        
        # 4. Software
        self._draw_sidebar_header(c, self.cv_data.software.title.upper(), col1_x, y_left, col1_w)
        y_left -= 20
        
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
        self._draw_sidebar_header(c, self.cv_data.languages.title.upper(), col1_x, y_left, col1_w)
        y_left -= 20
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
        c.drawString(x, y, section.title.upper())
        
        c.setFillColor(COLOR_TEXT_MAIN) # Reset
        y -= 35
        
        # Prepare modules (Sort by date descending)
        # We need a helper to extract date from module
        sorted_modules = sorted(section.modules, key=self._get_module_date, reverse=True)

        # Modules
        for m in sorted_modules:
            if not m.is_active: continue
            
            # Title / Role
            title = ""
            if hasattr(m, 'title') and m.title: title = m.title.upper()
            if hasattr(m, 'company'): title = f"{title}" # Just title
            
            # Draw Title
            c.setFont(FONT_HEADING, 11)
            c.setFillColor(COLOR_HEADER_BG)
            c.drawString(x, y, title)
            
            # Company / Date on same line or below?
            # Let's put Company | Date below
            y -= 14
            sub_line = []
            if hasattr(m, 'company') and m.company: sub_line.append(m.company)
            if hasattr(m, 'date_range') and m.date_range: sub_line.append(m.date_range)
            
            if sub_line:
                c.setFont("Helvetica-Oblique", 9)
                c.setFillColor(COLOR_TEXT_SUB)
                c.drawString(x, y, " | ".join(sub_line))
                c.setFillColor(COLOR_TEXT_MAIN)
                y -= 12
            
            # Text
            # Text
            text = m.text_summary if hasattr(m, 'use_summary') and m.use_summary else getattr(m, 'text_extended', "")
            y = self._draw_paragraph(c, text, x, y, width)
            y -= 15
            
            # Tags (Smart Render)
            if hasattr(m, 'tags') and m.tags:
                y = self._draw_tags(c, m.tags, x, y, width)
                y -= 5
            
            y -= 15
            
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
        text = text.replace('\n', '<br/>')
        p = Paragraph(text, self.style_body)
        w, h = p.wrap(width, PAGE_HEIGHT_A4)
        p.drawOn(c, x, y - h)
        return y - h

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
