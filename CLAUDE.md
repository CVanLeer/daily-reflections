# Daily Reflections — Project Context

## Architecture
- **Two-phase system**:
  1. **Weekly Planner** (`modules/planner.py`) — LLM analyzes prior show history, generates content outlines (pillars, quotes, topics, talking points). Stores in SQLite.
  2. **Daily Runner** (`main.py`) — Reads today's plan from SQLite, fetches live weather/news, generates full script from outline, produces audio.
- **Script generation**: GPT-5.1 via OpenAI API (`modules/content.py`)
- **Show flow**: `data/show_flow.md` — injected into both planner and script generation LLM calls
- **History tracking**: `data/reflections.db` (SQLite) — deduplication source for quotes, topics, pillars

## TTS Backends (in priority order)
1. **ElevenLabs** (default) — JEJ voice clone via API (`modules/tts_elevenlabs.py`)
2. **Kokoro** — 82M params, fast, local (`--kokoro`)
3. **Voicebox** — Qwen3-TTS 1.7B + MLX on localhost:8001 (`--voicebox`)
- Auto-fallback: ElevenLabs → Kokoro if API fails

## Environment
- Python 3.12 venv at `./venv`
- `.env` contains: `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `VOICEBOX_PROFILE_ID`
- Voicebox server (if used): `cd ~/Projects/voicebox && python -m backend.main --host 127.0.0.1 --port 8001`

## Key Details
- **ElevenLabs JEJ voice ID**: `DihGQaIZuuqae0qMrsGF`
- **Port 8001** for Voicebox (8000 is personality test app)
- **Voicebox known issue**: 1.7B model segfaults under memory pressure. ElevenLabs is now primary.
- **Database**: `data/reflections.db` — tables: `history`, `weekly_plan`

## CLI
```
python main.py                          # ElevenLabs + plan (if available), freeform if not
python main.py --plan                   # Require plan (fail if none for today)
python main.py --plan --dry-run         # Script from plan, no audio
python main.py --kokoro                 # Kokoro TTS
python main.py --voicebox              # Voicebox TTS (JEJ clone, local)
python main.py --dry-run                # Script only, no audio
python main.py --input-file path.txt    # Skip LLM, use existing script

python modules/planner.py              # Plan for today
python modules/planner.py --date 2026-02-23 --days 7  # Plan a full week
```
