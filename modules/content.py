
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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(generate_script("Sunny 75F", ["Tech stocks up", "New AI model released"], "Test Topic", "Test Quote"))
