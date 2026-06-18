"""
Email Generation Assistant – Entry Point

Usage:
  CLI evaluation:   python -m src.main
  FastAPI server:   python -m src.main serve
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables before any other imports that might need them
load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from typing import List  # noqa: E402
from openai import OpenAI  # noqa: E402

from .evaluator import Evaluator  # noqa: E402
from .compare_models import ModelComparator  # noqa: E402
from .email_generator import EmailGenerator  # noqa: E402


# ── FastAPI Application ──────────────────────────────────────────

app = FastAPI(
    title="Email Generation Assistant API",
    description="Generate professional emails using advanced prompt engineering.",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    """Request body for the /generate endpoint."""
    intent: str
    key_facts: List[str]
    tone: str
    strategy: str = "advanced"  # "advanced" or "baseline"


class GenerateResponse(BaseModel):
    """Response body for the /generate endpoint."""
    strategy: str
    generated_email: str


@app.post("/generate", response_model=GenerateResponse)
def generate_email(req: GenerateRequest) -> GenerateResponse:
    """Generate an email using the specified strategy."""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set.")

    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=base_url if base_url else None,
    )
    generator = EmailGenerator(client)

    if req.strategy.lower() == "baseline":
        email = generator.generate_baseline(req.intent, req.key_facts, req.tone)
    else:
        email = generator.generate_advanced(req.intent, req.key_facts, req.tone)

    return GenerateResponse(strategy=req.strategy, generated_email=email)


# ── CLI Pipeline ─────────────────────────────────────────────────

def run_cli() -> None:
    """Run the full evaluation pipeline from the command line."""
    print("Email Generation Assistant – Evaluation Pipeline")
    print("=" * 50)

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not found.")
        print("Please set it in the .env file or export it in your terminal.")
        sys.exit(1)

    # Phase 1: Run Evaluation
    print("\n[Phase 1] Running Evaluation on Test Scenarios...")
    evaluator = Evaluator()
    evaluator.run_evaluation()

    # Phase 2: Compare Models and Generate Report
    print("\n[Phase 2] Analysing Results and Generating Report...")
    comparator = ModelComparator()
    comparator.generate_report()

    print("\n✅ Pipeline Complete. Check the 'reports/' directory for results.")


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        run_cli()
