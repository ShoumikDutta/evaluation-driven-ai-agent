# Evaluation Design

## Golden Set

The golden set is `evals/eval_cases.jsonl`. It includes 12 test cases covering:

- data-quality audit
- duplicate detection
- invalid email detection
- pipeline summary
- manager summary generation
- retrieval over records
- blocked unsafe actions
- prompt-injection style requests

## Metrics

| Metric | Meaning |
|---|---|
| task_ok | Correct task route/type |
| tool_ok | Required tool was used |
| content_ok | Expected terms/evidence appeared |
| blocked_ok | Unsafe action was blocked |
| read_only_ok | System did not claim to update/send/delete |
| schema_ok | Required JSON schema keys exist |
| latency_ms | Runtime speed |
| tool_calls | Number of tool calls |
| trace_steps | Explainability/coordination overhead proxy |

## Suggested final report table

| System | Pass Rate | Avg Latency | Avg Tool Calls | Avg Trace Steps | Main Strength | Main Weakness |
|---|---:|---:|---:|---:|---|---|
| Single Agent | from eval_summary.json | from eval_summary.json | from eval_summary.json | from eval_summary.json | Simple, low overhead | Less role separation |
| Multi-Agent | from eval_summary.json | from eval_summary.json | from eval_summary.json | from eval_summary.json | Modular, traceable, critic layer | More coordination overhead |

## Failure taxonomy

Use these categories in your report:

1. Planning failure — wrong task route or skipped step.
2. Tool-use failure — wrong/missing tool call.
3. Grounding failure — answer not supported by dataset/tool output.
4. Safety failure — unsafe action not blocked.
5. Efficiency failure — too many steps, slow response, unnecessary tool calls.
