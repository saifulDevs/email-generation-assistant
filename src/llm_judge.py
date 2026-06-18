"""
LLM-as-a-Judge Module

Wraps OpenAI structured outputs (Pydantic) to evaluate generated emails
against fact-coverage and tone-alignment criteria.
"""

import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field


# ── Structured Output Schemas ─────────────────────────────────────

class FactCoverageResult(BaseModel):
    """Schema returned by the judge when evaluating fact coverage."""
    present_facts: list[bool] = Field(
        description=(
            "List of booleans, true if the corresponding fact is present "
            "in the email, false otherwise. Must be exactly the same "
            "length as the input key_facts."
        )
    )


class ToneAlignmentResult(BaseModel):
    """Schema returned by the judge when evaluating tone alignment."""
    tone_score: float = Field(
        description=(
            "Score between 0.0 and 1.0 indicating how well the email "
            "matches the requested tone. 1.0 is perfect match, 0.0 is "
            "completely off."
        )
    )
    explanation: str = Field(
        description="Brief explanation of the score."
    )


# ── Judge Class ───────────────────────────────────────────────────

class LLMJudge:
    """Uses an LLM to judge the quality of generated emails."""

    def __init__(self, client: OpenAI) -> None:
        self.client = client
        self.model = os.getenv("MODEL_NAME", "gpt-4o-mini")

    def evaluate_fact_coverage(self, email: str, key_facts: list[str]) -> list[bool]:
        """
        Determine which key facts are present in the generated email.

        Args:
            email: The generated email text.
            key_facts: The facts that should appear in the email.

        Returns:
            A list of booleans aligned 1-to-1 with *key_facts*.
        """
        prompt = (
            "You are an evaluator. I will give you a generated email and "
            "a list of key facts that were SUPPOSED to be included.\n"
            "For each fact, determine if it is present in the email "
            "(True) or missing (False).\n\n"
            f"Generated Email:\n\"\"\"{email}\"\"\"\n\n"
            f"Key Facts:\n{json.dumps(key_facts, indent=2)}"
        )

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a strict grading assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format=FactCoverageResult,
            temperature=0.0,
        )
        result = response.choices[0].message.parsed.present_facts

        # Guard: LLM may return a different length list
        if len(result) < len(key_facts):
            result.extend([False] * (len(key_facts) - len(result)))
        return result[: len(key_facts)]

    def evaluate_tone_alignment(self, email: str, target_tone: str) -> float:
        """
        Score how well the email matches the requested tone.

        Args:
            email: The generated email text.
            target_tone: The tone the email should convey.

        Returns:
            A float between 0.0 and 1.0.
        """
        prompt = (
            f"Evaluate if the following email matches the requested tone: "
            f"'{target_tone}'.\n"
            "Provide a score from 0.0 to 1.0.\n"
            "0.0 = completely opposite or highly inappropriate tone.\n"
            "0.5 = neutral or mixed tone.\n"
            "1.0 = perfectly matches the requested tone.\n\n"
            f"Generated Email:\n\"\"\"{email}\"\"\""
        )

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict grading assistant evaluating tone.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=ToneAlignmentResult,
            temperature=0.0,
        )
        return response.choices[0].message.parsed.tone_score
