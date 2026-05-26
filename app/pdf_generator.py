"""PDF generation for coloring books with story text"""
import logging
import os
from typing import List, Optional

from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import Color, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


def generate_coloring_book_pdf(
    pages: List[dict],
    output_path: str,
    include_story: bool = True,
    page_size: str = "letter"
) -> str:
    """Generate a printable PDF from coloring book pages with optional story text.

    Args:
        pages: List of dicts with 'image_path' and 'story_text' keys
        output_path: Path to save the PDF file
        include_story: Whether to include story text on pages
        page_size: Page size - "letter" or "a4"

    Returns:
        Path to generated PDF
    """
    valid_pages = [p for p in pages if os.path.exists(p.get("image_path", ""))]

    if not valid_pages:
        raise ValueError("No valid images found for PDF generation")

    # Select page size
    if page_size.lower() == "a4":
        page_dim = A4
    else:
        page_dim = letter

    # Create PDF using canvas for better control
    c = canvas.Canvas(output_path, pagesize=page_dim)
    width, height = page_dim

    # Margins
    margin = 0.5 * inch
    content_width = width - 2 * margin

    # Image area dimensions
    if include_story:
        # Split space: image on top, text below
        image_height = height * 0.65
        text_start_y = height * 0.30
    else:
        # Full page image
        image_height = height - 2 * margin
        text_start_y = None

    # Text styles
    styles = getSampleStyleSheet()
    title_color = Color(0.3, 0.3, 0.3)
    story_color = Color(0.2, 0.2, 0.2)
    page_num_color = Color(0.5, 0.5, 0.5)
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=title_color,
        spaceAfter=6
    )
    story_style = ParagraphStyle(
        'Story',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        leading=14,
        textColor=story_color,
        leftIndent=10,
        rightIndent=10
    )

    for i, page in enumerate(valid_pages):
        # Add page number at bottom
        page_num_text = f"Page {i + 1} of {len(valid_pages)}"

        # Draw image
        try:
            with Image.open(page["image_path"]) as img:
                img_width, img_height = img.size

            # Calculate image dimensions to fit in content area while maintaining aspect ratio
            max_img_width = content_width
            max_img_height = image_height - 0.5 * inch

            aspect = img_width / img_height
            if max_img_width / max_img_height > aspect:
                # Height constrained
                final_height = max_img_height
                final_width = final_height * aspect
            else:
                # Width constrained
                final_width = max_img_width
                final_height = final_width / aspect

            # Center image horizontally
            img_x = margin + (content_width - final_width) / 2
            img_y = height - margin - final_height

            c.drawImage(
                page["image_path"],
                img_x,
                img_y,
                width=final_width,
                height=final_height,
                preserveAspectRatio=True
            )

            # Add story text if enabled
            if include_story and page.get("story_text") and text_start_y is not None:
                story_text = page["story_text"]

                # Draw story text in a text box
                text_x = margin
                text_y = float(text_start_y)
                text_width = content_width

                # Use a text object for better text wrapping
                text_object = c.beginText(text_x, text_y)
                text_object.setFont("Helvetica", 11)
                text_object.setFillColor(story_color)

                # Simple word wrap
                words = story_text.split()
                lines = []
                current_line = []
                char_width = 5.5  # Approximate character width at 11pt

                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if len(test_line) * char_width < text_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))

                # Set leading
                text_object.setLeading(14)

                for line in lines:
                    text_object.textLine(line)

                c.drawText(text_object)

            # Add page number at bottom
            c.setFont("Helvetica", 8)
            c.setFillColor((0.5, 0.5, 0.5))
            c.drawCentredString(width / 2, margin / 2, page_num_text)

        except Exception as e:
            # If image fails, still add page with error message
            c.setFont("Helvetica", 12)
            c.drawCentredString(width / 2, height / 2, f"Image unavailable (Page {i + 1})")

        # New page for next iteration (except last)
        if i < len(valid_pages) - 1:
            c.showPage()

    c.save()
    return output_path


def generate_coloring_book_pdf_simple(
    pages: List[dict],
    output_path: str,
    page_size: str = "letter"
) -> str:
    """Generate a simple PDF with images only (backward compatible).

    Args:
        pages: List of dicts with 'image_path' keys
        output_path: Path to save the PDF file
        page_size: Page size - "letter" or "a4"

    Returns:
        Path to generated PDF
    """
    return generate_coloring_book_pdf(
        pages,
        output_path,
        include_story=False,
        page_size=page_size
    )