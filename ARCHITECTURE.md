# KidsColorAI Architecture

## System Structure

```
User Browser → FastAPI (8046) → Routes → Services → AI APIs
                                    ↓
                              SQLite Database
```

## Module Responsibilities

### app/main.py
- FastAPI application entry point
- Mounts static files and templates
- Defines request lifespan for DB initialization

### app/api/generate.py
- API route handlers for coloring book generation
- Start/queue generation jobs
- Returns job status and generated pages

### app/services/ai_client.py
- Wrapper for Stable Diffusion WebUI API
- KidsColorAI-specific defaults (line art prompts)
- Image generation with negative prompt for B&W output

### app/services/ollama_client.py
- Wrapper for Ollama LLM API
- Children's story generation with safety prompts
- Async HTTP client for text generation

### app/db/database.py
- SQLite database models (GenerationJob, Page)
- Session management and initialization

### app/utils/image_processor.py
- Image processing (white background, noise removal)
- Line art post-processing

## Data Flow

1. User submits theme via web form
2. POST /api/generate creates job in database
3. Background task generates stories (Ollama) and images (Stable Diffusion)
4. Pages saved to database and disk
5. User views results and downloads PDF

## External Dependencies

- Ollama (http://127.0.0.1:11434) - Text generation
- Stable Diffusion WebUI (http://127.0.0.1:7860) - Image generation

## Service Boundaries

- Routes never contain business logic
- Services contain all AI integration logic
- Database layer handles persistence only