"""Pydantic schemas for KidsColorAI"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GenerationRequest(BaseModel):
    theme: str
    page_count: int = 30
    image_size: int = 1024


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


class JobStatusResponse(BaseModel):
    job_id: int
    status: JobStatus
    progress: int
    message: str