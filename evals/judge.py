from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from evals.aggregator import aggregate_judge_results
from evals.config import JUDGE_SCORE_KEYS
from evals.prompt import JUDGE_RUBRIC
from llm_judge.base import JudgeResult as CloudJudgeResult
from llm_judge.base import parse_judge_response
from llm_judge.judge import (
    NO_PROVIDERS_WARNING,
    CloudLLMJudge,
    JudgeFailure,
    PanelResult,
    ProviderMetadata,
    configured_provider_metadata,
    create_default_judge,
)


Winner = Literal["single", "multi", "tie"]


class SystemScores(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accuracy: float = Field(ge=1, le=10)
    completeness: float = Field(ge=1, le=10)
    reasoning: float = Field(ge=1, le=10)
    instruction_following: float = Field(ge=1, le=10)
    hallucination: float = Field(ge=1, le=10)
    tool_use: float = Field(ge=1, le=10)
    overall: float = Field(ge=1, le=10)


class JudgeScores(BaseModel):
    model_config = ConfigDict(extra="ignore")

    single: SystemScores
    multi: SystemScores


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    winner: Winner
    confidence: float = Field(ge=0, le=1)
    scores: JudgeScores
    summary: str = Field(min_length=1)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_percent_confidence(cls, value: Any) -> Any:
        if isinstance(value, (int, float)) and 1 < float(value) <= 100:
            return float(value) / 100
        return value


def judge_pairwise(
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
) -> dict[str, Any]:
    return judge_responses(
        case_id=case["id"],
        prompt=case.get("prompt", ""),
        single_response=single_response,
        multi_response=multi_response,
        case_context=case,
    )


def judge_responses(
    case_id: str,
    prompt: str,
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
    case_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    case = {
        "id": case_id,
        "prompt": prompt,
        "expected_behavior": "",
        "must_use_tools": [],
        "must_not_do": [],
        "reference_notes": "",
    }
    if case_context:
        case.update(case_context)

    panel = create_default_judge()
    panel_results = run_judge_panel(case, single_response, multi_response, panel)
    aggregation = aggregate_judge_results(panel_results)

    return {
        "case_id": case_id,
        "judge_mode": judge_mode(),
        "judge_panel": [f"{provider.display_name}:{provider.model}" for provider in panel.providers],
        "panel_results": panel_results,
        "aggregation": aggregation,
        "winner_system": aggregation["winner"],
    }


def run_judge_panel(
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
    panel: CloudLLMJudge,
) -> list[dict[str, Any]]:
    results = panel.score_all(
        prompt=case.get("prompt", ""),
        response_a=stable_json(single_response),
        response_b=stable_json(multi_response),
        rubric=build_case_rubric(case),
    )
    return [panel_result_to_eval_result(result, case, single_response, multi_response) for result in results]


def judge_once(
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
    judge: CloudLLMJudge | None = None,
) -> dict[str, Any]:
    panel = judge or create_default_judge()
    results = run_judge_panel(case, single_response, multi_response, panel)
    return results[0] if results else no_provider_result(case, single_response, multi_response)


def configured_judges() -> list[ProviderMetadata]:
    return configured_provider_metadata()


def judge_mode() -> str:
    return "llm_jury" if any(provider.api_key_loaded for provider in configured_judges()) else "no_llm_providers"


def parse_judge_json(text: str) -> dict[str, Any]:
    parsed = parse_judge_response(text)
    result = {
        "winner": parsed["winner"],
        "confidence": parsed["confidence"],
        "scores": parsed["scores"],
        "summary": parsed["reasoning"],
    }
    return JudgeResult.model_validate(result).model_dump(mode="json")


def stable_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)


def build_case_rubric(case: dict[str, Any] | None = None) -> dict[str, Any]:
    case = case or {}
    return {
        "categories": list(JUDGE_SCORE_KEYS),
        "criteria": JUDGE_RUBRIC,
        "scale": "1-10, where 10 is best. For hallucination, 10 means low hallucination risk.",
        "case_context": {
            "expected_behavior": case.get("expected_behavior", ""),
            "must_use_tools": case.get("must_use_tools", []),
            "must_not_do": case.get("must_not_do", []),
            "reference_notes": case.get("reference_notes", ""),
        },
    }


def panel_result_to_eval_result(
    result: PanelResult,
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(result, JudgeFailure):
        return unavailable_result(
            judge=result.provider,
            model=result.model,
            status=result.status,
            error=result.error,
            latency_seconds=result.latency_seconds,
            endpoint=result.endpoint,
            api_key_loaded=result.api_key_loaded,
            last_http_status=result.last_http_status,
            last_error=result.last_error,
            retries=result.retries,
            retry_after=result.retry_after,
            quota_type=result.quota_type,
            case=case,
            single_response=single_response,
            multi_response=multi_response,
        )
    return cloud_result_to_eval_result(result, case, single_response, multi_response)


def cloud_result_to_eval_result(
    result: CloudJudgeResult,
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
) -> dict[str, Any]:
    scores = result.scores
    output = {
        "judge": result.provider,
        "model": result.model,
        "provider": result.provider.lower(),
        "status": result.status,
        "winner_system": result.winner,
        "winner": result.winner,
        "confidence": result.confidence,
        "scores": scores,
        "rubric_scores": scores,
        "summary": result.reasoning,
        "reasoning": result.reasoning,
        "overall_score_single": result.overall_score_single,
        "overall_score_multi": result.overall_score_multi,
        "accuracy_single": result.accuracy_single,
        "accuracy_multi": result.accuracy_multi,
        "reasoning_single": result.reasoning_single,
        "reasoning_multi": result.reasoning_multi,
        "tool_use_single": result.tool_use_single,
        "tool_use_multi": result.tool_use_multi,
        "hallucination_single": result.hallucination_single,
        "hallucination_multi": result.hallucination_multi,
        "instruction_following_single": result.instruction_following_single,
        "instruction_following_multi": result.instruction_following_multi,
        "completeness_single": result.completeness_single,
        "completeness_multi": result.completeness_multi,
        "latency_seconds": result.latency_seconds,
        "tokens": result.tokens,
        "endpoint": result.endpoint,
        "api_key_loaded": result.api_key_loaded,
        "last_http_status": result.last_http_status,
        "last_error": result.last_error,
        "retries": result.retries,
        "retry_after": result.retry_after,
        "quota_type": result.quota_type,
        "raw_json": result.raw_json,
        "raw_text": result.raw_text,
    }
    output.update(judge_input_context(case, single_response, multi_response))
    return output


def unavailable_result(
    judge: str,
    model: str,
    status: str,
    error: str,
    latency_seconds: float | None,
    endpoint: str,
    api_key_loaded: bool,
    last_http_status: int | None,
    last_error: str | None,
    retries: int,
    retry_after: str | None,
    quota_type: str | None,
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
) -> dict[str, Any]:
    output = {
        "judge": judge,
        "model": model,
        "provider": judge.lower(),
        "status": status,
        "winner_system": "unavailable",
        "winner": "unavailable",
        "confidence": 0.0,
        "latency_seconds": latency_seconds,
        "tokens": None,
        "error": error,
        "endpoint": endpoint,
        "api_key_loaded": api_key_loaded,
        "last_http_status": last_http_status,
        "last_error": last_error,
        "retries": retries,
        "retry_after": retry_after,
        "quota_type": quota_type,
    }
    output.update(judge_input_context(case, single_response, multi_response))
    return output


def no_provider_result(
    case: dict[str, Any] | None = None,
    single_response: dict[str, Any] | None = None,
    multi_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return unavailable_result(
        judge="LLM Judge",
        model="not configured",
        status="Configuration Missing",
        error=NO_PROVIDERS_WARNING,
        latency_seconds=None,
        endpoint="",
        api_key_loaded=False,
        last_http_status=None,
        last_error=NO_PROVIDERS_WARNING,
        retries=0,
        retry_after=None,
        quota_type=None,
        case=case or {},
        single_response=single_response or {},
        multi_response=multi_response or {},
    )


def judge_input_context(
    case: dict[str, Any],
    single_response: dict[str, Any],
    multi_response: dict[str, Any],
) -> dict[str, Any]:
    return {
        "input_prompt": case.get("prompt", ""),
        "case_context": {
            "expected_behavior": case.get("expected_behavior", ""),
            "must_use_tools": case.get("must_use_tools", []),
            "must_not_do": case.get("must_not_do", []),
            "reference_notes": case.get("reference_notes", ""),
        },
        "single_response": single_response,
        "multi_response": multi_response,
    }


def provider_metadata() -> list[ProviderMetadata]:
    return configured_provider_metadata()
