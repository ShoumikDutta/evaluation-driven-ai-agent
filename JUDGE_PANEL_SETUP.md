# Running the LLM Judge Panel

The **LLM Judge Panel** is a system that uses one or more LLMs to evaluate and compare your single-agent vs multi-agent responses fairly.

---

## Quick Start: Single Judge vs Judge Panel

### Current Setup (Mock Judge)

By default, the system uses a **mock judge** (deterministic, no API calls):

```bash
cd crm-agent-comparison
python run_eval_harness.py
```

Results will show `judge_mode: mock` in the output. This is fast and free, but uses rule-based scoring instead of real LLM judgment.

---

## Setup Steps

### Step 1: Create `.env` File

Copy the example:

```bash
cd crm-agent-comparison
cp .env.example .env
```

### Step 2: Choose Your Judge Configuration

Edit `.env` and set either:

**Option A: Single Judge Provider** (one LLM only)
```bash
JUDGE_PROVIDER=openai
```

**Option B: Judge Panel** (multiple LLMs - RECOMMENDED)
```bash
JUDGE_PANEL=mock,openai,ollama
```

---

## Available Judge Providers

### 1. **Mock Judge** (Free, Default)
```bash
JUDGE_PROVIDER=mock
# OR
JUDGE_PANEL=mock
```

✅ **Pros**:
- Free
- Fast (instant)
- Deterministic (same results every time)
- Good for testing

❌ **Cons**:
- Rule-based, not using real LLM reasoning
- Less sophisticated

**Setup**: No API key needed. Works out of box.

---

### 2. **Ollama Judge** (Free, Local)
```bash
JUDGE_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

✅ **Pros**:
- Free
- Runs locally (no API calls)
- Good open-source models
- Fast if you have GPU

❌ **Cons**:
- Requires Ollama installed
- Slower than mock
- Needs 8GB+ RAM

**Setup Steps**:

1. **Install Ollama**: https://ollama.ai
2. **Pull a model**:
   ```bash
   ollama pull llama3.1:8b
   ```
3. **Start Ollama server** (in separate terminal):
   ```bash
   ollama serve
   ```
4. **Set .env**:
   ```bash
   JUDGE_PROVIDER=ollama
   OLLAMA_MODEL=llama3.1:8b
   ```

5. **Run eval**:
   ```bash
   python run_eval_harness.py
   ```

---

### 3. **OpenAI Judge** (Paid, Cloud)
```bash
JUDGE_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```

✅ **Pros**:
- Excellent quality
- Fast
- Reliable

❌ **Cons**:
- Costs ~$0.50-2.00 per 20 eval cases
- Requires OpenAI account

**Setup Steps**:

1. **Get API key**: https://platform.openai.com/api/keys
2. **Set .env**:
   ```bash
   OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
   OPENAI_MODEL=gpt-4o-mini
   ```
3. **Run eval**:
   ```bash
   python run_eval_harness.py
   ```

---

### 4. **Google Gemini Judge** (Paid, Cloud)
```bash
JUDGE_PROVIDER=gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-3.5-flash
```

✅ **Pros**:
- Good quality
- Cheaper than OpenAI
- Fast

❌ **Cons**:
- Costs ~$0.30-0.75 per 20 eval cases
- Requires Google Cloud account

**Setup Steps**:

1. **Get API key**: https://aistudio.google.com/app/apikey
2. **Set .env**:
   ```bash
   GEMINI_API_KEY=AIza...YOUR_KEY_HERE
   GEMINI_MODEL=gemini-3.5-flash
   ```
3. **Run eval**:
   ```bash
   python run_eval_harness.py
   ```

---

### 5. **Groq Judge** (Free-ish, Cloud)
```bash
JUDGE_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant
```

✅ **Pros**:
- Free tier available
- Very fast
- Good quality

❌ **Cons**:
- Rate limits on free tier
- Requires Groq account

**Setup Steps**:

1. **Get API key**: https://groq.com/
2. **Set .env**:
   ```bash
   GROQ_API_KEY=gsk_...YOUR_KEY_HERE
   GROQ_MODEL=llama-3.1-8b-instant
   ```
3. **Run eval**:
   ```bash
   python run_eval_harness.py
   ```

---

### 6. **OpenRouter Judge** (Paid, Multi-Model)
```bash
JUDGE_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4-turbo
```

✅ **Pros**:
- Access to many models
- Can switch models easily
- Good pricing

❌ **Cons**:
- Requires OpenRouter account
- Costs depend on model

**Setup Steps**:

1. **Get API key**: https://openrouter.ai/
2. **Pick a model**: https://openrouter.ai/models
3. **Set .env**:
   ```bash
   OPENROUTER_API_KEY=sk-or-...YOUR_KEY_HERE
   OPENROUTER_MODEL=openai/gpt-4o-mini
   ```
4. **Run eval**:
   ```bash
   python run_eval_harness.py
   ```

---

## Judge Panel: Use Multiple Judges

The **judge panel** runs multiple judges and combines their verdicts. This is **RECOMMENDED** for rigor.

### Example Panel Configurations

**Option 1: Fast & Free**
```bash
JUDGE_PANEL=mock,ollama
```
- Mock judge (instant, deterministic)
- Ollama judge (free, local)
- Combined verdict

**Option 2: Production Quality**
```bash
JUDGE_PANEL=openai,gemini,groq
```
- OpenAI (gpt-4o-mini)
- Google Gemini (gemini-3.5-flash)
- Groq (llama-3.1-8b-instant)
- Takes majority vote

**Option 3: Everything**
```bash
JUDGE_PANEL=mock,openai,gemini,ollama
```
- All four judges
- Most robust
- Most expensive/slow

**Option 4: Baseline + Premium**
```bash
JUDGE_PANEL=mock,openai
```
- Mock (deterministic baseline)
- OpenAI (quality check)
- Good balance of cost & quality

---

## How Judge Panel Works

When you set `JUDGE_PANEL=mock,openai,groq`:

```
For each of 20 test cases:
  1. Run single-agent system
  2. Run multi-agent system
  3. For each judge (mock, openai, groq):
     a. Shuffle labels (is single "A" or "B"?)
     b. Run pass 1: A vs B
     c. Run pass 2: B vs A (swapped)
     d. Average passes
     e. Return score & winner
  4. Take majority vote from all judges
  5. Record verdict
```

**Result**: A robust, multi-judge verdict that accounts for LLM bias.

---

## Running Eval with Judge Panel

```bash
# Example 1: Single judge (OpenAI)
OPENAI_API_KEY=sk-proj-... python run_eval_harness.py

# Example 2: Judge panel (mock + openai)
OPENAI_API_KEY=sk-proj-... python run_eval_harness.py
# (with JUDGE_PANEL=mock,openai in .env)

# Example 3: Judge panel (mock + ollama)
# Ollama must be running first!
python run_eval_harness.py
# (with JUDGE_PANEL=mock,ollama in .env)
```

---

## Cost Estimates

If running on all 20 eval cases:

| Judge | Per 20 Cases | Notes |
|-------|-------------|-------|
| Mock | $0 | Free, instant |
| Ollama | $0 | Free, local (needs GPU for speed) |
| OpenAI gpt-4o-mini | ~$1.50 | Reliable, good quality |
| Gemini gemini-3.5-flash | ~$0.50 | Cheaper, good quality |
| Groq llama-3.1 | ~$0 | Free tier or very cheap |

**Panel of 3 (mock, openai, gemini)**: ~$2.00 per run

---

## Monitoring Judge Execution

When judges run, you'll see output like:

```
Running 20 eval cases...
case_001: single 0.86, multi 0.90, judge_mode=panel, winner=tie
case_002: single 0.88, multi 0.92, judge_mode=panel, winner=multi
...
Results saved to: evals/results/eval_results.json
Judge verdicts: single:3 multi:2 tie:15
```

### Check Results

```bash
# View results
cat evals/results/eval_results.csv

# View judge summary
cat evals/results/eval_results.json | grep -A5 "judge"
```

---

## Troubleshooting Judge Panel

### "judge_mode: mock" even though I set JUDGE_PROVIDER=openai

**Problem**: API key not set or environment not loaded  
**Fix**:
```bash
# Make sure .env file exists
ls -la .env

# Check env var is set
echo $OPENAI_API_KEY  # should print your key

# Re-run with explicit env
OPENAI_API_KEY=sk-proj-... python run_eval_harness.py
```

### "Ollama: Connection refused"

**Problem**: Ollama server not running  
**Fix**:
```bash
# In another terminal, start Ollama
ollama serve

# Then run eval in your original terminal
python run_eval_harness.py
```

### "JUDGE_PANEL only showing mock results"

**Problem**: Other judges not available (missing API keys)  
**Fix**:
```bash
# Check which judges are actually available
python -c "
import os
os.environ['JUDGE_PANEL'] = 'mock,openai,ollama'
from evals.judge import configured_judges
judges = configured_judges()
print([j.name for j in judges])
"
```

### Judge very slow

**Problem**: Running judges serially, and OpenAI/Gemini are slow  
**Fix**:
```bash
# Use faster judges only
JUDGE_PANEL=mock,groq python run_eval_harness.py

# Or use local Ollama
JUDGE_PANEL=mock,ollama python run_eval_harness.py
```

---

## For Your Presentation

### What to Say About Judge Panel

> "The judge panel runs multiple LLMs to evaluate both systems. Here, I'm using three judges: a deterministic mock baseline, OpenAI GPT-4, and Groq Llama. They independently rate each response on correctness, tool use, safety, and conciseness. I randomize which response is labeled A and which is B to prevent bias. Then I run both orderings (A vs B, then B vs A) and average the scores. The panel takes a majority vote from all judges. This triple-review approach removes individual LLM bias and gives us a robust verdict."

### What to Show

- Results file with `judge_panel: [openai, gemini, groq]`
- Judge verdicts: majority wins
- Score distributions across judges
- Evidence that judges agree on most cases (tie = agreement)

---

## Recommended Setup for Your Demo

**Option 1: Fastest (Best for Live Demo)**
```bash
JUDGE_PANEL=mock
```
✅ Instant results, always works
❌ Rule-based (not real LLM)

**Option 2: Balanced (Best for Presentation)**
```bash
JUDGE_PANEL=mock,ollama
```
✅ Free, fast-ish, real LLM (ollama)
❌ Needs Ollama installed and running

**Option 3: Production Quality (Best for Paper)**
```bash
JUDGE_PANEL=mock,openai,gemini
```
✅ Robust, real LLMs, multi-judge consensus
❌ Costs ~$2-3, slower

---

## Next Steps

1. **Pick your configuration** (mock, single judge, or panel)
2. **Set up `.env` file** with API keys
3. **Test with one case first**:
   ```bash
   python run_comparison.py --prompt "Find duplicate accounts" --mode both
   ```
4. **Run full eval**:
   ```bash
   python run_eval_harness.py
   ```
5. **Check results**:
   ```bash
   cat evals/results/eval_results.csv | head -5
   ```

---

**Questions?** Check the code:
- [evals/judge.py](evals/judge.py) — Judge implementation
- [run_eval_harness.py](run_eval_harness.py) — How eval harness calls judges
- [.env.example](.env.example) — All available environment variables
