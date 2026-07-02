from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agents.context import clone_shared_context, prepare_shared_context
from agents.multi_agent import execute_multi_agent
from agents.schemas import response_to_dict, validate_agent_response
from agents.single_agent import execute_single_agent
from evals.judge import judge_pairwise
from evals.metrics import compute_case_metrics, summarize_metrics
from tools.tool_registry import build_tool_registry

ROOT = Path(__file__).resolve().parent
EVAL_CASES_PATH = ROOT / "evals" / "eval_cases.jsonl"
RESULTS_DIR = ROOT / "evals" / "results"


def load_eval_cases(path: Path = EVAL_CASES_PATH) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        required = {"id", "category", "prompt", "expected_behavior", "must_use_tools", "must_not_do", "reference_notes"}
        missing = sorted(required - set(case))
        if missing:
            raise ValueError(f"{path}:{line_no} missing keys: {missing}")
        cases.append(case)
    return cases


def run_eval_cases(limit: int | None = None, save_results: bool = True) -> Dict[str, Any]:
    cases = load_eval_cases()
    if limit is not None:
        cases = cases[:limit]

    rows: List[Dict[str, Any]] = []
    registry = build_tool_registry()
    for case in cases:
        shared_context = prepare_shared_context(case["prompt"])
        single = execute_single_agent(case["prompt"], clone_shared_context(shared_context), registry, save_trace_file=True)
        multi = execute_multi_agent(case["prompt"], clone_shared_context(shared_context), registry, save_trace_file=True)

        single_response = response_to_dict(validate_agent_response(single["response"]))
        multi_response = response_to_dict(validate_agent_response(multi["response"]))
        single_public = public_run(single, single_response)
        multi_public = public_run(multi, multi_response)
        metrics = compute_case_metrics(case, single_public, multi_public)
        judge = judge_pairwise(case, single_response, multi_response)
        rows.append(
            {
                "case": case,
                "single": single_public,
                "multi": multi_public,
                "metrics": metrics,
                "judge": judge,
            }
        )

    summary = summarize_metrics(rows)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary["judge"] = summarize_judge(rows)
    summary["failed_cases"] = [
        {
            "id": row["case"]["id"],
            "category": row["case"]["category"],
            "single_pass": row["metrics"]["pass_single"],
            "multi_pass": row["metrics"]["pass_multi"],
            "winner_system": row["judge"]["winner_system"],
        }
        for row in rows
        if not row["metrics"]["pass_single"] or not row["metrics"]["pass_multi"]
    ]

    result = {"summary": summary, "rows": rows}
    if save_results:
        save_eval_results(result)
    return result


def public_run(run: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "response": response,
        "latency_ms": run["latency_ms"],
        "tool_call_count": run["tool_call_count"],
        "trace_path": run["trace_path"],
        "trace": run["trace"],
    }


def summarize_judge(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {"single": 0, "multi": 0, "tie": 0, "tie_uncertain": 0}
    score_totals = {
        "single": {"overall": 0, "count": 0},
        "multi": {"overall": 0, "count": 0},
    }
    for row in rows:
        winner = row["judge"]["winner_system"]
        counts[winner if winner in counts else "tie_uncertain"] += 1
        for pass_key, mapping_key in [("pass_1", "label_mapping_pass_1"), ("pass_2", "label_mapping_pass_2")]:
            mapping = row["judge"][mapping_key]
            scores = row["judge"][pass_key]["scores"]
            for label, system in mapping.items():
                if system in score_totals:
                    score_totals[system]["overall"] += scores[label]["overall"]
                    score_totals[system]["count"] += 1
    averages = {}
    for system, totals in score_totals.items():
        averages[system] = round(totals["overall"] / totals["count"], 2) if totals["count"] else 0
    return {
        "win_tie_loss_count": counts,
        "average_overall_scores": averages,
    }


def save_eval_results(result: Dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / "eval_results.json"
    csv_path = RESULTS_DIR / "eval_results.csv"
    summary_path = RESULTS_DIR / "summary.json"

    json_path.write_text(json.dumps(result["rows"], indent=2, ensure_ascii=True), encoding="utf-8")
    summary_path.write_text(json.dumps(result["summary"], indent=2, ensure_ascii=True), encoding="utf-8")

    flat_rows = [flatten_row(row) for row in result["rows"]]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)


def flatten_row(row: Dict[str, Any]) -> Dict[str, Any]:
    metrics = row["metrics"]
    judge = row["judge"]
    return {
        "case_id": row["case"]["id"],
        "category": row["case"]["category"],
        "prompt": row["case"]["prompt"],
        "single_status": row["single"]["response"]["status"],
        "multi_status": row["multi"]["response"]["status"],
        "single_tools": ";".join(row["single"]["response"]["tools_used"]),
        "multi_tools": ";".join(row["multi"]["response"]["tools_used"]),
        "single_latency_ms": row["single"]["latency_ms"],
        "multi_latency_ms": row["multi"]["latency_ms"],
        "single_tool_calls": row["single"]["tool_call_count"],
        "multi_tool_calls": row["multi"]["tool_call_count"],
        "single_pass": metrics["pass_single"],
        "multi_pass": metrics["pass_multi"],
        "schema_valid_single": metrics["schema_valid_single"],
        "schema_valid_multi": metrics["schema_valid_multi"],
        "required_tool_used_single": metrics["required_tool_used_single"],
        "required_tool_used_multi": metrics["required_tool_used_multi"],
        "forbidden_action_triggered_single": metrics["forbidden_action_triggered_single"],
        "forbidden_action_triggered_multi": metrics["forbidden_action_triggered_multi"],
        "human_approval_correct_single": metrics["human_approval_correct_single"],
        "human_approval_correct_multi": metrics["human_approval_correct_multi"],
        "status_correct_single": metrics["status_correct_single"],
        "status_correct_multi": metrics["status_correct_multi"],
        "judge_winner_system": judge["winner_system"],
        "judge_mode": judge["judge_mode"],
        "single_trace_path": row["single"]["trace_path"],
        "multi_trace_path": row["multi"]["trace_path"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CRM single-agent vs multi-agent eval harness.")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of cases to run.")
    args = parser.parse_args()
    result = run_eval_cases(limit=args.limit, save_results=True)
    print(json.dumps(result["summary"], indent=2))
    print(f"\nResults written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
