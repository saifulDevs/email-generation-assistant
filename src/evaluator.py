"""
Evaluator Module

Orchestrates the end-to-end evaluation pipeline:
  1. Load 10 test scenarios from data/test_cases.json
  2. Generate emails via Baseline and Advanced strategies
  3. Score each email using FCS, TAS, and PESS
  4. Save results to reports/evaluation_results.csv and .json
"""

import json
import os
import time
from typing import Any, Dict, List

import pandas as pd
from openai import OpenAI

from .email_generator import EmailGenerator
from .llm_judge import LLMJudge
from .metrics import calculate_fcs, calculate_tas, calculate_pess


class Evaluator:
    """Runs the full evaluation pipeline across both prompt strategies."""

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

    def __init__(
        self,
        data_path: str = "data/test_cases.json",
        output_dir: str = "reports/",
    ) -> None:
        self.data_path = data_path
        self.output_dir = output_dir

        base_url = os.getenv("OPENAI_BASE_URL")
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=base_url if base_url else None,
        )
        self.generator = EmailGenerator(client)
        self.judge = LLMJudge(client)

    def load_data(self) -> List[Dict[str, Any]]:
        """Load test scenarios from JSON."""
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _evaluate_single(
        self,
        strategy: str,
        intent: str,
        key_facts: list[str],
        tone: str,
    ) -> Dict[str, Any]:
        """
        Generate an email and evaluate it for a single strategy.

        Includes retry logic for transient API errors.
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                if strategy == "Baseline":
                    email = self.generator.generate_baseline(intent, key_facts, tone)
                else:
                    email = self.generator.generate_advanced(intent, key_facts, tone)

                fcs = calculate_fcs(self.judge, email, key_facts)
                tas = calculate_tas(self.judge, email, tone)
                pess = calculate_pess(email)
                overall = (fcs + tas + pess) / 3.0

                return {
                    "generated_email": email,
                    "fact_coverage_score": round(fcs, 3),
                    "tone_alignment_score": round(tas, 3),
                    "professional_structure_score": round(pess, 3),
                    "overall_score": round(overall, 3),
                }
            except Exception as e:
                print(
                    f"  [RETRY {attempt}/{self.MAX_RETRIES}] "
                    f"{strategy} failed: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    print(f"  [ERROR] Giving up on {strategy} after {self.MAX_RETRIES} retries.")
                    return {
                        "generated_email": f"[ERROR] {e}",
                        "fact_coverage_score": 0.0,
                        "tone_alignment_score": 0.0,
                        "professional_structure_score": 0.0,
                        "overall_score": 0.0,
                    }

    def run_evaluation(self) -> pd.DataFrame:
        """Execute the full evaluation across all scenarios and both strategies."""
        test_cases = self.load_data()
        results: list[dict] = []

        print(f"Starting evaluation of {len(test_cases)} scenarios...")

        for i, case in enumerate(test_cases, 1):
            scenario_id = case["scenario_id"]
            intent = case["intent"]
            key_facts = case["key_facts"]
            tone = case["tone"]

            print(f"[{i}/{len(test_cases)}] Processing {scenario_id}...")

            for strategy in ("Baseline", "Advanced"):
                scores = self._evaluate_single(strategy, intent, key_facts, tone)
                results.append(
                    {
                        "scenario_id": scenario_id,
                        "intent": intent,
                        "strategy": strategy,
                        **scores,
                    }
                )

        # ── Save outputs ──────────────────────────────────────────
        df = pd.DataFrame(results)
        os.makedirs(self.output_dir, exist_ok=True)

        csv_path = os.path.join(self.output_dir, "evaluation_results.csv")
        json_path = os.path.join(self.output_dir, "evaluation_results.json")

        csv_columns = [
            "scenario_id",
            "intent",
            "strategy",
            "fact_coverage_score",
            "tone_alignment_score",
            "professional_structure_score",
            "overall_score",
        ]
        df[csv_columns].to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")

        df.to_json(json_path, orient="records", indent=2)
        print(f"Full results saved to {json_path}")

        return df
