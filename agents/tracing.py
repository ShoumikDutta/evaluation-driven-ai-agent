from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agents.context import shared_context_summary
from agents.schemas import AgentResponse, AgentStepLog, ToolCallLog, TraceRecord, response_to_dict
from tools.crm_tools import sanitize_args, summarize_output
from tools.tool_registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = ROOT / "traces"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()))


class TraceBuilder:
    def __init__(self, mode: str, user_prompt: str, shared_context: Dict[str, Any]):
        self.mode = mode
        self.user_prompt = user_prompt
        self.shared_context = shared_context
        self.run_id = f"{mode}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.started = time.perf_counter()
        self.timestamp = utc_now()
        self.tool_calls: List[Dict[str, Any]] = []
        self.agent_steps: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def add_step(
        self,
        agent_name: str,
        step: str,
        input_summary: str = "",
        output_summary: str = "",
        success: bool = True,
    ) -> None:
        self.agent_steps.append(
            AgentStepLog(
                agent_name=agent_name,
                step=step,
                input_summary=input_summary,
                output_summary=output_summary,
                success=success,
                timestamp=utc_now(),
            ).model_dump(mode="json")
        )

    def call_tool(self, registry: ToolRegistry, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        started = time.perf_counter()
        success = True
        error = None
        output: Dict[str, Any] = {}
        try:
            output = registry.execute(tool_name, **kwargs)
        except Exception as exc:
            success = False
            error = str(exc)
            self.errors.append(f"{tool_name}: {error}")
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        self.tool_calls.append(
            ToolCallLog(
                tool_name=tool_name,
                input_args=sanitize_args(kwargs),
                output_summary=summarize_output(output) if success else "",
                success=success,
                timestamp=utc_now(),
                latency_ms=latency_ms,
                error=error,
            ).model_dump(mode="json")
        )
        if not success:
            raise RuntimeError(error or f"{tool_name} failed")
        return output

    def latency_ms(self) -> float:
        return round((time.perf_counter() - self.started) * 1000, 2)

    def build(self, response: AgentResponse) -> TraceRecord:
        output = response_to_dict(response)
        prompt_tokens = estimate_tokens(self.user_prompt)
        schema_tokens = estimate_tokens(json.dumps(self.shared_context.get("output_schema", {})))
        output_tokens = estimate_tokens(json.dumps(output))
        return TraceRecord(
            run_id=self.run_id,
            timestamp=self.timestamp,
            mode=self.mode,  # type: ignore[arg-type]
            user_prompt=self.user_prompt,
            shared_context_summary=shared_context_summary(self.shared_context),
            final_output=output,
            tool_calls=self.tool_calls,
            agent_steps=self.agent_steps,
            latency_ms=self.latency_ms(),
            token_usage_estimate={
                "input_tokens": prompt_tokens + schema_tokens,
                "output_tokens": output_tokens,
            },
            errors=self.errors,
        )


def save_trace(trace: TraceRecord) -> Path:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"{trace.run_id}.json"
    path.write_text(json.dumps(trace.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def trace_tool_names(trace: Dict[str, Any] | TraceRecord) -> List[str]:
    data = trace.model_dump(mode="json") if isinstance(trace, TraceRecord) else trace
    names: List[str] = []
    for call in data.get("tool_calls", []):
        if call.get("success") and call.get("tool_name"):
            names.append(call["tool_name"])
    return names
