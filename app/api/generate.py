"""API routes for coloring book generation"""
import asyncio
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stable_diffusion_api import StableDiffusionAPI

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.db.database import get_db, GenerationJob, Page, StoryPlan, StoryPage
from app.models.schemas import (
    CharacterDefinition,
    GenerationRequest,
    GenerationJob as GenerationJobSchema,
    PageResponse,
    JobStatusResponse,
    StoryPage as StoryPageSchema,
    JobStatus,
)
from app.services.ai_client import AIClient
from app.services.ollama_client import OllamaClient
from app.services.content_filter import content_filter
from app.utils.image_processor import process_line_art, validate_line_art_quality
from app.pdf_generator import generate_coloring_book_pdf

router = APIRouter()

# I-4: Cancellation flag for job interruption
_cancellation_flags: dict[int, bool] = {}


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

    asyncio.create_task(_generate_story_plan(job.id, request))

    return job


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of a generation job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pages = db.query(Page).filter(Page.job_id == job_id).all()
    progress = (len(pages) / job.page_count * 100) if job.page_count > 0 else 0

    story_pages = db.query(StoryPage).filter(StoryPage.job_id == job_id).all()
    story_pages_data = [
        StoryPageSchema(
            page_number=sp.page_number,
            story_text=sp.story_text,
            image_prompt=sp.image_prompt
        )
        for sp in sorted(story_pages, key=lambda x: x.page_number)
    ]

    character = None
    if job.story_plan:
        character = CharacterDefinition(
            name=job.story_plan.character_name,
            description=job.story_plan.character_description,
            appearance=job.story_plan.character_appearance,
            personality=job.story_plan.character_personality,
            key_features=job.story_plan.character_key_features,
            color_palette=job.story_plan.character_color_palette,
        )

    status_map = {
        JobStatus.PENDING: "Generating story plan...",
        JobStatus.GENERATING: f"Generating images: page {len(pages)} of {job.page_count}",
        JobStatus.COMPLETED: "Generation complete",
        JobStatus.FAILED: "Generation failed",
    }

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=int(progress),
        message=status_map.get(job.status, "Unknown status"),
        character=character,
        story_pages=story_pages_data if story_pages_data else None,
    )


@router.get("/pages/{job_id}", response_model=list[PageResponse])
async def get_job_pages(job_id: int, db: Session = Depends(get_db)):
    """Get all generated pages for a job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pages = db.query(Page).filter(Page.job_id == job_id).all()
    return [
        PageResponse(
            id=p.id,
            job_id=p.job_id,
            story_text=p.story_text,
            image_path=p.image_path,
            prompt_used=p.prompt_used,
            image_prompt=p.image_prompt
        )
        for p in pages
    ]


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

    # I-4: Set cancellation flag
    _cancellation_flags[job_id] = True

    ai_client = AIClient()
    ai_client.interrupt()

    job.status = JobStatus.FAILED
    db.commit()

    return {"message": "Generation interrupted"}


@router.get("/jobs", response_model=list[GenerationJobSchema])
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all generation jobs with pagination.
    
    I-9: Job History
    """
    logger.info(f"Listing jobs: limit={limit}, offset={offset}")
    jobs = db.query(GenerationJob).order_by(
        GenerationJob.created_at.desc()
    ).offset(offset).limit(limit).all()
    logger.debug(f"Found {len(jobs)} jobs")
    return jobs


@router.get("/jobs/{job_id}", response_model=GenerationJobSchema)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID."""
    logger.info(f"Getting job: {job_id}")
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/page/{page_id}/download")
async def download_page(page_id: int, db: Session = Depends(get_db)):
    """Download a single page image.
    
    I-10: Export Options - Individual page download
    """
    logger.info(f"Downloading page: {page_id}")
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        logger.warning(f"Page not found: {page_id}")
        raise HTTPException(status_code=404, detail="Page not found")
    
    if not os.path.exists(page.image_path):
        logger.error(f"Image file not found for page {page_id}: {page.image_path}")
        raise HTTPException(status_code=404, detail="Image file not found")
    
    logger.info(f"Serving page {page_id} from {page.image_path}")
    return FileResponse(
        page.image_path,
        media_type="image/png",
        filename=f"page_{page.id}.png",
    )


@router.get("/job/{job_id}/zip")
async def download_job_zip(job_id: int, db: Session = Depends(get_db)):
    """Download all pages of a job as a ZIP file.
    
    I-10: Export Options - ZIP download
    """
    import zipfile
    from io import BytesIO
    
    logger.info(f"Creating ZIP for job: {job_id}")
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        logger.warning(f"Job not found for ZIP: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    pages = db.query(Page).filter(Page.job_id == job_id).order_by(Page.id).all()
    if not pages:
        logger.warning(f"No pages found for ZIP job: {job_id}")
        raise HTTPException(status_code=400, detail="No pages found")
    
    # Create ZIP in memory
    zip_buffer = BytesIO()
    missing_files = []
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, page in enumerate(pages):
            if os.path.exists(page.image_path):
                zip_file.write(page.image_path, f"page_{i+1:02d}.png")
            else:
                missing_files.append(page.image_path)
                logger.warning(f"Missing file for ZIP: {page.image_path}")
    
    if missing_files:
        logger.warning(f"ZIP created with {len(missing_files)} missing files for job {job_id}")
    
    zip_buffer.seek(0)
    logger.info(f"ZIP created for job {job_id} with {len(pages)} pages")
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=coloring_book_{job_id}.zip"}
    )


@router.post("/job/{job_id}/page/{page_number}/regenerate")
async def regenerate_page(job_id: int, page_number: int, db: Session = Depends(get_db)):
    """Regenerate a single page of a coloring book.
    
    I-6: Individual page regeneration
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job must be completed to regenerate pages")

    # Get the story page data
    story_page = db.query(StoryPage).filter(
        StoryPage.job_id == job_id,
        StoryPage.page_number == page_number
    ).first()
    
    if not story_page:
        raise HTTPException(status_code=404, detail="Story page not found")

    # Get existing page if any
    existing_page = db.query(Page).filter(
        Page.job_id == job_id,
        Page.image_prompt == story_page.image_prompt
    ).first()

    output_dir = os.getenv("OUTPUT_DIR", "./generated_books")
    os.makedirs(output_dir, exist_ok=True)

    try:
        ai_client = AIClient()
        
        # I-1: Use retry logic for image generation
        image_result = ai_client.generate_line_art_with_retry(
            story_page.image_prompt,
            size=1024  # Default size
        )

        if image_result.get("images"):
            image_path = os.path.join(
                output_dir, f"job_{job_id}_page_{story_page.page_number}.png"
            )
            StableDiffusionAPI.decode_base64_to_image(
                image_result["images"][0], image_path
            )
            process_line_art(image_path, image_path)

            # I-3: Validate image quality
            is_valid, metrics = validate_line_art_quality(image_path)
            if not is_valid:
                logger.warning(f"Regenerated image quality check failed for page {page_number}: {metrics}")

            if existing_page:
                # Update existing page
                existing_page.image_path = image_path
                existing_page.prompt_used = story_page.image_prompt
            else:
                # Create new page
                new_page = Page(
                    job_id=job.id,
                    story_text=story_page.story_text,
                    image_path=image_path,
                    prompt_used=story_page.image_prompt,
                    image_prompt=story_page.image_prompt,
                )
                db.add(new_page)
            
            db.commit()

            return {
                "message": f"Page {page_number} regenerated successfully",
                "image_path": image_path,
                "quality_valid": is_valid,
                "quality_metrics": metrics
            }
        else:
            raise HTTPException(status_code=500, detail="Image generation returned no images")

    except Exception as e:
        logger.error(f"Failed to regenerate page {page_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_story_plan(job_id: int, request: GenerationRequest):
    """Background task to generate character, story plan with prompts first."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    ollama_client = OllamaClient()
    ollama_initialized = False

    try:
        ollama_initialized = await ollama_client.initialize()
        
        # B-4: Check if Ollama initialization succeeded
        if not ollama_initialized:
            logger.error(f"Ollama initialization failed for job {job_id}")
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                db.commit()
            return

        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            await ollama_client.close()
            db.close()
            return

        character_data = await ollama_client.generate_character(request.theme)

        # I-2: Validate character data for inappropriate content
        for field in ['name', 'description', 'appearance', 'personality']:
            if field in character_data:
                is_safe, matched = content_filter.check_text(character_data[field])
                if not is_safe:
                    logger.warning(f"Character {field} contains inappropriate content: {matched}")
                    if content_filter.is_critical(character_data[field]):
                        # Re-generate character
                        logger.warning("Critical content detected, re-generating character...")
                        character_data = await ollama_client.generate_character(request.theme)
                        break

        key_features = character_data.get("key_features", [])
        key_features_str = ", ".join(key_features) if isinstance(key_features, list) else str(key_features)

        story_plan = StoryPlan(
            job_id=job.id,
            character_name=character_data.get("name", "Hero"),
            character_description=character_data.get("description", ""),
            character_appearance=character_data.get("appearance", ""),
            character_personality=character_data.get("personality", ""),
            character_key_features=key_features_str,
            character_color_palette=character_data.get("color_palette", ""),
        )
        db.add(story_plan)
        db.commit()

        story_pages_data = await ollama_client.generate_story_plan(
            request.theme, request.page_count, character_data
        )

        for page_data in story_pages_data:
            sp = StoryPage(
                job_id=job.id,
                page_number=page_data.get("page_number", 0),
                story_text=page_data.get("story_text", ""),
                image_prompt=page_data.get("image_prompt", ""),
            )
            db.add(sp)
        db.commit()

        job.status = JobStatus.GENERATING
        db.commit()

        await ollama_client.close()

        await _generate_images(job_id, request)

    except Exception as e:
        logger.exception(f"Error in _generate_story_plan for job {job_id}: {e}")
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            db.commit()
        try:
            await ollama_client.close()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass


async def _generate_images(job_id: int, request: GenerationRequest):
    """Background task to generate images for all story pages."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    ai_client = AIClient()

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            db.close()
            return

        output_dir = os.getenv("OUTPUT_DIR", "./generated_books")
        os.makedirs(output_dir, exist_ok=True)

        story_pages = db.query(StoryPage).filter(StoryPage.job_id == job_id).order_by(StoryPage.page_number).all()

        for story_page in story_pages:
            # I-4: Check for cancellation
            if _cancellation_flags.get(job_id, False):
                logger.info(f"Job {job_id} cancelled, stopping image generation")
                _cancellation_flags.pop(job_id, None)
                return

            try:
                # I-1: Use retry logic for image generation
                image_result = ai_client.generate_line_art_with_retry(
                    story_page.image_prompt, 
                    size=request.image_size
                )

                if image_result.get("images"):
                    image_path = os.path.join(
                        output_dir, f"job_{job_id}_page_{story_page.page_number}.png"
                    )
                    StableDiffusionAPI.decode_base64_to_image(
                        image_result["images"][0], image_path
                    )
                    process_line_art(image_path, image_path)

                    # I-3: Validate image quality
                    is_valid, metrics = validate_line_art_quality(image_path)
                    if not is_valid:
                        logger.warning(f"Image quality check failed for page {story_page.page_number}: {metrics}")
                        # Continue anyway but log the issue

                    page = Page(
                        job_id=job.id,
                        story_text=story_page.story_text,
                        image_path=image_path,
                        prompt_used=story_page.image_prompt,
                        image_prompt=story_page.image_prompt,
                    )
                    db.add(page)
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to generate image for page {story_page.page_number}: {e}")
                # Continue with remaining pages but track failure
                continue

        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.exception(f"Error in _generate_images for job {job_id}: {e}")
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            db.commit()
    finally:
        db.close()