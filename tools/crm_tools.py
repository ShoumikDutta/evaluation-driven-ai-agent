from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Dict, Iterable, List

from agents.tools import (
    OPEN_STAGES,
    TODAY,
    data_quality_audit,
    draft_manager_summary,
    find_records,
    load_crm_records,
    load_rulebook,
    parse_date,
    pipeline_summary,
)

VALID_STAGES = {"Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"}


def _copy_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [dict(row) for row in records]


def _records_from_context(shared_context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    if shared_context and shared_context.get("records") is not None:
        return _copy_records(shared_context["records"])
    return load_crm_records()


def load_crm_data(shared_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    records = _records_from_context(shared_context)
    columns = list(records[0].keys()) if records else []
    return {
        "tool": "load_crm_data",
        "records": records,
        "record_count": len(records),
        "columns": columns,
    }


def check_missing_values(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit = data_quality_audit(_copy_records(records))
    issue_types = {
        "missing_owner",
        "missing_close_date",
        "missing_phone",
        "missing_last_activity_high_value",
        "invalid_email",
    }
    issues = [issue for issue in audit["issues"] if issue["issue_type"] in issue_types]
    return _issue_result("check_missing_values", records, issues)


def check_duplicate_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit = data_quality_audit(_copy_records(records))
    issues = [issue for issue in audit["issues"] if issue["issue_type"] == "duplicate_account"]
    return _issue_result("check_duplicate_records", records, issues)


def check_invalid_dates(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit = data_quality_audit(_copy_records(records))
    issues = [issue for issue in audit["issues"] if issue["issue_type"] == "past_close_date_open_opp"]

    for row in records:
        for field in ["close_date", "last_activity_date", "created_date"]:
            value = row.get(field)
            if value and parse_date(value) is None:
                issues.append(
                    {
                        "record_id": row.get("record_id"),
                        "account_name": row.get("account_name"),
                        "issue_type": "invalid_date_format",
                        "field": field,
                        "severity": "medium",
                        "detail": f"{field} is not a valid YYYY-MM-DD date.",
                    }
                )

    return _issue_result("check_invalid_dates", records, issues)


def check_pipeline_anomalies(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit = data_quality_audit(_copy_records(records))
    pipeline = pipeline_summary(_copy_records(records))
    issues = [
        issue
        for issue in audit["issues"]
        if issue["issue_type"]
        in {
            "missing_last_activity_high_value",
            "stale_activity_high_value",
            "stale_activity_low_value",
            "past_close_date_open_opp",
        }
    ]

    for row in records:
        if row.get("stage") not in VALID_STAGES:
            issues.append(
                {
                    "record_id": row.get("record_id"),
                    "account_name": row.get("account_name"),
                    "issue_type": "invalid_stage",
                    "field": "stage",
                    "severity": "medium",
                    "detail": f"Stage {row.get('stage')} is outside the approved CRM stage list.",
                }
            )

    result = _issue_result("check_pipeline_anomalies", records, issues)
    result["pipeline"] = pipeline
    result["open_stage_count"] = sum(1 for row in records if row.get("stage") in OPEN_STAGES)
    result["largest_country_exposure"] = sorted(
        pipeline["by_country_eur"].items(), key=lambda item: item[1], reverse=True
    )[:3]
    return result


def generate_audit_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit = data_quality_audit(_copy_records(records))
    pipeline = pipeline_summary(_copy_records(records))
    manager_draft = draft_manager_summary(audit, pipeline)
    return {
        "tool": "generate_audit_summary",
        "records_checked": audit["records_checked"],
        "total_issues": audit["total_issues"],
        "severity_counts": audit["severity_counts"],
        "issues": audit["issues"],
        "top_records": audit["top_records"],
        "pipeline": pipeline,
        "summary": manager_draft["summary"],
    }


def find_records_by_text(query: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    result = find_records(query, _copy_records(records))
    result["tool"] = "find_records"
    return result


def export_audit_log(records: List[Dict[str, Any]], approved: bool = False) -> Dict[str, Any]:
    if not approved:
        raise PermissionError("Human approval is required before exporting an audit log.")
    audit = data_quality_audit(_copy_records(records))
    return {
        "tool": "export_audit_log",
        "status": "draft_export_ready",
        "records_checked": audit["records_checked"],
        "total_issues": audit["total_issues"],
    }


def _issue_result(tool_name: str, records: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    severity_counts = Counter(issue.get("severity", "medium") for issue in issues)
    issue_type_counts = Counter(issue.get("issue_type", "unknown") for issue in issues)
    return {
        "tool": tool_name,
        "records_checked": len(records),
        "issue_count": len(issues),
        "severity_counts": dict(severity_counts),
        "issue_type_counts": dict(issue_type_counts),
        "issues": issues,
    }


def summarize_output(output: Any) -> str:
    if isinstance(output, dict):
        parts: List[str] = []
        for key in [
            "record_count",
            "records_checked",
            "total_issues",
            "issue_count",
            "open_stage_count",
            "status",
        ]:
            if key in output:
                parts.append(f"{key}={output[key]}")
        if "pipeline" in output and isinstance(output["pipeline"], dict):
            parts.append(f"open_pipeline_eur={output['pipeline'].get('open_pipeline_eur')}")
        if "count" in output:
            parts.append(f"matches={output['count']}")
        if "issue_type_counts" in output:
            top_types = sorted(output["issue_type_counts"].items(), key=lambda item: item[0])[:5]
            parts.append(f"issue_types={top_types}")
        if parts:
            return "; ".join(parts)
    return str(output)[:300]


def sanitize_args(args: Dict[str, Any]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key, value in args.items():
        if key == "records" and isinstance(value, list):
            sanitized[key] = {"record_count": len(value)}
        elif key == "shared_context" and isinstance(value, dict):
            sanitized[key] = {
                "record_count": value.get("record_count"),
                "rulebook_loaded": bool(value.get("rulebook")),
            }
        else:
            sanitized[key] = deepcopy(value)
    return sanitized


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_stage: Dict[str, int] = defaultdict(int)
    by_country: Dict[str, int] = defaultdict(int)
    for row in records:
        by_stage[row.get("stage", "unknown")] += 1
        by_country[row.get("country", "unknown")] += 1
    return {
        "record_count": len(records),
        "stages": dict(sorted(by_stage.items())),
        "countries": dict(sorted(by_country.items())),
    }


def shared_rulebook() -> Dict[str, Any]:
    return load_rulebook()
