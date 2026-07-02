from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from agents.prompts import SHARED_RULEBOOK_SUMMARY
from agents.schemas import AgentResponse
from tools.crm_tools import load_crm_data, shared_rulebook, summarize_records
from tools.tool_registry import build_tool_registry


def prepare_shared_context(user_prompt: str) -> Dict[str, Any]:
    data = load_crm_data()
    records = data["records"]
    rulebook = shared_rulebook()
    registry = build_tool_registry()
    record_summary = summarize_records(records)
    return {
        "user_prompt": user_prompt,
        "records": deepcopy(records),
        "record_count": data["record_count"],
        "columns": data["columns"],
        "record_summary": record_summary,
        "rulebook": rulebook,
        "system_rules": SHARED_RULEBOOK_SUMMARY,
        "tool_registry": registry.describe(),
        "output_schema": AgentResponse.model_json_schema(),
    }


def clone_shared_context(shared_context: Dict[str, Any]) -> Dict[str, Any]:
    return deepcopy(shared_context)


def shared_context_summary(shared_context: Dict[str, Any]) -> str:
    summary = shared_context.get("record_summary", {})
    stage_count = len(summary.get("stages", {}))
    country_count = len(summary.get("countries", {}))
    tool_count = len(shared_context.get("tool_registry", []))
    return (
        f"{summary.get('record_count', shared_context.get('record_count', 0))} CRM records, "
        f"{stage_count} stage values, {country_count} countries, {tool_count} registered tools, "
        "shared read-only rulebook, shared AgentResponse schema."
    )
