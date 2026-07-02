from __future__ import annotations

import json
from typing import Any, Dict, List

from agents.agent_utils import (
    build_guardrail_response,
    build_human_loop_response,
    build_out_of_scope_response,
    build_response_from_results,
    classify_user_prompt,
    tool_plan_for_prompt,
)
from agents.context import clone_shared_context, prepare_shared_context
from agents.prompts import MULTI_AGENT_ROLES
from agents.schemas import AgentResponse, response_to_dict, validate_agent_response
from agents.tracing import TraceBuilder, save_trace, trace_tool_names
from tools.guardrails import evaluate_prompt, forbidden_action_triggered
from tools.tool_registry import ToolRegistry, build_tool_registry


class RouterOrchestratorAgent:
    name = "router_orchestrator"

    def route(self, prompt: str, guardrail: Any, trace: TraceBuilder) -> Dict[str, Any]:
        intent = classify_user_prompt(prompt, guardrail)
        plan = tool_plan_for_prompt(prompt, intent)
        specialists: List[str] = []
        if any(tool in plan for tool in ["check_missing_values", "check_duplicate_records", "check_invalid_dates", "check_pipeline_anomalies"]):
            specialists.append("data_quality_specialist")
        if "generate_audit_summary" in plan or intent in {"manager_summary", "pipeline"}:
            specialists.append("business_summary_specialist")
        if "find_records" in plan:
            specialists.append("data_quality_specialist")
        specialists.append("critic")
        trace.add_step(self.name, "route", prompt[:200], f"intent={intent}; plan={plan}; specialists={specialists}")
        return {"intent": intent, "plan": plan, "specialists": specialists}


class DataQualitySpecialist:
    name = "data_quality_specialist"

    def run(
        self,
        prompt: str,
        records: List[Dict[str, Any]],
        tools: List[str],
        registry: ToolRegistry,
        trace: TraceBuilder,
    ) -> Dict[str, Any]:
        trace.add_step(self.name, "start", ",".join(tools), MULTI_AGENT_ROLES["data_quality_specialist"])
        results: Dict[str, Any] = {}
        for tool_name in tools:
            if tool_name == "find_records":
                results[tool_name] = trace.call_tool(registry, tool_name, query=prompt, records=records)
            else:
                results[tool_name] = trace.call_tool(registry, tool_name, records=records)
        trace.add_step(self.name, "finish", ",".join(results), f"{len(results)} tool outputs")
        return results


class BusinessSummarySpecialist:
    name = "business_summary_specialist"

    def run(
        self,
        records: List[Dict[str, Any]],
        tools: List[str],
        registry: ToolRegistry,
        trace: TraceBuilder,
    ) -> Dict[str, Any]:
        trace.add_step(self.name, "start", ",".join(tools), MULTI_AGENT_ROLES["business_summary_specialist"])
        results: Dict[str, Any] = {}
        for tool_name in tools:
            results[tool_name] = trace.call_tool(registry, tool_name, records=records)
        trace.add_step(self.name, "finish", ",".join(results), f"{len(results)} tool outputs")
        return results


class ToolVerificationCriticAgent:
    name = "critic"

    def check(self, response: AgentResponse, expected_plan: List[str], trace: TraceBuilder) -> List[str]:
        flags: List[str] = []
        used = set(response.tools_used)
        missing = [tool for tool in expected_plan if tool not in used]
        if missing:
            flags.append("missing_expected_tool:" + ",".join(missing))
        if forbidden_action_triggered(response.answer):
            flags.append("read_only_violation_risk")
        if response.status == "ok" and not response.answer.strip():
            flags.append("empty_answer")
        trace.add_step(self.name, "verify", ",".join(expected_plan), f"flags={flags}")
        return flags


def run_agent(
    user_prompt: str,
    shared_context: Dict[str, Any] | None = None,
    tool_registry: ToolRegistry | None = None,
) -> AgentResponse:
    """Return exactly the shared AgentResponse schema for the multi-agent path."""
    return execute_multi_agent(user_prompt, shared_context, tool_registry, save_trace_file=False)["response"]


def execute_multi_agent(
    user_prompt: str,
    shared_context: Dict[str, Any] | None = None,
    tool_registry: ToolRegistry | None = None,
    save_trace_file: bool = True,
) -> Dict[str, Any]:
    context = clone_shared_context(shared_context) if shared_context else prepare_shared_context(user_prompt)
    registry = tool_registry or build_tool_registry()
    trace = TraceBuilder("multi", user_prompt, context)
    trace.add_step("system", "start", user_prompt[:200], "multi-agent orchestrator-worker comparison path")

    guardrail = evaluate_prompt(user_prompt)
    router = RouterOrchestratorAgent()
    data_quality = DataQualitySpecialist()
    business_summary = BusinessSummarySpecialist()
    critic = ToolVerificationCriticAgent()
    route = router.route(user_prompt, guardrail, trace)
    intent = route["intent"]
    plan: List[str] = route["plan"]

    if guardrail.blocked:
        response = build_guardrail_response(user_prompt, guardrail)
    elif intent == "human_loop":
        response = build_human_loop_response(user_prompt, guardrail)
    elif intent in {"empty", "out_of_scope"}:
        response = build_out_of_scope_response(user_prompt)
    else:
        records_payload = trace.call_tool(registry, "load_crm_data", shared_context=context)
        records = records_payload["records"]
        results: Dict[str, Any] = {"load_crm_data": records_payload}

        remaining = [tool for tool in plan if tool != "load_crm_data"]
        dq_tools = [
            tool
            for tool in remaining
            if tool
            in {
                "check_missing_values",
                "check_duplicate_records",
                "check_invalid_dates",
                "check_pipeline_anomalies",
                "find_records",
            }
        ]
        bs_tools = [tool for tool in remaining if tool == "generate_audit_summary"]

        # Max three internal specialist rounds: route, specialists, critic.
        if dq_tools:
            results.update(data_quality.run(user_prompt, records, dq_tools, registry, trace))
        if bs_tools:
            results.update(business_summary.run(records, bs_tools, registry, trace))

        preliminary = build_response_from_results(
            user_prompt,
            intent,
            results,
            trace_tool_names({"tool_calls": trace.tool_calls}),
            architecture="multi",
            requires_human_approval=guardrail.requires_human_approval,
        )
        flags = critic.check(preliminary, plan, trace)
        response = build_response_from_results(
            user_prompt,
            intent,
            results,
            trace_tool_names({"tool_calls": trace.tool_calls}),
            architecture="multi",
            requires_human_approval=guardrail.requires_human_approval,
            critic_flags=flags,
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
    run = execute_multi_agent(query, save_trace_file=True)
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
    parser.add_argument("query", nargs="+", help="Question/task for the multi-agent system")
    args = parser.parse_args()
    print(json.dumps(run_task(" ".join(args.query)), indent=2))
