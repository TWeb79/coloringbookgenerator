# Implementation Plan: KidsColorAI (Project 46)

**Author:** Inventions4All - github:TWeb79  
**Version:** 0.2.0  
**Project ID:** 46

## Overview
Local AI coloring book generator using FastAPI, Ollama (text), and Stable Diffusion (images).

---

## Port Allocation (Project 46)

Following RULES_ports.md:
- `8046` → FastAPI web application (main UI) ✓
- `8146` → FastAPI API service (if separated)
- `8246` → SQLite database (file-based, no port needed) ✓
- `8946` → Ollama LLM service

---

## Docker Deployment (Pending)

### 5.3 Remaining Tasks
- [ ] Create `Dockerfile` for Python FastAPI app
- [ ] Create `docker-compose.yml`
- [ ] Document both deployment methods

---

## Technical Dependencies

### Python Packages
```
fastapi
uvicorn
pydantic
httpx
sqlalchemy
pillow
img2pdf
python-multipart
jinja2
requests
```

---

## Docker Standards

Per RULES_coding.md:
- Base image: `debian:12-slim`
- Container names: `46-coloringbook-web` (if Docker deployed)
- Keep Dockerfile minimal with multi-stage builds

---

## Testing Requirements

Per RULES_coding.md:
- Create `tests/test_api.py` and `tests/test_services.py` ✓
- Use pytest framework ✓
- Tests must be runnable locally before commits ✓

---

## Success Criteria

1. Generate 30 coloring pages in under 2 hours on consumer GPU
2. All images are clean B&W line art
3. Stories are child-appropriate (5-12 years)
4. PDF output is printable A4 format
5. Application runs entirely offline after model downloads