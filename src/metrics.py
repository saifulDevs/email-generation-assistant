"""
Custom Evaluation Metrics Module

Three metrics designed specifically for email generation evaluation:
  1. Fact Coverage Score  (FCS)  – LLM-as-a-Judge
  2. Tone Alignment Score (TAS)  – LLM-as-a-Judge
  3. Professional Email Structure Score (PESS) – Heuristic / Regex
"""

import re
from typing import List

from .llm_judge import LLMJudge


# ── Metric 1: Fact Coverage Score ─────────────────────────────────

def calculate_fcs(judge: LLMJudge, email: str, key_facts: List[str]) -> float:
    """
    Fact Coverage Score (FCS).

    Uses LLM-as-a-Judge to determine whether each required fact
    appears in the generated email.

    Returns:
        Normalised score between 0.0 and 1.0.
    """
    if not key_facts:
        return 1.0

    try:
        present_facts = judge.evaluate_fact_coverage(email, key_facts)
        matches = sum(1 for present in present_facts[: len(key_facts)] if present)
        return matches / len(key_facts)
    except Exception as e:
        print(f"[WARNING] Error calculating FCS: {e}")
        return 0.0


# ── Metric 2: Tone Alignment Score ────────────────────────────────

def calculate_tas(judge: LLMJudge, email: str, tone: str) -> float:
    """
    Tone Alignment Score (TAS).

    Uses LLM-as-a-Judge to rate how well the generated email matches
    the requested tone.

    Returns:
        Normalised score between 0.0 and 1.0.
    """
    try:
        return judge.evaluate_tone_alignment(email, tone)
    except Exception as e:
        print(f"[WARNING] Error calculating TAS: {e}")
        return 0.0


# ── Metric 3: Professional Email Structure Score ──────────────────

# Patterns compiled once at module level for performance
_GREETING_RE = re.compile(
    r"^(Hi|Dear|Hello|To Whom|Greetings|Good\s?morning|Good\s?afternoon"
    r"|Good\s?evening|Welcome|Team)\b",
    re.IGNORECASE,
)

_CLOSING_RE = re.compile(
    r"^(Best|Regards|Sincerely|Thanks|Thank\s?you|Warmly|Warm\s?regards"
    r"|Kind\s?regards|Cheers|Respectfully|With\s?appreciation"
    r"|Yours\s?truly|Cordially|All\s?the\s?best|Warmest)",
    re.IGNORECASE,
)


def calculate_pess(email: str) -> float:
    """
    Professional Email Structure Score (PESS).

    Checks for three structural components:
      1. **Greeting**  – e.g. "Dear ...", "Hi ..."
      2. **Body**      – substantive content between greeting and closing
      3. **Closing**   – e.g. "Best regards,", "Sincerely,"

    Returns:
        Normalised score:  0 | 0.333 | 0.667 | 1.0
    """
    lines = [line.strip() for line in email.split("\n") if line.strip()]

    # Skip subject line if present
    start_idx = 0
    if lines and lines[0].lower().startswith("subject:"):
        start_idx = 1

    content_lines = lines[start_idx:]
    if len(content_lines) < 3:
        return 0.0

    score = 0.0

    # 1. Greeting — check first 2 non-subject lines
    has_greeting = any(
        _GREETING_RE.search(line) or line.endswith(",")
        for line in content_lines[:2]
    )
    if has_greeting:
        score += 1.0 / 3.0

    # 2. Closing — check last 5 lines
    has_closing = any(
        _CLOSING_RE.search(line)
        for line in content_lines[-5:]
    )
    if has_closing:
        score += 1.0 / 3.0

    # 3. Body — at least 3 lines of content beyond greeting/closing
    if len(content_lines) >= 3:
        score += 1.0 / 3.0

    return min(1.0, score)
