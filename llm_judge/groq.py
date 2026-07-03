from __future__ import annotations

from typing import Any

from llm_judge.base import BaseJudgeProvider, ProviderResponse


class GroqJudgeProvider(BaseJudgeProvider):
    provider_name = "Groq"

    @property
    def endpoint(self) -> str:
        return "https://api.groq.com/openai/v1/chat/completions"

    def _generate(self, prompt: str) -> ProviderResponse:
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError("groq is not installed") from exc

        client = Groq(api_key=self.api_key, timeout=self.timeout_seconds)
        completion = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        text = completion.choices[0].message.content or ""
        if not text:
            raise ValueError("Groq returned an empty judge response")
        return ProviderResponse(text=text, tokens=extract_total_tokens(completion))


def extract_total_tokens(completion: Any) -> int | None:
    usage = getattr(completion, "usage", None)
    total = getattr(usage, "total_tokens", None)
    return total if isinstance(total, int) else None
