from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # pragma: no cover - requirements.txt installs python-dotenv.
    _load_dotenv = None

from llm_judge.base import (
    BaseJudgeProvider,
    JudgeProviderError,
    JudgeResult,
    ProviderStatus,
    describe_exception,
    provider_status_from_exception,
    quota_type_from_exception,
    retry_after_from_exception,
    status_code_from_exception,
)
from llm_judge.cerebras import CerebrasJudgeProvider
from llm_judge.gemini import GeminiJudgeProvider
from llm_judge.groq import GroqJudgeProvider


logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_CEREBRAS_MODEL = "gpt-oss-120b"
DEFAULT_TIMEOUT_SECONDS = 60

NO_PROVIDERS_WARNING = (
    "No LLM providers configured.\n\n"
    "Please configure at least one of:\n\n"
    "GEMINI_API_KEY\n"
    "GROQ_API_KEY\n"
    "CEREBRAS_API_KEY"
)


class NoProvidersConfiguredError(JudgeProviderError):
    pass


@dataclass(frozen=True)
class ProviderMetadata:
    provider: str
    model: str
    endpoint: str
    api_key_loaded: bool
    status: ProviderStatus


@dataclass(frozen=True)
class JudgeFailure:
    provider: str
    model: str
    status: ProviderStatus
    error: str
    latency_seconds: float | None = None
    endpoint: str = ""
    api_key_loaded: bool = False
    last_http_status: int | None = None
    last_error: str | None = None
    retries: int = 0
    retry_after: str | None = None
    quota_type: str | None = None


PanelResult = JudgeResult | JudgeFailure


class CloudLLMJudge:
    def __init__(self, providers: list[BaseJudgeProvider], missing_providers: list[JudgeFailure] | None = None) -> None:
        self.providers = providers
        self.missing_providers = missing_providers or []

    def score_all(
        self,
        prompt: str,
        response_a: str,
        response_b: str,
        rubric: dict[str, Any],
    ) -> list[PanelResult]:
        if not self.providers and not self.missing_providers:
            logger.warning(NO_PROVIDERS_WARNING.replace("\n", " "))
            raise NoProvidersConfiguredError(NO_PROVIDERS_WARNING)

        results: list[PanelResult] = list(self.missing_providers)
        for provider in self.providers:
            results.append(self._score_provider_with_retry(provider, prompt, response_a, response_b, rubric))
        logger.info("LLM judge panel completed with %s/%s available judges", count_successes(results), len(results))
        return results

    def score(
        self,
        prompt: str,
        response_a: str,
        response_b: str,
        rubric: dict[str, Any],
    ) -> list[PanelResult]:
        return self.score_all(prompt, response_a, response_b, rubric)

    def _score_provider_with_retry(
        self,
        provider: BaseJudgeProvider,
        prompt: str,
        response_a: str,
        response_b: str,
        rubric: dict[str, Any],
    ) -> PanelResult:
        logger.info("Running %s judge", provider.display_name)
        start = time.perf_counter()
        errors: list[str] = []
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                result = provider.score(prompt, response_a, response_b, rubric)
                result = replace(result, retries=attempt)
                logger.info(
                    "%s finished in %.2f sec; tokens=%s; winner=%s",
                    provider.display_name,
                    result.latency_seconds or 0.0,
                    result.tokens if result.tokens is not None else "n/a",
                    result.winner,
                )
                return result
            except Exception as exc:
                last_exc = exc
                status = status_code_from_exception(exc)
                provider_status = provider_status_from_exception(exc)
                errors.append(describe_exception(exc))
                if attempt == 0 and provider_status not in {"Authentication Failed", "Model Not Found", "Invalid Endpoint"}:
                    logger.warning(
                        "%s failed with status=%s%s; retrying once",
                        provider.display_name,
                        provider_status,
                        f" ({status})" if status is not None else "",
                    )
                    continue
                logger.warning(
                    "%s failed with status=%s%s: %s",
                    provider.display_name,
                    provider_status,
                    f" ({status})" if status is not None else "",
                    exc,
                )
                break

        final_status = provider_status_from_exception(last_exc) if last_exc is not None else "Unavailable"
        last_http_status = status_code_from_exception(last_exc) if last_exc is not None else None
        retry_after = retry_after_from_exception(last_exc) if last_exc is not None else None
        quota_type = quota_type_from_exception(last_exc) if last_exc is not None else None
        return JudgeFailure(
            provider=provider.display_name,
            model=provider.model,
            status=final_status,
            error=" | ".join(errors),
            latency_seconds=time.perf_counter() - start,
            endpoint=provider.endpoint,
            api_key_loaded=provider.api_key_loaded,
            last_http_status=last_http_status,
            last_error=errors[-1] if errors else None,
            retries=max(0, len(errors) - 1),
            retry_after=retry_after,
            quota_type=quota_type,
        )


def count_successes(results: list[PanelResult]) -> int:
    return sum(1 for result in results if isinstance(result, JudgeResult))


def create_default_judge() -> CloudLLMJudge:
    load_environment()
    providers, missing = configured_provider_slots()
    return CloudLLMJudge(providers, missing)


def configured_provider_metadata() -> list[ProviderMetadata]:
    load_environment()
    providers, missing = configured_provider_slots()
    configured = [
        ProviderMetadata(
            provider=provider.display_name,
            model=provider.model,
            endpoint=provider.endpoint,
            api_key_loaded=provider.api_key_loaded,
            status="Unavailable",
        )
        for provider in providers
    ]
    missing_metadata = [
        ProviderMetadata(
            provider=failure.provider,
            model=failure.model,
            endpoint=failure.endpoint,
            api_key_loaded=False,
            status=failure.status,
        )
        for failure in missing
    ]
    return configured + missing_metadata


def configured_providers() -> list[BaseJudgeProvider]:
    providers, _ = configured_provider_slots()
    return providers


def configured_provider_slots() -> tuple[list[BaseJudgeProvider], list[JudgeFailure]]:
    timeout_seconds = get_timeout_seconds()
    providers: list[BaseJudgeProvider] = []
    missing: list[JudgeFailure] = []

    gemini_key = env_value("GEMINI_API_KEY")
    gemini_model = env_value("GEMINI_MODEL", DEFAULT_GEMINI_MODEL) or DEFAULT_GEMINI_MODEL
    log_provider_startup("Gemini", gemini_key, gemini_model, "google-genai:models.generate_content")
    if gemini_key:
        providers.append(
            GeminiJudgeProvider(
                api_key=gemini_key,
                model=gemini_model,
                timeout_seconds=timeout_seconds,
            )
        )
    else:
        missing.append(configuration_missing_failure("Gemini", gemini_model, "google-genai:models.generate_content"))

    groq_key = env_value("GROQ_API_KEY")
    groq_model = env_value("GROQ_MODEL", DEFAULT_GROQ_MODEL) or DEFAULT_GROQ_MODEL
    log_provider_startup("Groq", groq_key, groq_model, "https://api.groq.com/openai/v1/chat/completions")
    if groq_key:
        providers.append(
            GroqJudgeProvider(
                api_key=groq_key,
                model=groq_model,
                timeout_seconds=timeout_seconds,
            )
        )
    else:
        missing.append(configuration_missing_failure("Groq", groq_model, "https://api.groq.com/openai/v1/chat/completions"))

    cerebras_key = env_value("CEREBRAS_API_KEY")
    cerebras_model = env_value("CEREBRAS_MODEL", DEFAULT_CEREBRAS_MODEL) or DEFAULT_CEREBRAS_MODEL
    log_provider_startup("Cerebras", cerebras_key, cerebras_model, "https://api.cerebras.ai/v1/chat/completions")
    logger.info("Loaded Cerebras key: %s", mask_secret(cerebras_key))
    if cerebras_key:
        providers.append(
            CerebrasJudgeProvider(
                api_key=cerebras_key,
                model=cerebras_model,
                timeout_seconds=timeout_seconds,
            )
        )
        logger.info(
            "Cerebras diagnostics: API Key Loaded=%s Model=%s Endpoint=%s",
            "Yes",
            cerebras_model,
            "https://api.cerebras.ai/v1/chat/completions",
        )
    else:
        missing.append(configuration_missing_failure("Cerebras", cerebras_model, "https://api.cerebras.ai/v1/chat/completions"))
        logger.info(
            "Cerebras diagnostics: API Key Loaded=%s Model=%s Endpoint=%s",
            "No",
            cerebras_model,
            "https://api.cerebras.ai/v1/chat/completions",
        )

    return providers, missing


def env_value(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip().strip('"').strip("'")


def mask_secret(secret: str) -> str:
    cleaned = secret.strip()
    if not cleaned:
        return "<missing>"
    if len(cleaned) <= 8:
        return f"{cleaned[:2]}..."
    return f"{cleaned[:8]}...{cleaned[-4:]}"


def log_provider_startup(provider: str, api_key: str, model: str, endpoint: str) -> None:
    logger.info(
        "%s startup health: API key detected=%s; Endpoint=%s; Model=%s; HTTP Status=%s; Raw error message=%s",
        provider,
        "Yes" if api_key else "No",
        endpoint,
        model,
        "Not checked at startup",
        "n/a",
    )


def configuration_missing_failure(provider: str, model: str, endpoint: str) -> JudgeFailure:
    return JudgeFailure(
        provider=provider,
        model=model,
        status="Configuration Missing",
        error=f"{provider} API key is not configured.",
        endpoint=endpoint,
        api_key_loaded=False,
        last_error=f"{provider} API key missing",
        retries=0,
    )


def get_timeout_seconds() -> int:
    try:
        return int(os.getenv("LLM_JUDGE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def load_environment() -> None:
    if _load_dotenv is not None:
        _load_dotenv(ROOT / ".env", override=False)
        return
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
