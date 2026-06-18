# AGENTS.md

## Cursor Cloud specific instructions

### Repository layout
- The actual project source lives under `email-generation-assistant/`. It was originally committed only as `email-generation-assistant.zip`; the source has been extracted into that directory. The startup update script re-extracts the zip if the directory is missing, so both states are supported.
- **Run all commands from inside `email-generation-assistant/`.** The app reads relative paths (`prompts/`, `data/`) and writes to `reports/`, so it only works when that directory is the working directory.

### Python environment
- Python 3.12. Dependencies are installed system-wide with `pip install --break-system-packages` (the base image is PEP 668 "externally managed" and does **not** ship `python3-venv`, so a virtualenv is intentionally not used). User scripts land in `~/.local/bin`.

### Required configuration
- A valid `OPENAI_API_KEY` is required for the generation pipeline and the `/generate` endpoint; both hard-fail (CLI exits, API returns HTTP 500) without one. Set it in `email-generation-assistant/.env` or as a shell env var.
- For OpenRouter keys (`sk-or-...`) also set `OPENAI_BASE_URL=https://openrouter.ai/api/v1` and a routed `MODEL_NAME` such as `openai/gpt-4o-mini`. Use `.env.example` as the template. Do not commit `.env` (it is gitignored).

### Running the product (from `email-generation-assistant/`)
- Evaluation pipeline (default): `python3 -m src.main` — generates emails for 10 scenarios with both strategies and writes `reports/`. Note: this makes ~60 LLM calls and retries 3x (5s apart) on errors, so it is slow.
- API server (optional): `python3 -m src.main serve` — Uvicorn on port 8000; interactive docs at `http://localhost:8000/docs`.
- Docker path also exists (`docker compose up --build evaluate` / `api`) but is not needed; running directly with Python is faster for development.

### Gotchas
- stdout is buffered when piped; run with `python3 -u -m src.main` to see live progress logs.
- The `professional_structure_score` (PESS) metric in `src/metrics.py` is a pure heuristic and runs without any API key — useful for offline smoke testing.
- There are no automated tests or lint configs in this repo.
