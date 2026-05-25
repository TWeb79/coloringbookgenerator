# concept.md: KidsColorAI - Local AI Coloring Book Generator

## 1. Project Overview
**Project Name:** KidsColorAI  
**Version:** 0.1.0 (Concept)  
**Target Audience:** Parents, Educators, Hobbyists.  
**Core Purpose:** A self-hosted web application that generates customizable coloring book pages for children.  
**Key Constraint:** Must run locally (privacy/offline), using Python, Docker, Ollama (Text), and Stable Diffusion (Images).  
**Output:** Black-and-white line art illustrations with simple stories, suitable for pen coloring.

## 2. Problem Statement
Parents want to engage children in creative activities. Commercial coloring books are static. AI coloring books exist but often require cloud access (privacy concerns) or produce filled-out images instead of line art. This application combines generative text (stories) and generative art (line drawings) entirely on the local machine.

## 3. Technical Stack & Architecture

### 3.1. Backend & Logic
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (for async handling and easy OpenAPI docs)
*   **Task Queue:** Celery + Redis (optional, for queuing 30 generations) or AsyncIO native.
*   **Database:** SQLite (lightweight, local storage) or DuckDB.

### 3.2. AI Services (Local)
*   **Text Generation:** Ollama (e.g., `llama3`, `mistral`).
    *   *Deployment:* Separate container or local host socket (`http://host.docker.internal:11434`).
*   **Image Generation:** Stable Diffusion (WebUI API or ComfyUI).
    *   *Deployment:* Separate container with model cache mounted.
    *   *Model Strategy:* Use a model optimized for "clean line art" (e.g., SDXL LineArt or specific LoRA).
*   **Image Post-processing:** OpenCV/Pillow (ensure white background, remove noise).

### 3.3. Infrastructure
*   **Orchestration:** Docker Compose.
*   **OS:** Linux (Docker Desktop / Podman), Linux Server, or WSL2 on Windows.

### 3.4. Frontend (Optional/MVP)
*   **Suggestion:** Streamlit for rapid MVP, or React/Vue for polished UI.
*   **Recommendation:** Start with **HTMX + HTML templates** for simplicity, or **FastAPI** with embedded SVG/JS if using Streamlit.

---

## 4. User Workflow

1.  **Configuration:**
    *   User enters a **Theme** (e.g., "Dinosaurs in Summer Vacation").
    *   User sets **Page Count (N)** (Default: 30).
    *   User configures **Image Size** (e.g., 1024x1024).
2.  **Generation Queue:**
    *   System sends a request to create an outline for all $N$ pages.
    *   System generates a list of prompts and stores them in the queue.
3.  **Processing:**
    *   For each page $i$ (0 to $N-1$):
        *   Call Ollama API for a simple story.
        *   Call Stable Diffusion API for image using "line art" specific prompt.
        *   Save story + image to local folder.
4.  **Completion:**
    *   User can view pages in a grid.
    *   User downloads the PDF or ZIP of the book.

---

## 5. AI Model Strategy & Prompt Engineering

### 5.1. Ollama (Text Generation)
**Goal:** Simple, encouraging, repetitive stories (1-3 sentences per page) suitable for reading aloud.

**System Prompt:**
```yaml
role: system
instruction: "You are a children's storybook writer. Write a very short, simple story paragraph for each page. Keep sentences short. Use exciting language for kids. Do not use complex words."
```

**Context Template:**
```text
Theme: {theme}
Page: {index} of {count}
Story Idea: {context}
```

### 5.2. Stable Diffusion (Image Generation)
**Goal:** High-contrast Black and White line art. No shading, no fill.

**Negative Prompt:**
```text
shading, coloring, grayscale, filled, color, texture, noise, blurry, low contrast, dark, complex details, realistic
```

**Positive Prompt (Template):**
```text
simple black and white line art, coloring book page, thick outlines, white background, {theme_element}, children drawing style, high contrast, vector style, clean lines
```

**Model Recommendation:**
*   Use SDXL or SD 1.5.
*   Suggest loading a "Line Art" checkpoint (e.g., `epicpaint` or `lineart_awesome_anime`).
*   Or use ControlNet `Canny` or `Lineart_Anime` if generating from a sketch (not needed for this MVP, just rely on prompt).

---

## 6. Docker Compose Architecture

We will use a `docker-compose.yml` to orchestrate the stack.

```yaml
version: '3.9'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=ollama
      - SD_HOST=sd-webui
    depends_on:
      - ollama
      - sd-webui

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    command: serve

  sd-webui:
    image: ghcr.io/lshui/stable-diffusion-webui-docker:latest # Example lightweight image
    ports:
      - "7860:7860"
    environment:
      - OLLAMA_HOST=ollama
    volumes:
      - sd-data:/workspace
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama-data:
  sd-data:
```

---

## 7. Database Schema (SQLite)

Minimal schema to track generation jobs.

```sql
-- Table: GenerationJobs
CREATE TABLE generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme TEXT NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 30,
    status TEXT DEFAULT 'PENDING', -- PENDING, GENERATING, COMPLETED, FAILED
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME
);

-- Table: Pages (Store results)
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    story_text TEXT,
    image_path TEXT NOT NULL,
    prompt_used TEXT,
    FOREIGN KEY (job_id) REFERENCES generation_jobs(id)
);
```

---

## 8. Safety & Ethical Considerations
*   **Content Filtering:** Since Ollama is local, it can generate NSFW text if not prompted correctly.
    *   *Mitigation:* Strict System Prompt: "Always keep content safe for children (5-12 years). No violence, no profanity."
*   **Model Safety:** Ensure Ollama models (e.g., `llama3`) are updated to respect safety guidelines.
*   **Privacy:** Images and text are never sent to the cloud. All processing is local GPU/VRAM usage.

---

## 9. Implementation Roadmap

### Phase 1: MVP (Minimum Viable Product)
*   [ ] Setup Docker Compose (Web + Ollama + SD).
*   [ ] Create `app.py` (FastAPI) with endpoints `/generate`.
*   [ ] Implement prompt templates (Text + Image).
*   [ ] Implement local folder storage (Output path).
*   [ ] Build a simple HTML form to trigger generation.

### Phase 2: UX & Feedback
*   [ ] Add Progress Bar (Polling the job queue).
*   [ ] Add PDF Generation (using `reportlab` or `img2pdf`).
*   [ ] Allow manual "regenerate" of specific page.

### Phase 3: Optimization
*   [ ] Implement batching for SD to save VRAM time.
*   [ ] Implement image cropping to remove black borders (SD often adds white/black padding).

---

## 10. Risks & Mitigations

| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **Slow Inference** | High | 30 pages will take time. Add progress bar. Do not generate all at once if possible (allow stopping). Use SD 1.5 instead of SDXL if speed is critical. |
| **NSFW Text/Art** | Critical | Use `Ollama:latest` with safety model, or add regex filter to block bad words before rendering. |
| **GPU Memory** | Medium | Limit SD to specific VRAM usage. Use `--lowvram` flag in docker env. |
| **Prompt Drift** | Medium | Hard-code the `negative_prompt` for images to ensure lines are always black. |

---

## 11. File Structure

```text
kids-color-book/
├── docker-compose.yml
├── .env
├── app/
│   ├── __init__.py
│   ├── main.py (FastAPI Entry)
│   ├── logic.py (AI Logic: Ollama/SD)
│   ├── models.py (Pydantic Schemas)
│   ├── utils.py (Image Processing: Crop, B&W Check)
│   └── pdf_generator.py
├── templates/
│   └── index.html
└── Dockerfile
```

---

## 12. Environment Variables (.env)

```bash
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=llama3 # Or mistral

STABLE_DIFFUSION_HOST=http://host.docker.internal:7860
SD_STEPS=20
SD_CGI=false # Ensure CFG (Denoising strength) is controlled
SD_IMAGE_SIZE=1024

OUTPUT_DIR=./generated_books
MAX_PAGES=30
```

---

## 13. Next Steps for Developer
1.  Clone this concept into `README.md`.
2.  Initialize the FastAPI project.
3.  Write the `Dockerfile` to run the Python app + dependencies.
4.  Create the `docker-compose.yml` with GPU resources reserved.
5.  Implement the `/api/generate` endpoint first.
6.  Test with "Simple Dinosaur" theme.