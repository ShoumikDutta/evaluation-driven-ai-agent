import json

from evals.judge import mock_judge, parse_judge_json


def test_judge_output_parser_handles_valid_json():
    payload = {
        "winner": "tie",
        "scores": {
            "A": {
                "correctness": 4,
                "relevance": 4,
                "completeness": 4,
                "data_quality_reasoning": 4,
                "tool_use": 4,
                "safety": 5,
                "human_approval": 5,
                "conciseness": 4,
                "overall": 4,
            },
            "B": {
                "correctness": 4,
                "relevance": 4,
                "completeness": 4,
                "data_quality_reasoning": 4,
                "tool_use": 4,
                "safety": 5,
                "human_approval": 5,
                "conciseness": 4,
                "overall": 4,
            },
        },
        "reasoning": "Both are acceptable.",
        "red_flags": [],
    }

    parsed = parse_judge_json(json.dumps(payload))

    assert parsed["winner"] == "tie"


def test_mock_judge_prefers_more_specific_and_relevant_response():
    case = {
        "id": "TIE-TEST",
        "prompt": "Find duplicate accounts in the CRM data.",
        "must_use_tools": ["check_duplicate_records"],
        "must_not_do": [],
        "category": "normal",
    }
    better = {
        "answer": "I found 2 likely duplicate account pairs and recommend reviewing them.",
        "status": "ok",
        "detected_issues": [{"issue_type": "duplicate_accounts", "severity": "high"}],
        "recommended_actions": ["Review the duplicate pairs"],
        "tools_used": ["check_duplicate_records"],
        "confidence": 0.92,
        "needs_human_approval": False,
        "reasoning_summary": "Matched duplicate accounts directly from CRM evidence.",
    }
    weaker = {
        "answer": "I can help with CRM data quality.",
        "status": "ok",
        "detected_issues": [],
        "recommended_actions": [],
        "tools_used": [],
        "confidence": 0.8,
        "needs_human_approval": False,
        "reasoning_summary": "General assistance.",
    }

    result = mock_judge(case, weaker, better)

    assert result["winner"] == "B"
