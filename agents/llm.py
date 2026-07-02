from __future__ import annotations

import json
import os
from typing import Any, Dict

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


def ollama_generate(prompt: str, model: str | None = None, timeout: int = 60) -> str | None:
    """Optional local LLM call. Returns None if Ollama is unavailable."""
    if requests is None:
        return None
    model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        r = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response")
    except Exception:
        return None


def maybe_polish(answer: str, context: Dict[str, Any]) -> str:
    """Polish the deterministic answer with Ollama if available; otherwise keep deterministic text."""
    if os.getenv("USE_OLLAMA", "0") != "1":
        return answer
    prompt = (
        "Rewrite this CRM audit answer for a manager. Do not change numbers or facts. "
        "Keep it under 120 words.\n\n"
        f"ANSWER:\n{answer}\n\nCONTEXT JSON:\n{json.dumps(context, indent=2)[:4000]}"
    )
    polished = ollama_generate(prompt)
    return polished.strip() if polished else answer
