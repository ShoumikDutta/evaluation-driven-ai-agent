from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

import requests


logger = logging.getLogger(__name__)

Winner = Literal["single", "multi", "tie"]
ProviderStatus = Literal[
    "Healthy",
    "Quota Exceeded",
    "Rate Limited",
    "Authentication Failed",
    "Configuration Missing",
    "Model Not Found",
    "Invalid Endpoint",
    "Connection Timeout",
    "Network Error",
    "Unavailable",
]

RUBRIC_SCORE_KEYS = [
    "overall",
    "accuracy",
    "reasoning",
    "completeness",
    "tool_use",
    "hallucination",
    "instruction_following",
]


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    tokens: int | None = None
    http_status: int | None = None


@dataclass(frozen=True)
class JudgeResult:
    provider: str
    model: str
    winner: Winner
    confidence: float
    overall_score_single: float
    overall_score_multi: float
    accuracy_single: float
    accuracy_multi: float
    reasoning_single: float
    reasoning_multi: float
    tool_use_single: float
    tool_use_multi: float
    hallucination_single: float
    hallucination_multi: float
    instruction_following_single: float
    instruction_following_multi: float
    completeness_single: float
    completeness_multi: float
    reasoning: str
    rubric_scores: dict[str, dict[str, float]]
    latency_seconds: float | None = None
    tokens: int | None = None
    status: ProviderStatus = "Healthy"
    endpoint: str = ""
    api_key_loaded: bool = True
    last_http_status: int | None = None
    last_error: str | None = None
    retries: int = 0
    retry_after: str | None = None
    quota_type: str | None = None
    raw_json: dict[str, Any] | None = None
    raw_text: str | None = None

    @property
    def scores(self) -> dict[str, dict[str, float]]:
        return self.rubric_scores


class JudgeProviderError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class JudgeResponseError(JudgeProviderError):
    pass


class BaseJudgeProvider(ABC):
    provider_name: str

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 60) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def display_name(self) -> str:
        return self.provider_name

    @property
    def endpoint(self) -> str:
        return ""

    @property
    def api_key_loaded(self) -> bool:
        return bool(self.api_key.strip())

    def score(
        self,
        prompt: str,
        response_a: str,
        response_b: str,
        rubric: dict[str, Any],
    ) -> JudgeResult:
        judge_prompt = build_judge_prompt(
            prompt,
            response_a,
            response_b,
            rubric,
            provider=self.display_name,
            model=self.model,
        )
        start = time.perf_counter()
        raw = self._generate(judge_prompt)
        latency = time.perf_counter() - start
        parsed = parse_judge_response(raw.text)
        scores = parsed["scores"]
        result = JudgeResult(
            provider=self.display_name,
            model=self.model,
            winner=parsed["winner"],
            confidence=parsed["confidence"],
            overall_score_single=scores["single"]["overall"],
            overall_score_multi=scores["multi"]["overall"],
            accuracy_single=scores["single"]["accuracy"],
            accuracy_multi=scores["multi"]["accuracy"],
            reasoning_single=scores["single"]["reasoning"],
            reasoning_multi=scores["multi"]["reasoning"],
            tool_use_single=scores["single"]["tool_use"],
            tool_use_multi=scores["multi"]["tool_use"],
            hallucination_single=scores["single"]["hallucination"],
            hallucination_multi=scores["multi"]["hallucination"],
            instruction_following_single=scores["single"]["instruction_following"],
            instruction_following_multi=scores["multi"]["instruction_following"],
            completeness_single=scores["single"]["completeness"],
            completeness_multi=scores["multi"]["completeness"],
            reasoning=parsed["reasoning"],
            rubric_scores=scores,
            latency_seconds=latency,
            tokens=raw.tokens,
            endpoint=self.endpoint,
            api_key_loaded=self.api_key_loaded,
            last_http_status=raw.http_status,
            raw_json=parsed["raw_json"],
            raw_text=raw.text,
        )
        token_label = raw.tokens if raw.tokens is not None else "n/a"
        logger.info(
            "%s completed in %.2f sec with model %s; tokens=%s",
            self.display_name,
            latency,
            self.model,
            token_label,
        )
        return result

    @abstractmethod
    def _generate(self, prompt: str) -> ProviderResponse:
        raise NotImplementedError


def build_judge_prompt(
    prompt: str,
    response_a: str,
    response_b: str,
    rubric: dict[str, Any],
    provider: str = "",
    model: str = "",
) -> str:
    payload = {
        "original_prompt": prompt,
        "single_agent_response": response_a,
        "multi_agent_response": response_b,
        "rubric": rubric,
        "required_output_schema": {
            "provider": provider,
            "model": model,
            "winner": "single | multi | tie",
            "confidence": 88,
            "single": {key: 8 for key in RUBRIC_SCORE_KEYS},
            "multi": {key: 9 for key in RUBRIC_SCORE_KEYS},
            "reasoning": "brief evidence-based explanation",
        },
    }
    return (
        "You are an impartial LLM-as-a-Judge for an academic CRM data-quality agent evaluation.\n"
        "Compare the Single Agent and Multi-Agent outputs using the same rubric for both systems.\n"
        "Judge only the visible outputs and provided case context. Do not prefer a system because of its architecture name.\n"
        "Score each category from 1 to 10, where 10 is best. For hallucination, 10 means the response is highly grounded and low risk.\n"
        "Rubric categories: Overall, Accuracy, Reasoning, Completeness, Tool Use, Hallucination, Instruction Following.\n"
        "Choose winner as exactly one of: single, multi, tie.\n"
        "Confidence must be a number from 0 to 100 indicating confidence in the winner.\n"
        "Return ONLY valid JSON with exactly these top-level keys: provider, model, winner, confidence, single, multi, reasoning.\n"
        "Do not include Markdown, code fences, or extra text.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=True)
    )


def parse_judge_response(text: str) -> dict[str, Any]:
    cleaned = strip_json_markdown(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise JudgeResponseError(f"Judge returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise JudgeResponseError("Judge response JSON must be an object")

    winner = normalize_winner(data.get("winner"))
    confidence = parse_confidence(data.get("confidence"))
    single_scores = parse_system_scores(get_system_payload(data, "single"), "single")
    multi_scores = parse_system_scores(get_system_payload(data, "multi"), "multi")
    reasoning = str(data.get("reasoning") or data.get("summary") or "").strip()
    if not reasoning:
        raise JudgeResponseError("Judge response is missing reasoning")

    return {
        "winner": winner,
        "confidence": confidence,
        "scores": {"single": single_scores, "multi": multi_scores},
        "reasoning": reasoning,
        "raw_json": data,
    }


def get_system_payload(data: dict[str, Any], system: Literal["single", "multi"]) -> Any:
    if system in data:
        return data[system]
    scores = data.get("scores", {})
    if isinstance(scores, dict) and system in scores:
        return scores[system]
    raise JudgeResponseError(f"Judge response is missing {system} scores")


def parse_system_scores(value: Any, system: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise JudgeResponseError(f"Judge response {system} scores must be an object")
    return {key: parse_score(value.get(key), f"{system}.{key}") for key in RUBRIC_SCORE_KEYS}


def normalize_winner(value: Any) -> Winner:
    text = str(value or "").strip().lower().replace("_", " ")
    if text in {"single", "single agent", "a", "response a"}:
        return "single"
    if text in {"multi", "multi agent", "multi-agent", "b", "response b"}:
        return "multi"
    if text in {"tie", "draw", "equal"}:
        return "tie"
    raise JudgeResponseError("Judge response winner must be single, multi, or tie")


def parse_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise JudgeResponseError("Judge response confidence must be numeric") from exc
    if 1 < confidence <= 100:
        confidence /= 100
    if not 0 <= confidence <= 1:
        raise JudgeResponseError("Judge response confidence must be between 0 and 100")
    return round(confidence, 4)


def parse_score(value: Any, field_name: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise JudgeResponseError(f"Judge response {field_name} must be numeric") from exc
    if not 1 <= score <= 10:
        raise JudgeResponseError(f"Judge response {field_name} must be between 1 and 10")
    return score


def strip_json_markdown(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return cleaned


def status_code_from_exception(exc: Exception) -> int | None:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code
    text = str(exc).lower()
    for candidate in [400, 401, 403, 404, 408, 429, 500, 502, 503, 504]:
        if str(candidate) in text:
            return candidate
    return None


def retry_after_from_exception(exc: Exception) -> str | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) or {}
    if not headers:
        headers = getattr(exc, "response_headers", {}) or {}
    retry_after = headers.get("Retry-After") if hasattr(headers, "get") else None
    return str(retry_after) if retry_after else None


def quota_type_from_exception(exc: Exception) -> str | None:
    text = str(exc)
    lowered = text.lower()
    if "resource_exhausted" in lowered:
        return "RESOURCE_EXHAUSTED"
    if "quota" in lowered:
        return "Quota"
    if "rate limit" in lowered or "too many requests" in lowered:
        return "Rate Limit"
    return None


def provider_status_from_exception(exc: Exception) -> ProviderStatus:
    status = status_code_from_exception(exc)
    text = str(exc).lower()
    if status == 429 or "resource_exhausted" in text or "quota" in text or "rate limit" in text:
        return "Rate Limited"
    if status in {401, 403} or "unauthorized" in text or "invalid api key" in text:
        return "Authentication Failed"
    if status == 404 and ("model" in text or "not found" in text):
        return "Model Not Found"
    if status == 404:
        return "Invalid Endpoint"
    if isinstance(exc, requests.exceptions.Timeout) or "timed out" in text or "timeout" in text:
        return "Connection Timeout"
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return "Network Error"
    if "invalid endpoint" in text:
        return "Invalid Endpoint"
    if "connection" in text:
        return "Network Error"
    return "Unavailable"


def describe_exception(exc: Exception) -> str:
    status = status_code_from_exception(exc)
    response_body = response_body_from_exception(exc)
    body_text = f" Response body: {response_body}" if response_body else ""
    if status is not None:
        return f"{type(exc).__name__} ({status}): {exc}{body_text}"
    return f"{type(exc).__name__}: {exc}{body_text}"


def response_body_from_exception(exc: Exception) -> str | None:
    body = getattr(exc, "response_body", None)
    if not body:
        response = getattr(exc, "response", None)
        body = getattr(response, "text", None)
    if not body:
        return None
    text = str(body).strip()
    if not text:
        return None
    return text[:1000]
