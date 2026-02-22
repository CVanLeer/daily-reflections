# Daily Reflections & Morning Radio Show

**A personalized, AI-generated morning radio show that wakes you up with faith, wisdom, strategy, and the news.**

This project generates a ~6 minute audio show every morning, tailored to your interests. It combines real-time data (weather, news) with a content planner (history-aware, variety-enforcing) and high-quality Text-to-Speech via ElevenLabs.

---

## How It Works

1. **Plan** (weekly or daily): The planner analyzes past show history, selects pillars/quotes/topics, and generates content outlines. Stored in SQLite.
2. **Generate**: The daily runner reads today's plan, fetches live weather + news, and generates a full conversational script via GPT-5.1.
3. **Speak**: ElevenLabs produces audio using a James Earl Jones Jr. voice clone.

---

## Quick Start

### 1. Plan Today's Show
```bash
source venv/bin/activate
python -m modules.planner                    # Plan for today
python -m modules.planner --days 7           # Plan a full week
python -m modules.planner --date 2026-02-23  # Plan for a specific date
```

### 2. Generate Show (Default — ElevenLabs JEJ Voice Clone)
```bash
python main.py --plan              # Script + ElevenLabs audio from plan
python main.py --plan --dry-run    # Script only, no audio
python main.py                     # Uses plan if available, freeform if not
```
Output: `output/audio/daily_reflection_elevenlabs_[DATE].mp3`

### 3. Generate Show (Alternative TTS)
```bash
python main.py --kokoro                 # Kokoro (fast, local)
python main.py --kokoro --voice bf_emma # Kokoro with specific voice
python main.py --voicebox               # Voicebox (JEJ clone, local server)
python main.py --dry-run                # Script only, no audio
python main.py --input-file path.txt    # Skip LLM, use existing script
```

---

## Project Structure

```
daily-reflections/
├── main.py                  # Orchestrator: plan → weather/news → script → audio → history
├── run_show.sh              # Wrapper script for automation (activates venv)
├── .env                     # API keys (OpenAI, ElevenLabs, Voicebox)
├── requirements.txt         # Dependencies
├── modules/
│   ├── planner.py           # Weekly content planner (LLM-powered, history-aware)
│   ├── db.py                # SQLite schema + queries (history, weekly_plan)
│   ├── content.py           # Script generation (GPT-5.1)
│   ├── tts_elevenlabs.py    # ElevenLabs API TTS (default, JEJ voice clone)
│   ├── tts_kokoro.py        # Kokoro 82M local TTS (fast fallback)
│   ├── tts_voicebox.py      # Voicebox/Qwen3-TTS local TTS (voice clone)
│   ├── tts_sesame.py        # Sesame CSM-1B TTS (experimental)
│   ├── weather.py           # Weather from Open-Meteo (Chamblee, GA)
│   └── news.py              # Headlines from NewsAPI
├── data/
│   ├── reflections.db       # SQLite database (history + weekly plans)
│   ├── show_flow.md         # Show flow guide (injected into LLM prompts)
│   ├── quotes.md            # 230+ curated quotes
│   ├── topics.md            # Pillar definitions + topic reference
│   ├── cs-lewis/            # C.S. Lewis quotes and content
│   └── jordan peterson/     # Jordan Peterson affirmations
├── scripts/                 # Setup and utility scripts
└── output/                  # Generated scripts (.txt) and audio (.mp3/.wav)
```

---

## Configuration

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Script generation (GPT-5.1) |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS |
| `ELEVENLABS_VOICE_ID` | JEJ voice clone ID (default: `DihGQaIZuuqae0qMrsGF`) |
| `NEWS_API_KEY` | News headlines (optional) |
| `VOICEBOX_PROFILE_ID` | Voicebox voice profile (if using `--voicebox`) |

### Show Flow
Edit `data/show_flow.md` to change show structure, pillar definitions, variety rules, and tone. This file is injected into both the planner and script generation prompts.

### Quotes
Add new quotes to `data/quotes.md`. The planner selects from this bank with 30-day no-repeat enforcement.

---

## Technical Notes

- **Python 3.12** venv at `./venv`
- **Database**: SQLite at `data/reflections.db` — tracks show history (pillars, quotes, topics used) and weekly plans
- **Variety enforcement**: 14-day topic gap, 30-day quote gap, no same pillar combo two days in a row
- **TTS fallback**: ElevenLabs → Kokoro automatic fallback if API fails
- **Voicebox**: If using `--voicebox`, server must run on localhost:8001 (port 8000 is taken)
