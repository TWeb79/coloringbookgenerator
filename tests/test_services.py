"""Tests for KidsColorAI services"""
import pytest

from app.services.ai_client import AIClient
from app.services.ollama_client import OllamaClient


class TestAIClient:
    def test_line_art_prompt_template(self):
        assert "{theme_element}" in AIClient.LINE_ART_PROMPT_TEMPLATE

    def test_negative_prompt_contains_expected_terms(self):
        assert "shading" in AIClient.NEGATIVE_PROMPT
        assert "color" in AIClient.NEGATIVE_PROMPT


class TestOllamaClient:
    def test_children_system_prompt_exists(self):
        assert len(OllamaClient.CHILDREN_SYSTEM_PROMPT) > 0
        assert "children" in OllamaClient.CHILDREN_SYSTEM_PROMPT.lower()

    def test_client_initialization(self):
        client = OllamaClient(base_url="http://localhost:11434")
        assert client.base_url == "http://localhost:11434"
        assert client.model == "llama3"