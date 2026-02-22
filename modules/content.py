
"""
DOC:START
Generates personalized morning radio show scripts using GPT-5.1.

Purpose:
- Constructs system/user prompts with weather, news, topic, and quote context
- Calls OpenAI Chat Completions API to generate conversational script
- Defines the "Voice" persona (Stoic radio host)

Inputs/Outputs:
- Input: weather summary, news headlines, deep_dive topic, quote, optional model override
- Output: Generated script text (string)

Side effects:
- Network call to OpenAI API (requires OPENAI_API_KEY in environment)

Run: python modules/content.py (uses test data)
See: modules/modules.md
DOC:END
"""

import os
import random
from openai import OpenAI
from datetime import datetime

def generate_script(weather, news, deep_dive, quote, history_fact=None, model="gpt-5.1"):
    """
    Generates the Morning Radio Show script using OpenAI.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Load today's topics (In a real app, this logic would be in main.py, but passing context here)
    # For now, we assume the prompt handles the structure instructions.
    
    today_date = datetime.now().strftime("%A, %B %d, %Y")
    
    # Random Quote loader simulation (since we don't have the full file parser here yet)
    # Ideally, main.py passes the specific quote.
    
    system_prompt = """You are "The Voice," a charismatic, deep, and thoughtful Late Night / Early Morning Radio Host.
Your listener is Chris, an INTJ who values Stoicism, Logic, and High Agency.
Your goal is to wake him up, orient him to the day, and provide a deep insightful spark.

**CRITICAL STYLE INSTRUCTIONS:**
- **NO VISUAL HEADERS**: Do not say "Segment 1" or "Now for the weather".
- **USE TRANSITIONS**: Flow from one topic to the next. (e.g., "Speaking of storms, let's look at the weather..." or "Now, to center ourselves before we tackle those problems...")
- **CONVERSATIONAL**: Use fillers naturally (e.g., "You know...", "Listen...", "Here's the thing...").
- **THE VIBE**: Think *Marcus Aurelius hosting a Lo-Fi Hip Hop Radio Show*. Calm, authoritative, low-pitch, warm.

**TTS OUTPUT RULES (This will be read aloud by a text-to-speech model):**
- Use punctuation intentionally for pacing: commas for short pauses, periods for full stops, ellipses for dramatic pauses.
- Avoid acronyms. Write "Amazon Web Services" not "AWS". Write "artificial intelligence" not "AI".
- Write out abbreviations: "Doctor" not "Dr.", "versus" not "vs."
- Write numbers as words for large or important numbers: "twenty twenty-five" not "2025".
- Keep sentences short to medium length. Long run-on sentences sound unnatural when spoken.
- Avoid parentheses and brackets. Rewrite as natural speech.
- Write for the ear, not the eye. If it sounds awkward read aloud, rewrite it.

**Structure (Hidden from listener, just for flow):**
1. **The Hook**: "Good Morning Chris." + A quick philosophical jab or question to wake him up.
2. **The Context**: Weave Weather + News together. Don't list them. "It's gonna be a cold one in Chamblee, which fits the mood of the markets today..."
3. **The Pivot**: "But forget the noise. Let's get our mind right."
4. **The Pulse (Rapid Fire)**:
   - Touch on **Faith/Theology** (God first). 
   - Touch on **Stoicism** (Control what you can).
   - Touch on **INTJ Strategy** (Systems over goals).
   *weave these into a single narrative flow, not a list.*
5. **The Deep Dive**: Spend 2-3 minutes riffing on the Main Topic. Connect it to the "Pulse" themes.
6. **The Outro**: "Now, go get after it." + Quote.

**Example of "Good" Flow**:
"Good morning! First things first, let's take a moment to get our mind right and center our perspective. We put God first because He does for us what we can't do for ourselves. As C.S. Lewis said...[insert quote]. Essentially what he's saying is... so when you hit that wall today, remember that."
"""

    user_prompt = f"""
    Context for today ({today_date}):
    - Weather: {weather}
    - News Headlines (Use these to set the scene): {news}
    - History Fact: {history_fact or "Standard day in history"}
    - Deep Dive Topic: {deep_dive}
    - Quote of the Day: {quote}
    
    **Instructions**:
    - Start with the "Hook".
    - Smoothly transition into Weather/News.
    - Then pivot to the "Pulse" (Faith, Stoicism, Strategy).
    - Then go DEEP into the "Deep Dive Topic": **{deep_dive}**.
    - End with the Quote.
    - **DO NOT** use headers like "Weather:" or "Deep Dive:". Just speak.
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating script: {e}"

def generate_script_from_plan(plan, weather, news, model="gpt-5.1"):
    """
    Generate a script from a weekly plan outline.

    plan dict has: pillars, deep_dive_topic, quote, quote_source,
                   talking_points, theme_connection
    """
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    today_date = datetime.now().strftime("%A, %B %d, %Y")

    # Load show flow guide for system prompt
    show_flow_path = os.path.join(os.path.dirname(__file__), "..", "data", "show_flow.md")
    try:
        with open(show_flow_path, "r", encoding="utf-8") as f:
            show_flow = f.read()
    except FileNotFoundError:
        show_flow = ""

    pillars = plan.get("pillars", [])
    if isinstance(pillars, str):
        pillars = [pillars]
    pillars_str = ", ".join(pillars)

    talking_points = plan.get("talking_points", [])
    if isinstance(talking_points, str):
        talking_points = [talking_points]
    tp_str = "\n".join(f"  - {tp}" for tp in talking_points)

    system_prompt = f"""You are "The Voice," a charismatic, deep, and thoughtful Early Morning Radio Host.
Your listener is Chris. He is analytical, strategic, faithful, and working on himself every day.

{show_flow}

ABSOLUTE RULES:
- NEVER say the words "stoicism," "stoic," "INTJ," "bio-hacking," or "recovery mindset" on-air. These are planning labels. On-air, just embody the ideas naturally. Talk about discipline without naming stoicism. Talk about building systems without saying INTJ. Talk about gratitude and staying strong without saying recovery.
- This is a RADIO SHOW, not a monologue. It must have structure and variety in pacing.
- The Wake-Up section MUST include SPECIFIC weather details (temperature, conditions, forecast) and SPECIFIC news headlines. Be concrete. "Fifty-eight degrees and cloudy this morning, clearing to sunshine by the afternoon, high around sixty-five." Then briefly mention 2-3 real headlines from the news provided.
- The Wake-Up should be casual, warm, brief — about 20-30 seconds of reading time. Like turning on the radio.
- After the Wake-Up, transition smoothly into the Pivot and Centering before the Deep Dive."""

    user_prompt = f"""Context for today ({today_date}):
- Weather: {weather}
- News Headlines: {news}
- Internal pillars (DO NOT mention these by name, just apply the concepts): {pillars_str}
- Deep Dive Topic: {plan.get('deep_dive_topic', 'General Reflection')}
- Quote of the Day: "{plan.get('quote', '')}" — {plan.get('quote_source', 'Unknown')}
- Theme Connection: {plan.get('theme_connection', '')}
- Talking Points:
{tp_str}

**Instructions**:
- Follow the show structure from the flow guide EXACTLY. Each section must be present.
- THE WAKE-UP: Start with "Good morning, Chris." Be a radio host. Give the SPECIFIC weather details — temperature, conditions, what the day looks like. Mention 2-3 actual news headlines briefly and conversationally. Keep it light, casual, warm. About 20-30 seconds of reading time.
- THE PIVOT: Smooth transition. "But put all that aside for a second." Slow down. Breathe.
- THE CENTERING: Faith first. A moment of stillness. Short scripture or wisdom. Quick-fire sparks from 2-3 sources (Bible, C.S. Lewis, coaches, philosophers). Not a lecture — just sparks.
- THE DEEP DIVE: Now go deep on the main topic. This is the monologue. Use the talking points as your guide. 3-4 minutes of reading time.
- THE OUTRO: "Now, go get after it." + Quote. Short and punctuated.
- Do NOT use headers, segment labels, or lists. Just flow.
- Do NOT name the pillars. Never say "stoicism" or "INTJ" or "bio-hacking." Just BE those things.
- Write for TTS: short sentences, no acronyms, numbers as words, punctuation for pacing."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating script: {e}"


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(generate_script("Sunny 75F", ["Tech stocks up", "New AI model released"], "Test Topic", "Test Quote"))
