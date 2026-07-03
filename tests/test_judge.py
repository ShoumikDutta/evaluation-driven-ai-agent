import json

from evals.aggregator import aggregate_judge_results
from evals.judge import parse_judge_json


def valid_result(winner: str = "multi", confidence: float = 0.91) -> dict:
    return {
        "winner": winner,
        "confidence": confidence,
        "scores": {
            "single": {
                "accuracy": 4,
                "completeness": 4,
                "reasoning": 4,
                "instruction_following": 4,
                "hallucination": 4,
                "tool_use": 4,
                "overall": 4,
            },
            "multi": {
                "accuracy": 5,
                "completeness": 5,
                "reasoning": 5,
                "instruction_following": 5,
                "hallucination": 5,
                "tool_use": 5,
                "overall": 5,
            },
        },
        "summary": "The multi-agent response is more complete and better grounded.",
    }


def test_judge_output_parser_handles_valid_json():
    parsed = parse_judge_json(json.dumps(valid_result()))

    assert parsed["winner"] == "multi"
    assert parsed["scores"]["multi"]["overall"] == 5


def test_judge_output_parser_handles_top_level_jury_json():
    payload = {
        "winner": "multi",
        "confidence": 88,
        "single": {
            "overall": 8,
            "accuracy": 8,
            "reasoning": 7,
            "completeness": 8,
            "tool_use": 6,
            "hallucination": 9,
            "instruction_following": 9,
        },
        "multi": {
            "overall": 9,
            "accuracy": 9,
            "reasoning": 9,
            "completeness": 9,
            "tool_use": 10,
            "hallucination": 9,
            "instruction_following": 9,
        },
        "reasoning": "Multi-agent used more complete evidence gathering.",
    }

    parsed = parse_judge_json(json.dumps(payload))

    assert parsed["winner"] == "multi"
    assert parsed["confidence"] == 0.88
    assert parsed["scores"]["single"]["tool_use"] == 6


def test_judge_output_parser_normalizes_percent_confidence():
    payload = valid_result(confidence=94)

    parsed = parse_judge_json(json.dumps(payload))

    assert parsed["confidence"] == 0.94


def test_aggregator_uses_available_judges_and_reports_unavailable():
    results = [
        {"judge": "Qwen3", "status": "ok", **valid_result("multi", 0.94)},
        {"judge": "Llama3.1", "status": "ok", **valid_result("multi", 0.81)},
        {"judge": "Gemma3", "status": "ok", **valid_result("tie", 0.88)},
        {"judge": "Mistral", "status": "unavailable", "error": "connection refused"},
    ]

    aggregated = aggregate_judge_results(results)

    assert aggregated["winner"] == "multi"
    assert aggregated["majority_vote"] == {"single": 0, "multi": 2, "tie": 1}
    assert aggregated["judge_agreement_percent"] == 67
    assert aggregated["unavailable_judges"] == ["Mistral"]
