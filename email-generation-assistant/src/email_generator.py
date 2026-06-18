"""
Email Generator Module

Uses the OpenAI SDK to generate professional emails using two strategies:
  - Baseline: Simple instruction-only prompting
  - Advanced: Role Prompting + Few-Shot Examples + Structured Rules
"""

import os
from openai import OpenAI


class EmailGenerator:
    """Generates professional emails using configurable prompt strategies."""

    def __init__(self, client: OpenAI) -> None:
        self.client = client
        self.baseline_prompt = self._load_prompt("prompts/baseline_prompt.txt")
        self.advanced_prompt = self._load_prompt("prompts/advanced_prompt.txt")
        self.model = os.getenv("MODEL_NAME", "gpt-4o-mini")

    @staticmethod
    def _load_prompt(path: str) -> str:
        """Load a prompt template from disk."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _call_llm(self, prompt: str, system_message: str | None = None) -> str:
        """
        Internal helper – sends a prompt to the LLM and returns the response text.

        Args:
            prompt: The user-facing prompt (with variables already substituted).
            system_message: Optional system-role instruction for role prompting.

        Returns:
            The raw text content of the model's response.
        """
        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content

    @staticmethod
    def _format_facts(key_facts: list[str]) -> str:
        """Format a list of facts into a bulleted string."""
        return "\n".join(f"- {fact}" for fact in key_facts)

    # ── Public API ────────────────────────────────────────────────

    def generate_baseline(self, intent: str, key_facts: list[str], tone: str) -> str:
        """Generate an email using the *Baseline* (simple instruction) strategy."""
        facts_str = self._format_facts(key_facts)
        prompt = self.baseline_prompt.format(
            intent=intent, key_facts=facts_str, tone=tone
        )
        return self._call_llm(prompt)

    def generate_advanced(self, intent: str, key_facts: list[str], tone: str) -> str:
        """Generate an email using the *Advanced* (role + few-shot + rules) strategy."""
        facts_str = self._format_facts(key_facts)
        prompt = self.advanced_prompt.format(
            intent=intent, key_facts=facts_str, tone=tone
        )
        system_message = (
            "You are an expert executive communications assistant. "
            "You specialize in crafting professional, well-structured business emails."
        )
        return self._call_llm(prompt, system_message=system_message)
