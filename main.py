
"""
DOC:START
Main orchestrator for the Daily Reflection personalized morning radio show.

Purpose:
- Coordinates data fetching (weather, news), script generation (LLM), and audio synthesis (TTS)
- Provides CLI interface with --dry-run, --production, --voice, --input-file options

Inputs/Outputs:
- Inputs: API keys from .env, optional --input-file for existing scripts
- Outputs: Script files to output/scripts/, audio files to output/audio/

Side effects:
- Network calls to Open-Meteo, NewsAPI, OpenAI
- Writes files to output/ directory

Run: ./run_show.sh or python main.py [--dry-run] [--production] [--voice bf_emma]
See: README.md, modules/modules.md
DOC:END
"""

import os
import argparse
import random
import datetime
from modules import weather, news, content, tts_kokoro, tts_sesame
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

def run_show(dry_run=False, production=False, input_file=None, output_dir="output", voice="am_michael"):
    print("--- Starting Daily Reflection Generation ---")
    
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
        # 1. Gather Data (Only if generating new)
        print("1. Fetching Weather...")
        weather_data = weather.get_weather()
        weather_summary = weather_data['summary']
        
        print("2. Fetching News...")
        top_headlines = news.get_top_headlines()
        news_summary = "; ".join(top_headlines)
        
        # quote
        quote = load_random_quote("quotes.md")
        
        # topic
        deep_dive = determine_deep_dive_topic()
        
        print(f"   Context: {weather_summary} | Topic: {deep_dive}")

        # 2. Generate Script
        print("3. Generating Script with LLM...")
        
        # Construct a richer prompt context
        full_prompt_context = f"""
        Weather: {weather_summary}
        News: {news_summary}
        Deep Dive Topic: {deep_dive}
        Random Quote: "{quote}"
        """
        
        script = content.generate_script(weather_summary, news_summary, deep_dive, quote)
        
        # Save script
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        scripts_dir = os.path.join(output_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        
        dataset_path = os.path.join(scripts_dir, f"script_{today_str}.txt")
        with open(dataset_path, "w") as f:
            f.write(script)
        print(f"   Script saved to {dataset_path}")
    
    if dry_run:
        print("Dry run complete. Exiting.")
        return

    # 3. Audio Synthesis
    print("4. Synthesizing Audio...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    
    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    if production:
        print("   >>> MODE: PRODUCTION (Sesame CSM-1B) <<<")
        audio_filename = f"daily_reflection_sesame_{timestamp}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_sesame.text_to_speech(script, audio_path)
    else:
        print(f"   >>> MODE: TESTING (Kokoro) [Voice: {voice}] <<<")
        audio_filename = f"daily_reflection_kokoro_{timestamp}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        success = tts_kokoro.text_to_speech(script, audio_path, voice=voice)
    
    if success:
        print(f"SUCCESS! Show ready at: {audio_path}")
        # Here we would move to iCloud Drive
        # os.system(f"cp {audio_path} ~/Library/Mobile\ Documents/com~apple~CloudDocs/Reflections/")
    else:
        print("FAILED to generate audio.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip audio generation")
    parser.add_argument("--production", action="store_true", help="Use Sesame CSM-1B (High Quality) instead of Kokoro")
    parser.add_argument("--input-file", type=str, help="Path to existing script file to generate audio from (skips LLM generation)")
    parser.add_argument("--voice", type=str, default="am_michael", help="Kokoro voice id (e.g., am_michael, bf_emma)")
    args = parser.parse_args()
    
    from dotenv import load_dotenv
    load_dotenv()
    
    run_show(dry_run=args.dry_run, production=args.production, input_file=args.input_file, voice=args.voice)
