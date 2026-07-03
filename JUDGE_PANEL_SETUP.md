# Cloud Judge Panel Setup

The evaluation harness uses a cloud LLM-as-a-Judge panel with three independent providers: Google Gemini, Groq, and Cerebras. Each provider receives the same prompt, returns the same JSON schema, and feeds the existing majority-vote aggregator.

## Default Panel

Configured in `llm_judge/judge.py`:

```text
Gemini   gemini-3.5-flash
Groq     llama-3.3-70b-versatile
Cerebras gpt-oss-120b
```

## Configure API Keys

Create a local `.env` file from `.env.example` and configure at least one provider:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash

GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

CEREBRAS_API_KEY=
CEREBRAS_MODEL=gpt-oss-120b
```

The app uses `python-dotenv` to load `.env`. Missing keys appear as `Configuration Missing` in the dashboard instead of crashing the evaluation.

## Run Evaluation

```bash
python run_eval_harness.py
```

Optional smaller run:

```bash
python run_eval_harness.py --limit 3
```

Outputs:

- `evals/results/eval_results.json`
- `evals/results/eval_results.csv`
- `evals/results/summary.json`

## How Aggregation Works

Each judge returns structured JSON:

```json
{
  "provider": "Gemini",
  "model": "gemini-3.5-flash",
  "winner": "single|multi|tie",
  "confidence": 0.94,
  "single": {
    "accuracy": 4,
    "completeness": 4,
    "reasoning": 4,
    "instruction_following": 5,
    "hallucination": 5,
    "tool_use": 4,
    "overall": 4
  },
  "multi": {
    "accuracy": 5,
    "completeness": 5,
    "reasoning": 5,
    "instruction_following": 5,
    "hallucination": 5,
    "tool_use": 5,
    "overall": 5
  },
  "reasoning": "The multi-agent response is more complete while remaining grounded."
}
```

The aggregator computes:

- majority winner
- average confidence
- average scores by criterion
- judge agreement percentage
- unavailable judge list

Example:

| Judge | Winner | Confidence |
| ----- | ------ | ---------- |
| Gemini | Multi | 94% |
| Groq | Tie | 81% |
| Cerebras | Multi | 91% |

Final winner: `multi`. Agreement: `66%`.

## Failure Behavior

If one provider is unavailable, evaluation continues with the remaining judges. The Streamlit dashboard shows the provider health status for that provider.

If all judges are unavailable, deterministic agent metrics still save, and the judge winner is recorded as `unavailable`.

## Streamlit Dashboard

```bash
streamlit run app.py
```

The Evaluation Demo section displays:

- Overall Winner
- Majority Vote
- Judge Agreement %
- Average Overall Score
- Average Accuracy
- Average Reasoning
- Average Completeness
- Average Tool Use
- Average Hallucination Score
- Individual Judge Results
