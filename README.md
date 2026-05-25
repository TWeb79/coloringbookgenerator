# KidsColorAI - Local AI Coloring Book Generator

**Version:** 0.2.0  
**Author:** Inventions4All - github:TWeb79

## Project Overview

KidsColorAI is a self-hosted web application that generates customizable coloring book pages for children. It combines generative text (stories) and generative art (line drawings) entirely on the local machine.

## Service Ports

| Port | Service |
|------|---------|
| 8046 | FastAPI web application (main UI) |
| 8146 | FastAPI API service (optional) |
| 8946 | Ollama LLM service |

## Startup Instructions

### Prerequisites
- Python 3.11+
- Ollama installed and running (`ollama serve`)
- Stable Diffusion WebUI running with API enabled (`--api` flag)

### Installation
```bash
pip install -r requirements.txt
```

### Running
```bash
python launch.py
```

Or directly:
```bash
uvicorn app.main:app --port 8046
```

## Dependencies

- fastapi - Web framework
- uvicorn - ASGI server
- SQLAlchemy - Database ORM
- pillow - Image processing
- httpx - HTTP client for async requests

## API Endpoints

### POST /api/generate
Start a new coloring book generation.
```json
{
  "theme": "Dinosaurs",
  "page_count": 30,
  "image_size": 1024
}
```

### GET /api/job/{job_id}
Check generation status.

### GET /api/pages/{job_id}
List generated pages.

### GET /api/pdf/{job_id}
Download generated coloring book as PDF.

### POST /api/job/{job_id}/interrupt
Interrupt an ongoing generation.

### GET /output/{job_id}/{filename}
Download generated images.

## Example Request
```bash
curl -X POST http://localhost:8046/api/generate \
  -H "Content-Type: application/json" \
  -d '{"theme": "Space Adventures", "page_count": 10}'
```# coloringbookgenerator
