from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


AgentStatus = Literal["ok", "needs_human_review", "cannot_answer"]
IssueSeverity = Literal["low", "medium", "high"]


class DetectedIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: str = Field(min_length=1)
    severity: IssueSeverity
    affected_records: Optional[int] = Field(default=None, ge=0)
    evidence: str = Field(min_length=1)


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    status: AgentStatus
    detected_issues: List[DetectedIssue] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    needs_human_approval: bool = False
    reasoning_summary: str = Field(min_length=1)


class ToolCallLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str
    input_args: Dict[str, Any] = Field(default_factory=dict)
    output_summary: str
    success: bool
    timestamp: str
    latency_ms: float = Field(ge=0)
    error: Optional[str] = None


class AgentStepLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str
    step: str
    input_summary: str = ""
    output_summary: str = ""
    success: bool = True
    timestamp: str


class TraceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    mode: Literal["single", "multi"]
    user_prompt: str
    shared_context_summary: str
    final_output: Dict[str, Any]
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    agent_steps: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = Field(ge=0)
    token_usage_estimate: Dict[str, Optional[int]]
    errors: List[str] = Field(default_factory=list)


def response_to_dict(response: AgentResponse) -> Dict[str, Any]:
    return response.model_dump(mode="json")


def validate_agent_response(value: AgentResponse | Dict[str, Any]) -> AgentResponse:
    if isinstance(value, AgentResponse):
        return AgentResponse.model_validate(value.model_dump(mode="json"))
    return AgentResponse.model_validate(value)
