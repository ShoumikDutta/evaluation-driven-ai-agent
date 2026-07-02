# Presentation Quick Reference Card

Print this and keep it next to you during the demo.

---

## 10-MINUTE DEMO FLOW

### [0:00-1:30] PROBLEM & CONTEXT
**Say**: "CRM data is messy. We're comparing 1 agent vs 2 agents."
**Show**: Nothing (just talk clearly) OR pitch slide #2

### [1:30-3:00] ARCHITECTURE 
**Say**: "System A: Single generalist. System B: Multi with orchestrator."
**MUST SHOW**: Architecture diagram (mermaid flowchart)
- Single: User → Agent → Tools → Response
- Multi: User → Orchestrator → Specialists → Response

### [3:00-6:00] LIVE DEMO (KEY SECTION)
**Action**: Open Streamlit app → type prompt → click "Run both"
**Prompt to use**: "Find duplicate accounts in the CRM data."
**Show these metrics**:
- ✅ Status: OK (both)
- ✅ Tools used: Same (both)
- Latency: Single 20ms, Multi 25ms
- Tool calls: Single 2, Multi 2

**Mention**: "Same answer, slightly different overhead. Traces available for debugging."

### [6:00-8:00] EVALUATION
**Say**: "Let's see if this holds across 20 test cases."
**Show**: eval_results.csv OR Streamlit eval section
- 20 cases: 8 normal + 4 edge + 3 long + 3 injection + 2 human
- Pass rate: 100% both
- All prompt injections blocked ✅
- All schema valid ✅

**Key insight**: "No major performance gap. It's about trade-offs."

### [8:00-10:00] CONCLUSION
**Say**: "Single is faster. Multi is clearer. For CRM? Single agent is enough."
**Show**: Nothing (just end strong)

---

## TIMING CHECKPOINTS (WATCH YOUR CLOCK!)

- **1:30** — You should be finishing "problem" and starting architecture
- **3:00** — Should be opening Streamlit NOW
- **6:00** — Should be showing eval results NOW
- **8:00** — Should be wrapping up NOW
- **10:00** — STOP. Q&A begins.

**If you're behind**: Skip the second test case, just show CSV results.  
**If you're ahead**: Take 10 seconds and let people absorb each output.

---

## BACKUP PLAN (IF STREAMLIT CRASHES)

1. Have screenshot saved: `screenshots/streamlit_demo.png`
2. Have pre-recorded video saved: `demo_video_backup.mp4`
3. Have CSV open in Excel as backup: `evals/results/eval_results.csv`

**Say if it happens**: "Let me show you the recording from our test run earlier." (Don't apologize, just move on.)

---

## Q&A BATTLE PLAN

### You WILL get asked:

1. **"Why these architectures?"** 
   → "Baseline (single) vs emerging pattern (multi). We measured trade-offs."

2. **"How is the judge fair?"**
   → "Randomized labels + two passes + published rubric = no hidden bias."

3. **"What's surprising?"**
   → "Same correctness. Different overhead. Single wins for simplicity."

4. **"Scale to 1000 records?"**
   → "Linear scaling. Right now: 20 cases × 2 systems × judges. Parallelizable."

5. **"What if answers differed?"**
   → "Traces are saved. I'd debug tool-calls and routing."

6. **"What next?"**
   → "Real LLM judges + real data + prompt optimization."

### You MIGHT get asked:

- "Why deterministic tools?"  
  → "Safety + reproducibility + debugging. LLM shouldn't guess numbers."

- "Open source?"  
  → "Yes, on GitHub. Reproducible evaluation framework."

- "Cost?"  
  → "Single agent ~$0.01 per query. Multi ~$0.015. Negligible difference."

---

## VOICE & DELIVERY TIPS

✅ **DO**:
- Speak at 140 words/minute (not too fast)
- Pause 2 seconds after showing results
- Make eye contact (in video: look at camera)
- Use hand gestures to point at screen
- Say "I" and "we" — own your work

❌ **DON'T**:
- Read from slides word-for-word
- Talk about code implementation details
- Use filler words ("um", "like", "you know")
- Apologize for things (just move on)
- Show more than 3 JSON blobs (too much info)

---

## VIDEO RECORDING SETUP

**Software**: 
- OBS Studio (free) or ScreenFlow (Mac) or built-in screen record

**Settings**:
- Resolution: 1920×1080 or 1280×720
- Frame rate: 30 fps
- Audio: USB headset (clear mic)
- Background: Quiet room, decent lighting

**Recording tips**:
- Do 2-3 takes. Pick the best one.
- Record Streamlit first (in case it crashes live)
- Do voiceover separately if needed (easier to edit)

---

## FILE CHECKLIST

Before presenting, verify these exist and work:

- [ ] `crm-agent-comparison/app.py` — Streamlit app
- [ ] `crm-agent-comparison/evals/eval_cases.jsonl` — 20 test cases
- [ ] `crm-agent-comparison/evals/results/eval_results.csv` — Results
- [ ] `crm-agent-comparison/docs/architecture.md` — Architecture doc
- [ ] `crm-agent-comparison/README.md` — Project overview

**To test**:
```bash
cd crm-agent-comparison
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Should load at `http://localhost:8501` with no errors.

---

## FINAL CHECKLIST (DAY BEFORE PRESENTATION)

- [ ] Streamlit app tested and working
- [ ] One demo run completed successfully
- [ ] Results CSV generated and spot-checked
- [ ] Backup video recorded and saved
- [ ] Pitch slides printed or on USB
- [ ] Presentation script memorized (first 2 min especially)
- [ ] Q&A answers written down and practiced
- [ ] Laptop fully charged
- [ ] HDMI/USB-C adapter ready
- [ ] Backup USB with files and slides

---

## ENERGY & CONFIDENCE

This is your research. You built it. You tested it. You know what it does.

The professor isn't trying to trick you. They want to see:
1. You understand the problem
2. You built a fair comparison
3. You can explain the results
4. You thought about limitations

You have all of this. **Nail the demo, the rest is easy.**

Good luck! 🚀
