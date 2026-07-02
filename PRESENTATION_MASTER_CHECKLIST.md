# PRESENTATION MASTER CHECKLIST

Your capstone presentation is 10 minutes (demo) + 5 minutes (Q&A) = 15 minutes total.

**This folder now contains 4 comprehensive guides.** Use them in this order:

---

## 📋 YOUR PRESENTATION DOCUMENTS

1. **[DEMO_SCRIPT_10MIN.md](DEMO_SCRIPT_10MIN.md)** ← START HERE
   - Full 10-minute script with timing checkpoints
   - What to say at each moment
   - Visuals to show
   - Q&A prep guide

2. **[DEMO_QUICK_REFERENCE.md](DEMO_QUICK_REFERENCE.md)** ← PRINT THIS
   - One-page quick ref to keep during recording
   - Timing checkpoints (watch your clock!)
   - Backup plan if things crash
   - Delivery tips

3. **[DEMO_VISUAL_TIMELINE.md](DEMO_VISUAL_TIMELINE.md)** ← USE WHILE RECORDING
   - Shot-by-shot breakdown of what's on screen at each moment
   - Exactly what to show and when
   - Editing tips

4. **[RECORDING_SETUP_GUIDE.md](RECORDING_SETUP_GUIDE.md)** ← TECHNICAL SETUP
   - How to record video (OBS, QuickTime, etc.)
   - Audio & microphone tips
   - Video quality checklist
   - File delivery format

---

## 🎯 YOUR 10-MINUTE DEMO BREAKDOWN

| Time | Segment | Duration | What To Do |
|------|---------|----------|-----------|
| 0:00-1:30 | **Problem & Context** | 1:30 | Speak about messy CRM data. Show or mention pitch slide. |
| 1:30-3:00 | **Architecture** | 1:30 | Show architecture diagram. Explain single vs multi paths. |
| 3:00-6:00 | **Live Demo** | 3:00 | Open Streamlit app, run test case, show results. |
| 6:00-8:00 | **Evaluation Results** | 2:00 | Show CSV with 20 test cases. Explain judge methodology. |
| 8:00-10:00 | **Conclusion** | 2:00 | Key findings, trade-offs, final thoughts. |

---

## ✅ PRE-RECORDING CHECKLIST (DO THIS FIRST)

### Day 1: Preparation

- [ ] Read DEMO_SCRIPT_10MIN.md completely
- [ ] Memorize the opening (0:00-1:30) word-for-word
- [ ] Memorize the architecture explanation
- [ ] Know the 3 key findings cold
- [ ] Practice Q&A answers (see DEMO_SCRIPT_10MIN.md)

### Day 2: Technical Setup

- [ ] Install OBS Studio (Windows) or use QuickTime (Mac)
- [ ] Test USB microphone or laptop mic
- [ ] Start Streamlit app: `streamlit run app.py`
- [ ] Open browser to http://localhost:8501
- [ ] Set screen to 1920×1080 or 1280×720
- [ ] Disable notifications (Slack, Teams, Discord)
- [ ] Plug in laptop (do NOT record on battery)

### Day 3: Do a Dry Run

- [ ] Record a 2-minute test segment
- [ ] Play it back. Does it sound clear? Confident?
- [ ] Adjust mic distance, volume, pace
- [ ] DO NOT use this for final submission

### Day 4: Record Final Video

- [ ] Do 2-3 full 10-minute takes
- [ ] Pick the best one
- [ ] Export as MP4 (1920×1080, H.264 codec)
- [ ] File size should be <500 MB
- [ ] Watch entire video once before submitting

### Day 5: Submit

- [ ] Upload to YouTube (Unlisted) or Google Drive
- [ ] Send link to professor with subject line
- [ ] Have local MP4 backup on USB
- [ ] Keep source file (for edits if needed)

---

## 🎬 RECORDING COMMAND (Quick Start)

```bash
# 1. Navigate to project
cd crm-agent-comparison

# 2. Activate environment
.venv\Scripts\activate  # Windows
# OR
source .venv/bin/activate  # Mac/Linux

# 3. Start Streamlit
streamlit run app.py

# 4. Open second terminal and run eval (optional, to pre-generate results)
python run_eval_harness.py

# 5. Open OBS Studio (or QuickTime) and start recording
# 6. Read script from DEMO_SCRIPT_10MIN.md
# 7. Stop recording
# 8. Export as MP4
```

---

## 🎯 WHAT YOUR PROFESSOR WANTS TO SEE

From the feedback meeting, the professor emphasized:

✅ **Live demo or video backup**  
✅ **Explanation of AI evaluation harness (two-pass, randomized judging)**  
✅ **How you interpret results**  
✅ **Architecture choice reasoning**  
✅ **Tool setup and workflow**  

**Your demo covers all of this.** ✓

---

## 📊 TIMING GUIDE (WATCH YOUR CLOCK)

Wear a watch or have a timer visible:

- **1:30** — Should be finishing intro, moving to architecture
- **3:00** — Should be opening Streamlit NOW
- **6:00** — Should be showing eval results NOW
- **8:00** — Should be summarizing NOW
- **10:00** — STOP. Q&A begins.

**If you're behind by 30 seconds at any checkpoint, skip the next section and jump ahead.**

---

## 💡 PRO TIPS

1. **Speak at 140 words/minute** (natural, not rushed)
2. **Pause 2 seconds** after showing results (let it sink in)
3. **Point with cursor** when highlighting data
4. **No filler words** ("um", "like", "you know")
5. **Confidence** — You built this. Own it.
6. **One demo case** — Don't run 5 different prompts, just one
7. **Traces matter** — Mention they exist, don't drill into JSON details
8. **Judge randomization is key** — Emphasize the two-pass, shuffled labels approach

---

## ❌ WHAT NOT TO DO

- ❌ Don't read from slides word-for-word
- ❌ Don't show more than 3 JSON objects (overwhelming)
- ❌ Don't explain code implementation in detail
- ❌ Don't try to run live demo if internet is shaky (use video instead)
- ❌ Don't apologize if something goes wrong (just move on)
- ❌ Don't spend more than 30 seconds on one slide

---

## 🆘 IF THINGS GO WRONG

### Streamlit app won't start?
```bash
# Restart Python environment
deactivate
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Can't find eval results?
```bash
python run_eval_harness.py
```

### Video recording is laggy?
- Close all other apps
- Plug in laptop
- Reduce resolution to 1280×720
- Use lower bitrate (4500 Kbps instead of 5000)

### Audio is too quiet?
- Move mic closer (4-6 inches from mouth)
- Boost mic volume in OBS (right-click audio source → Advanced)
- USB headset is better than laptop mic

### Video file is huge (>1 GB)?
- Reduce bitrate from 5000 Kbps to 3000 Kbps
- Re-record at 720p instead of 1080p

---

## 📝 Q&A PREPARATION (5 MINUTES)

Be ready for these 6 questions (see DEMO_SCRIPT_10MIN.md for answers):

1. **"Why these two architectures?"**
2. **"How is the judge fair?"**
3. **"What's the most surprising finding?"**
4. **"Can you scale this?"**
5. **"What if results were different?"**
6. **"What would you do with more time?"**

Plus likely follow-ups on:
- Why deterministic tools
- Cost per query
- Open source availability

---

## 🎬 YOUR FILES

These exist now in the `crm-agent-comparison/` folder:

**Presentation Guides** (NEW):
- `DEMO_SCRIPT_10MIN.md` ← Script with full timing
- `DEMO_QUICK_REFERENCE.md` ← One-page ref card
- `DEMO_VISUAL_TIMELINE.md` ← Shot-by-shot breakdown
- `RECORDING_SETUP_GUIDE.md` ← Technical setup
- `PRESENTATION_MASTER_CHECKLIST.md` ← This file

**Code/Data** (Existing):
- `app.py` ← Streamlit frontend
- `run_comparison.py` ← Run single demo
- `run_eval_harness.py` ← Run all 20 test cases
- `evals/eval_cases.jsonl` ← 20 test cases
- `evals/judge.py` ← LLM judge with randomization
- `evals/results/eval_results.csv` ← Results from June 30
- `docs/architecture.md` ← Architecture documentation
- `docs/eval_design.md` ← Evaluation methodology

**Backup Visuals** (Create these):
- `screenshots/streamlit_demo.png` ← Screenshot as backup
- `backup_video.mp4` ← Pre-recorded Streamlit demo
- Pitch slide deck (if you have one)

---

## 🚀 THE TIMELINE

**This week (June 30 - July 4)**:
- Mon-Tue: Read scripts, practice delivery
- Wed-Thu: Do dry runs, test equipment
- Fri: Record final video, submit

**Next week (July 7-11)**:
- Your presentation slot (professor said first half if possible)
- 10 minutes: demo video + live Q&A
- 5 minutes: questions from class
- Done!

---

## 🎯 FINAL MINDSET

You've done the hard work. You:
- ✅ Built two working agent systems
- ✅ Ran 20 test cases
- ✅ Implemented LLM judge with randomization and two passes
- ✅ Generated results and verified everything works
- ✅ Created documentation

Now you just need to **explain it clearly for 10 minutes**.

You've explained it to your professor already (hence the feedback meeting).
You can do it again on video.

**Be confident. Be clear. Be concise.**

---

## 📞 LAST RESORT: If You're Stuck

**Script won't run?** → Restart environment, reinstall packages  
**Streamlit won't load?** → Kill process, wait 5 seconds, restart  
**Don't know what to say?** → Open DEMO_SCRIPT_10MIN.md and read it aloud  
**Forgot timing?** → Check the timing checkpoints every 2 minutes  
**Audio bad?** → Move mic closer, use headset, re-record  
**Video glitchy?** → Reduce OBS bitrate, close other apps  
**Out of time?** → Skip detailed code explanation, focus on results  

**Everything else?** → Backup plan is a pre-recorded video. You have that.

---

## ✨ YOU'VE GOT THIS

This is a solid project. The implementation is clean. The evaluation is rigorous. The findings are clear.

Now go record a 10-minute demo and ace your presentation.

**Start with DEMO_SCRIPT_10MIN.md. That's your north star.**

Good luck! 🚀

---

**Questions?** Check the relevant guide:
- "What do I say at X:XX?" → DEMO_SCRIPT_10MIN.md
- "What's on screen at X:XX?" → DEMO_VISUAL_TIMELINE.md
- "How do I record?" → RECORDING_SETUP_GUIDE.md
- "Is there a backup plan?" → DEMO_QUICK_REFERENCE.md
