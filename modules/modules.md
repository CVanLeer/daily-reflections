---
important: true
status: stable
last_reviewed: 2026-01-18
review_interval_days: 90
---

This folder contains core application modules that fetch data, generate content, and synthesize audio.

## Purpose
Houses the main functional components of the Daily Reflection system:
- Data fetching (weather, news)
- Content generation (LLM script writing)
- Audio synthesis (TTS engines)

## What's inside
- `weather.py`: Fetches local weather from Open-Meteo API
- `news.py`: Fetches top US headlines from NewsAPI
- `content.py`: Generates radio show script using GPT-5.1
- `tts_kokoro.py`: Fast local TTS using Kokoro-82M
- `tts_sesame.py`: High-quality TTS using Sesame CSM-1B (slow, experimental)

## How it connects
- Called by `main.py` orchestrator
- Requires `.env` for API keys (OPENAI_API_KEY, NEWS_API_KEY)
- Outputs text scripts and audio files to `output/`

## Key workflows
1. **Generate script**: `content.generate_script(weather, news, topic, quote)`
2. **Generate audio (fast)**: `tts_kokoro.text_to_speech(text, path, voice)`
3. **Generate audio (production)**: `tts_sesame.text_to_speech(text, path)`

## Verification
- Run `python modules/content.py` to test script generation
- Run `python modules/tts_kokoro.py` to test audio synthesis
- Check `.env` exists with valid API keys
