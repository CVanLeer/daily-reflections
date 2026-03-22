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
from modules import weather, news, content, tts_kokoro, tts_voicebox, tts_elevenlabs, notify, context
from modules.db import init_db, get_plan_for_date, mark_plan_generated, save_history, get_recent_hosts
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

def pick_freeform_topic():
    """Pick a topic dynamically for freeform (no-plan) generation."""
    import random
    topics = [
        "Building discipline as infrastructure, not willpower",
        "The difference between being busy and being productive",
        "Why discomfort is the cost of admission to growth",
        "What it means to steward your time like it's borrowed",
        "The compounding power of small daily decisions",
        "Silence as a strategic advantage",
        "How to lead when you'd rather be building",
        "The relationship between gratitude and ambition",
        "Why the best systems are invisible",
        "What your habits reveal about your actual priorities",
        "The art of finishing — why starting is cheap",
        "How to think in decades while acting in days",
        "Why certainty is the enemy of learning",
        "The cost of keeping your options open forever",
    ]
    return random.choice(topics)

def select_host(tts_backend, manual_host=None):
    """Select the host for today's show based on TTS backend and rotation history."""
    if manual_host:
        host = content.load_host(manual_host)
        if host:
            return host["name"]
        print(f"WARNING: Host '{manual_host}' not found in hosts.json, using auto-selection.")

    if tts_backend == "elevenlabs":
        return "Anaya"

    # Kokoro: rotate between Emma, Bella, Hannah
    kokoro_hosts = ["Emma", "Bella", "Hannah"]
    recent = get_recent_hosts(days=7)

    # Pick the least-recently-used Kokoro host
    for host_name in kokoro_hosts:
        if host_name not in recent:
            return host_name

    # All used recently — pick the one used longest ago
    for host_name in reversed(recent):
        if host_name in kokoro_hosts:
            # This was the earliest (oldest) usage — the others are more recent
            remaining = [h for h in kokoro_hosts if h != host_name]
            return random.choice(remaining) if remaining else kokoro_hosts[0]

    return random.choice(kokoro_hosts)


def run_show(dry_run=False, tts_backend="elevenlabs", input_file=None,
             output_dir="output", voice="am_michael", use_plan=False,
             target_date=None, manual_host=None):
    print("--- Starting Daily Reflection Generation ---")

    init_db()
    today_str = target_date or datetime.datetime.now().strftime("%Y-%m-%d")
    plan = None
    script = None
    script_path = None

    # Select host
    host_name = select_host(tts_backend, manual_host)
    host_data = content.load_host(host_name)
    if host_data:
        print(f"   Host: {host_name} ({host_data['engine']}, {host_data['accent']})")
        # Override voice to match host
        if host_data["engine"] == "kokoro":
            voice = host_data["voice_id"]
    else:
        print(f"   Host: {host_name} (no persona found)")

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

        print("2. Fetching News (world + local + AI)...")
        news_data = news.get_all_news()
        news_summary = news_data["combined_summary"]

        # Gather personal context (git, calendar, email, open loops)
        print("   Gathering personal context...")
        personal_context = context.gather_all_context()

        # Build anti-repetition context + weather mood
        print("   Building anti-repetition context...")
        recent_context = content.build_anti_repetition_context()
        recent_context["weather_mood"] = weather_data.get("mood", "balanced")
        recent_context["personal_context"] = personal_context.get("formatted_prompt_section", "")

        if plan:
            # Plan-based generation
            print(f"3. Generating Script from plan (pillars: {plan.get('pillars', [])})...")
            script = content.generate_script_from_plan(plan, weather_summary, news_summary, recent_context=recent_context, host_name=host_name)
        else:
            # Freeform generation (original flow)
            quote = load_random_quote("quotes.md")
            deep_dive = pick_freeform_topic()
            print(f"   Context: {weather_summary} | Topic: {deep_dive}")
            print("3. Generating Script with LLM...")
            script = content.generate_script(weather_summary, news_summary, deep_dive, quote, recent_context=recent_context, host_name=host_name)

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
                host=host_name,
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
            print("   WARNING: Voicebox failed — falling back to Kokoro (bf_emma)...")
            audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
            audio_path = os.path.join(audio_dir, audio_filename)
            success = tts_kokoro.text_to_speech(script, audio_path, voice="bf_emma")

    elif tts_backend == "kokoro":
        print(f"   >>> MODE: Kokoro [Voice: {voice}] <<<")
        audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_kokoro.text_to_speech(script, audio_path, voice=voice)

    else:
        # Default: ElevenLabs with Kokoro fallback
        print("   >>> MODE: ElevenLabs (Anaya) <<<")
        audio_filename = f"daily_reflection_elevenlabs_{timestamp}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_elevenlabs.text_to_speech(script, audio_path)

        if not success:
            print("   WARNING: ElevenLabs failed — falling back to Kokoro (bf_emma)...")
            audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
            audio_path = os.path.join(audio_dir, audio_filename)
            success = tts_kokoro.text_to_speech(script, audio_path, voice="bf_emma")

    if success:
        print(f"SUCCESS! Show ready at: {audio_path}")

        # 5. Send via Telegram
        print("5. Sending to Telegram...")
        topic = plan.get("deep_dive_topic", "Daily Reflection") if plan else "Daily Reflection"
        pillars = ", ".join(plan.get("pillars", [])) if plan else ""
        summary = f"🌅 *Daily Reflection — {today_str}*\n_{topic}_"
        if pillars:
            summary += f"\nPillars: {pillars}"
        notify.send_telegram(audio_path, summary)
    else:
        print("FAILED to generate audio.")

    # 6. Log history
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
            host=host_name,
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
    parser.add_argument("--host", type=str, default=None, help="Host name (Anaya, Emma, Bella, Hannah)")
    parser.add_argument("--date", type=str, default=None, help="Target date (YYYY-MM-DD, default: today)")
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
        target_date=args.date,
        manual_host=args.host,
    )
