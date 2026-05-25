"""FastAPI main application for KidsColorAI"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.db.database import init_db
from app.api.generate import router

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