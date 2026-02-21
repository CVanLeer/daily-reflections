# Daily Reflections & Morning Radio Show

**A personalized, AI-generated morning radio show that wakes you up with Stoicism, Theology, Strategy, and the News.**

This project automatically generates a 5-minute audio monologue every morning, tailored to your interests and specific "Deep Dive" topics for the day. It combines real-time data (weather, news) with a custom LLM persona ("The Voice") and high-quality Text-to-Speech.

---

## 🚀 Quick Start

### 1. Generate Today's Show (Standard/Fast)
Uses **Kokoro TTS** (runs in seconds).
```bash
./run_show.sh
```
Output: `output/daily_reflection_kokoro_[DATE].wav`

### 2. Generate Show (Production/High-Quality)
Uses **Sesame CSM-1B** (runs in ~30-60 mins).
**Warning**: Requires significant hardware resources.
```bash
./run_show.sh --production
```
Output: `output/daily_reflection_sesame_[DATE].wav`

---

## 🛠 Project Structure

```
daily-reflections/
├── main.py              # The Conductor: Orchestrates data fetching, script gen, and audio.
├── run_show.sh          # Wrapper script to run from cron/calendar (activates venv).
├── topics.md            # Your Interests: Core Pillars + Daily Topics.
├── quotes.md            # Your Inspiration: Database of quotes for the Outro.
├── .env                 # Secrets: API Keys (OPENAI_API_KEY, NEWS_API_KEY).
├── requirements.txt     # Dependencies.
├── modules/
│   ├── content.py       # The Brain: Generates script using OpenAI (GPT-5.1/4o).
│   ├── news.py          # The Eyes: Fetches top US headlines.
│   ├── weather.py       # The Skin: Fetches local weather (Chamblee, GA).
│   ├── tts_kokoro.py    # The Mouth (Fast): Standard TTS.
│   └── tts_sesame.py    # The Mouth (Pro): High-fidelity conversational TTS.
└── output/              # Where the magic happens (Generated .txt scripts and .wav audio).
```

---

## ⚙️ Configuration

### Changing the Vibe
Edit `modules/content.py` to tweak the **System Prompt**. This controls the persona (currently "Marcus Aurelius hosting Lo-Fi Radio").

### Changing Content
- **Topics**: Edit `topics.md`. The system rotates through the "Deep Dive" schedule automatically (Monday=Stoicism, etc.).
- **Quotes**: Add new quotes to `quotes.md`.

### Changing Models
- **Script**: Defaults to `gpt-5.1` (cheapest/smartest). defined in `modules/content.py`.
- **Audio**: Defaults to `Kokoro` (fastest).

---

## 🤖 Automation (Mac)

To wake up to this:

1.  **Mac Schedule**:
    - Open **Calendar.app**.
    - Create a daily event for 5:30 AM (or 1 hour before wake up if using Production mode).
    - **Alert**: Custom... -> Open File... -> Select `daily-reflections/run_show.sh`.

2.  **iPhone Alarm**:
    - Ensure your Mac syncs the `output/` folder to iCloud Drive (uncomment the `cp` line in `run_show.sh`).
    - in iOS **Shortcuts App**:
        - Automation: "When 6:00 AM" -> "Get File (icloud)" -> "Play Sound".

---

## 🧠 Technical Notes

- **Voice Chaining**: The Sesame TTS module uses a technique called "voice chaining" to ensure the speaker's voice remains consistent across the entire monologue, even though the text is chunked into small segments.
- **Hardware**: Kokoro runs efficiently on any Apple Silicon Mac. Sesame requires decent RAM/GPU overhead.
