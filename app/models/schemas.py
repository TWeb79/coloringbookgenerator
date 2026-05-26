"""Pydantic schemas for KidsColorAI"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class JobStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GenerationRequest(BaseModel):
    theme: str
    page_count: int = 45
    image_size: int = 1024

    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Sanitize and validate theme input."""
        if not v or not v.strip():
            raise ValueError('Theme cannot be empty')
        # Limit theme length
        if len(v) > 200:
            raise ValueError('Theme must be 200 characters or less')
        return v.strip()

    @field_validator('page_count')
    @classmethod
    def validate_page_count(cls, v: int) -> int:
        """Validate page count range."""
        if v < 1:
            raise ValueError('Page count must be at least 1')
        if v > 100:
            raise ValueError('Page count must be 100 or less')
        return v

    @field_validator('image_size')
    @classmethod
    def validate_image_size(cls, v: int) -> int:
        """Validate image size is a power of 2 between 256 and 2048."""
        valid_sizes = [256, 512, 768, 1024, 1536, 2048]
        if v not in valid_sizes:
            raise ValueError(f'Image size must be one of: {valid_sizes}')
        return v


class GenerationJob(BaseModel):
    id: int
    theme: str
    page_count: int
    status: JobStatus
    created_at: datetime
    finished_at: Optional[datetime] = None


class PageResponse(BaseModel):
    id: int
    job_id: int
    story_text: str
    image_path: str
    prompt_used: str
    image_prompt: Optional[str] = None


class CharacterDefinition(BaseModel):
    name: str
    description: str
    appearance: str
    personality: str
    key_features: Optional[str] = None
    color_palette: Optional[str] = None


class StoryPage(BaseModel):
    page_number: int
    story_text: str
    image_prompt: str


class JobStatusResponse(BaseModel):
    job_id: int
    status: JobStatus
    progress: int
    message: str
    character: Optional[CharacterDefinition] = None
    story_pages: Optional[list[StoryPage]] = None