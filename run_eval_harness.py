from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from agents.context import clone_shared_context, prepare_shared_context
from agents.multi_agent import execute_multi_agent
from agents.schemas import response_to_dict, validate_agent_response
from agents.single_agent import execute_single_agent
from evals.config import JUDGE_SCORE_KEYS
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
    counts = {"single": 0, "multi": 0, "tie": 0, "unavailable": 0}
    judge_vote_totals = {"single": 0, "multi": 0, "tie": 0}
    score_values = {system: {key: [] for key in JUDGE_SCORE_KEYS} for system in ["single", "multi"]}
    confidence_values: list[float] = []
    agreement_values: list[float] = []
    unavailable_judge_runs = 0
    total_judge_runs = 0

    for row in rows:
        judge = row["judge"]
        winner = judge.get("winner_system", "unavailable")
        counts[winner if winner in counts else "unavailable"] += 1

        aggregation = judge.get("aggregation", {})
        if aggregation.get("available_judges", 0):
            agreement_values.append(float(aggregation.get("judge_agreement", 0.0)))

        for result in judge.get("panel_results", []):
            total_judge_runs += 1
            if result.get("status") not in {"ok", "Healthy"}:
                unavailable_judge_runs += 1
                continue
            result_winner = result.get("winner")
            if result_winner in judge_vote_totals:
                judge_vote_totals[result_winner] += 1
            confidence_values.append(float(result.get("confidence", 0.0)))
            for system in ["single", "multi"]:
                scores = result.get("scores", {}).get(system, {})
                for key in JUDGE_SCORE_KEYS:
                    if key in scores:
                        score_values[system][key].append(float(scores[key]))

    average_scores = {
        system: {
            key: round(mean(values), 2) if values else 0.0
            for key, values in metrics.items()
        }
        for system, metrics in score_values.items()
    }

    available_judge_runs = total_judge_runs - unavailable_judge_runs
    average_available_judges = round(available_judge_runs / len(rows), 2) if rows else 0.0
    configured_judges_per_case = round(total_judge_runs / len(rows), 2) if rows else 0.0

    return {
        "win_tie_loss_count": counts,
        "overall_winner": winner_from_counts(counts),
        "majority_vote": {key: counts[key] for key in ["single", "multi", "tie"]},
        "judge_vote_totals": judge_vote_totals,
        "average_confidence": round(mean(confidence_values), 4) if confidence_values else 0.0,
        "average_judge_agreement": round(mean(agreement_values), 4) if agreement_values else 0.0,
        "average_judge_agreement_percent": round(mean(agreement_values) * 100) if agreement_values else 0,
        "average_scores": average_scores,
        "average_overall_scores": {
            "single": average_scores["single"]["overall"],
            "multi": average_scores["multi"]["overall"],
        },
        "available_judge_runs": available_judge_runs,
        "available_judges_text": f"{available_judge_runs} / {total_judge_runs}",
        "average_available_judges": average_available_judges,
        "configured_judges_per_case": configured_judges_per_case,
        "average_available_judges_text": f"{average_available_judges:g} / {configured_judges_per_case:g}",
        "unavailable_judge_runs": unavailable_judge_runs,
        "total_judge_runs": total_judge_runs,
    }


def winner_from_counts(counts: Dict[str, int]) -> str:
    available_counts = {key: counts.get(key, 0) for key in ["single", "multi", "tie"]}
    if not any(available_counts.values()):
        return "unavailable"
    best_count = max(available_counts.values())
    leaders = [winner for winner, count in available_counts.items() if count == best_count]
    return leaders[0] if len(leaders) == 1 else "tie"


def save_eval_results(result: Dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / "eval_results.json"
    csv_path = RESULTS_DIR / "eval_results.csv"
    summary_path = RESULTS_DIR / "summary.json"

    json_path.write_text(json.dumps(result["rows"], indent=2, ensure_ascii=True), encoding="utf-8")
    summary_path.write_text(json.dumps(result["summary"], indent=2, ensure_ascii=True), encoding="utf-8")

    flat_rows = [flatten_row(row) for row in result["rows"]]
    if not flat_rows:
        csv_path.write_text("", encoding="utf-8")
        return

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)


def flatten_row(row: Dict[str, Any]) -> Dict[str, Any]:
    metrics = row["metrics"]
    judge = row["judge"]
    aggregation = judge.get("aggregation", {})
    average_scores = aggregation.get("average_scores", {})
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
        "judge_panel": ";".join(judge.get("judge_panel", [])),
        "judge_majority_vote": json.dumps(aggregation.get("majority_vote", {}), ensure_ascii=True),
        "judge_agreement_percent": aggregation.get("judge_agreement_percent", 0),
        "judge_average_confidence": aggregation.get("average_confidence", 0.0),
        "judge_unavailable": ";".join(aggregation.get("unavailable_judges", [])),
        "single_judge_overall": average_scores.get("single", {}).get("overall", 0.0),
        "multi_judge_overall": average_scores.get("multi", {}).get("overall", 0.0),
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
