# Daily Reflections — Project Context

## Architecture
- **Script generation**: GPT-5.1 via OpenAI API (`modules/content.py`)
- **TTS backends** (in priority order):
  1. **Voicebox** (default) — Qwen3-TTS 1.7B + MLX on localhost:8001, JEJ voice clone
  2. **Kokoro** — 82M params, fast, local (`--kokoro`)
  3. **Sesame CSM-1B** — slow, high quality (`--sesame`)
- Auto-fallback: Voicebox -> Kokoro if server unreachable

## Environment
- Python 3.12 venv at `./venv`
- `.env` contains: `OPENAI_API_KEY`, `NEWS_API_KEY`, `VOICEBOX_PROFILE_ID`, `VOICEBOX_URL`
- Voicebox server must run separately: `cd ~/Projects/voicebox && python -m backend.main --host 127.0.0.1 --port 8001`

## Key Details
- **Port 8001** for Voicebox (8000 is personality test app)
- **JEJ profile ID**: `eec39811-11cb-4c22-bfe9-60fee91cbdeb` (91 training clips from "To Be A Drum")
- **Voicebox API limit**: 5000 chars per `/generate` call. `tts_voicebox.py` chunks at 4500.
- **Known issue**: 1.7B model segfaults under memory pressure on Mac Mini. May need to reduce `MAX_CHARS` to ~1000 or use smaller model.

## CLI
```
python main.py                          # Voicebox (default, JEJ voice)
python main.py --kokoro                 # Kokoro (fast)
python main.py --kokoro --voice bf_emma # Kokoro with specific voice
python main.py --sesame                 # Sesame CSM-1B (slow, high quality)
python main.py --dry-run                # Script only, no audio
python main.py --input-file path.txt    # Skip LLM, use existing script
```
