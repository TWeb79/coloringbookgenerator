"""Image processing utilities for KidsColorAI"""
import os
from typing import Optional

from PIL import Image, ImageOps


def ensure_white_background(image_path: str, output_path: Optional[str] = None) -> str:
    """Ensure image has a white background.

    Args:
        image_path: Path to input image
        output_path: Path to save processed image (defaults to input path)

    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = image_path

    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))

        # If image has alpha channel, paste using it as mask
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert("RGB")

        img.save(output_path, format="PNG")

    return output_path


def remove_noise(image_path: str, output_path: Optional[str] = None,
                 threshold: int = 128) -> str:
    """Remove noise from image by applying binary threshold.

    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        threshold: Binarization threshold (0-255)

    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = image_path

    with Image.open(image_path) as img:
        if img.mode != "L":
            img = ImageOps.grayscale(img)

        img = img.point(lambda p: 255 if p > threshold else 0, mode="1")
        img = img.convert("RGB")
        img.save(output_path, format="PNG")

    return output_path


def process_line_art(input_path: str, output_path: Optional[str] = None) -> str:
    """Full line art processing pipeline.

    Args:
        input_path: Path to input image
        output_path: Path to save processed image

    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = input_path

    ensure_white_background(input_path, output_path)
    remove_noise(output_path, output_path)

    return output_path


def crop_black_borders(image_path: str, output_path: Optional[str] = None,
                       border_threshold: int = 10) -> str:
    """Remove black borders from image edges.

    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        border_threshold: Distance from edge to check for black pixels

    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = image_path

    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        bbox = img.getbbox()

        if bbox:
            img = img.crop(bbox)
            img.save(output_path, format="PNG")

    return output_path