"""Ollama API client for text generation"""
import json
import logging
import os
import re
from typing import Optional

import httpx

from app.prompts import (
    CHILDREN_SYSTEM_PROMPT,
    CHARACTER_SYSTEM_PROMPT,
    CHARACTER_PROMPT_TEMPLATE,
    STORY_PLAN_PROMPT_TEMPLATE,
    IMAGE_PROMPT_SUFFIX,
)

logger = logging.getLogger(__name__)


def extract_json(text: str) -> str:
    """Extract JSON from a response that may be wrapped in markdown code blocks."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    return text


class OllamaClient:
    """Client for Ollama LLM API"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self._configured_model = model or os.getenv("OLLAMA_MODEL")
        self.model = None
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def _get_first_available_model(self) -> str:
        """Get the first available model from Ollama."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    model_name = models[0].get("name", "llama3")
                    logger.info(f"Auto-selected Ollama model: {model_name}")
                    return model_name
        except Exception as e:
            logger.warning(f"Failed to get available models from Ollama: {e}")
        return "llama3"

    async def initialize(self):
        """Initialize the client, auto-selecting model if not configured."""
        if self._configured_model:
            self.model = self._configured_model
        else:
            self.model = await self._get_first_available_model()
        if self.model is None:
            self.model = "llama3"

    async def generate_character(self, theme: str) -> dict:
        """Generate a main character definition for the story.

        Returns:
            Dictionary with character_name, character_description,
            character_appearance, character_personality, key_features, color_palette
        """
        logger.info(f"Generating character for theme: {theme}")
        prompt = CHARACTER_PROMPT_TEMPLATE.format(theme=theme)

        payload = {
            "model": self.model,
            "system": CHARACTER_SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            raw_response = result.get("response", "{}")
            json_text = extract_json(raw_response)
            character = json.loads(json_text)
            logger.info(f"Character generated: {character.get('name', 'Unknown')}")
            return character
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating character: {e.response.status_code} - {e}")
            raise
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse character JSON: {e}, using fallback")
            return {
                "name": "Hero",
                "description": "A brave adventurer",
                "appearance": "simple friendly character",
                "personality": "brave and curious",
                "key_features": ["big eyes", "friendly smile", "colorful outfit"],
                "color_palette": "blue shirt, brown hair"
            }

    async def generate_story_plan(
        self, theme: str, page_count: int, character: dict
    ) -> list[dict]:
        """Generate story broken down into pages with image prompts.

        Args:
            theme: The coloring book theme
            page_count: Total number of pages
            character: Character definition dictionary

        Returns:
            List of dicts with page_number, story_text, image_prompt
        """
        logger.info(f"Generating story plan for theme '{theme}' with {page_count} pages")
        char_name = character.get("name", "Hero")
        char_appearance = character.get("appearance", "a friendly character")
        key_features = character.get("key_features", ["friendly smile", "big eyes"])
        color_palette = character.get("color_palette", "various colors")

        # Format key features as a comma-separated string
        key_features_str = ", ".join(key_features) if isinstance(key_features, list) else key_features

        prompt = STORY_PLAN_PROMPT_TEMPLATE.format(
            theme=theme,
            page_count=page_count,
            char_name=char_name,
            char_appearance=char_appearance,
            key_features=key_features_str,
            color_palette=color_palette,
        )

        payload = {
            "model": self.model,
            "system": CHILDREN_SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            raw_response = result.get("response", "[]")
            json_text = extract_json(raw_response)
            story_pages = json.loads(json_text)
            # Append suffix to each image prompt to ensure consistent coloring book style
            for page in story_pages:
                if page.get("image_prompt"):
                    page["image_prompt"] = page["image_prompt"] + IMAGE_PROMPT_SUFFIX
            logger.info(f"Generated {len(story_pages)} story pages")
            return story_pages
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating story plan: {e.response.status_code} - {e}")
            raise
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse story plan JSON: {e}, using fallback")
            return [
                {
                    "page_number": i + 1,
                    "story_text": f"Page {i + 1} of the adventure",
                    "image_prompt": f"{theme}, page {i + 1}, featuring {char_name} as {char_appearance}" + IMAGE_PROMPT_SUFFIX,
                }
                for i in range(page_count)
            ]

    async def generate_story(
        self, theme: str, page_index: int, page_count: int,
        context: Optional[str] = None
    ) -> str:
        """Generate a short story for a coloring book page.

        Args:
            theme: The coloring book theme
            page_index: Current page number (0-indexed)
            page_count: Total number of pages
            context: Optional context/idea for the story

        Returns:
            Generated story text
        """
        prompt = (
            f"Theme: {theme}\n"
            f"Page: {page_index + 1} of {page_count}\n"
            f"Story Idea: {context or 'Create a fun adventure'}"
        )

        payload = {
            "model": self.model,
            "system": CHILDREN_SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
        }

        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")

    async def is_available(self) -> bool:
        """Check if Ollama API is available."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def health_check(self) -> bool:
        """Check if Ollama is healthy and ready."""
        try:
            # Try to get models list as a health check
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return len(models) >= 0  # Even empty list means service is up
            return False
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()