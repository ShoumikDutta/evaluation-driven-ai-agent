from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - requirements.txt installs python-dotenv.
    load_dotenv = None


ROOT = Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if load_dotenv is not None:
        load_dotenv(env_path, override=False)
        return
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


JUDGE_MODELS = [
    "qwen3:8b",
    "llama3.1:8b",
    "gemma3:12b",
]

JUDGE_SCORE_KEYS = [
    "overall",
    "accuracy",
    "reasoning",
    "completeness",
    "tool_use",
    "hallucination",
    "instruction_following",
]

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 180
DEFAULT_MAX_JUDGE_WORKERS = 3


def get_judge_models() -> list[str]:
    configured = os.getenv("JUDGE_MODELS", "").strip()
    if configured:
        return [model.strip() for model in configured.split(",") if model.strip()]
    return list(JUDGE_MODELS)


def get_ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")


def get_ollama_timeout_seconds() -> int:
    return _int_env("OLLAMA_TIMEOUT_SECONDS", DEFAULT_OLLAMA_TIMEOUT_SECONDS)


def get_max_judge_workers() -> int:
    return max(1, _int_env("MAX_JUDGE_WORKERS", DEFAULT_MAX_JUDGE_WORKERS))


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
