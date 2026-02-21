# Daily Reflections & Morning Radio Show

**A personalized, AI-generated morning radio show that wakes you up with Stoicism, Theology, Strategy, and the News.**

This project automatically generates a 5-minute audio monologue every morning, tailored to your interests and specific "Deep Dive" topics for the day. It combines real-time data (weather, news) with a custom LLM persona ("The Voice") and high-quality Text-to-Speech.

---

## Quick Start

### 1. Generate Today's Show (Default — Voicebox JEJ Voice Clone)
Uses **Voicebox** (Qwen3-TTS + MLX, James Earl Jones voice clone). Falls back to Kokoro if server is down.
```bash
./run_show.sh
```
Output: `output/audio/daily_reflection_voicebox_[DATE].wav`

### 2. Generate Show (Kokoro — Fast)
Uses **Kokoro TTS** (82M params, runs in seconds).
```bash
./run_show.sh --kokoro
./run_show.sh --kokoro --voice bf_emma  # specific voice
```
Output: `output/audio/daily_reflection_kokoro_[DATE].wav`

### 3. Generate Show (Sesame — High Quality)
Uses **Sesame CSM-1B** (runs in ~30-60 mins).
```bash
./run_show.sh --sesame
```
Output: `output/audio/daily_reflection_sesame_[DATE].wav`

### 4. Script Only (No Audio)
```bash
./run_show.sh --dry-run
```

---

## Voicebox Setup

The Voicebox backend must be running before generating audio with the default TTS.

### 1. Start the Voicebox server
```bash
cd ~/Projects/voicebox/backend
source venv/bin/activate
python -m backend.main --host 127.0.0.1 --port 8000
```

### 2. Create the JEJ voice profile (one-time)
```bash
cd ~/Projects/daily-reflections
source venv/bin/activate
python scripts/setup_voicebox_profile.py
```

This uploads 91 James Earl Jones training clips and saves the profile ID to `.env`.

---

## Project Structure

```
daily-reflections/
├── main.py              # The Conductor: Orchestrates data fetching, script gen, and audio.
├── run_show.sh          # Wrapper script to run from cron/calendar (activates venv).
├── topics.md            # Your Interests: Core Pillars + Daily Topics.
├── quotes.md            # Your Inspiration: Database of quotes for the Outro.
├── .env                 # Secrets: API Keys + VOICEBOX_PROFILE_ID.
├── requirements.txt     # Dependencies.
├── modules/
│   ├── content.py       # The Brain: Generates script using OpenAI (GPT-5.1/4o).
│   ├── news.py          # The Eyes: Fetches top US headlines.
│   ├── weather.py       # The Skin: Fetches local weather (Chamblee, GA).
│   ├── tts_voicebox.py  # The Mouth (Default): Voicebox/Qwen3-TTS voice clone.
│   ├── tts_kokoro.py    # The Mouth (Fast): Kokoro 82M local TTS.
│   └── tts_sesame.py    # The Mouth (Pro): Sesame CSM-1B high-fidelity TTS.
├── scripts/
│   └── setup_voicebox_profile.py  # One-time JEJ voice profile setup.
└── output/              # Generated .txt scripts and .wav audio.
```

---

## Configuration

### Changing the Vibe
Edit `modules/content.py` to tweak the **System Prompt**. This controls the persona (currently "Marcus Aurelius hosting Lo-Fi Radio").

### Changing Content
- **Topics**: Edit `topics.md`. The system rotates through the "Deep Dive" schedule automatically (Monday=Stoicism, etc.).
- **Quotes**: Add new quotes to `quotes.md`.

### Changing Models
- **Script**: Defaults to `gpt-5.1` (cheapest/smartest). defined in `modules/content.py`.
- **Audio**: Defaults to `Voicebox` (JEJ voice clone). Use `--kokoro` for fast local, `--sesame` for highest quality.

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Script generation (GPT-5.1) |
| `NEWS_API_KEY` | News headlines |
| `VOICEBOX_URL` | Voicebox server (default: `http://localhost:8000`) |
| `VOICEBOX_PROFILE_ID` | JEJ voice profile ID (set by setup script) |

---

## Automation (Mac)

To wake up to this:

1.  **Mac Schedule**:
    - Open **Calendar.app**.
    - Create a daily event for 5:30 AM (or 1 hour before wake up if using Sesame).
    - **Alert**: Custom... -> Open File... -> Select `daily-reflections/run_show.sh`.

2.  **iPhone Alarm**:
    - Ensure your Mac syncs the `output/` folder to iCloud Drive (uncomment the `cp` line in `run_show.sh`).
    - in iOS **Shortcuts App**:
        - Automation: "When 6:00 AM" -> "Get File (icloud)" -> "Play Sound".

---

## Technical Notes

- **Voice Cloning**: Voicebox uses Qwen3-TTS with MLX acceleration. The JEJ profile uses 91 training clips from "To Be A Drum" audiobook for voice cloning.
- **Fallback**: If Voicebox server is unreachable, the default mode automatically falls back to Kokoro with a warning.
- **Voice Chaining**: The Sesame TTS module uses voice chaining to ensure consistent speaker identity across chunked segments.
- **Hardware**: Kokoro runs efficiently on any Apple Silicon Mac. Sesame requires decent RAM/GPU overhead. Voicebox benefits from MLX acceleration on Apple Silicon.
