# TECHNICAL SETUP GUIDE: Recording Your Demo Video

---

## PART 1: PRE-RECORDING CHECKLIST

### Streamlit App Preparation

1. **Clean up any test outputs**:
   ```bash
   cd crm-agent-comparison
   # Clear old trace files (optional, keeps it clean)
   rm -r traces/*.json  (or just leave them)
   ```

2. **Ensure all dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Streamlit**:
   ```bash
   streamlit run app.py
   ```

4. **Check URL**: `http://localhost:8501`

5. **Pre-fill a prompt** (in the app code, optional):
   Edit [app.py](app.py) line where it says:
   ```python
   prompt = st.text_area(
       "CRM prompt",
       value="Find the top data-quality issues in the CRM pipeline and summarize for a manager.",  # ← change this
       height=120,
   )
   ```
   
   Change to:
   ```python
   value="Find duplicate accounts in the CRM data.",
   ```
   
   (Or just type it in during demo—both work.)

6. **Set window size**: Open browser to 1920×1080 or 1280×720. 
   - On Mac: Hover top of window, click green button, select size
   - On Windows: Right-click title bar → Maximize
   - Zoom level: 100% (Ctrl+0 to reset)

---

## PART 2: RECORDING SOFTWARE SETUP

### Windows: Use OBS Studio (Free)

1. **Download**: https://obsproject.com/

2. **Setup**:
   - Launch OBS Studio
   - Click `+` under "Sources" → "Display Capture" → Select your monitor
   - Audio Input: USB headset or laptop mic (test first)
   - Output: MP4 format, 1080p, 30fps

3. **Settings**:
   - Settings → Output → Video bitrate: 5000 Kbps (good quality)
   - Audio bitrate: 128 Kbps
   - Encoder: Use default (usually NVENC or x264)

4. **Record**:
   - Click "Start Recording"
   - Read your script (see DEMO_SCRIPT_10MIN.md)
   - Click "Stop Recording"
   - Video saved to default folder (check settings)

### Mac: Use QuickTime (Built-in)

1. **Open**: Command + Space → type "QuickTime Player" → Enter

2. **File → New Screen Recording**

3. **Select microphone**: Dropdown menu → USB headset (or Built-in mic)

4. **Record**:
   - Click red record button
   - Do your demo
   - Command + Control + Esc to stop

### Chrome: Use Built-in Screen Recorder

1. **Open Chrome** → Press `Ctrl+Shift+Escape` → Search bar at top

2. **Type**: "screen capture" → Click extension

3. **Record**: Simple but limited quality

**Recommendation**: Use OBS (Windows) or QuickTime (Mac) for best results.

---

## PART 3: AUDIO & MICROPHONE TIPS

1. **Get a USB headset** (~$30-50):
   - Blue Yeti, Audio-Technica AT2020USB, Razer, etc.
   - Eliminates background noise

2. **Before recording**:
   - Test mic levels (input ~-18dB to -6dB is ideal)
   - Mute notifications (Slack, Teams, Discord)
   - Close browser tabs with auto-play audio
   - Find a quiet room (bedroom closet = surprisingly good)

3. **While recording**:
   - Speak clearly at 140 words per minute (not too fast)
   - Pause 2 seconds after each point (let it sink in)
   - No "um", "like", "you know"
   - Take a breath between sentences

4. **Test your voice**:
   - Do a 1-minute practice run
   - Play it back. Does it sound clear? Confident?
   - Adjust mic distance (4-6 inches from mouth)

---

## PART 4: VIDEO QUALITY CHECKLIST

Before you start recording:

- [ ] Screen resolution: 1920×1080 minimum (or 1280×720)
- [ ] Window zoom: 100%
- [ ] Streamlit text readable (not tiny)
- [ ] Mic test: Record 10 seconds, listen back, sounds good?
- [ ] No notifications visible (disable Slack, Teams, etc.)
- [ ] Battery: Laptop plugged in (do NOT run on battery—will drop frames)
- [ ] Thermal: Laptop cool (close other apps)
- [ ] Lighting: Well-lit face (window to your side, not front-backlit)
- [ ] Background: Neutral (wall, not messy desk)

---

## PART 5: RECORDING STRATEGY (THE SAFE WAY)

### Option A: Record in Segments (RECOMMENDED)

Do multiple short recordings, edit together:

1. **Segment 1** (0:00-3:00): Problem + Architecture (with slides)
2. **Segment 2** (3:00-6:00): Live Streamlit demo
3. **Segment 3** (6:00-10:00): Results + Conclusion (with slides)

**Advantage**: If one segment fails, you only re-record that part.

**How to edit together**:
- Use iMovie (Mac), Windows Photos (Windows), or free tool like OpenShot
- Just concatenate the 3 MP4 files in order
- Add title/intro slide at beginning (2 seconds)

### Option B: One Full 10-Minute Take

Go all the way through, minimal edits.

**Advantage**: No editing, faster upload.

**Disadvantage**: If you mess up at 8:30, you re-do the whole thing.

**Recommendation**: Do 3-4 full takes, pick the best one.

---

## PART 6: LIVE DEMO BACKUP PLAN

**If Streamlit crashes during your presentation**:

1. Have this screenshot saved:
   ```
   screenshots/streamlit_working.png
   ```
   Show it and say: "Here's what the output looks like."

2. Have this CSV printed or in terminal:
   ```
   evals/results/eval_results.csv
   ```
   Show the results and say: "All 20 cases passed."

3. Have this video file:
   ```
   backup_streamlit_demo.mp4
   ```
   Play it and say: "Here's a recorded run from earlier."

---

## PART 7: VIDEO FILE DELIVERY

### Format:
- **File name**: `CRM_Agent_Comparison_Demo_YourName.mp4` (or .mov)
- **Resolution**: 1920×1080 or 1280×720
- **Duration**: 10:00-10:30 (including titles/transitions)
- **Audio**: Clear, no background noise, ~-18dB to -6dB level
- **Codec**: H.264 (standard MP4)

### Upload:
- [ ] YouTube (Unlisted) — share link with professor
- [ ] Google Drive (Shared with professor)
- [ ] Dropbox (Public link)
- [ ] Submitted to LMS (Moodle, Canvas, etc.)

**Send with email**:
```
Subject: Capstone Demo Video — CRM Agent Comparison

Dear Professor,

Attached/linked is my 10-minute demo video for the capstone presentation.

Demo covers:
- Problem & architecture (1.5 min)
- Live Streamlit demo (3 min)
- Evaluation results (2 min)
- Key findings (2 min)
- Q&A ready

Link: [YouTube/Drive link]

Best regards,
[Your name]
```

---

## PART 8: TIMING & PACING GUIDE

**Read this while recording to match pace**:

### [0:00-1:30] Problem (18-25 words per 10 seconds)
- Speak SLIGHTLY SLOWER here (introduce the topic)
- Pause after each sentence

### [1:30-3:00] Architecture (20-25 words per 10 seconds)
- NORMAL PACE (they're engaged now)
- Point to diagram while speaking

### [3:00-6:00] Demo (VARY PACE)
- Pre-demo intro (slow, clear): "Let me show you..."
- During demo: QUIET (let the app speak)
- After results: MEDIUM (explain what we see)

### [6:00-8:00] Results (FAST but CLEAR)
- You know this cold. Confidence.
- Point to specific numbers in CSV

### [8:00-10:00] Conclusion (SLOW, POWERFUL)
- Final takeaways = most important
- End on strong note

---

## PART 9: EDITING (IF NEEDED)

Use free tools:
- **iMovie** (Mac): Drag MP4s in, trim, add title slide, export
- **Windows Photos** (Windows): Create story, add clips, export
- **OpenShot** (Cross-platform): More control, slightly more complex
- **Adobe Premiere Pro** (Paid): Professional, but overkill

### Simple edits to make:

1. **Add title card** (2 seconds):
   - Black background
   - White text: "CRM Agent Comparison — Capstone Demo"
   - Your name
   - Date

2. **Add closing card** (2 seconds):
   - "Questions?"
   - Your name
   - University logo

3. **Trim silences** between segments (0.5-1 second cuts)

4. **Fade between segments** (0.5 second fade)

---

## PART 10: FINAL REVIEW (DAY OF PRESENTATION)

### Before submission:
- [ ] Watch entire video once (catch any issues)
- [ ] Check audio volume (not too quiet, not loud)
- [ ] Confirm no personal info visible (no email, API keys, etc.)
- [ ] Check file size (<500 MB recommended)
- [ ] Test YouTube/Drive link works (click it yourself)
- [ ] Have local MP4 backup on USB

### Confidence check:
- ✅ Do I understand what I'm explaining? YES
- ✅ Did I test this multiple times? YES
- ✅ Can I answer follow-up questions? YES
- ✅ Do I have backup plans? YES

**You're good to go.**

---

## SAMPLE VOICE PACE EXERCISE

Read this aloud at ~140 words/minute. Should take ~10 seconds:

> "Good morning. I'm presenting a capstone project comparing two AI architectures for CRM data quality. The problem is that CRM data gets messy over time—duplicates, missing fields, inconsistent names. A human reviews this manually, which is slow and error-prone. My research question is: is one well-designed agent enough, or does a multi-agent setup give better results? That's what we're benchmarking."

Did it take ~10 seconds? Good pace!  
Faster? Slow down a bit.  
Slower? That's fine—you're being clear.

---

## LAST-MINUTE TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| Streamlit slow | Restart app, close other apps, restart computer |
| Mic muffled | Move closer (4 inches), USB mic instead of laptop mic |
| Video fuzzy | Increase OBS bitrate to 6000 Kbps, record at 1080p |
| Can't find traces | Run one eval first: `python run_eval_harness.py` |
| Results CSV empty | Re-run: `python run_eval_harness.py` in terminal |
| Audio/video out of sync | Re-export from editor, or use sync tool in Premiere |

---

## FINAL PUNCHLINE

Your demo is **10 minutes long**. Make it **10 minutes of clear, confident explanation backed by working code and real data**. You don't need fancy editing or music or effects. Just you, your project, and good audio.

Go record it. You've got this. 🎬🚀
