from __future__ import annotations

import json
from typing import Any


JUDGE_RUBRIC = {
    "overall": "Overall quality for a CRM data-quality assistant response.",
    "accuracy": "Does the response correctly answer the user's CRM request using the provided evidence?",
    "reasoning": "Does it explain the decision clearly without exposing hidden chain-of-thought?",
    "completeness": "Does it cover the important requested issue categories, evidence, and next steps?",
    "tool_use": "Does it use required deterministic tools and avoid unnecessary or forbidden tools?",
    "hallucination": "Does it stay grounded? Score 10 for low hallucination risk and 1 for high hallucination risk.",
    "instruction_following": "Does it follow the task, schema, safety, and human-approval instructions?",
}

STRICT_JSON_SCHEMA = {
    "winner": "single | multi | tie",
    "confidence": 0.0,
    "scores": {
        "single": {
            "overall": 1,
            "accuracy": 1,
            "reasoning": 1,
            "completeness": 1,
            "tool_use": 1,
            "hallucination": 1,
            "instruction_following": 1,
        },
        "multi": {
            "overall": 1,
            "accuracy": 1,
            "reasoning": 1,
            "completeness": 1,
            "tool_use": 1,
            "hallucination": 1,
            "instruction_following": 1,
        },
    },
    "summary": "brief explanation without hidden chain-of-thought",
}


def build_evaluation_prompt(
    original_prompt: str,
    single_agent_response: dict[str, Any],
    multi_agent_response: dict[str, Any],
    case: dict[str, Any] | None = None,
) -> str:
    case = case or {}
    payload = {
        "original_prompt": original_prompt,
        "case_context": {
            "expected_behavior": case.get("expected_behavior", ""),
            "must_use_tools": case.get("must_use_tools", []),
            "must_not_do": case.get("must_not_do", []),
            "reference_notes": case.get("reference_notes", ""),
        },
        "single_agent_response": single_agent_response,
        "multi_agent_response": multi_agent_response,
        "rubric": JUDGE_RUBRIC,
        "required_output_schema": STRICT_JSON_SCHEMA,
    }
    return (
        "You are an impartial LLM-as-a-Judge for a university capstone comparing two CRM assistants.\n"
        "Evaluate the single-agent response and multi-agent response independently.\n"
        "Do not prefer a response because it is longer or because of the architecture name.\n"
        "Use scores from 1 to 10, where 10 is best. For hallucination, 10 means low hallucination risk.\n"
        "Confidence must be a number from 0 to 100.\n"
        "Return ONLY valid JSON. Do not wrap it in Markdown. Do not include any extra text.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=True)
    )
