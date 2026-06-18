# Email Generation Assistant

> **AI Engineer Candidate Assessment** – A production-quality LLM evaluation framework for comparing email generation strategies.

---

## Overview

This project builds an **Email Generation Assistant** that accepts an **Intent**, **Key Facts**, and **Tone**, then generates a professional email. It implements a rigorous evaluation framework with **three custom LLM-as-a-Judge metrics** and compares two prompting strategies across **10 diverse test scenarios**.

## Architecture

```
email-generation-assistant/
├── .env.example               # Environment variable template
├── Dockerfile                  # Python 3.12 container
├── docker-compose.yml          # Evaluate & API services
├── requirements.txt            # Python dependencies
│
├── data/
│   ├── test_cases.json         # 10 evaluation scenarios
│   └── references.json         # Human-written reference emails
│
├── prompts/
│   ├── baseline_prompt.txt     # Strategy B: simple instruction
│   └── advanced_prompt.txt     # Strategy A: role + few-shot + rules
│
├── reports/                    # Generated outputs (gitignored)
│   ├── evaluation_results.csv
│   ├── evaluation_results.json
│   └── final_report.md
│
└── src/
    ├── __init__.py
    ├── email_generator.py      # Email generation (Baseline & Advanced)
    ├── llm_judge.py            # LLM-as-a-Judge (structured outputs)
    ├── metrics.py              # FCS, TAS, PESS metric functions
    ├── evaluator.py            # Evaluation orchestrator
    ├── compare_models.py       # Statistical comparison & report
    └── main.py                 # CLI entry point & FastAPI server
```

## Prompt Engineering Techniques

| Technique | Strategy A (Advanced) | Strategy B (Baseline) |
|---|---|---|
| Role Prompting | ✅ System message as expert communications assistant | ❌ |
| Few-Shot Examples | ✅ 3 diverse examples | ❌ |
| Structured Rules | ✅ 5 explicit rules (structure, tone, facts, clarity, subject) | ❌ |

## Custom Evaluation Metrics

| # | Metric | Method | Score Range |
|---|--------|--------|-------------|
| 1 | **Fact Coverage Score (FCS)** | LLM-as-a-Judge with Pydantic structured output | 0.0 – 1.0 |
| 2 | **Tone Alignment Score (TAS)** | LLM-as-a-Judge with Pydantic structured output | 0.0 – 1.0 |
| 3 | **Professional Structure Score (PESS)** | Heuristic regex (Greeting + Body + Closing) | 0.0 – 1.0 |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- An OpenAI-compatible API key

### Setup

```bash
# 1. Clone the repository
git clone <repo-url> && cd email-generation-assistant

# 2. Configure your API key
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# 3. Run the evaluation pipeline
docker compose up --build evaluate

# 4. (Optional) Start the FastAPI server
docker compose up --build api -d
# API available at http://localhost:8000/docs
```

### API Usage

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Schedule a team meeting",
    "key_facts": ["Meeting is on Friday at 3 PM", "Duration is 1 hour"],
    "tone": "Professional and friendly",
    "strategy": "advanced"
  }'
```

## Tech Stack

- **Python 3.12** – Core language
- **OpenAI SDK** – LLM interaction with structured outputs
- **Pydantic v2** – Type-safe structured LLM responses
- **Pandas** – Data aggregation and CSV export
- **FastAPI + Uvicorn** – Optional REST API
- **Docker** – Containerised execution

## Output Files

After running the pipeline, check `reports/`:

| File | Description |
|------|-------------|
| `evaluation_results.csv` | Per-scenario scores for both strategies |
| `evaluation_results.json` | Full data including generated email text |
| `final_report.md` | Comparative analysis answering questions A, B, C |
