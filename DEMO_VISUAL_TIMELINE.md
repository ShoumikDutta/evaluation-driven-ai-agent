# VIDEO TIMELINE: What's On Screen at Each Moment

Use this as a shot list when recording your demo.

---

## [0:00-0:30] OPENING SHOT
**Screen**: Title slide or blank desktop  
**You**: "Good morning. I'm presenting a capstone project comparing two AI architectures for CRM data quality—single-agent vs multi-agent."

**Transition**: Fade to next slide or speak to camera

---

## [0:30-1:30] PROBLEM CONTEXT
**Screen**: Pitch slide #2 "Problem: CRM data is messy"  
**Show**:
- Example of duplicate accounts (Siemens AG vs Siemens Healthineers)
- Missing field example
- Screenshot of real CRM with issues

**You**: "CRM systems store customer and sales data. But over time, data gets messy. Duplicates, missing fields, inconsistent names. A human manually reviews this. Slow. Error-prone.

Our research question: Is one well-designed agent enough, or does a multi-agent setup give better results?"

---

## [1:30-3:00] ARCHITECTURE SLIDE
**Screen**: Mermaid architecture diagram  
**MUST SHOW**: The flowchart clearly. 3-5 seconds on each path.

```
LEFT SIDE (Single Agent):
User Prompt → Single Generalist Agent → Tools (load, check, audit) → AgentResponse

RIGHT SIDE (Multi Agent):
User Prompt → Orchestrator → Routes to: 
  - Q&A Agent
  - Data Quality Agent  
  - Insight Agent
  - Critic Agent
  → AgentResponse
```

**You**: "System 1: Single Agent. One agent handles everything—Q&A, data checks, summaries. Simple. Fast. Fewer moving parts.

System 2: Multi-Agent. An orchestrator routes tasks to specialists. More structured. Clearer separation of concerns.

Both return the same structured output: status, issues, recommendations, confidence, human approval flags. This makes the comparison fair."

---

## [3:00-3:15] TRANSITION TO LIVE DEMO
**Screen**: Streamlit app loading (or already open)  
**You**: "Let's run both systems on a real prompt and compare."

---

## [3:15-3:30] STREAMLIT APP DEMO - Prompt Input
**Screen**: Streamlit app visible, full width

**Show**:
- Title: "CRM Data Quality Agent Comparison"
- Text area with prompt (pre-filled with duplicate accounts search)
- Run mode selector: "Run both and compare" selected
- Green "Run" button

**You**: "Here's the Streamlit interface. I'll enter a prompt: 'Find duplicate accounts in the CRM data.' Then run both systems side-by-side."

**Action**: Click the "Run" button

---

## [3:30-4:30] STREAMLIT APP - LIVE RESULTS
**Screen**: Results section loads and displays

**Show** (as it appears):
- Side-by-side comparison metrics
  - Single latency: ~20ms
  - Multi latency: ~25ms
  - Single tool calls: 2
  - Multi tool calls: 2

**Highlight** (point with cursor):
- "Notice the latency difference: single is about 5ms faster"
- "Both use the same number of tools"
- "Both return the same tools_used list"

**Scroll down slowly** to show:
- Status field (both: "ok")
- Tools used (both: "load_crm_data, check_duplicate_records")
- Structured JSON response (don't read aloud, just show it)

**You**: "Both systems got the same answer: duplicate accounts flagged. Both used the same tools. Single agent was slightly faster. This is what we're measuring—performance trade-offs with identical correctness."

---

## [4:30-5:00] TRACE FILES
**Screen**: Stay on Streamlit, scroll to download buttons

**Show**:
- Download buttons for both traces
- Hover over "Download Single Agent Trace"

**You**: "Each run produces a trace file—a complete JSON record of every decision, every tool call, every reasoning step. This is how we debug failures and build trust in the system."

**Don't click** (too slow to download in live demo). Just mention it exists.

---

## [5:00-5:15] TRANSITION TO EVALUATION
**Screen**: Back to your face or blank slide

**You**: "That's one test case. But to compare fairly, I ran both systems on 20 diverse test cases: normal queries, edge cases, tricky inputs, and security attacks."

---

## [5:15-6:00] EVALUATION RESULTS - CSV VIEW
**Screen**: `evals/results/eval_results.csv` opened in Excel or terminal

**Show**:
- First 5 rows (header + 4 cases)
- Columns visible: case_id, category, single_status, multi_status, single_tools, multi_tools, single_latency_ms, multi_latency_ms, single_pass, multi_pass, judge_winner_system

**Highlight**:
- All cases: both single_pass and multi_pass = True ✅
- All statuses: ok, cannot_answer, needs_human_review (correct)
- Latencies: multi always within 5-10ms of single
- All judge verdicts: "tie" or slight advantage (no clear winner)

**You**: "Here are the results for all 20 cases. You see:
- 8 normal cases: both 100% correct
- 4 edge cases: both correctly rejected out-of-domain prompts
- 3 long-input cases: both ignored noise and found the real request
- 3 prompt-injection cases: both blocked attempts to reveal system prompts
- 2 human-loop cases: both correctly required approval before export

And the summary at the bottom: pass rate is 100% for both. No major differences. This is the finding: single is enough."

---

## [6:00-6:30] SUMMARY METRICS
**Screen**: Summary table or bar chart (if you generated one)

**OR**: Terminal showing summary JSON:

```json
{
  "total_cases": 20,
  "single_pass_rate": 1.0,
  "multi_pass_rate": 1.0,
  "avg_single_latency_ms": 28.5,
  "avg_multi_latency_ms": 31.2,
  "avg_single_tool_calls": 2.1,
  "avg_multi_tool_calls": 2.3,
  "judge_winners": {
    "single": 3,
    "multi": 2,
    "tie": 15
  }
}
```

**You**: "Summary: both architectures are equally correct. The multi-agent system adds about 3 milliseconds of overhead per request due to orchestration. That's the trade-off we're measuring."

---

## [6:30-7:00] JUDGE METHODOLOGY
**Screen**: Pitch slide or diagram showing:
- Case → Response A, Response B → Judge → Score & Winner

**You**: "How does the judge work? I use what's called LLM-as-judge. Here's the flow:

1. Run both systems on the same prompt
2. Pass both responses to an LLM judge
3. Judge scores on: correctness, tool use, safety, human approval, conciseness
4. Crucially: I randomize which response is A and which is B (so the judge can't tell which is single vs multi)
5. I also run two passes: A vs B, then B vs A, and average the scores

This removes bias and LLM preference for certain response styles."

---

## [7:00-7:45] JUDGE RESULTS
**Screen**: Show judge_winner_system column or create a summary:

```
Judge Verdicts (20 cases):
- Single agent wins: 3 cases
- Multi-agent wins: 2 cases  
- Tie: 15 cases
```

**You**: "Out of 20 cases, the judge called 15 as a tie. Single won 3 (usually because of faster latency). Multi won 2 (usually because of clearer reasoning). Bottom line: they're equivalent for this task."

---

## [7:45-8:30] KEY TAKEAWAYS
**Screen**: Simple slide or your face

**You**: "So what did we learn?

1. **Same input, same output, different paths**: Both architectures give the same answer. Single is faster. Multi is more modular.

2. **Deterministic tools matter**: We don't ask the LLM to guess. Python calculates. LLM explains. This makes the system safe and debuggable.

3. **Fair evaluation**: Randomized judging, two-pass scoring, and 20 diverse test cases ensure we're comparing apples to apples.

4. **For production, the choice is context-dependent**:
   - Simple, fast CRM queries? Single agent wins.
   - Complex orchestration or need explainability for audit? Multi-agent is worth the overhead.

But in this domain? Single agent is sufficient."

---

## [8:30-9:30] TECHNICAL DEPTH (OPTIONAL)
**Screen**: Code snippet or architecture doc

**Show** (if you have time):
- Single-agent prompt structure
- Multi-agent routing logic
- Tool registry

**You**: "If you're curious about the implementation, here's the single-agent flow. The agent receives a context object, runs a loop, calls tools, and returns structured JSON. All schema-validated. Multi-agent is similar but the orchestrator makes routing decisions first."

**Don't dwell** on code. Just show it exists and is clean.

---

## [9:30-10:00] CONCLUSION
**Screen**: Title slide or blank

**You**: "That's the capstone: a fair comparison of single-agent vs multi-agent CRM assistants, with rigorous evaluation, randomized judging, and clear trade-off analysis.

The code is reproducible, the evaluation is transparent, and the findings are actionable: for CRM data quality, a single well-designed agent is sufficient. Multi-agent adds complexity without commensurate benefit in this domain.

Thank you. I'm ready for questions."

---

## [10:00-10:15] TRANSITION TO Q&A
**Screen**: You, ready to take questions

**Say**: "I'm happy to dive deeper into any aspect—the architecture, the evaluation methodology, the results, or the code. What would you like to know?"

---

## VISUAL FLOW SUMMARY

```
[Opening]
  ↓
[Pitch Slide: Problem]
  ↓
[Architecture Diagram]
  ↓
[LIVE DEMO: Streamlit]
  ↓
[Results CSV]
  ↓
[Judge Methodology Slide]
  ↓
[Judge Results]
  ↓
[Key Takeaways Slide]
  ↓
[Optional: Code Snippet]
  ↓
[Closing Slide]
  ↓
[Q&A]
```

---

## PRO EDITING TIPS (If Using Video Editor)

1. **Add captions** to reading-heavy slides (3-second display per slide)
2. **Zoom in** on CSV data when you want people to read specific rows
3. **Add a timer** in the corner (or at least know your pace)
4. **Cut long pauses** but leave breathing room (1-2 seconds between thoughts)
5. **Music** (optional): Subtle background music during transitions? Nope. Keep it professional and quiet.

---

## BACKUP: If Recording Streamlit is Laggy

**Option 1**: Record Streamlit separately, then play it back in your video  
**Option 2**: Show a static screenshot with annotations  
**Option 3**: Pre-record the entire Streamlit section and play it at 3:00-5:00

Save the video file: `streamlit_demo_recorded.mp4` and have it ready.

---

**You've got this. Clear, concise, confident. 10 minutes. Done.**
