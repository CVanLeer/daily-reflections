"""
DOC:START
Main orchestrator for the Daily Reflection personalized morning radio show.

Purpose:
- Coordinates data fetching (weather, news), script generation (LLM), and audio synthesis (TTS)
- Supports plan-based generation (from weekly planner) or freeform generation
- CLI: --plan, --dry-run, --kokoro, --voicebox, --voice, --input-file

Inputs/Outputs:
- Inputs: API keys from .env, optional --input-file for existing scripts
- Outputs: Script files to output/scripts/, audio files to output/audio/

Side effects:
- Network calls to Open-Meteo, NewsAPI, OpenAI, ElevenLabs/Voicebox/Kokoro
- Writes files to output/ directory
- Logs show metadata to data/reflections.db

Run: ./run_show.sh or python main.py [--plan] [--dry-run] [--kokoro] [--voicebox] [--voice bf_emma]
See: README.md, modules/modules.md
DOC:END
"""

import os
import argparse
import random
import datetime
from modules import weather, news, content, tts_kokoro, tts_voicebox, tts_elevenlabs
from modules.db import init_db, get_plan_for_date, mark_plan_generated, save_history
import sys

def load_random_quote(quotes_file):
    """Parses quotes.md and returns a random quote."""
    if not os.path.exists(quotes_file):
        return "Carpe Diem."

    with open(quotes_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Simple heuristic: Split by newlines, filter empty/comments
    quotes = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    if quotes:
        return random.choice(quotes)
    return "Carpe Diem."

def determine_deep_dive_topic():
    """Returns today's deep dive topic based on day of week."""
    # Mon=0, Sun=6
    day_idx = datetime.datetime.now().weekday()
    schedule = {
        0: "Stoicism (The Obstacle is the Way)",
        1: "Theology / CS Lewis",
        2: "Jordan Peterson / Responsibility",
        3: "AA / Recovery / Gratitude",
        4: "INTJ Strategy & Professional Growth",
        5: "Bio-hacking & Health",
        6: "Free-form Synthesis & Rest"
    }
    return schedule.get(day_idx, "General Reflection")

def run_show(dry_run=False, tts_backend="elevenlabs", input_file=None,
             output_dir="output", voice="am_michael", use_plan=False):
    print("--- Starting Daily Reflection Generation ---")

    init_db()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    plan = None
    script = None
    script_path = None

    # 1. Gather Data
    if input_file:
        print(f"1. Reading Script from {input_file}...")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                script = f.read()
            print("   Script loaded successfully.")
        except Exception as e:
            print(f"Error reading input file: {e}")
            sys.exit(1)

    else:
        # Check for plan
        plan = get_plan_for_date(today_str)

        if use_plan and not plan:
            print(f"ERROR: --plan flag set but no plan found for {today_str}.")
            print("Run the planner first: python modules/planner.py")
            sys.exit(1)

        # Fetch live data
        print("1. Fetching Weather...")
        weather_data = weather.get_weather()
        weather_summary = weather_data['summary']

        print("2. Fetching News...")
        top_headlines = news.get_top_headlines()
        news_summary = "; ".join(top_headlines)

        if plan:
            # Plan-based generation
            print(f"3. Generating Script from plan (pillars: {plan.get('pillars', [])})...")
            script = content.generate_script_from_plan(plan, weather_summary, news_summary)
        else:
            # Freeform generation (original flow)
            quote = load_random_quote("quotes.md")
            deep_dive = determine_deep_dive_topic()
            print(f"   Context: {weather_summary} | Topic: {deep_dive}")
            print("3. Generating Script with LLM...")
            script = content.generate_script(weather_summary, news_summary, deep_dive, quote)

        # Save script
        scripts_dir = os.path.join(output_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)

        script_path = os.path.join(scripts_dir, f"script_{today_str}.txt")
        with open(script_path, "w") as f:
            f.write(script)
        print(f"   Script saved to {script_path}")

    if dry_run:
        print("Dry run complete. Exiting.")
        # Log history even on dry run
        if plan:
            save_history(
                show_date=today_str,
                pillars=plan.get("pillars", []),
                quote=plan.get("quote"),
                quote_source=plan.get("quote_source"),
                deep_dive_topic=plan.get("deep_dive_topic"),
                talking_points=plan.get("talking_points"),
                script_path=script_path,
            )
            mark_plan_generated(today_str)
        return

    # 4. Audio Synthesis
    print("4. Synthesizing Audio...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    audio_path = None
    success = False

    if tts_backend == "voicebox":
        print("   >>> MODE: Voicebox (JEJ voice clone) <<<")
        audio_filename = f"daily_reflection_voicebox_{timestamp}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_voicebox.text_to_speech(script, audio_path)

        if not success:
            print("   WARNING: Voicebox failed — falling back to Kokoro...")
            audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
            audio_path = os.path.join(audio_dir, audio_filename)
            success = tts_kokoro.text_to_speech(script, audio_path, voice=voice)

    elif tts_backend == "kokoro":
        print(f"   >>> MODE: Kokoro [Voice: {voice}] <<<")
        audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_kokoro.text_to_speech(script, audio_path, voice=voice)

    else:
        # Default: ElevenLabs with Kokoro fallback
        print("   >>> MODE: ElevenLabs (JEJ voice clone) <<<")
        audio_filename = f"daily_reflection_elevenlabs_{timestamp}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_elevenlabs.text_to_speech(script, audio_path)

        if not success:
            print("   WARNING: ElevenLabs failed — falling back to Kokoro...")
            audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
            audio_path = os.path.join(audio_dir, audio_filename)
            success = tts_kokoro.text_to_speech(script, audio_path, voice=voice)

    if success:
        print(f"SUCCESS! Show ready at: {audio_path}")
    else:
        print("FAILED to generate audio.")

    # 5. Log history
    if plan:
        save_history(
            show_date=today_str,
            pillars=plan.get("pillars", []),
            quote=plan.get("quote"),
            quote_source=plan.get("quote_source"),
            deep_dive_topic=plan.get("deep_dive_topic"),
            talking_points=plan.get("talking_points"),
            script_path=script_path,
            audio_path=audio_path if success else None,
        )
        mark_plan_generated(today_str)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Reflection morning radio show generator")
    parser.add_argument("--plan", action="store_true", help="Require a plan from the weekly planner (fail if none exists)")
    parser.add_argument("--dry-run", action="store_true", help="Script only, skip audio generation")
    parser.add_argument("--kokoro", action="store_true", help="Use Kokoro TTS (fast, local)")
    parser.add_argument("--voicebox", action="store_true", help="Use Voicebox TTS (JEJ clone, local)")
    parser.add_argument("--input-file", type=str, help="Path to existing script file (skips LLM generation)")
    parser.add_argument("--voice", type=str, default="am_michael", help="Kokoro voice id (e.g., am_michael, bf_emma)")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    # Determine TTS backend
    if args.voicebox:
        tts_backend = "voicebox"
    elif args.kokoro:
        tts_backend = "kokoro"
    else:
        tts_backend = "elevenlabs"  # default

    run_show(
        dry_run=args.dry_run,
        tts_backend=tts_backend,
        input_file=args.input_file,
        voice=args.voice,
        use_plan=args.plan,
    )
