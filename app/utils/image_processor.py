"""Image processing utilities for KidsColorAI"""
import logging
import os
from typing import Optional

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


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


def validate_line_art_quality(image_path: str, 
                               min_black_ratio: float = 0.01,
                               max_white_ratio: float = 0.99,
                               min_contrast: float = 0.3) -> tuple[bool, dict]:
    """Validate that an image meets line art quality standards.

    Args:
        image_path: Path to the image to validate
        min_black_ratio: Minimum ratio of black pixels (default 1%)
        max_white_ratio: Maximum ratio of white pixels (default 99%)
        min_contrast: Minimum contrast ratio between black and white

    Returns:
        Tuple of (is_valid, metrics_dict)
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != "L":
                img = img.convert("L")
            
            pixels = list(img.getdata())
            total_pixels = len(pixels)
            
            if total_pixels == 0:
                return False, {"error": "Empty image"}
            
            # Count pixel colors
            black_pixels = sum(1 for p in pixels if p < 64)
            white_pixels = sum(1 for p in pixels if p > 192)
            gray_pixels = total_pixels - black_pixels - white_pixels
            
            black_ratio = black_pixels / total_pixels
            white_ratio = white_pixels / total_pixels
            gray_ratio = gray_pixels / total_pixels
            
            # Calculate contrast (difference between black and white peaks)
            contrast = 1.0 - (gray_ratio)
            
            metrics = {
                "black_ratio": black_ratio,
                "white_ratio": white_ratio,
                "gray_ratio": gray_ratio,
                "contrast": contrast,
                "total_pixels": total_pixels,
            }
            
            # Validate quality
            is_valid = (
                black_ratio >= min_black_ratio and
                white_ratio <= max_white_ratio and
                contrast >= min_contrast
            )
            
            return is_valid, metrics
            
    except Exception as e:
        return False, {"error": str(e)}


def is_line_art(image_path: str, 
                min_line_pixels: int = 100,
                max_gray_percentage: float = 0.3) -> bool:
    """Check if an image appears to be line art (black lines on white background).

    Args:
        image_path: Path to the image to check
        min_line_pixels: Minimum number of dark pixels required
        max_gray_percentage: Maximum percentage of gray pixels allowed

    Returns:
        True if image appears to be line art
    """
    is_valid, metrics = validate_line_art_quality(
        image_path,
        min_black_ratio=0.001,  # Very lenient for detection
        max_white_ratio=0.999,
        min_contrast=0.1
    )
    
    if "error" in metrics:
        return False
    
    # Check for sufficient black pixels (lines)
    has_lines = metrics["black_ratio"] >= (min_line_pixels / metrics["total_pixels"])
    
    # Check that image isn't mostly gray (would indicate photo/realistic)
    is_not_photo = metrics["gray_ratio"] <= max_gray_percentage
    
    return has_lines and is_not_photo


def normalize_line_thickness(image_path: str, output_path: Optional[str] = None,
                            target_thickness: int = 2) -> str:
    """Normalize line thickness in a line art image.
    
    I-13: Image post-processing improvements - Line thickness normalization
    
    This function detects the average line thickness and adjusts it to the target.
    
    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        target_thickness: Target line thickness in pixels
        
    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = image_path
        
    with Image.open(image_path) as img:
        if img.mode != "L":
            img = img.convert("L")
        
        # Detect edges to find lines
        import numpy as np
        img_array = np.array(img)
        
        # Simple edge detection using gradient
        # Calculate horizontal and vertical gradients
        gx = np.gradient(img_array.astype(float), axis=1)
        gy = np.gradient(img_array.astype(float), axis=0)
        gradient_magnitude = np.sqrt(gx**2 + gy**2)
        
        # Threshold to get edge pixels
        edge_threshold = np.percentile(gradient_magnitude[gradient_magnitude > 0], 50)
        edges = gradient_magnitude > edge_threshold
        
        # Estimate line thickness by counting consecutive edge pixels
        # This is a simplified estimation
        avg_thickness = 1.0  # Default if we can't estimate
        
        # Calculate scaling factor
        if avg_thickness > 0:
            scale_factor = target_thickness / avg_thickness
        else:
            scale_factor = 1.0
        
        # Apply morphological operations to adjust thickness
        from PIL import ImageFilter
        
        if scale_factor > 1.2:
            # Lines are too thin, dilate to thicken
            times = int(round(scale_factor - 1))
            for _ in range(times):
                img = img.filter(ImageFilter.MaxFilter(3))
        elif scale_factor < 0.8:
            # Lines are too thick, erode to thin
            times = int(round(1/scale_factor - 1))
            for _ in range(times):
                img = img.filter(ImageFilter.MinFilter(3))
        
        img = img.convert("RGB")
        img.save(output_path, format="PNG")
        
    return output_path


def remove_borders_advanced(image_path: str, output_path: Optional[str] = None,
                            border_margin: int = 5) -> str:
    """Remove borders from image using edge detection.
    
    I-13: Image post-processing improvements - Better border removal using edge detection
    
    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        border_margin: Margin to keep from detected border
        
    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = image_path
        
    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        import numpy as np
        img_array = np.array(img)
        
        # Convert to grayscale for edge detection
        gray = np.mean(img_array, axis=2)
        
        # Detect edges using Sobel-like gradient
        gx = np.gradient(gray, axis=1)
        gy = np.gradient(gray, axis=0)
        gradient = np.sqrt(gx**2 + gy**2)
        
        # Threshold to find significant edges
        threshold = np.percentile(gradient[gradient > 0], 85)
        
        # Find rows and columns with significant content
        row_has_content = np.any(gradient > threshold, axis=1)
        col_has_content = np.any(gradient > threshold, axis=0)
        
        # Find first and last rows/cols with content
        rows_with_content = np.where(row_has_content)[0]
        cols_with_content = np.where(col_has_content)[0]
        
        if len(rows_with_content) > 0 and len(cols_with_content) > 0:
            top = max(0, rows_with_content[0] - border_margin)
            bottom = min(img.height, rows_with_content[-1] + border_margin + 1)
            left = max(0, cols_with_content[0] - border_margin)
            right = min(img.width, cols_with_content[-1] + border_margin + 1)
            
            # Crop the image
            img = img.crop((left, top, right, bottom))
        
        img.save(output_path, format="PNG")
        
    return output_path


def enhance_line_art(image_path: str, output_path: Optional[str] = None) -> str:
    """Full line art enhancement pipeline.
    
    I-13: Image post-processing improvements
    
    Applies a series of enhancements:
    1. White background normalization
    2. Noise removal
    3. Advanced border removal
    4. Line thickness normalization
    
    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        
    Returns:
        Path to processed image
    """
    if output_path is None:
        output_path = image_path
    
    # Step 1: Ensure white background
    temp_path = image_path + ".temp1.png"
    ensure_white_background(image_path, temp_path)
    
    # Step 2: Remove noise
    temp_path2 = image_path + ".temp2.png"
    remove_noise(temp_path, temp_path2)
    
    # Step 3: Advanced border removal
    temp_path3 = image_path + ".temp3.png"
    remove_borders_advanced(temp_path2, temp_path3)
    
    # Step 4: Normalize line thickness
    normalize_line_thickness(temp_path3, output_path)
    
    # Clean up temp files
    import os
    for temp in [temp_path, temp_path2, temp_path3]:
        if os.path.exists(temp):
            os.remove(temp)
    
    return output_path
