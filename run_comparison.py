from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from agents.context import clone_shared_context, prepare_shared_context
from agents.multi_agent import execute_multi_agent
from agents.schemas import response_to_dict
from agents.single_agent import execute_single_agent
from tools.tool_registry import build_tool_registry


def run_comparison(prompt: str, mode: str = "both", save_traces: bool = True) -> Dict[str, Any]:
    if mode not in {"single", "multi", "both"}:
        raise ValueError("mode must be one of: single, multi, both")

    shared_context = prepare_shared_context(prompt)
    registry = build_tool_registry()
    result: Dict[str, Any] = {"prompt": prompt, "mode": mode}

    if mode in {"single", "both"}:
        single = execute_single_agent(prompt, clone_shared_context(shared_context), registry, save_trace_file=save_traces)
        result["single"] = _public_run(single)

    if mode in {"multi", "both"}:
        multi = execute_multi_agent(prompt, clone_shared_context(shared_context), registry, save_trace_file=save_traces)
        result["multi"] = _public_run(multi)

    if mode == "both":
        result["comparison"] = compare_runs(result["single"], result["multi"])

    return result


def compare_runs(single: Dict[str, Any], multi: Dict[str, Any]) -> Dict[str, Any]:
    single_response = single["response"]
    multi_response = multi["response"]
    return {
        "status_match": single_response["status"] == multi_response["status"],
        "single_latency_ms": single["latency_ms"],
        "multi_latency_ms": multi["latency_ms"],
        "latency_delta_ms_multi_minus_single": round(multi["latency_ms"] - single["latency_ms"], 2),
        "single_tool_calls": single["tool_call_count"],
        "multi_tool_calls": multi["tool_call_count"],
        "single_tools": single_response["tools_used"],
        "multi_tools": multi_response["tools_used"],
        "human_approval_match": single_response["needs_human_approval"] == multi_response["needs_human_approval"],
        "issue_count_single": len(single_response["detected_issues"]),
        "issue_count_multi": len(multi_response["detected_issues"]),
    }


def _public_run(run: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "response": response_to_dict(run["response"]),
        "latency_ms": run["latency_ms"],
        "tool_call_count": run["tool_call_count"],
        "trace_path": run["trace_path"],
        "trace": run["trace"],
    }


def print_readable(result: Dict[str, Any]) -> None:
    for key in ["single", "multi"]:
        if key not in result:
            continue
        run = result[key]
        response = run["response"]
        print("\n" + key.upper())
        print("-" * len(key))
        print(f"Status: {response['status']}")
        print(f"Confidence: {response['confidence']}")
        print(f"Needs human approval: {response['needs_human_approval']}")
        print(f"Latency ms: {run['latency_ms']}")
        print(f"Tool calls: {run['tool_call_count']}")
        print(f"Tools: {', '.join(response['tools_used']) or '(none)'}")
        print(f"Trace: {run['trace_path']}")
        print(f"Answer: {response['answer']}")

    if "comparison" in result:
        print("\nCOMPARISON")
        print(json.dumps(result["comparison"], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run single-agent, multi-agent, or both on one CRM prompt.")
    parser.add_argument("--prompt", required=True, help="CRM data-quality prompt to run.")
    parser.add_argument("--mode", choices=["single", "multi", "both"], default="both")
    args = parser.parse_args()

    result = run_comparison(args.prompt, args.mode, save_traces=True)
    print_readable(result)


if __name__ == "__main__":
    main()
