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

## Host Roster
The show rotates between 4 named host personalities. Each has a backstory and persona injected into the LLM system prompt via `data/hosts.json` (symlink → `~/Projects/personas/hosts.json`).

**Canonical source**: `~/Projects/personas/` — DO NOT edit `data/hosts.json` directly. Edit the profile in `personas/profiles/`, run `python3 build_hosts.py`, and the symlink picks up changes automatically. Persona depth (core beliefs, psychologist notes) evolves through Forge sessions and flows into the LLM prompt.

| Name | Engine | Voice ID | Accent | Personality |
|------|--------|----------|--------|-------------|
| **Anaya** | ElevenLabs | `3vbrfmIQGJrswxh7ife4` | British | The Anchor. Former BBC presenter, warm, authoritative, well-spoken. Supports voice direction tags. |
| **Emma** | Kokoro | `bf_emma` | British | The Thinker. Oxford philosophy background, cerebral, measured, literary. |
| **Bella** | Kokoro | `af_bella` | American | The Strategist. Operations background, direct, grounded, practical, dry humor. |
| **Hannah** | Kokoro | `af_heart` | American | The Podcaster. Building her following, intimate, playful, warm, a little flirty, spiritually grounded. |

- **ElevenLabs backend** → always Anaya
- **Kokoro backend** → rotates Emma/Bella/Hannah (LRU from `get_recent_hosts()`)
- **Manual override**: `--host Bella` (any host name)
- Voice direction tags (`[sighs]`, `[whispers]`, etc.) only generated for Anaya; stripped by `tts_kokoro.py` as safety net

## TTS Backends (in priority order)
1. **ElevenLabs** (default) — Anaya voice via API (`modules/tts_elevenlabs.py`), model `eleven_v3`
2. **Kokoro** — 82M params, fast, local (`--kokoro`). Voice auto-selected from host.
3. **Voicebox** — Qwen3-TTS 1.7B + MLX on localhost:8001 (`--voicebox`)
- Auto-fallback: ElevenLabs → Kokoro (bf_emma) if API fails
- Explicit `--kokoro` uses the selected host's voice (or `--voice` override)

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
- **Voicebox known issue**: 1.7B model segfaults under memory pressure. ElevenLabs is now primary.
- **Database**: `data/reflections.db` — tables: `history`, `weekly_plan`
- **Known issue (resolved)**: ElevenLabs returned 401s from Mar 2-17 2026, cause unknown. Key and voice were valid. Added key prefix logging to diagnose if it recurs.
- **Weather mood classification**: `weather.classify_mood()` maps temp + conditions → contemplative/activating/intense/reflective/balanced, which drives pillar selection

## CLI
```
python main.py                          # ElevenLabs (Anaya) + plan (if available), freeform if not
python main.py --plan                   # Require plan (fail if none for today)
python main.py --plan --dry-run         # Script from plan, no audio
python main.py --kokoro                 # Kokoro TTS (auto-rotates Emma/Bella/Hannah)
python main.py --kokoro --host Emma     # Kokoro with specific host
python main.py --host Anaya             # Manual host override (any backend)
python main.py --voicebox              # Voicebox TTS (JEJ clone, local)
python main.py --dry-run                # Script only, no audio
python main.py --input-file path.txt    # Skip LLM, use existing script
python main.py --date 2026-03-22       # Generate for a specific date

python modules/planner.py              # Plan for today
python modules/planner.py --date 2026-02-23 --days 7  # Plan a full week
```
