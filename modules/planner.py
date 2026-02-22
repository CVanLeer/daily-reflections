"""
Weekly content planner for Daily Reflections.

Analyzes show history, selects pillars/quotes/topics, and generates
content outlines for upcoming shows. Stores plans in SQLite.

Run: python modules/planner.py [--date YYYY-MM-DD] [--days N]
"""

import os
import json
import datetime
from openai import OpenAI
from modules.db import init_db, get_history, save_weekly_plan


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_file(path):
    """Load a text file, return empty string if missing."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _load_content_sources():
    """Load all reference content for the planner."""
    show_flow = _load_file(os.path.join(DATA_DIR, "show_flow.md"))
    quotes = _load_file(os.path.join(DATA_DIR, "quotes.md"))
    topics = _load_file(os.path.join(DATA_DIR, "topics.md"))
    cs_lewis = _load_file(os.path.join(DATA_DIR, "cs-lewis", "cs-lewis_quotes.md"))
    jp_affirmations = _load_file(os.path.join(DATA_DIR, "jordan peterson", "daily_affirmations.md"))
    return show_flow, quotes, topics, cs_lewis, jp_affirmations


def _format_history(history):
    """Format history list into a readable summary for the LLM."""
    if not history:
        return "No prior show history available."

    lines = []
    for h in history:
        pillars = h.get("pillars", [])
        if isinstance(pillars, str):
            pillars = [pillars]
        lines.append(
            f"- {h['show_date']}: pillars={pillars}, "
            f"quote=\"{h.get('quote', 'N/A')}\", "
            f"topic=\"{h.get('deep_dive_topic', 'N/A')}\""
        )
    return "\n".join(lines)


def generate_plan(target_date, num_days=1):
    """
    Generate content plans for num_days starting at target_date.

    1. Load show_flow.md as reference
    2. Load last 90 days of history from SQLite
    3. Load quotes + topic sources
    4. Call GPT-5.1 with JSON response format
    5. Save plans to weekly_plan table
    6. Return the plans
    """
    init_db()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Load all content sources
    show_flow, quotes, topics, cs_lewis, jp_affirmations = _load_content_sources()
    history = get_history(days=90)
    history_summary = _format_history(history)

    # Build target dates
    start = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    target_days = []
    for i in range(num_days):
        d = start + datetime.timedelta(days=i)
        target_days.append({
            "date": d.strftime("%Y-%m-%d"),
            "day_of_week": d.strftime("%A"),
        })

    targets_str = "\n".join(
        f"- {t['date']} ({t['day_of_week']})" for t in target_days
    )

    system_prompt = """You are a content planner for a daily morning radio show called "Daily Reflections."
Your job is to select pillars, topics, quotes, and talking points that avoid repetition and create variety.

You MUST follow the show flow guide and variety rules provided. Study the history carefully to avoid repeats.

Respond with valid JSON only. No markdown, no code fences."""

    user_prompt = f"""## Show Flow Guide
{show_flow}

## Available Quotes
{quotes}

## Topic Reference
{topics}

## C.S. Lewis Quotes (use when faith/theology pillar is selected)
{cs_lewis[:3000]}

## Jordan Peterson Affirmations (use when psychology/INTJ pillar is selected)
{jp_affirmations[:3000]}

## Show History (last 90 days — avoid repeating these)
{history_summary}

## Target Date(s)
{targets_str}

## Instructions
Generate a content plan for each target date. For each day, select:
- 2-4 pillars that fit well together (from the show flow guide)
- A deep dive topic (specific and interesting, not generic)
- A quote from the available quotes (exact text + attribution)
- 3-4 talking points / angles for the script writer
- A theme connection explaining how the pillars relate

Return this exact JSON structure:
{{
  "plans": [
    {{
      "day_date": "YYYY-MM-DD",
      "day_of_week": "Monday",
      "pillars": ["stoicism", "bio-hacking"],
      "deep_dive_topic": "Specific topic title — with a hook",
      "quote": "Exact quote text from the quotes bank",
      "quote_source": "Attribution",
      "talking_points": [
        "First talking point with specific angle",
        "Second talking point",
        "Third talking point"
      ],
      "theme_connection": "How the pillars connect to each other and the topic"
    }}
  ]
}}"""

    print(f"Generating plan for {num_days} day(s) starting {target_date}...")

    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )

        result = json.loads(response.choices[0].message.content)
        plans = result.get("plans", [])

        if not plans:
            print("Error: LLM returned no plans.")
            return []

        # Compute week_start (Sunday of the target week)
        start_dt = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        days_since_sunday = (start_dt.weekday() + 1) % 7
        week_start = (start_dt - datetime.timedelta(days=days_since_sunday)).strftime("%Y-%m-%d")

        # Save to database
        save_weekly_plan(week_start, plans)
        print(f"Saved {len(plans)} plan(s) to database.")

        return plans

    except Exception as e:
        print(f"Error generating plan: {e}")
        return []


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate content plans for Daily Reflections")
    parser.add_argument("--date", type=str,
                        default=datetime.datetime.now().strftime("%Y-%m-%d"),
                        help="Target date (YYYY-MM-DD, default: today)")
    parser.add_argument("--days", type=int, default=1,
                        help="Number of days to plan (default: 1)")
    args = parser.parse_args()

    plans = generate_plan(args.date, args.days)
    if plans:
        print("\n--- Generated Plan(s) ---")
        print(json.dumps(plans, indent=2))
    else:
        print("No plans generated.")
