from __future__ import annotations

import json
from typing import Any, Dict

from agents.agent_utils import (
    build_guardrail_response,
    build_human_loop_response,
    build_out_of_scope_response,
    build_response_from_results,
    classify_user_prompt,
    run_planned_tools,
    tool_plan_for_prompt,
)
from agents.context import clone_shared_context, prepare_shared_context
from agents.prompts import SINGLE_AGENT_ROLE
from agents.schemas import AgentResponse, response_to_dict, validate_agent_response
from agents.tracing import TraceBuilder, save_trace, trace_tool_names
from tools.guardrails import evaluate_prompt
from tools.tool_registry import ToolRegistry, build_tool_registry


def run_agent(
    user_prompt: str,
    shared_context: Dict[str, Any] | None = None,
    tool_registry: ToolRegistry | None = None,
) -> AgentResponse:
    """Return exactly the shared AgentResponse schema for the single-agent path."""
    return execute_single_agent(user_prompt, shared_context, tool_registry, save_trace_file=False)["response"]


def execute_single_agent(
    user_prompt: str,
    shared_context: Dict[str, Any] | None = None,
    tool_registry: ToolRegistry | None = None,
    save_trace_file: bool = True,
) -> Dict[str, Any]:
    context = clone_shared_context(shared_context) if shared_context else prepare_shared_context(user_prompt)
    registry = tool_registry or build_tool_registry()
    trace = TraceBuilder("single", user_prompt, context)
    trace.add_step("single_generalist", "start", user_prompt[:200], SINGLE_AGENT_ROLE)

    guardrail = evaluate_prompt(user_prompt)
    intent = classify_user_prompt(user_prompt, guardrail)
    trace.add_step("single_generalist", "classify", user_prompt[:200], f"intent={intent}; guardrails={guardrail.reasons}")

    if guardrail.blocked:
        response = build_guardrail_response(user_prompt, guardrail)
    elif intent == "human_loop":
        response = build_human_loop_response(user_prompt, guardrail)
    elif intent in {"empty", "out_of_scope"}:
        response = build_out_of_scope_response(user_prompt)
    else:
        plan = tool_plan_for_prompt(user_prompt, intent)
        trace.add_step("single_generalist", "plan_tools", ",".join(plan), f"{len(plan)} tools selected")
        results = run_planned_tools(user_prompt, intent, context, lambda name, **kwargs: trace.call_tool(registry, name, **kwargs), plan)
        response = build_response_from_results(
            user_prompt,
            intent,
            results,
            trace_tool_names({"tool_calls": trace.tool_calls}),
            architecture="single",
            requires_human_approval=guardrail.requires_human_approval,
        )

    validated = validate_agent_response(response)
    trace_record = trace.build(validated)
    trace_path = save_trace(trace_record) if save_trace_file else None
    return {
        "response": validated,
        "trace": trace_record.model_dump(mode="json"),
        "trace_path": str(trace_path) if trace_path else None,
        "latency_ms": trace_record.latency_ms,
        "tool_call_count": len(trace_record.tool_calls),
    }


def run_task(query: str) -> Dict[str, Any]:
    """Compatibility wrapper used by the older scripts."""
    run = execute_single_agent(query, save_trace_file=True)
    response_dict = response_to_dict(run["response"])
    response_dict.update(
        {
            "latency_ms": run["latency_ms"],
            "tool_calls": run["tool_call_count"],
            "trace_file": run["trace_path"],
            "trace": run["trace"]["agent_steps"],
            "tool_call_log": run["trace"]["tool_calls"],
        }
    )
    return response_dict


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Question/task for the single agent")
    args = parser.parse_args()
    print(json.dumps(run_task(" ".join(args.query)), indent=2))
