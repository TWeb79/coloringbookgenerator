"""PDF generation for coloring books"""
import os
from typing import List

import img2pdf


def generate_coloring_book_pdf(pages: List[dict], output_path: str) -> str:
    """Generate a printable PDF from coloring book pages.

    Args:
        pages: List of dicts with 'image_path' and 'story_text' keys
        output_path: Path to save the PDF file

    Returns:
        Path to generated PDF
    """
    image_paths = [p["image_path"] for p in pages if os.path.exists(p["image_path"])]

    if not image_paths:
        raise ValueError("No valid images found for PDF generation")

    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(image_paths, fit=img2pdf.FitMode.FIT, auto_orient=True))

    return output_path