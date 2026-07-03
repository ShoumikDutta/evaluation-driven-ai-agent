from __future__ import annotations

from typing import Any

from llm_judge.base import BaseJudgeProvider, ProviderResponse


class GeminiJudgeProvider(BaseJudgeProvider):
    provider_name = "Gemini"

    @property
    def endpoint(self) -> str:
        return "google-genai:models.generate_content"

    def _generate(self, prompt: str) -> ProviderResponse:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed") from exc

        try:
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=self.timeout_seconds * 1000),
            )
        except TypeError:
            client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        )
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        text = getattr(response, "text", "") or ""
        if not text:
            raise ValueError("Gemini returned an empty judge response")
        return ProviderResponse(text=text, tokens=extract_total_tokens(response))


def extract_total_tokens(response: Any) -> int | None:
    usage = getattr(response, "usage_metadata", None)
    total = getattr(usage, "total_token_count", None)
    return total if isinstance(total, int) else None
