from __future__ import annotations

import logging
from collections import Counter
from statistics import mean
from typing import Any

from evals.config import JUDGE_SCORE_KEYS


logger = logging.getLogger(__name__)

WINNERS = {"single", "multi", "tie"}
SUCCESS_STATUSES = {"ok", "Healthy"}


def aggregate_judge_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    available = [result for result in results if result.get("status") in SUCCESS_STATUSES and result.get("winner") in WINNERS]
    unavailable = [result for result in results if result.get("status") not in SUCCESS_STATUSES]

    if not available:
        aggregation = {
            "winner": "unavailable",
            "majority_vote": {"single": 0, "multi": 0, "tie": 0},
            "majority_count": 0,
            "majority_total": len(results),
            "majority_text": f"0 / {len(results)}",
            "average_confidence": 0.0,
            "average_scores": empty_average_scores(),
            "judge_agreement": 0.0,
            "judge_agreement_percent": 0,
            "available_judges": 0,
            "unavailable_judges": [result.get("judge", "unknown") for result in unavailable],
            "total_judges": len(results),
        }
        logger.info("Aggregation complete: no available judges")
        return aggregation

    vote_counts = Counter(result["winner"] for result in available)
    majority_count = max(vote_counts.values())
    leaders = sorted(winner for winner, count in vote_counts.items() if count == majority_count)
    winner = leaders[0] if len(leaders) == 1 else "tie"

    aggregation = {
        "winner": winner,
        "majority_vote": {label: vote_counts.get(label, 0) for label in ["single", "multi", "tie"]},
        "majority_count": majority_count,
        "majority_total": len(available),
        "majority_text": f"{majority_count} / {len(available)}",
        "average_confidence": round(mean(float(result.get("confidence", 0.0)) for result in available), 4),
        "average_scores": average_scores(available),
        "judge_agreement": round(majority_count / len(available), 4),
        "judge_agreement_percent": round((majority_count / len(available)) * 100),
        "available_judges": len(available),
        "unavailable_judges": [result.get("judge", "unknown") for result in unavailable],
        "total_judges": len(results),
    }
    logger.info(
        "Aggregation complete: winner=%s agreement=%s%% available=%s/%s",
        winner,
        aggregation["judge_agreement_percent"],
        aggregation["available_judges"],
        aggregation["total_judges"],
    )
    return aggregation


def average_scores(results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    averaged: dict[str, dict[str, float]] = {"single": {}, "multi": {}}
    for system in ["single", "multi"]:
        for key in JUDGE_SCORE_KEYS:
            values = [
                float(result.get("scores", {}).get(system, {}).get(key, 0))
                for result in results
                if key in result.get("scores", {}).get(system, {})
            ]
            averaged[system][key] = round(mean(values), 2) if values else 0.0
    return averaged


def empty_average_scores() -> dict[str, dict[str, float]]:
    return {system: {key: 0.0 for key in JUDGE_SCORE_KEYS} for system in ["single", "multi"]}
