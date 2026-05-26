"""FastAPI main application for KidsColorAI"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.db.database import init_db
from app.api.generate import router
from app.services.ai_client import AIClient
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

APP_VERSION = "0.2.0"
APP_DATETIME = "2026-05-25"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="KidsColorAI",
    description="Local AI Coloring Book Generator",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

app.mount("/output", StaticFiles(directory="generated_books"), name="output")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    version_info = f"v{APP_VERSION} ({APP_DATETIME})"
    return {"message": "KidsColorAI API", "version": version_info}


# I-11: AI Service Health Check Endpoint
@app.get("/health/ai")
async def health_ai():
    """Check health of all AI services (Stable Diffusion and Ollama)."""
    from app.services.ai_client import AIClient
    from app.services.ollama_client import OllamaClient
    
    services = {
        "stable_diffusion": {"status": "unknown", "details": None},
        "ollama": {"status": "unknown", "details": None},
    }
    
    # Check Stable Diffusion
    try:
        sd_client = AIClient()
        if sd_client.is_ready():
            services["stable_diffusion"]["status"] = "healthy"
            services["stable_diffusion"]["details"] = "Ready to generate"
        else:
            services["stable_diffusion"]["status"] = "unhealthy"
            services["stable_diffusion"]["details"] = "Not ready"
    except Exception as e:
        services["stable_diffusion"]["status"] = "error"
        services["stable_diffusion"]["details"] = str(e)
    
    # Check Ollama
    try:
        ollama_client = OllamaClient()
        is_ready = await ollama_client.health_check()
        if is_ready:
            services["ollama"]["status"] = "healthy"
            services["ollama"]["details"] = "Ollama is running"
        else:
            services["ollama"]["status"] = "unhealthy"
            services["ollama"]["details"] = "Ollama not responding"
        await ollama_client.close()
    except Exception as e:
        services["ollama"]["status"] = "error"
        services["ollama"]["details"] = str(e)
    
    # Overall status
    all_healthy = all(s["status"] == "healthy" for s in services.values())
    overall = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall,
        "version": f"v{APP_VERSION}",
        "services": services,
    }
