from __future__ import annotations

from typing import Any

import requests

from llm_judge.base import BaseJudgeProvider, JudgeProviderError, ProviderResponse


CEREBRAS_CHAT_COMPLETIONS_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_PUBLIC_MODEL_IDS = ("gpt-oss-120b", "gemma-4-31b", "zai-glm-4.7")


class CerebrasHTTPError(JudgeProviderError):
    def __init__(self, response: requests.Response, *, model: str, endpoint: str) -> None:
        self.response = response
        self.response_body = response.text
        detail = classify_cerebras_error(response.status_code, response.text, model=model, endpoint=endpoint)
        super().__init__(detail, status_code=response.status_code)


class CerebrasJudgeProvider(BaseJudgeProvider):
    provider_name = "Cerebras"

    @property
    def endpoint(self) -> str:
        return CEREBRAS_CHAT_COMPLETIONS_URL

    def _generate(self, prompt: str) -> ProviderResponse:
        response = requests.post(
            CEREBRAS_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise CerebrasHTTPError(response, model=self.model, endpoint=CEREBRAS_CHAT_COMPLETIONS_URL)
        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("Cerebras returned no choices")
        text = choices[0].get("message", {}).get("content", "") or ""
        if not text:
            raise ValueError("Cerebras returned an empty judge response")
        return ProviderResponse(text=text, tokens=extract_total_tokens(payload), http_status=response.status_code)


def extract_total_tokens(payload: dict[str, Any]) -> int | None:
    total = payload.get("usage", {}).get("total_tokens")
    return total if isinstance(total, int) else None


def classify_cerebras_error(status_code: int, body: str, *, model: str, endpoint: str) -> str:
    lowered = (body or "").lower()
    if status_code in {401, 403}:
        return f"Authentication Failed for Cerebras. HTTP {status_code}"
    if status_code == 404:
        known_models = ", ".join(CEREBRAS_PUBLIC_MODEL_IDS)
        if model not in CEREBRAS_PUBLIC_MODEL_IDS:
            return (
                f"Model Not Found for Cerebras model '{model}'. "
                f"Known public models: {known_models}. HTTP 404"
            )
        return f"Invalid Endpoint for Cerebras endpoint '{endpoint}'. HTTP 404"
    if status_code == 429 or "rate" in lowered or "quota" in lowered:
        return f"Rate Limited by Cerebras. HTTP {status_code}"
    if status_code >= 500:
        return f"Cerebras service unavailable. HTTP {status_code}"
    return f"Cerebras API error. HTTP {status_code}"
