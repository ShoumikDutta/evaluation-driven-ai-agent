# Architecture Notes

## Single Agent Flow

```text
User Query
  -> Single Generalist Agent
      -> classify_intent
      -> load_crm_records
      -> data_quality_audit / pipeline_summary / find_records
      -> structured JSON response
```

## Multi-Agent Flow

```text
User Query
  -> Orchestrator Agent
      -> routes task
      -> Data Quality Agent
      -> Sales Insight Agent
      -> Retrieval Agent
      -> Critic Agent
  -> structured JSON response
```

## Why this is fair

The comparison is fair because both variants are controlled by the same external conditions:

- Same frozen date: 2026-06-25
- Same CSV file
- Same rulebook
- Same tool functions
- Same output schema
- Same evaluation cases

## Why deterministic tools matter

The LLM or agent should not calculate business-critical numbers by itself. The deterministic tool calculates the audit and pipeline numbers. The model/agent only decides which tool to use and how to explain the output.
