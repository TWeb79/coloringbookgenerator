# KidsColorAI - Local AI Coloring Book Generator

**Version:** 0.2.0  
**Author:** Inventions4All - github:TWeb79

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Project Overview

KidsColorAI is a self-hosted web application that generates customizable coloring book pages for children. It combines generative text (stories) and generative art (line drawings) entirely on the local machine.

- **Privacy-first**: All processing runs locally - no cloud dependencies
- **Offline-capable**: Works after initial model downloads
- **Customizable**: Themes, page counts, and image sizes configurable

## Features

- Generate black & white line art coloring pages
- Create simple children's stories for each page
- Export as PDF for printing
- Interrupt generation on demand
- Process images for clean line art output

## Service Ports

| Port | Service | Description |
|------|---------|-------------|
| 8046 | FastAPI web application | Main UI |
| 8146 | FastAPI API service | If separated |
| 8246 | SQLite database | File-based, no port |
| 8946 | Ollama LLM service | Text generation |

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running (`ollama serve`)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) with API enabled (`--api` flag)

## Installation

```bash
# Clone the repository
git clone https://github.com/TWeb79/46-coloringbook.git
cd 46-coloringbook

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Starting the Application

```bash
python launch.py
```

Or directly with uvicorn:

```bash
uvicorn app.main:app --port 8046
```

Access the application at `http://localhost:8046`

### Generating a Coloring Book

1. Enter a theme (e.g., "Dinosaurs", "Space Adventures")
2. Set the number of pages (default: 30)
3. Choose image size (512x512, 768x768, or 1024x1024)
4. Click "Generate Coloring Book"
5. Wait for generation to complete
6. Download the PDF or view individual pages

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.0 | Web framework |
| uvicorn | 0.30.6 | ASGI server |
| SQLAlchemy | 2.0.35 | Database ORM |
| pillow | 10.4.0 | Image processing |
| httpx | 0.27.2 | HTTP client |
| jinja2 | 3.1.4 | Template rendering |

## API Reference

### POST /api/generate

Start a new coloring book generation.

**Request Body:**
```json
{
  "theme": "Dinosaurs",
  "page_count": 30,
  "image_size": 1024
}
```

**Response:**
```json
{
  "id": 1,
  "theme": "Dinosaurs",
  "page_count": 30,
  "status": "PENDING",
  "created_at": "2026-05-25T12:00:00"
}
```

### GET /api/job/{job_id}

Check generation status.

**Response:**
```json
{
  "job_id": 1,
  "status": "COMPLETED",
  "progress": 100,
  "message": "Generation complete"
}
```

### GET /api/pages/{job_id}

List generated pages with stories and image paths.

### GET /api/pdf/{job_id}

Download the complete coloring book as a PDF.

### POST /api/job/{job_id}/interrupt

Interrupt an ongoing generation (useful for stopping long-running jobs).

## Project Structure

```
46-coloringbook/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   └── generate.py      # API routes
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── ai_client.py     # Stable Diffusion wrapper
│   │   └── ollama_client.py # Ollama API client
│   ├── db/
│   │   └── database.py      # SQLite models
│   ├── utils/
│   │   └── image_processor.py # Image utilities
│   └── pdf_generator.py     # PDF generation
├── templates/
│   └── index.html           # Web UI
├── static/
│   ├── style.css            # Styles
│   └── app.js               # Frontend logic
├── tests/
│   ├── test_api.py
│   └── test_services.py
├── launch.py                # Desktop entry point
├── requirements.txt
└── README.md
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

**Ollama not responding:**
- Ensure `ollama serve` is running
- Check OLLAMA_HOST in `.env` matches your setup

**Stable Diffusion not responding:**
- Start SD WebUI with `--api --listen` flags
- Verify SD_HOST in `.env` is correct

**Generation taking too long:**
- Reduce page count
- Use smaller image size
- Enable interrupt to stop and retry

## Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- NVIDIA GPU with Docker GPU support (optional, for SD acceleration)

### Running with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Docker Volumes

- `ollama-data`: Persistent Ollama model storage
- `sd-data`: Stable Diffusion model storage
- `./generated_books`: Generated coloring books (host-mounted)

### Environment Variables

Configure in `.env` or docker-compose.yml:

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_HOST | http://ollama:11434 | Ollama API endpoint |
| STABLE_DIFFUSION_HOST | http://sd-webui:7860 | SD WebUI API endpoint |
| OUTPUT_DIR | /app/generated_books | Output directory |

Access the application at `http://localhost:8046`