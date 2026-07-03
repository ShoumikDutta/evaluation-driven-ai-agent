from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://api.cerebras.ai/v1/chat/completions"
MODELS_ENDPOINT = "https://api.cerebras.ai/v1/models"
DEFAULT_MODEL = "gpt-oss-120b"


def main() -> None:
    load_environment()
    api_key = clean_value(os.getenv("CEREBRAS_API_KEY", ""))
    model = clean_value(os.getenv("CEREBRAS_MODEL", DEFAULT_MODEL)) or DEFAULT_MODEL

    print("Cerebras diagnostics")
    print(f"Implementation: OpenAI-compatible REST API")
    print(f"API key detected: {'Yes' if api_key else 'No'}")
    print(f"Loaded Cerebras key: {mask_secret(api_key)}")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Model: {model}")

    if not api_key:
        print("Error: CEREBRAS_API_KEY is missing.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    print("\nListing models")
    request("GET", MODELS_ENDPOINT, headers=headers)

    print("\nSimple chat request")
    request(
        "POST",
        ENDPOINT,
        headers=headers,
        json_body={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with JSON: {\"ok\": true}"}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
    )


def load_environment() -> None:
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
        os.environ.setdefault(key.strip(), clean_value(value))


def request(method: str, url: str, *, headers: dict[str, str], json_body: dict[str, Any] | None = None) -> None:
    try:
        response = requests.request(method, url, headers=headers, json=json_body, timeout=30)
        print(f"HTTP status: {response.status_code}")
        print_response_body(response)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"Exception type: {type(exc).__name__}")
        print(f"Exception: {exc}")
        response = getattr(exc, "response", None)
        if response is not None:
            print(f"Response status: {response.status_code}")
            print_response_body(response)


def print_response_body(response: requests.Response) -> None:
    text = response.text.strip()
    if not text:
        print("Response body: <empty>")
        return
    try:
        parsed = response.json()
    except ValueError:
        print(f"Response body: {text}")
        return
    print("Response body:")
    print(json.dumps(parsed, indent=2, ensure_ascii=True))


def clean_value(value: str) -> str:
    return str(value or "").strip().strip('"').strip("'")


def mask_secret(secret: str) -> str:
    cleaned = clean_value(secret)
    if not cleaned:
        return "<missing>"
    if len(cleaned) <= 8:
        return f"{cleaned[:2]}..."
    return f"{cleaned[:8]}...{cleaned[-4:]}"


if __name__ == "__main__":
    main()
