from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "crm_records.csv"
RULEBOOK_PATH = ROOT / "config" / "rulebook.json"
TODAY = date(2026, 6, 25)  # frozen for reproducible capstone evaluation
OPEN_STAGES = {"Prospecting", "Qualification", "Proposal", "Negotiation"}


def load_rulebook() -> Dict[str, Any]:
    return json.loads(RULEBOOK_PATH.read_text(encoding="utf-8"))


def load_crm_records(path: Path = DATA_PATH) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["amount_eur"] = float(r["amount_eur"] or 0)
    return rows


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def is_valid_email(email: str) -> bool:
    pattern = load_rulebook()["dq_rules"]["invalid_email_regex"]
    return bool(re.match(pattern, email or ""))


def data_quality_audit(records: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    records = records or load_crm_records()
    rulebook = load_rulebook()["dq_rules"]
    severity_map = rulebook["severity"]
    issues: List[Dict[str, Any]] = []

    account_country_count = Counter((r["account_name"].strip().lower(), r["country"]) for r in records)

    for r in records:
        rid = r["record_id"]
        amount = float(r["amount_eur"])
        stage = r["stage"]
        close = parse_date(r.get("close_date"))
        activity = parse_date(r.get("last_activity_date"))

        def add(issue_type: str, field: str, detail: str):
            issues.append({
                "record_id": rid,
                "account_name": r["account_name"],
                "issue_type": issue_type,
                "field": field,
                "severity": severity_map.get(issue_type, "medium"),
                "detail": detail,
            })

        if not r.get("owner"):
            add("missing_owner", "owner", "Owner is required for accountability and follow-up routing.")
        if not r.get("close_date"):
            add("missing_close_date", "close_date", "Open opportunity has no expected close date.")
        if stage in OPEN_STAGES and close and close < TODAY:
            add("past_close_date_open_opp", "close_date", f"Open opportunity close date {close.isoformat()} is before {TODAY.isoformat()}.")
        if not r.get("email") or not is_valid_email(r.get("email", "")):
            add("invalid_email", "email", "Email is missing or not in a valid address format.")
        if not r.get("phone"):
            add("missing_phone", "phone", "Phone number is missing.")
        if not activity and amount >= rulebook["high_value_threshold_eur"]:
            add("missing_last_activity_high_value", "last_activity_date", "High-value opportunity has no last activity date.")
        elif activity:
            days = (TODAY - activity).days
            if days > rulebook["stale_activity_days"] and stage in OPEN_STAGES:
                issue = "stale_activity_high_value" if amount >= rulebook["high_value_threshold_eur"] else "stale_activity_low_value"
                add(issue, "last_activity_date", f"Last activity is {days} days old.")
        if account_country_count[(r["account_name"].strip().lower(), r["country"])] > 1:
            add("duplicate_account", "account_name", "Same account name appears more than once in the same country.")

    sev_counts = Counter(i["severity"] for i in issues)
    return {
        "tool": "data_quality_audit",
        "records_checked": len(records),
        "total_issues": len(issues),
        "severity_counts": dict(sev_counts),
        "issues": issues,
        "top_records": sorted(
            Counter(i["record_id"] for i in issues).items(), key=lambda x: (-x[1], x[0])
        )[:5],
    }


def pipeline_summary(records: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    records = records or load_crm_records()
    by_stage: Dict[str, float] = defaultdict(float)
    by_owner: Dict[str, float] = defaultdict(float)
    by_country: Dict[str, float] = defaultdict(float)
    open_value = 0.0
    for r in records:
        amount = float(r["amount_eur"])
        by_stage[r["stage"]] += amount
        by_owner[r.get("owner") or "Unassigned"] += amount
        by_country[r["country"]] += amount
        if r["stage"] in OPEN_STAGES:
            open_value += amount
    return {
        "tool": "pipeline_summary",
        "record_count": len(records),
        "open_pipeline_eur": round(open_value, 2),
        "by_stage_eur": dict(sorted(by_stage.items())),
        "by_owner_eur": dict(sorted(by_owner.items())),
        "by_country_eur": dict(sorted(by_country.items())),
        "highest_value_open": sorted(
            [r for r in records if r["stage"] in OPEN_STAGES],
            key=lambda r: float(r["amount_eur"]),
            reverse=True,
        )[:3],
    }


def find_records(query: str, records: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    records = records or load_crm_records()
    q = query.lower()
    matches = []
    for r in records:
        blob = " ".join(str(v) for v in r.values()).lower()
        if any(tok in blob for tok in q.split() if len(tok) > 2):
            matches.append(r)
    return {"tool": "find_records", "query": query, "count": len(matches), "records": matches[:10]}


def draft_manager_summary(audit: Dict[str, Any], pipeline: Dict[str, Any]) -> Dict[str, Any]:
    sev = audit["severity_counts"]
    high = sev.get("high", 0)
    medium = sev.get("medium", 0)
    low = sev.get("low", 0)
    answer = (
        f"CRM data-quality audit checked {audit['records_checked']} records and found "
        f"{audit['total_issues']} issues: {high} high, {medium} medium, {low} low. "
        f"Open pipeline value is €{pipeline['open_pipeline_eur']:,.0f}. "
        "Recommended next step: review high-severity records first, especially missing owner, missing close date, "
        "past close dates on open opportunities, and high-value stale activity. No CRM changes were made."
    )
    return {"tool": "draft_manager_summary", "summary": answer}


def classify_intent(query: str) -> str:
    q = query.lower()
    # Safety first: action verbs are blocked before any other route.
    if any(x in q for x in ["send", "update", "delete", "write to crm", "automatically", "ignore previous instructions"]):
        return "blocked_action"
    # Pipeline summaries by stage/owner are sales insight, not manager prose.
    if "pipeline" in q and any(x in q for x in ["stage", "owner", "country", "value"]):
        return "sales_insight"
    # Manager-summary queries often mention email/draft/report, but remain draft-only.
    if any(x in q for x in ["summary", "manager", "draft", "report"]):
        return "manager_summary"
    if any(x in q for x in [
        "quality", "issue", "missing", "invalid", "duplicate", "audit", "stale",
        "past close", "close dates", "high severity", "severity", "compliance-safe"
    ]):
        return "data_quality"
    if any(x in q for x in ["pipeline", "value", "stage", "owner", "country", "deal", "opportunity"]):
        return "sales_insight"
    return "general"


def make_response(task_type: str, answer: str, evidence: List[Any], actions: List[str], flags: List[str], confidence: float, trace: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "task_type": task_type,
        "answer": answer,
        "evidence": evidence,
        "actions": actions,
        "flags": flags,
        "confidence": confidence,
        "trace": trace,
    }
