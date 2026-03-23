# Daily Reflections — Project Context

## Architecture
- **Two-phase system**:
  1. **Weekly Planner** (`modules/planner.py`) — LLM analyzes prior show history, generates content outlines (topics, quotes, talking points). Stores in SQLite. Does NOT assign pillars (those are selected dynamically).
  2. **Daily Runner** (`main.py`) — Reads today's plan from SQLite, fetches live weather/news/context, dynamically selects pillars based on weather mood + news + history, generates full script, produces audio.
- **Script generation**: GPT-5.1 via OpenAI API (`modules/content.py`)
- **Show flow**: `data/show_flow.md` — injected into both planner and script generation LLM calls. Contains pivot pool, thinker pool, anti-repetition rules, and voice direction tag guide.
- **History tracking**: `data/reflections.db` (SQLite) — deduplication source for quotes, topics, pillars, recent scripts
- **Anti-repetition system**: `content.py` builds context from recent shows (quotes, thinkers, pillar combos, script excerpts) and injects it into the LLM prompt as hard constraints
- **Dynamic pillar selection**: `content.select_pillars()` — weather mood + news keywords + recent history → 2-4 pillars per day, never repeating yesterday's combo
- **Personal context**: `modules/context.py` — gathers git activity, calendar events, Gmail summary, open loops and weaves them into the show

## News Sources
- **World**: NewsAPI (requires `NEWS_API_KEY`) with Google News RSS fallback
- **Local**: Google News RSS filtered to Atlanta (via `feedparser`)
- **AI/Tech**: Google News RSS for "artificial intelligence"
- All assembled by `news.get_all_news()` → structured dict with `combined_summary`

## Host Roster & Unified Rotation
The show rotates between 6 hosts across 3 TTS engines. Selection is LRU over 14-day window via `select_host()`. Config lives in `HOST_TTS_CONFIG` dict in `main.py`.

**Canonical personas**: `~/Projects/personas/` — DO NOT edit `data/hosts.json` directly. Edit profiles in `personas/profiles/`, run `python3 build_hosts.py`. Note: Vivienne and JEJ are mlx-only hosts without entries in `hosts.json` — they use default/inline prompts.

| Name | Engine | Voice/Mode | Accent | Personality |
|------|--------|------------|--------|-------------|
| **Anaya** | ElevenLabs | `3vbrfmIQGJrswxh7ife4` | British | The Anchor. Former BBC presenter, warm, authoritative. Supports voice tags. |
| **Emma** | Kokoro | `bf_emma` | British | The Thinker. Oxford philosophy, cerebral, measured, literary. |
| **Bella** | Kokoro | `af_bella` | American | The Strategist. Operations background, direct, dry humor. |
| **Hannah** | Kokoro | `af_heart` | American | The Podcaster. Intimate, playful, warm, spiritually grounded. |
| **Vivienne** | mlx (VoiceDesign) | NL description | British | Thoughtful, cerebral, Oxford accent. Generated via Qwen3-TTS VoiceDesign. |
| **JEJ** | mlx (Clone) | `jej_0006.wav` | American | James Earl Jones voice clone. speed=0.75, 12.5s reference clip. |

- **No backend flags needed** — `python main.py` auto-selects host and uses correct engine
- **Manual override**: `--host Bella` (any host name)
- **Backend override**: `--kokoro`, `--mlx`, `--elevenlabs` force a specific engine
- Voice direction tags only generated for Anaya (ElevenLabs); stripped by Kokoro and mlx modules

## TTS Backends
1. **ElevenLabs** — Anaya voice via API (`modules/tts_elevenlabs.py`), model `eleven_v3`
2. **Kokoro** — 82M params, fast, local (`modules/tts_kokoro.py`). Voice auto-selected from host.
3. **mlx-audio (Qwen3-TTS)** — Local Apple Silicon (`modules/tts_mlx.py`). Two modes:
   - **VoiceDesign**: NL voice description → consistent speaker embedding (model: `1.7B-VoiceDesign-bf16`)
   - **Clone**: Reference audio clip → voice clone (model: `1.7B-Base-bf16`, ref: `jej_0006.wav`)
   - RTF ~0.25x (4x slower than real-time). Fine for batch, not real-time.
   - No prosody control on Base model. Speed param + reference clip selection are the only levers.
4. **Voicebox** (legacy) — Qwen3-TTS via localhost:8001 (`--voicebox`)
- Auto-fallback: ElevenLabs → Kokoro (bf_emma) if API fails

## Environment
- Python 3.12 venv at `./venv`
- `.env` contains: `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `VOICEBOX_PROFILE_ID`
- Voicebox server (if used): `cd ~/Projects/voicebox && python -m backend.main --host 127.0.0.1 --port 8001`
- Calendar/Gmail context requires ADC with `calendar.readonly` and `gmail.readonly` scopes (fails gracefully if missing)

## Key Details
- **ElevenLabs Anaya voice ID**: `3vbrfmIQGJrswxh7ife4` (British Well-Spoken & Friendly)
- **ElevenLabs JEJ voice ID** (retired): `DihGQaIZuuqae0qMrsGF`
- **Voice direction tags**: ElevenLabs v3 supports inline tags like `[sighs]`, `[whispers]`, `[curious]`, `[excited]`, `[happy]`, `[laughs]`, `[exhales]`. Only generated for Anaya (ElevenLabs). Kokoro hosts have `voice_tags: false` in hosts.json which instructs the LLM to skip them, and `tts_kokoro.py` strips any that leak through.
- **Port 8001** for Voicebox (8000 is personality test app)
- **Voicebox known issue** (legacy): 1.7B model segfaults under memory pressure. Replaced by `tts_mlx.py`.
- **mlx-audio models kept**: `1.7B-Base-bf16` (cloning), `1.7B-VoiceDesign-bf16` (Vivienne). All others deleted (~11GB freed).
- **Database**: `data/reflections.db` — tables: `history`, `weekly_plan`
- **Known issue (resolved)**: ElevenLabs returned 401s from Mar 2-17 2026, cause unknown. Key and voice were valid. Added key prefix logging to diagnose if it recurs.
- **Weather mood classification**: `weather.classify_mood()` maps temp + conditions → contemplative/activating/intense/reflective/balanced, which drives pillar selection

## CLI
```
python main.py                          # Auto-select host + engine from rotation
python main.py --plan                   # Require plan (fail if none for today)
python main.py --plan --dry-run         # Script from plan, no audio
python main.py --host Emma              # Force specific host (uses their configured engine)
python main.py --kokoro                 # Force Kokoro engine (overrides host config)
python main.py --mlx                    # Force mlx engine
python main.py --elevenlabs             # Force ElevenLabs engine
python main.py --voicebox              # Force Voicebox (legacy)
python main.py --dry-run                # Script only, no audio
python main.py --input-file path.txt    # Skip LLM, use existing script
python main.py --date 2026-03-22       # Generate for a specific date

python modules/planner.py              # Plan for today
python modules/planner.py --date 2026-02-23 --days 7  # Plan a full week
```
