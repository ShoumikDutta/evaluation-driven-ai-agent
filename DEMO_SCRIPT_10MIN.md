# 10-Minute Demo Script: CRM Agent Comparison

**Total time: 10 minutes**  
**Pace: Speak clearly, show not tell. Avoid excessive talking.**

---

## Segment 1: Problem & Context (1.5 minutes)

### What to say:
> "Good morning. I'm presenting a capstone project comparing two AI architectures for CRM data quality—single-agent vs multi-agent.
>
> The problem: CRM data gets messy. Duplicates, missing fields, inconsistent names. A human reviews this manually, which is slow and error-prone.
>
> The research question: Is one well-designed agent enough, or does a multi-agent setup give better results? That's what we're benchmarking."

### Visual (optional):
- Show the pitch deck slide on "Problem: CRM data is messy"
- Or show a sample CRM record with issues highlighted (3-5 seconds)

**Time checkpoint: 1.5 min**

---

## Segment 2: Architecture Overview (1.5 minutes)

### What to say:
> "I built two systems. Both read-only, both use the same CRM CSV, same tools, same rules.
>
> **System 1: Single Agent** – One agent handles everything: Q&A, data checks, summaries. Simple, fast, fewer moving parts.
>
> **System 2: Multi-Agent** – An orchestrator routes tasks to specialists: Q&A agent, data-quality agent, insight agent, plus a critic. More structured, clearer separation of concerns.
>
> Both return the same structured output: status, detected issues, recommendations, confidence, human approval flags. This makes comparison fair."

### Visual (REQUIRED - show the architecture diagram):
- Display the mermaid diagram from README.md (flowchart with both paths)
- Point to single-agent flow, then multi-agent flow (10 seconds total)

**Time checkpoint: 3 min**

---

## Segment 3: Live Demo – Running a Test Case (3 minutes)

### Demo flow:

#### 3.1 Open Streamlit App (30 seconds)
```bash
streamlit run app.py
```

Show:
- Title: "CRM Data Quality Agent Comparison"
- Text area with a sample prompt
- **Select a prompt**. Suggest: "Find duplicate accounts in the CRM data."

#### 3.2 Run Both Systems Side-by-Side (2 minutes)
- Click "Run both and compare"
- **Show the output**:
  - Latency comparison (single vs multi)
  - Tool calls count
  - Structured JSON response
  - **Highlight**:
    - Both got the same "answer" field ✅
    - Both used the same tools: `load_crm_data`, `check_duplicate_records` ✅
    - Both returned `status: ok` ✅
    - Single agent: ~20ms, Multi-agent: ~25ms (mention multi has coordination overhead)

#### 3.3 Show Trace Files (30 seconds)
- Click **"Download Single Agent Trace"** button
- Mention: "This JSON file captures every decision, every tool call, every step. Transparency and debuggability."
- Don't open the file (too complex for live demo), just show it downloaded

**What NOT to do**:
- Don't try 3+ different prompts (wastes time)
- Don't read all JSON output aloud (boring, hard to follow)
- Don't explain every field in the schema (save for Q&A)

**Time checkpoint: 6 min**

---

## Segment 4: Evaluation Harness & Judging (2 minutes)

### What to say:
> "Now, how do we compare 20 test cases fairly? I use LLM-as-judge.
>
> Here's how it works:
> - I run both systems on the same prompt
> - I pass both responses to an LLM judge
> - **Crucially**: I randomize which is A and which is B (so bias is reduced)
> - I also run two passes: A vs B, then B vs A, and average the scores
> - The judge scores on: correctness, tool use, safety, human approval, conciseness, etc.
>
> Let's see the results."

### Visual (REQUIRED):
Open the evaluation section in Streamlit or show the CSV:

**Option A: Show Streamlit Eval Section** (best)
- Scroll to "Evaluation Demo" section in Streamlit
- Click "Run Evaluation"
- Show results summary (30 seconds of waiting/showing output)

**Option B: Show Results CSV** (backup if Streamlit eval section is slow)
```bash
cat evals/results/eval_results.csv | head -5
```

**Show**:
- All 20 cases: 8 normal, 4 edge, 3 long-input, 3 prompt-injection, 2 human-loop
- Pass rates: Both 100% ✅
- Judge winner: Mostly "tie" or slight advantage to one
- Tool correctness: 100%
- Safety: All prompt injections blocked ✅

**Key insight to mention**:
> "Notice that both systems passed all tests. The difference isn't in correctness—it's in overhead. Multi-agent uses more tool calls (coordination cost), but returns the same answer. This is the trade-off we're measuring."

**Time checkpoint: 8 min**

---

## Segment 5: Wrap-up & Key Takeaways (2 minutes)

### What to say:
> "So what did we learn?
>
> 1. **Same input, same output, different paths**: Both architectures give the same answer. Single is faster. Multi is more traceable and modular.
>
> 2. **Deterministic tools matter**: We don't ask the LLM to guess. Python calculates. LLM explains. This makes the system safe and debuggable.
>
> 3. **Fair evaluation**: Randomized judging, two-pass scoring, and 20 diverse test cases (including edge cases and injection attacks) ensure we're comparing apples to apples.
>
> 4. **For production, the choice is context-dependent**:
>    - Simple, fast queries? Single agent wins.
>    - Complex orchestration, need explainability, or multi-team handoffs? Multi-agent is worth the overhead.
>
> That's the core finding."

### Visual:
- **Slide**: Summary table (if you have one)
- Or just speak confidently without slides (your code is the visual proof)

**Time checkpoint: 10 min EXACTLY**

---

## Post-Demo: 5-Minute Q&A Preparation

### Likely Q&A (in order of probability):

**Q1: "Why did you choose these two architectures specifically?"**
- A: "Single-agent is the industry baseline—it's what most teams use. Multi-agent is the emerging pattern for complex reasoning. I wanted to test whether the added complexity actually helps for CRM tasks, or if it's just overhead."

**Q2: "How do you know the judge is fair?"**
- A: "Three techniques: (1) I randomize label assignment, (2) I run two passes and average, (3) I use multiple judges if LLM APIs are available. Also, the scoring rubric is explicit and published in the code, not hidden."

**Q3: "What's the most surprising finding?"**
- A: "Both systems performed equally on correctness. The trade-off is latency and tool-call count. Multi-agent adds ~5-10ms overhead for coordination but gives better explainability in traces. For a 10-second overall response time, it's negligible."

**Q4: "Can you scale this to 1000 CRM records or 100 prompts?"**
- A: "The evaluation harness scales linearly. 20 cases × 2 systems × N judges = 40N evaluations. Right now it's mock judges (instant). With real LLMs it takes ~5-10 seconds per case. To run 1000 cases, you'd want parallel execution or cached results."

**Q5: "What if the systems gave different answers?"**
- A: "Then I'd dig into the traces. The tool-call history is saved in JSON. I'd check: Did one system skip a tool? Did one system misinterpret the data? Did the prompt routing fail in multi-agent? The transparency is the point."

**Q6: "What would you do differently if you had more time?"**
- A: "Three things: (1) Integrate real LLM judges (OpenAI, Gemini) instead of mock judges, (2) Test with real CRM data from a company (currently synthetic), (3) Add prompt optimization—maybe single-agent just needs a better prompt to compete with multi-agent."

---

## Pro Tips for Live Presentation

1. **Backup plan**: If Streamlit crashes, have a pre-recorded screen recording saved locally. Point to it and say, "Let me show you the recorded run from earlier."

2. **Talk speed**: Aim for ~140 words/minute. Faster = sounds panicked. Slower = boring. Record yourself once to calibrate.

3. **Silence is okay**: After you show a result, take 2-3 seconds for the audience to absorb it. Don't fill every second with talking.

4. **One prompt**: Don't try 5 different test cases. One live run is enough. The CSV shows you tested 20.

5. **Confidence**: You built this. You know it. Speak like it. "This is the single-agent trace—notice how it calls load_crm_data, then check_duplicate_records, then returns." Clear and direct.

6. **Avoid code details**: Don't open VS Code and start explaining the agent loop or prompts. That's 15-minute depth. You have 10 minutes. The code is on GitHub if they want to see it.

---

## Video Recording Checklist

- [ ] Streamlit app running and responsive
- [ ] One test case pre-selected (duplicate accounts)
- [ ] Results CSV or Eval section cached/ready
- [ ] Backup: Screenshot of good eval results saved
- [ ] Slides (pitch deck or simple visuals)
- [ ] Quiet background, good lighting
- [ ] Audio: Clear voice, no background noise
- [ ] Video: 1080p or 720p minimum
- [ ] Upload: YouTube unlisted or MP4 file, shared with professor

---

## Timing Summary

| Segment | Duration | What |
|---------|----------|------|
| Problem & Context | 1.5 min | Why this matters |
| Architecture | 1.5 min | Single vs Multi (with diagram) |
| Live Demo | 3 min | Run both systems, show outputs |
| Evaluation | 2 min | Judge results, pass rates |
| Takeaways | 2 min | Key findings, trade-offs |
| **TOTAL** | **10 min** | |

---

## Expected Reactions & Comebacks

- **"Both systems are equally good. What's the point?"** → "Exactly. That's the finding. In this domain, simplicity wins. Multi-agent isn't worth it unless you need explainability for humans."

- **"Why not use GPT-4 instead of multiple LLMs?"** → "Cost and reproducibility. I wanted to show the approach works with different models. The judge framework is model-agnostic."

- **"This is just a fancy tool-calling system."** → "Yes, and that's the insight—for CRM data quality, structured tool calls matter more than raw language generation. Most LLM failures are prompt-routing or tool-misuse, not bad reasoning."

---

**Good luck! You've got this. 🚀**
