from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from tools import crm_tools


ToolFunction = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    human_approval_required: bool
    function: ToolFunction

    def public_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "human_approval_required": self.human_approval_required,
        }


class ToolRegistry:
    def __init__(self, specs: List[ToolSpec]):
        self._specs = {spec.name: spec for spec in specs}

    def names(self) -> List[str]:
        return sorted(self._specs)

    def describe(self) -> List[Dict[str, Any]]:
        return [self._specs[name].public_metadata() for name in self.names()]

    def get(self, name: str) -> ToolSpec:
        if name not in self._specs:
            raise KeyError(f"Unknown tool: {name}")
        return self._specs[name]

    def execute(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        spec = self.get(name)
        return spec.function(**kwargs)

    def requires_approval(self, name: str) -> bool:
        return self.get(name).human_approval_required


def build_tool_registry() -> ToolRegistry:
    records_input = {
        "type": "object",
        "properties": {"records": {"type": "array", "description": "CRM rows from shared context"}},
        "required": ["records"],
    }
    issue_output = {
        "type": "object",
        "properties": {
            "records_checked": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "issues": {"type": "array"},
        },
    }
    specs = [
        ToolSpec(
            name="load_crm_data",
            description="Load the shared CRM dataset for this run.",
            input_schema={"type": "object", "properties": {"shared_context": {"type": "object"}}},
            output_schema={
                "type": "object",
                "properties": {
                    "record_count": {"type": "integer"},
                    "columns": {"type": "array"},
                    "records": {"type": "array"},
                },
            },
            human_approval_required=False,
            function=crm_tools.load_crm_data,
        ),
        ToolSpec(
            name="check_missing_values",
            description="Check missing owner, close date, contact fields, and required activity fields.",
            input_schema=records_input,
            output_schema=issue_output,
            human_approval_required=False,
            function=crm_tools.check_missing_values,
        ),
        ToolSpec(
            name="check_duplicate_records",
            description="Find duplicate account records in the same country.",
            input_schema=records_input,
            output_schema=issue_output,
            human_approval_required=False,
            function=crm_tools.check_duplicate_records,
        ),
        ToolSpec(
            name="check_invalid_dates",
            description="Find invalid date formats and open opportunities with past close dates.",
            input_schema=records_input,
            output_schema=issue_output,
            human_approval_required=False,
            function=crm_tools.check_invalid_dates,
        ),
        ToolSpec(
            name="check_pipeline_anomalies",
            description="Summarize pipeline exposure and detect stale, high-risk, or invalid-stage opportunities.",
            input_schema=records_input,
            output_schema={
                "type": "object",
                "properties": {
                    "pipeline": {"type": "object"},
                    "issues": {"type": "array"},
                    "largest_country_exposure": {"type": "array"},
                },
            },
            human_approval_required=False,
            function=crm_tools.check_pipeline_anomalies,
        ),
        ToolSpec(
            name="generate_audit_summary",
            description="Run the standard CRM data-quality audit and manager summary.",
            input_schema=records_input,
            output_schema={
                "type": "object",
                "properties": {
                    "records_checked": {"type": "integer"},
                    "total_issues": {"type": "integer"},
                    "severity_counts": {"type": "object"},
                    "summary": {"type": "string"},
                },
            },
            human_approval_required=False,
            function=crm_tools.generate_audit_summary,
        ),
        ToolSpec(
            name="find_records",
            description="Retrieve CRM records related to a text query.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}, "records": {"type": "array"}},
                "required": ["query", "records"],
            },
            output_schema={"type": "object", "properties": {"count": {"type": "integer"}, "records": {"type": "array"}}},
            human_approval_required=False,
            function=crm_tools.find_records_by_text,
        ),
        ToolSpec(
            name="export_audit_log",
            description="Create a draft export of the audit log after explicit human approval.",
            input_schema={
                "type": "object",
                "properties": {"records": {"type": "array"}, "approved": {"type": "boolean"}},
                "required": ["records", "approved"],
            },
            output_schema={"type": "object", "properties": {"status": {"type": "string"}}},
            human_approval_required=True,
            function=crm_tools.export_audit_log,
        ),
    ]
    return ToolRegistry(specs)
