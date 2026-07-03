from __future__ import annotations

import json
import logging

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - requirements.txt installs python-dotenv.
    def load_dotenv() -> bool:
        return False

from evals.prompt import JUDGE_RUBRIC
from llm_judge.base import JudgeResult
from llm_judge.judge import NO_PROVIDERS_WARNING, JudgeFailure, create_default_judge


def label_winner(winner: str) -> str:
    if winner == "single":
        return "Single Agent"
    if winner == "multi":
        return "Multi-Agent"
    return "Tie"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()
    judge = create_default_judge()
    if not judge.providers:
        print(NO_PROVIDERS_WARNING)
        return

    results = judge.score_all(
        prompt="Find duplicate CRM accounts and recommend safe next steps.",
        response_a=json.dumps(
            {
                "answer": "Found likely duplicate accounts and recommended a manual review before merging.",
                "status": "ok",
                "tools_used": ["find_duplicate_accounts"],
                "confidence": 0.88,
            },
            ensure_ascii=True,
        ),
        response_b=json.dumps(
            {
                "answer": "Found likely duplicates, grouped evidence by account, and flagged owner review before action.",
                "status": "ok",
                "tools_used": ["find_duplicate_accounts", "summarize_data_quality"],
                "confidence": 0.92,
            },
            ensure_ascii=True,
        ),
        rubric=JUDGE_RUBRIC,
    )

    for result in results:
        if isinstance(result, JudgeFailure):
            print(f"Provider:\n{result.provider}\n")
            print(f"Model:\n{result.model}\n")
            print(f"Status:\n{result.status}\n")
            print(f"Error:\n{result.error}\n")
            continue

        assert isinstance(result, JudgeResult)
        winning_score = (
            result.overall_score_single
            if result.winner == "single"
            else result.overall_score_multi
            if result.winner == "multi"
            else max(result.overall_score_single, result.overall_score_multi)
        )
        print(f"Provider:\n{result.provider}\n")
        print(f"Model:\n{result.model}\n")
        print(f"Winner:\n{label_winner(result.winner)}\n")
        print(f"Score:\n{winning_score:.1f}\n")
        print(f"Reasoning:\n{result.reasoning}\n")


if __name__ == "__main__":
    main()
