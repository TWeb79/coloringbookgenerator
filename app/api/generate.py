"""API routes for coloring book generation"""
import asyncio
import os
import shutil
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stable_diffusion_api import StableDiffusionAPI

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db, GenerationJob, Page
from app.models.schemas import (
    GenerationRequest,
    GenerationJob as GenerationJobSchema,
    PageResponse,
    JobStatusResponse,
    JobStatus,
)
from app.services.ai_client import AIClient
from app.services.ollama_client import OllamaClient
from app.utils.image_processor import process_line_art
from app.pdf_generator import generate_coloring_book_pdf

router = APIRouter()


@router.post("/generate", response_model=GenerationJobSchema)
async def generate_coloring_book(request: GenerationRequest, db: Session = Depends(get_db)):
    """Start a new coloring book generation job."""
    job = GenerationJob(
        theme=request.theme,
        page_count=request.page_count,
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    asyncio.create_task(_generate_pages(job.id, request))

    return job


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of a generation job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pages = db.query(Page).filter(Page.job_id == job_id).all()
    progress = (len(pages) / job.page_count * 100) if job.page_count > 0 else 0

    status_map = {
        JobStatus.PENDING: "Queued for generation",
        JobStatus.GENERATING: f"Generating page {len(pages)} of {job.page_count}",
        JobStatus.COMPLETED: "Generation complete",
        JobStatus.FAILED: "Generation failed",
    }

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=int(progress),
        message=status_map.get(job.status, "Unknown status"),
    )


@router.get("/pages/{job_id}", response_model=list[PageResponse])
async def get_job_pages(job_id: int, db: Session = Depends(get_db)):
    """Get all generated pages for a job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pages = db.query(Page).filter(Page.job_id == job_id).all()
    return pages


@router.get("/pdf/{job_id}")
async def download_pdf(job_id: int, db: Session = Depends(get_db)):
    """Generate and download PDF for a completed job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    pages = db.query(Page).filter(Page.job_id == job_id).all()
    if not pages:
        raise HTTPException(status_code=400, detail="No pages generated")

    output_dir = os.getenv("OUTPUT_DIR", "./generated_books")
    pdf_path = os.path.join(output_dir, f"job_{job_id}_coloring_book.pdf")

    try:
        page_data = [
            {"image_path": p.image_path, "story_text": p.story_text}
            for p in pages
        ]
        generate_coloring_book_pdf(page_data, pdf_path)

        if os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"coloring_book_{job_id}.pdf",
            )
        raise HTTPException(status_code=500, detail="PDF generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job/{job_id}/interrupt")
async def interrupt_job(job_id: int, db: Session = Depends(get_db)):
    """Interrupt an ongoing generation job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in [JobStatus.PENDING, JobStatus.GENERATING]:
        raise HTTPException(status_code=400, detail="Job cannot be interrupted")

    ai_client = AIClient()
    ai_client.interrupt()

    job.status = JobStatus.FAILED
    db.commit()

    return {"message": "Generation interrupted"}


async def _generate_pages(job_id: int, request: GenerationRequest):
    """Background task to generate all coloring book pages."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    ai_client = AIClient()
    ollama_client = OllamaClient()

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.GENERATING
        db.commit()

        output_dir = os.getenv("OUTPUT_DIR", "./generated_books")
        os.makedirs(output_dir, exist_ok=True)

        for i in range(request.page_count):
            try:
                story = await ollama_client.generate_story(
                    theme=request.theme,
                    page_index=i,
                    page_count=request.page_count,
                )

                prompt_element = f"{request.theme}, page {i + 1}"
                image_result = ai_client.generate_line_art(prompt_element)

                if image_result.get("images"):
                    image_path = os.path.join(
                        output_dir, f"job_{job_id}_page_{i + 1}.png"
                    )
                    StableDiffusionAPI.decode_base64_to_image(
                        image_result["images"][0], image_path
                    )
                    process_line_art(image_path, image_path)

                    page = Page(
                        job_id=job.id,
                        story_text=story,
                        image_path=image_path,
                        prompt_used=prompt_element,
                    )
                    db.add(page)
                    db.commit()
            except Exception as e:
                pass

        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        job.status = JobStatus.FAILED
        db.commit()
    finally:
        await ollama_client.close()
        db.close()