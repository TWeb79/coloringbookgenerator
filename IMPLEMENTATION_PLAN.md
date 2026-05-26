# Implementation Plan: KidsColorAI (Project 46)

**Author:** Inventions4All - github:TWeb79  
**Version:** 0.5.0
**Project ID:** 46

## Overview
Local AI coloring book generator using FastAPI, Ollama (text), and Stable Diffusion (images).

---

## Port Allocation (Project 46)

Following RULES_ports.md:
- `8046` → FastAPI web application (main UI)
- `8146` → FastAPI API service (if separated)
- `8246` → SQLite database (file-based, no port needed)
- `8946` → Ollama LLM service

---

## Pending Improvements

### I-7: Character Consistency Validation
**Priority:** Low
**Issue:** No guarantee character looks consistent across pages.
**Solution:** Include character reference in all prompts. Consider using img2img with previous page as reference (low denoising).

### I-8: WebSocket Support for Real-time Updates
**Priority:** Low
**Files:** `app/main.py`, `static/app.js`
**Issue:** Polling every 2 seconds is inefficient.
**Solution:** Implement WebSocket for push notifications when job status changes.

### I-12: Configuration File
**Priority:** Low
**Solution:** Support `config.yaml` in addition to environment variables for easier setup.

### I-14: Batch Processing for Images
**Priority:** Low
**File:** `app/services/ai_client.py`
**Solution:** If SD API supports batch generation, generate multiple images in parallel to speed up generation.

### I-15: Rate Limiting
**Priority:** Low
**Solution:** Add rate limiting to prevent abuse of generation endpoint.

### I-16: Caching for Character Descriptions
**Priority:** Low
**Solution:** Cache generated character descriptions for similar themes to reduce Ollama calls.

### I-17: Exception Handling and Error Logging ✅
**Priority:** High
**Files:** All service files

**Completed:**
- Added `logging` module import to all service files
- Added `logger = logging.getLogger(__name__)` in all modules
- Added logging in `app/api/generate.py` for list_jobs, get_job, download_page, download_job_zip
- Fixed `is_ready()` logic in `app/services/ai_client.py` - now correctly checks state != "busy"
- Added HTTP error handling in `app/services/ollama_client.py` for generate_character and generate_story_plan
- Added logging in `app/services/ollama_client.py` for model selection and generation
- Added logging in `app/services/ai_client.py` for retry logic and readiness checks
- Added logging in `app/main.py` (logger defined but not heavily used as it's mainly a routing module)
- Added logging in `app/pdf_generator.py` and `app/utils/image_processor.py`
- Fixed `download_job_zip` to track and log missing files instead of silently skipping

---

## Completed Improvements

### I-9: Job History ✅
**Files:** `app/api/generate.py`
**Implementation:** Added `GET /jobs` endpoint with pagination, `GET /jobs/{job_id}` for individual job retrieval

### I-10: Export Options ✅
**Files:** `app/api/generate.py`
**Implementation:** Added `GET /page/{page_id}/download` for individual page download, `GET /job/{job_id}/zip` for ZIP download

---

## Future Enhancements

### Phase LLM-1: SVG Approach (Recommended)
- [ ] A1-SVG-1: Add `cairosvg` or `svglib` to requirements.txt
- [ ] A1-SVG-2: Create `app/services/svg_generator.py`
- [ ] A1-SVG-3: Create SVG prompt template in `app/prompts.py`
- [ ] A1-SVG-4: Create `render_svg_to_image()` function
- [ ] A1-SVG-5: Update `app/services/ollama_client.py` to add `generate_svg()` method
- [ ] A1-SVG-6: Create `app/services/image_generator.py` as factory
- [ ] A1-SVG-7: Update `app/api/generate.py` to use new image generator
- [ ] A1-SVG-8: Add SVG validation
- [ ] A1-SVG-9: Add fallback prompts if SVG generation fails

### Phase LLM-2: Coordinate Approach (Alternative)
- [ ] A3-COORD-1: Define drawing schema in `app/models/schemas.py`
- [ ] A3-COORD-2: Create `app/services/coordinate_renderer.py`
- [ ] A3-COORD-3: Create coordinate prompt template
- [ ] A3-COORD-4: Add JSON validation and error recovery
- [ ] A3-COORD-5: Optimize for drawing speed

### Phase LLM-3: Integration
- [ ] Add configuration option to choose image generation method
- [ ] Add UI toggle: "Use Stable Diffusion" vs "Use LLM Only"
- [ ] Document hardware requirements for each approach
- [ ] Performance comparison testing

---

## Dependencies for LLM-Only Mode

```
# Add to requirements.txt
cairosvg>=2.7.0  # SVG rendering (requires cairo system library)
# OR
svglib>=1.5.0    # Pure Python SVG rendering
reportlab>=4.0   # For PDF generation with text