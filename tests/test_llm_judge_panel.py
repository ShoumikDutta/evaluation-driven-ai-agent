from __future__ import annotations

from llm_judge.base import BaseJudgeProvider, JudgeResult, ProviderResponse, provider_status_from_exception
from llm_judge.cerebras import CerebrasHTTPError
from llm_judge.judge import CloudLLMJudge, JudgeFailure, configured_provider_metadata, env_value


class FailingProvider(BaseJudgeProvider):
    provider_name = "Gemini"

    def __init__(self) -> None:
        super().__init__(api_key="test", model="gemini-test")
        self.calls = 0

    def _generate(self, prompt: str) -> ProviderResponse:
        self.calls += 1
        raise RuntimeError("429 rate limit")


class PassingProvider(BaseJudgeProvider):
    provider_name = "Groq"

    def __init__(self) -> None:
        super().__init__(api_key="test", model="groq-test")
        self.calls = 0

    def _generate(self, prompt: str) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(
            text=(
                '{"winner":"multi","confidence":88,'
                '"single":{"overall":8,"accuracy":8,"reasoning":7,"completeness":8,'
                '"tool_use":6,"hallucination":9,"instruction_following":9},'
                '"multi":{"overall":9,"accuracy":9,"reasoning":9,"completeness":9,'
                '"tool_use":10,"hallucination":9,"instruction_following":9},'
                '"reasoning":"Multi is more complete."}'
            ),
            tokens=123,
        )


def test_cloud_judge_runs_all_providers_and_records_failures() -> None:
    failing = FailingProvider()
    passing = PassingProvider()
    judge = CloudLLMJudge([failing, passing])

    results = judge.score_all("prompt", "response a", "response b", {"overall": "quality"})

    assert failing.calls == 2
    assert passing.calls == 1
    assert len(results) == 2
    assert isinstance(results[0], JudgeFailure)
    assert isinstance(results[1], JudgeResult)
    assert results[1].provider == "Groq"
    assert results[1].model == "groq-test"
    assert results[1].winner == "multi"
    assert results[1].overall_score_multi == 9
    assert results[1].tokens == 123


def test_configured_provider_metadata_uses_cerebras(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")
    monkeypatch.setenv("GROQ_MODEL", "groq-test-model")
    monkeypatch.setenv("CEREBRAS_API_KEY", "cerebras-test-key")
    monkeypatch.setenv("CEREBRAS_MODEL", "cerebras-test-model")

    metadata = configured_provider_metadata()

    assert [provider.provider for provider in metadata] == ["Gemini", "Groq", "Cerebras"]
    assert [provider.model for provider in metadata] == [
        "gemini-test-model",
        "groq-test-model",
        "cerebras-test-model",
    ]
    assert metadata[2].endpoint == "https://api.cerebras.ai/v1/chat/completions"


def test_env_value_strips_quotes_and_whitespace(monkeypatch) -> None:
    monkeypatch.setenv("CEREBRAS_MODEL", ' "gpt-oss-120b" ')

    assert env_value("CEREBRAS_MODEL") == "gpt-oss-120b"


def test_cerebras_404_is_model_not_found() -> None:
    response = type("Response", (), {})()
    response.status_code = 404
    response.text = '{"error":{"message":"model not found"}}'
    response.headers = {}
    error = CerebrasHTTPError(
        response,
        model="llama-3.3-70b",
        endpoint="https://api.cerebras.ai/v1/chat/completions",
    )

    assert provider_status_from_exception(error) == "Model Not Found"
