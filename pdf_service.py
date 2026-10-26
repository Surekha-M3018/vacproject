"""
PDF Export Service.
Generates print-ready, illustrated children's storybook PDFs using ReportLab.
Includes:
- Elegant cover page with title, target age group, character names, and theme.
- Individual story pages with text and properly scaled illustrations.
- Graceful fallback for missing or pending illustrations.
- Moral page and transparent Responsible AI disclosure and credits.
"""

import os
import logging
from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    PageBreak, Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas
from config import Config

logger = logging.getLogger(__name__)

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        # Do not draw page number on cover page (page 1)
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#718096"))
            # Footer
            footer_text = f"Page {self._pageNumber} of {total_pages} • StorySprout AI"
            self.drawCentredString(letter[0] / 2.0, 0.45 * inch, footer_text)
            self.restoreState()


class PDFService:
    @classmethod
    def generate_storybook_pdf(cls, storybook, pages):
        """
        Creates an illustrated storybook PDF file.
        Returns the relative web path: pdf/storybook_<id>.pdf
        """
        Config.ensure_directories()
        
        storybook_id = storybook["id"]
        filename = f"storybook_{storybook_id}.pdf"
        output_filepath = Config.PDF_FOLDER / filename
        
        # Document Setup: Letter size with generous child-friendly 0.6 inch margins
        doc = SimpleDocTemplate(
            str(output_filepath),
            pagesize=letter,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch
        )
        
        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=28,
            leading=34,
            textColor=colors.HexColor('#FF6B4A'),
            alignment=1, # Center
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=13,
            leading=18,
            textColor=colors.HexColor('#4A5568'),
            alignment=1,
            spaceAfter=25
        )
        
        badge_style = ParagraphStyle(
            'CoverBadge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#2E7D32'),
            alignment=1
        )
        
        story_heading = ParagraphStyle(
            'StoryPageHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#FF7B60'),
            spaceAfter=10
        )
        
        story_text_style = ParagraphStyle(
            'StoryPageText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=14,
            leading=22,
            textColor=colors.HexColor('#1A202C'),
            spaceAfter=15
        )
        
        moral_title_style = ParagraphStyle(
            'MoralHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=24,
            textColor=colors.HexColor('#3FA796'),
            alignment=1,
            spaceAfter=12
        )
        
        moral_text_style = ParagraphStyle(
            'MoralContent',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=14,
            leading=22,
            textColor=colors.HexColor('#2D3748'),
            alignment=1,
            spaceAfter=25
        )
        
        disclaimer_style = ParagraphStyle(
            'AIDisclaimer',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#718096')
        )

        prompt_box_style = ParagraphStyle(
            'PromptBox',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#5C6773')
        )
        
        story = []
        
        # -------------------------------------------------------------
        # 1. COVER PAGE
        # -------------------------------------------------------------
        story.append(Spacer(1, 1.2 * inch))
        story.append(Paragraph("🌱 STORYSPROUT PICTURE BOOK", badge_style))
        story.append(Spacer(1, 0.2 * inch))
        
        cover_title = storybook.get("cover_title") or storybook.get("title") or "Children's Storybook"
        story.append(Paragraph(cover_title, title_style))
        
        age_group = storybook.get("age_group", "Children")
        theme = str(storybook.get("theme", "")).capitalize()
        char_name = storybook.get("character_name", "")
        
        meta_summary = f"Age Group: <b>{age_group}</b> &nbsp;|&nbsp; Theme: <b>{theme}</b>"
        if char_name:
            meta_summary += f" &nbsp;|&nbsp; Starring: <b>{char_name}</b>"
        story.append(Paragraph(meta_summary, subtitle_style))
        
        story.append(Spacer(1, 0.8 * inch))
        
        # Decorative cover box
        cover_box_data = [[
            Paragraph(
                f"<b>A Gentle Tale of {theme}</b><br/><br/>"
                f"Co-created with AI storytelling assistance and human heart.<br/>"
                f"Illustrated for growing imaginations.",
                subtitle_style
            )
        ]]
        cover_table = Table(cover_box_data, colWidths=[6.5 * inch])
        cover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF9F0')),
            ('BORDER', (0, 0), (-1, -1), 1.5, colors.HexColor('#FFE0B2')),
            ('ROUNDEDCORNERS', [12, 12, 12, 12]),
            ('TOPPADDING', (0, 0), (-1, -1), 25),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 25),
            ('LEFTPADDING', (0, 0), (-1, -1), 25),
            ('RIGHTPADDING', (0, 0), (-1, -1), 25),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(cover_table)
        
        story.append(PageBreak())
        
        # -------------------------------------------------------------
        # 2. STORY PAGES
        # -------------------------------------------------------------
        max_img_w = 5.8 * inch
        max_img_h = 4.0 * inch
        
        for p in pages:
            page_elements = []
            page_num = p.get("page_number", 1)
            page_text = p.get("text", "")
            img_rel_path = p.get("image_path", "")
            img_prompt = p.get("illustration_prompt", "")
            img_source = p.get("image_source", "none")
            
            page_elements.append(Paragraph(f"PAGE {page_num}", story_heading))
            page_elements.append(Spacer(1, 0.1 * inch))
            
            # Embed Image or Graceful Placeholder Box
            img_rendered = False
            if img_rel_path:
                abs_img_path = Config.STATIC_DIR / img_rel_path.replace("/", os.sep)
                if abs_img_path.exists() and abs_img_path.is_file():
                    try:
                        # Inspect dimensions with Pillow
                        with PILImage.open(abs_img_path) as pil_img:
                            orig_w, orig_h = pil_img.size
                        
                        # Scale maintaining aspect ratio
                        scale = min(max_img_w / orig_w, max_img_h / orig_h)
                        draw_w = orig_w * scale
                        draw_h = orig_h * scale
                        
                        rl_img = RLImage(str(abs_img_path), width=draw_w, height=draw_h)
                        page_elements.append(rl_img)
                        page_elements.append(Spacer(1, 0.15 * inch))
                        img_rendered = True
                    except Exception as e:
                        logger.warning(f"Could not embed image {abs_img_path} in PDF: {e}")

            if not img_rendered:
                # Beautiful placeholder box explaining prompt & provenance
                source_label = "Visual Sketch / Prompt Description"
                if img_source == "none":
                    source_label = "🎨 Ready for Illustration"
                
                placeholder_content = [
                    Paragraph(f"<b>{source_label}</b>", story_heading),
                    Spacer(1, 4),
                    Paragraph(f"<i>Visual Concept:</i> {img_prompt or 'No prompt description entered yet.'}", prompt_box_style)
                ]
                ph_table = Table([[placeholder_content]], colWidths=[6.4 * inch])
                ph_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                    ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                    ('TOPPADDING', (0, 0), (-1, -1), 16),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
                    ('LEFTPADDING', (0, 0), (-1, -1), 16),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 16),
                ]))
                page_elements.append(ph_table)
                page_elements.append(Spacer(1, 0.2 * inch))

            # Story Text
            page_elements.append(Paragraph(page_text, story_text_style))
            
            story.append(KeepTogether(page_elements))
            story.append(PageBreak())

        # -------------------------------------------------------------
        # 3. MORAL & RESPONSIBLE AI DISCLOSURE PAGE
        # -------------------------------------------------------------
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("🌟 The Moral of Our Story", moral_title_style))
        story.append(Spacer(1, 0.15 * inch))
        
        moral_text = storybook.get("moral") or "Kindness, empathy, and courage brighten our world."
        moral_box_data = [[Paragraph(f"“{moral_text}”", moral_text_style)]]
        moral_table = Table(moral_box_data, colWidths=[6.5 * inch])
        moral_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#A5D6A7')),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(moral_table)
        
        story.append(Spacer(1, 0.6 * inch))
        
        # Transparent Disclosure Box
        ai_disclosure_text = (
            "<b>Responsible AI Disclosure & Attribution:</b><br/>"
            f"{Config.RESPONSIBLE_AI_DISCLOSURE}<br/><br/>"
            "<b>Human-in-the-Loop Safeguards:</b><br/>"
            "• Checked for age-appropriate language, vocabulary, and phonetic clarity.<br/>"
            "• Screened for zero violence, fearful concepts, discrimination, or PII.<br/>"
            "• Character consistency anchors maintained across illustration prompts.<br/>"
            "• Created with StorySprout AI (Python Flask + ReportLab)."
        )
        
        disclosure_table = Table([[Paragraph(ai_disclosure_text, disclaimer_style)]], colWidths=[6.5 * inch])
        disclosure_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('LINELEFT', (0, 0), (-1, -1), 3.5, colors.HexColor('#4A90E2')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ]))
        story.append(disclosure_table)
        
        # Build document with custom numbered canvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return f"pdf/{filename}"
