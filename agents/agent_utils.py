from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any, Callable, Dict, Iterable, List, Tuple

from agents.schemas import AgentResponse, DetectedIssue
from tools.guardrails import GuardrailDecision

ToolCaller = Callable[[str, Dict[str, Any]], Dict[str, Any]]


DATA_QUALITY_TERMS = [
    "quality",
    "issue",
    "missing",
    "invalid",
    "duplicate",
    "audit",
    "stale",
    "past close",
    "close date",
    "high severity",
    "owner accountability",
    "phone",
    "email format",
    "contact",
]

PIPELINE_TERMS = ["pipeline", "stage", "owner", "country", "value", "deal", "opportunity", "exposure"]
MANAGER_TERMS = ["summary", "manager", "executive", "brief", "report", "draft email", "sales ops"]
SPECIFIC_DATA_QUALITY_TERMS = [
    "missing",
    "invalid",
    "duplicate",
    "stale",
    "past close",
    "owner accountability",
    "phone",
    "email format",
]
CRM_TERMS = DATA_QUALITY_TERMS + PIPELINE_TERMS + MANAGER_TERMS + ["crm", "account", "records", "customer"]


def classify_user_prompt(prompt: str, guardrail: GuardrailDecision | None = None) -> str:
    q = (prompt or "").lower().strip()
    if not q:
        return "empty"
    if guardrail and guardrail.blocked:
        return "blocked_action"
    if guardrail and guardrail.requires_human_approval and any(word in q for word in ["export", "send", "update", "write"]):
        if not any(term in q for term in DATA_QUALITY_TERMS + PIPELINE_TERMS + MANAGER_TERMS):
            return "human_loop"
    if "related to" in q or "find records" in q or "record related" in q:
        return "record_lookup"
    if any(term in q for term in SPECIFIC_DATA_QUALITY_TERMS):
        return "data_quality"
    if any(term in q for term in MANAGER_TERMS):
        return "manager_summary"
    if any(term in q for term in DATA_QUALITY_TERMS):
        return "data_quality"
    if any(term in q for term in PIPELINE_TERMS):
        return "pipeline"
    if any(term in q for term in CRM_TERMS):
        return "general_crm"
    return "out_of_scope"


def tool_plan_for_prompt(prompt: str, intent: str) -> List[str]:
    q = (prompt or "").lower()
    if intent in {"empty", "blocked_action", "out_of_scope", "human_loop"}:
        return []
    if intent == "record_lookup":
        return ["load_crm_data", "find_records"]
    if intent == "pipeline":
        return ["load_crm_data", "check_pipeline_anomalies"]
    if intent == "manager_summary":
        return ["load_crm_data", "generate_audit_summary"]

    tools = ["load_crm_data"]
    if intent in {"data_quality", "general_crm"}:
        broad = any(term in q for term in ["top", "overall", "audit", "quality", "summary", "high severity", "risk"])
        if broad:
            tools.append("generate_audit_summary")
        if any(term in q for term in ["missing", "owner", "phone", "email", "close date", "contact"]):
            tools.append("check_missing_values")
        if "duplicate" in q:
            tools.append("check_duplicate_records")
        if any(term in q for term in ["date", "past close", "close date"]):
            tools.append("check_invalid_dates")
        if any(term in q for term in ["activity", "stale", "pipeline", "stage", "exposure", "recent"]):
            tools.append("check_pipeline_anomalies")
        if len(tools) == 1:
            tools.append("generate_audit_summary")
    return unique_preserve_order(tools)


def run_planned_tools(
    prompt: str,
    intent: str,
    shared_context: Dict[str, Any],
    call_tool: Callable[..., Dict[str, Any]],
    plan: List[str] | None = None,
) -> Dict[str, Any]:
    selected = plan or tool_plan_for_prompt(prompt, intent)
    results: Dict[str, Any] = {}
    records = shared_context.get("records", [])
    for tool_name in selected:
        if tool_name == "load_crm_data":
            payload = call_tool("load_crm_data", shared_context=shared_context)
            records = payload["records"]
            results[tool_name] = payload
        elif tool_name == "find_records":
            results[tool_name] = call_tool("find_records", query=prompt, records=records)
        else:
            results[tool_name] = call_tool(tool_name, records=records)
    return results


def build_guardrail_response(prompt: str, guardrail: GuardrailDecision, tools_used: List[str] | None = None) -> AgentResponse:
    reasons = ", ".join(guardrail.reasons) or "guardrail"
    answer = (
        "I cannot perform that request in this read-only CRM data-quality system. "
        "I can help with a draft summary, audit findings, or recommended actions for a human reviewer."
    )
    return AgentResponse(
        answer=answer,
        status="cannot_answer",
        detected_issues=[
            DetectedIssue(
                issue_type="blocked_or_unsafe_request",
                severity="high",
                affected_records=None,
                evidence=f"Blocked reason: {reasons}. No CRM data was changed, exported, or sent.",
            )
        ],
        recommended_actions=[
            "Rephrase the request as a read-only CRM audit or draft recommendation.",
            "Get human approval before any send, update, or export action.",
        ],
        tools_used=tools_used or [],
        confidence=0.98,
        needs_human_approval=guardrail.requires_human_approval,
        reasoning_summary="The prompt matched a blocked safety rule, so no operational action was taken.",
    )


def build_human_loop_response(prompt: str, guardrail: GuardrailDecision, tools_used: List[str] | None = None) -> AgentResponse:
    return AgentResponse(
        answer=(
            "Human approval is required before I create an export, send email, or update CRM records. "
            "No external action was performed. I can continue with a read-only audit or draft after approval."
        ),
        status="needs_human_review",
        detected_issues=[],
        recommended_actions=[
            "Ask the CRM data owner to approve the requested external action.",
            "Keep any output as a draft until approval is recorded.",
        ],
        tools_used=tools_used or [],
        confidence=0.95,
        needs_human_approval=True,
        reasoning_summary="The request asks for an action that is allowed only after human approval.",
    )


def build_out_of_scope_response(prompt: str, tools_used: List[str] | None = None) -> AgentResponse:
    if not prompt.strip():
        answer = "Please enter a CRM data-quality or pipeline question."
        summary = "The request was empty, so there was no CRM task to run."
    else:
        answer = "I can only answer CRM data-quality, pipeline, or draft-summary questions for this capstone dataset."
        summary = "The request did not match the CRM data-quality scope."
    return AgentResponse(
        answer=answer,
        status="cannot_answer",
        detected_issues=[],
        recommended_actions=["Ask about CRM data quality, pipeline exposure, duplicates, missing fields, or a manager draft."],
        tools_used=tools_used or [],
        confidence=0.9,
        needs_human_approval=False,
        reasoning_summary=summary,
    )


def build_response_from_results(
    prompt: str,
    intent: str,
    results: Dict[str, Any],
    tools_used: List[str],
    architecture: str,
    requires_human_approval: bool = False,
    critic_flags: List[str] | None = None,
) -> AgentResponse:
    critic_flags = critic_flags or []
    status = "needs_human_review" if requires_human_approval or critic_flags else "ok"
    confidence = 0.86 if architecture == "single" else 0.9
    if critic_flags:
        confidence = min(confidence, 0.72)

    if intent in {"data_quality", "general_crm"}:
        issues = filter_issues_for_prompt(collect_issues(results), prompt)
        detected = aggregate_detected_issues(issues)
        answer = data_quality_answer(results, issues, detected)
        actions = default_actions(detected, requires_human_approval)
        reasoning = "The assistant used deterministic CRM quality checks and summarized user-facing evidence."
    elif intent == "pipeline":
        pipeline = get_pipeline(results)
        issues = filter_issues_for_prompt(collect_issues(results), prompt)
        detected = aggregate_detected_issues(issues)
        answer = pipeline_answer(pipeline, detected)
        actions = [
            "Review countries, owners, or stages with the largest open exposure.",
            "Investigate stale high-value opportunities before taking operational action.",
        ]
        reasoning = "The assistant used the shared pipeline tool and surfaced exposure plus data-quality risks."
    elif intent == "manager_summary":
        audit = results.get("generate_audit_summary", {})
        issues = collect_issues(results)
        detected = aggregate_detected_issues(issues)
        answer = manager_answer(audit, detected, requires_human_approval)
        actions = default_actions(detected, requires_human_approval)
        reasoning = "The assistant turned the shared audit output into a concise manager-facing draft."
    elif intent == "record_lookup":
        lookup = results.get("find_records", {})
        detected = []
        answer = lookup_answer(lookup)
        actions = ["Use matching records only as evidence; do not update CRM records without owner review."]
        reasoning = "The assistant used text retrieval over the shared CRM dataset."
    else:
        return build_out_of_scope_response(prompt, tools_used)

    if requires_human_approval and "Human approval is required" not in answer:
        answer += " Human approval is required before sending, exporting, or updating anything outside this draft."

    if critic_flags:
        actions.append("Resolve critic findings before relying on the result: " + ", ".join(critic_flags))

    return AgentResponse(
        answer=answer,
        status=status,
        detected_issues=detected,
        recommended_actions=unique_preserve_order(actions),
        tools_used=unique_preserve_order(tools_used),
        confidence=confidence,
        needs_human_approval=requires_human_approval,
        reasoning_summary=reasoning,
    )


def collect_issues(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    seen = set()
    for result in results.values():
        if not isinstance(result, dict):
            continue
        for issue in result.get("issues", []):
            key = (issue.get("record_id"), issue.get("issue_type"), issue.get("field"))
            if key not in seen:
                issues.append(issue)
                seen.add(key)
    return issues


def filter_issues_for_prompt(issues: List[Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
    q = prompt.lower()
    requested: set[str] = set()
    if "duplicate" in q:
        requested.add("duplicate_account")
    if "invalid email" in q or "email format" in q:
        requested.add("invalid_email")
    if "missing owner" in q or "owner accountability" in q:
        requested.add("missing_owner")
    if "missing phone" in q or "phone" in q:
        requested.add("missing_phone")
    if "missing close" in q or "close date" in q:
        requested.update({"missing_close_date", "past_close_date_open_opp"})
    if "past close" in q:
        requested.add("past_close_date_open_opp")
    if any(term in q for term in ["activity", "stale", "recent"]):
        requested.update({"missing_last_activity_high_value", "stale_activity_high_value", "stale_activity_low_value"})
    if "stage" in q:
        requested.add("invalid_stage")

    if not requested:
        return issues
    filtered = [issue for issue in issues if issue.get("issue_type") in requested]
    return filtered or issues


def aggregate_detected_issues(issues: List[Dict[str, Any]]) -> List[DetectedIssue]:
    grouped: "OrderedDict[Tuple[str, str], Dict[str, Any]]" = OrderedDict()
    for issue in issues:
        issue_type = str(issue.get("issue_type", "unknown"))
        severity = str(issue.get("severity", "medium"))
        if severity not in {"low", "medium", "high"}:
            severity = "medium"
        key = (issue_type, severity)
        group = grouped.setdefault(key, {"records": [], "accounts": [], "details": []})
        record_id = issue.get("record_id")
        account = issue.get("account_name")
        detail = issue.get("detail")
        if record_id and record_id not in group["records"]:
            group["records"].append(record_id)
        if account and account not in group["accounts"]:
            group["accounts"].append(account)
        if detail and detail not in group["details"]:
            group["details"].append(detail)

    detected: List[DetectedIssue] = []
    for (issue_type, severity), group in grouped.items():
        records = group["records"]
        accounts = group["accounts"][:3]
        evidence_bits = []
        if records:
            evidence_bits.append("Records: " + ", ".join(records[:12]))
        if accounts:
            evidence_bits.append("Examples: " + ", ".join(accounts))
        if group["details"]:
            evidence_bits.append(group["details"][0])
        detected.append(
            DetectedIssue(
                issue_type=issue_type,
                severity=severity,  # type: ignore[arg-type]
                affected_records=len(records) if records else None,
                evidence=" | ".join(evidence_bits) or "Issue identified by deterministic CRM checks.",
            )
        )
    return detected


def data_quality_answer(results: Dict[str, Any], issues: List[Dict[str, Any]], detected: List[DetectedIssue]) -> str:
    audit = results.get("generate_audit_summary", {})
    records_checked = audit.get("records_checked") or first_value(results, "records_checked") or 0
    total = audit.get("total_issues") if audit else len(issues)
    if not issues:
        return f"I checked {records_checked} CRM records and found no matching data-quality issues. No CRM changes were made."
    severity = count_detected_severity(detected)
    issue_preview = "; ".join(f"{item.issue_type}: {item.affected_records or 0}" for item in detected[:5])
    evidence_preview = " ".join(item.evidence for item in detected[:3]).rstrip(". ")
    return (
        f"I checked {records_checked} CRM records and found {len(issues)} matching issue rows "
        f"({total} total audit issues when a full audit was run). "
        f"Severity by category: high={severity.get('high', 0)}, medium={severity.get('medium', 0)}, low={severity.get('low', 0)}. "
        f"Top issue categories: {issue_preview}. Evidence: {evidence_preview}. No CRM changes were made."
    )


def pipeline_answer(pipeline: Dict[str, Any], detected: List[DetectedIssue]) -> str:
    if not pipeline:
        return "I could not calculate pipeline exposure from the shared CRM context."
    country = pipeline.get("by_country_eur", {})
    top_countries = sorted(country.items(), key=lambda item: item[1], reverse=True)[:3]
    top_country_text = "; ".join(f"{name}: EUR {value:,.0f}" for name, value in top_countries)
    top_open = pipeline.get("highest_value_open", [])[:3]
    top_open_text = "; ".join(
        f"{row.get('record_id')} {row.get('account_name')} EUR {float(row.get('amount_eur', 0)):,.0f}" for row in top_open
    )
    risk_text = f" I also found {len(detected)} data-quality risk categories related to pipeline follow-up." if detected else ""
    return (
        f"Open pipeline is EUR {pipeline.get('open_pipeline_eur', 0):,.0f}. "
        f"Largest country exposure: {top_country_text}. Highest-value open opportunities: {top_open_text}.{risk_text} "
        "No CRM changes were made."
    )


def manager_answer(audit: Dict[str, Any], detected: List[DetectedIssue], requires_human_approval: bool) -> str:
    if not audit:
        return "I could not create the manager draft because the audit summary tool did not return data."
    severity = audit.get("severity_counts", {})
    approval = " Human approval is required before sending or exporting this draft." if requires_human_approval else ""
    return (
        f"Manager draft: the CRM audit checked {audit.get('records_checked')} records and found "
        f"{audit.get('total_issues')} issues: high={severity.get('high', 0)}, "
        f"medium={severity.get('medium', 0)}, low={severity.get('low', 0)}. "
        f"Open pipeline is EUR {audit.get('pipeline', {}).get('open_pipeline_eur', 0):,.0f}. "
        f"Priority issue categories include {', '.join(item.issue_type for item in detected[:4]) or 'none'}. "
        f"No CRM changes were made.{approval}"
    )


def lookup_answer(lookup: Dict[str, Any]) -> str:
    matches = lookup.get("records", [])
    if not matches:
        return "I found no CRM records matching that request in the shared dataset. No CRM changes were made."
    preview = "; ".join(f"{row.get('record_id')} {row.get('account_name')}" for row in matches[:5])
    return f"I found {lookup.get('count', len(matches))} possibly relevant CRM records: {preview}. No CRM changes were made."


def default_actions(detected: List[DetectedIssue], requires_human_approval: bool) -> List[str]:
    actions = [
        "Review high-severity issue categories first.",
        "Assign CRM data owners to verify corrections before any update.",
        "Keep this output as a draft recommendation.",
    ]
    if requires_human_approval:
        actions.append("Obtain human approval before sending, exporting, or updating any CRM system.")
    if any(issue.issue_type == "duplicate_account" for issue in detected):
        actions.append("Merge or mark duplicates only after account-owner review.")
    return actions


def get_pipeline(results: Dict[str, Any]) -> Dict[str, Any]:
    if "check_pipeline_anomalies" in results:
        return results["check_pipeline_anomalies"].get("pipeline", {})
    if "generate_audit_summary" in results:
        return results["generate_audit_summary"].get("pipeline", {})
    return {}


def first_value(results: Dict[str, Any], key: str) -> Any:
    for result in results.values():
        if isinstance(result, dict) and key in result:
            return result[key]
    return None


def count_detected_severity(detected: List[DetectedIssue]) -> Dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for issue in detected:
        counts[issue.severity] += 1
    return counts


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def json_preview(value: Any, limit: int = 300) -> str:
    try:
        text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    except TypeError:
        text = str(value)
    return text[:limit]
