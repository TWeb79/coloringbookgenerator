"""AI client wrapper for Stable Diffusion API with KidsColorAI-specific defaults"""
import os
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stable_diffusion_api import StableDiffusionAPI


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
                         height: Optional[int] = None) -> dict:
        """Generate a line art image for a coloring book page.

        Args:
            theme_element: The theme element to generate (e.g., "a friendly dinosaur")
            steps: Number of sampling steps (default from env/STEPS)
            cfg_scale: CFG scale for generation (default from env/CFG_SCALE)
            width: Image width (default 1024)
            height: Image height (default 1024)

        Returns:
            API response with base64-encoded images
        """
        prompt = self.LINE_ART_PROMPT_TEMPLATE.format(theme_element=theme_element)

        return self.client.txt2img(
            prompt=prompt,
            negative_prompt=self.NEGATIVE_PROMPT,
            steps=steps or int(os.getenv("SD_STEPS", self.DEFAULT_STEPS)),
            cfg_scale=cfg_scale or float(os.getenv("SD_CFG_SCALE", self.DEFAULT_CFG_SCALE)),
            width=width or int(os.getenv("SD_IMAGE_SIZE", self.DEFAULT_IMAGE_SIZE)),
            height=height or int(os.getenv("SD_IMAGE_SIZE", self.DEFAULT_IMAGE_SIZE)),
            sampler_name="Euler",
        )

    def is_available(self) -> bool:
        """Check if the Stable Diffusion API is available."""
        return self.client.is_available()

    def get_progress(self) -> dict:
        """Get current generation progress."""
        return self.client.progress()

    def interrupt(self) -> dict:
        """Interrupt current generation."""
        return self.client.interrupt()