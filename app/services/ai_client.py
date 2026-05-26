"""AI client wrapper for Stable Diffusion API with KidsColorAI-specific defaults"""
import logging
import os
import time
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stable_diffusion_api import StableDiffusionAPI

logger = logging.getLogger(__name__)


class AIClient:
    """Wrapper for Stable Diffusion API with KidsColorAI-specific defaults"""

    LINE_ART_PROMPT_TEMPLATE = (
        "simple black and white line art, coloring book page, thick outlines, "
        "white background, {theme_element}, children drawing style, high contrast, "
        "vector style, clean lines"
    )

    NEGATIVE_PROMPT = (
        "shading, coloring, grayscale, filled, color, texture, noise, blurry, "
        "low contrast, dark, complex details, realistic"
    )

    DEFAULT_STEPS = 20
    DEFAULT_CFG_SCALE = 7.0
    DEFAULT_IMAGE_SIZE = 1024

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("STABLE_DIFFUSION_HOST", "http://127.0.0.1:7860")
        self.client = StableDiffusionAPI(self.base_url)

    def generate_line_art(self, theme_element: str, steps: Optional[int] = None,
                         cfg_scale: Optional[float] = None, width: Optional[int] = None,
                         height: Optional[int] = None, size: Optional[int] = None) -> dict:
        """Generate a line art image for a coloring book page.

        Args:
            theme_element: The theme element to generate (e.g., "a friendly dinosaur")
            steps: Number of sampling steps (default from env/STEPS)
            cfg_scale: CFG scale for generation (default from env/CFG_SCALE)
            width: Image width (default 1024)
            height: Image height (default 1024)
            size: Square image size (overrides width/height if provided)

        Returns:
            API response with base64-encoded images
        """
        prompt = self.LINE_ART_PROMPT_TEMPLATE.format(theme_element=theme_element)
        
        # Use size if provided, otherwise use width/height or defaults
        if size:
            img_width = size
            img_height = size
        else:
            img_width = width or int(os.getenv("SD_IMAGE_SIZE", self.DEFAULT_IMAGE_SIZE))
            img_height = height or int(os.getenv("SD_IMAGE_SIZE", self.DEFAULT_IMAGE_SIZE))

        return self.client.txt2img(
            prompt=prompt,
            negative_prompt=self.NEGATIVE_PROMPT,
            steps=steps or int(os.getenv("SD_STEPS", self.DEFAULT_STEPS)),
            cfg_scale=cfg_scale or float(os.getenv("SD_CFG_SCALE", self.DEFAULT_CFG_SCALE)),
            width=img_width,
            height=img_height,
            sampler_name="Euler",
        )

    def is_available(self) -> bool:
        """Check if the Stable Diffusion API is available."""
        return self.client.is_available()

    def is_ready(self) -> bool:
        """Check if the Stable Diffusion API is ready to generate images."""
        try:
            progress = self.client.progress()
            # Check if not busy and has valid progress data
            state = progress.get("state", "idle")
            progress_value = progress.get("progress", 0)
            is_ready = state != "busy" and progress_value >= 0
            logger.debug(f"SD readiness check: state={state}, progress={progress_value}, ready={is_ready}")
            return is_ready
        except Exception as e:
            logger.error(f"Failed to check SD readiness: {e}")
            return False

    def get_progress(self) -> dict:
        """Get current generation progress."""
        return self.client.progress()

    def interrupt(self) -> dict:
        """Interrupt current generation."""
        return self.client.interrupt()

    def generate_line_art_with_retry(self, theme_element: str, max_retries: int = 3,
                                     base_delay: float = 1.0, steps: Optional[int] = None,
                                     cfg_scale: Optional[float] = None, width: Optional[int] = None,
                                     height: Optional[int] = None, size: Optional[int] = None) -> dict:
        """Generate a line art image with retry logic and exponential backoff.

        Args:
            theme_element: The theme element to generate
            max_retries: Maximum number of retry attempts (default 3)
            base_delay: Base delay in seconds for exponential backoff (default 1.0)
            steps: Number of sampling steps
            cfg_scale: CFG scale for generation
            width: Image width
            height: Image height
            size: Square image size

        Returns:
            API response with base64-encoded images

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                result = self.generate_line_art(
                    theme_element=theme_element,
                    steps=steps,
                    cfg_scale=cfg_scale,
                    width=width,
                    height=height,
                    size=size
                )

                # Validate we got images back
                if result.get("images"):
                    return result

                # If no images, treat as failure and retry
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: No images returned")

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")

            # Exponential backoff (skip delay on last attempt)
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)

        # All retries exhausted
        error_msg = f"All {max_retries} attempts failed"
        if last_exception:
            error_msg += f": {last_exception}"
        logger.error(error_msg)
        raise Exception(error_msg)
