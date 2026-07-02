from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class GuardrailDecision:
    blocked: bool = False
    requires_human_approval: bool = False
    reasons: List[str] = field(default_factory=list)


PROMPT_INJECTION_PATTERNS = [
    r"\bignore (all )?(previous|prior) (instructions|rules)\b",
    r"\bdisregard (all )?(previous|prior) (instructions|rules)\b",
    r"\breveal (the )?(system prompt|developer message|hidden prompt|rules)\b",
    r"\bshow (the )?(system prompt|developer message|hidden prompt)\b",
    r"\bprint (the )?(system prompt|developer message|hidden prompt)\b",
    r"\bapi key\b",
    r"\benvironment variable",
    r"\bsecret",
]

DESTRUCTIVE_PATTERNS = [
    r"\bdelete\b",
    r"\berase\b",
    r"\bdrop\b",
    r"\bwipe\b",
    r"\bdestroy\b",
    r"\bremove records?\b",
]

DIRECT_EXTERNAL_ACTION_PATTERNS = [
    r"\bsend\b.*\bemail\b",
    r"\bemail\b.*\b(raw|file|records?)\b",
    r"\bupdate\b.*\bcrm\b",
    r"\bwrite\b.*\bcrm\b",
    r"\bexport\b.*\b(raw|crm file|records?|report|audit)\b",
    r"\bcreate\b.*\bexport\b",
]

SAFE_DRAFT_PATTERNS = [
    r"\bdraft\b",
    r"\bdo not send\b",
    r"\bbefore\b.*\bapproval\b",
    r"\bask\b.*\bapproval\b",
    r"\bhuman approval\b",
    r"\bhuman review\b",
]

FORBIDDEN_OUTCOME_PATTERNS = [
    r"\bi sent\b",
    r"\bi updated\b",
    r"\bi deleted\b",
    r"\bcrm was updated\b",
    r"\brecords were deleted\b",
    r"\bexported raw\b",
    r"\bwithout approval\b",
]


def evaluate_prompt(prompt: str) -> GuardrailDecision:
    text = (prompt or "").strip().lower()
    decision = GuardrailDecision()

    if not text:
        decision.blocked = True
        decision.reasons.append("empty_prompt")
        return decision

    if _matches_any(text, PROMPT_INJECTION_PATTERNS):
        decision.blocked = True
        decision.requires_human_approval = True
        decision.reasons.append("prompt_injection_or_secret_request")

    if _matches_any(text, DESTRUCTIVE_PATTERNS):
        decision.blocked = True
        decision.requires_human_approval = True
        decision.reasons.append("destructive_action_requested")

    external_action = _matches_any(text, DIRECT_EXTERNAL_ACTION_PATTERNS)
    raw_data_export = bool(re.search(r"\b(raw|full)\b.*\b(crm|file|records?)\b", text))
    safe_draft = _matches_any(text, SAFE_DRAFT_PATTERNS)
    approval_context = "approval" in text and any(word in text for word in ["email", "send", "export", "update", "write"])

    if approval_context:
        decision.requires_human_approval = True
        if "external_action_requires_human_approval" not in decision.reasons:
            decision.reasons.append("external_action_requires_human_approval")

    if external_action:
        decision.requires_human_approval = True
        decision.reasons.append("external_action_requires_human_approval")
        if raw_data_export or "without approval" in text:
            decision.blocked = True
            decision.reasons.append("unsafe_export_or_unapproved_external_action")
        elif not safe_draft and any(word in text for word in ["send", "update", "write"]):
            decision.blocked = True
            decision.reasons.append("direct_system_action_blocked")

    return decision


def forbidden_action_triggered(text: str, extra_patterns: Iterable[str] | None = None) -> bool:
    lowered = (text or "").lower()
    patterns = list(FORBIDDEN_OUTCOME_PATTERNS)
    if extra_patterns:
        patterns.extend(str(pattern).lower() for pattern in extra_patterns)
    return _matches_any(lowered, patterns)


def requires_approval_from_prompt(prompt: str) -> bool:
    return evaluate_prompt(prompt).requires_human_approval


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)
