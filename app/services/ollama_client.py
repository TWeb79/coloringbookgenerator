"""Ollama API client for text generation"""
import os
from typing import Optional

import httpx


class OllamaClient:
    """Client for Ollama LLM API"""

    CHILDREN_SYSTEM_PROMPT = (
        "You are a children's storybook writer. Write a very short, simple story "
        "paragraph for each page. Keep sentences short. Use exciting language for kids. "
        "Do not use complex words. Always keep content safe for children (5-12 years). "
        "No violence, no profanity."
    )

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def generate_story(self, theme: str, page_index: int, page_count: int,
                            context: Optional[str] = None) -> str:
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
            "system": self.CHILDREN_SYSTEM_PROMPT,
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

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()