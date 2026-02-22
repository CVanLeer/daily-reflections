# Daily Reflection - Build Tasks

## Overview
Two-phase content system: a **Weekly Planner** generates content outlines (pillars, quotes, topics, talking points) stored in SQLite, and a **Daily Runner** reads the plan, fetches live data, generates a full script, and produces audio via ElevenLabs.

---

## Completed

### Weekly Planner Refactor (Feb 22, 2026)
- [x] `modules/db.py` — SQLite schema (history + weekly_plan tables), CRUD functions
- [x] `modules/planner.py` — GPT-5.1 content planner with history-aware dedup
- [x] `modules/tts_elevenlabs.py` — ElevenLabs API TTS client (JEJ voice clone)
- [x] `data/show_flow.md` — Show flow guide (structure, pillars, variety rules, tone, TTS rules)
- [x] `modules/content.py` — Added `generate_script_from_plan()` alongside original `generate_script()`
- [x] `main.py` — ElevenLabs default TTS, `--plan` flag, history logging to SQLite
- [x] `.env` — Added `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`
- [x] End-to-end test: planner → dry-run → full audio (ElevenLabs JEJ clone)
- [x] Show flow refinement: radio show structure (wake-up → pivot → centering → deep dive → outro), no pillar labels on-air

### Previous (Superseded)
The original "Theme Engine" plan (Phases 1-4 below) was superseded by the Weekly Planner approach. The planner uses the LLM itself to select themes/quotes/topics with history context, rather than building a deterministic scoring engine. Key ideas preserved:
- History-based dedup (now in SQLite instead of JSON)
- Quote/topic variety windows (30-day quote, 14-day topic gaps)
- Weather/news integration (live fetch in daily runner)

---

## Phase 5: Scale + Automation (Next)

### 5.1 Scale planner to 7 days
- [ ] `generate_plan(target_date, num_days=7)` — LLM produces a full week with intentional arc
- [ ] Weekly arc logic: Monday energizes, midweek deepens, weekend reflects

### 5.2 Automation (launchd)
- [ ] launchd plist for weekly planner — runs Sunday evening
- [ ] launchd plist for daily runner — runs each morning

### 5.3 HTML review page
- [ ] After planner runs, generate simple HTML showing the week's plan
- [ ] Upload to GCS bucket, send link to Chris via Claudia Telegram bot

### 5.4 Rating workflow
- [ ] `python rate_today.py 4 "Great theme choice"` — logs feedback
- [ ] Store ratings in SQLite (new table or extend history)

---

## Theme Reference

| Pillar | Core idea |
|--------|-----------|
| Faith / Theology | God first, stewardship, C.S. Lewis, grace |
| Stoicism | Control what you can, virtue, memento mori |
| AA / Recovery | Serenity, gratitude, one day at a time |
| INTJ Growth | Systems over goals, strategic thinking |
| Leadership | Responsibility, influence, servant leadership |
| Bio-hacking / Health | Body as tool, sleep, movement, nutrition |
| Psychology | Self-knowledge, cognitive biases, motivation |
| Philosophy | First principles, meaning, purpose |

---

*Last updated: 2026-02-22*
