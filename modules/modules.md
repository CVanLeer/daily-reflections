---
important: true
status: stable
last_reviewed: 2026-02-22
review_interval_days: 90
---

This folder contains core application modules that fetch data, plan content, generate scripts, and synthesize audio.

## Purpose
Houses the main functional components of the Daily Reflection system:
- Content planning (LLM-powered weekly planner)
- Data storage (SQLite history + plans)
- Data fetching (weather, news)
- Content generation (LLM script writing)
- Audio synthesis (TTS engines)

## What's inside
- `planner.py`: Weekly content planner — selects pillars, quotes, topics with history-aware dedup
- `db.py`: SQLite database (history + weekly_plan tables) at `data/reflections.db`
- `content.py`: Generates radio show script using GPT-5.1 (freeform or plan-based)
- `weather.py`: Fetches local weather from Open-Meteo API
- `news.py`: Fetches top US headlines from NewsAPI
- `tts_elevenlabs.py`: ElevenLabs API TTS (default, JEJ voice clone)
- `tts_kokoro.py`: Fast local TTS using Kokoro-82M
- `tts_voicebox.py`: Local TTS using Voicebox/Qwen3-TTS (JEJ voice clone, requires server)
- `tts_sesame.py`: High-quality TTS using Sesame CSM-1B (slow, experimental)

## How it connects
- Called by `main.py` orchestrator
- `planner.py` can also run standalone: `python -m modules.planner`
- Requires `.env` for API keys (OPENAI_API_KEY, ELEVENLABS_API_KEY)
- Uses `data/show_flow.md` as LLM context for both planning and script generation
- Outputs text scripts and audio files to `output/`

## Key workflows
1. **Plan content**: `python -m modules.planner` → saves to SQLite
2. **Generate script from plan**: `content.generate_script_from_plan(plan, weather, news)`
3. **Generate script freeform**: `content.generate_script(weather, news, topic, quote)`
4. **Generate audio (default)**: `tts_elevenlabs.text_to_speech(text, path)`
5. **Generate audio (fast)**: `tts_kokoro.text_to_speech(text, path, voice)`

## Verification
- `python -c "from modules.db import init_db; init_db()"` — creates database
- `python -m modules.planner` — generates and saves a content plan
- `python main.py --plan --dry-run` — generates script from plan, no audio
