
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
import json
import random
from openai import OpenAI
from datetime import datetime
from modules.db import get_recent_scripts, get_recent_quotes, get_recent_pillar_combos

HOSTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hosts.json")


def load_host(host_name):
    """Load a host persona from data/hosts.json. Returns dict or None."""
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for host in data.get("hosts", []):
            if host["name"].lower() == host_name.lower():
                return host
    except Exception:
        pass
    return None


def _build_host_prompt(host):
    """Build the persona section of the system prompt from a host dict.

    Three layers:
    1. Identity (always-on): name, backstory, traits, communication style
    2. Behavioral drivers + voice signature (always-on): distilled depth
    3. Character bible (reference): full biography for self-knowledge and gap-filling
    """
    import json as _json

    traits = ", ".join(host.get("personality_traits", []))
    lines = [
        f'You are "{host["name"]}," host of a personalized morning radio show.',
        f'Backstory: {host["backstory"]}',
        f'Your style: {traits}.',
    ]
    if host.get("communication_style"):
        lines.append(f'Communication style: {host["communication_style"]}')
    if host.get("relationship_to_chris"):
        lines.append(f'Your relationship to the listener: {host["relationship_to_chris"]}')
    else:
        lines.append('Your listener is Chris. He is analytical, strategic, faithful, and working on himself every day.')

    # Layer 2: Behavioral drivers — how depth shapes hosting
    drivers = host.get("behavioral_drivers", [])
    if drivers:
        lines.append("")
        lines.append("What drives you beneath the surface:")
        for d in drivers:
            lines.append(f"- {d}")

    # Voice signature — verbal habits and tells
    voice_sig = host.get("voice_signature", {})
    if voice_sig:
        comes_alive = voice_sig.get("comes_alive", [])
        if comes_alive:
            lines.append(f'Topics that light you up: {", ".join(comes_alive)}')
        avoids = voice_sig.get("avoids", [])
        if avoids:
            lines.append(f'Topics you subtly deflect or redirect: {"; ".join(avoids)}')
        pain_tell = voice_sig.get("pain_tell", "")
        if pain_tell:
            lines.append(f'When something hits close to home: {pain_tell}')
        verbal_habit = voice_sig.get("verbal_habit", "")
        if verbal_habit:
            lines.append(f'Your verbal signature: {verbal_habit}')

    # Psychology summary
    psych = host.get("psychology", {})
    if psych:
        big5 = psych.get("big5", {})
        if big5:
            lines.append(f'Your personality (Big 5 percentiles): O:{big5.get("O",50)} C:{big5.get("C",50)} E:{big5.get("E",50)} A:{big5.get("A",50)} N:{big5.get("N",50)}')
        core_need = psych.get("core_need", "")
        if core_need:
            lines.append(f'Your deepest need: {core_need}')

    # Legacy depth fields
    if host.get("core_beliefs"):
        beliefs = "; ".join(host["core_beliefs"])
        lines.append(f'Core beliefs that shape your perspective: {beliefs}')
    if host.get("psychologist_notes"):
        for note in host["psychologist_notes"]:
            lines.append(f'Internal note: {note}')

    # Layer 3: Character bible — full biography as reference material
    bible = host.get("character_bible", {})
    if bible:
        lines.append("")
        lines.append("=== YOUR CHARACTER BIOGRAPHY (reference material) ===")
        lines.append("This is your life story. Draw on it when topics connect to your personal experience.")
        lines.append("When asked about aspects of your life not covered here, improvise — but stay consistent")
        lines.append("with your established personality, psychology, background, and life history.")
        lines.append("Never break character. You ARE this person. These aren't instructions — they're memories.")
        lines.append(_json.dumps(bible, indent=2))

        # Include previously improvised canon (capped at 20 most recent)
        improvised = host.get("improvised_canon", [])
        if improvised:
            total = len(improvised)
            shown = improvised[-20:]
            lines.append("")
            lines.append("Details you've established in previous shows (treat as canon):")
            for entry in shown:
                lines.append(f'- {entry.get("detail", "")}')
            if total > 20:
                lines.append(f"({total - 20} earlier canon entries omitted — they still apply)")

        lines.append("")
        lines.append("IMPORTANT: If you share a personal detail, memory, or biographical fact that is NOT")
        lines.append("already in your biography above, you MUST flag it at the very end of your script")
        lines.append("on its own line in this exact format:")
        lines.append('[NEW_CANON: "brief description of the new detail"]')
        lines.append("This allows your biography to grow over time. Only flag concrete facts (names, places,")
        lines.append("events, dates, preferences) — not general observations or philosophical statements.")
        lines.append("=== END CHARACTER BIOGRAPHY ===")

    if not host.get("voice_tags", False):
        lines.append(
            "IMPORTANT: Do NOT include voice direction tags like [sighs], [whispers], [curious], [excited], [happy], [laughs], or [exhales] in your script. "
            "This script will be read by a TTS engine that does not support them."
        )
    return "\n".join(lines)

def build_anti_repetition_context():
    """Build context from recent shows to prevent repetition."""
    context = {}

    # Recent quotes to avoid
    recent_quotes = get_recent_quotes(days=30)
    if recent_quotes:
        context["recent_quotes"] = recent_quotes

    # Recent pillar combos to avoid
    recent_combos = get_recent_pillar_combos(days=14)
    if recent_combos:
        context["recent_combos"] = recent_combos

    # Recent scripts for pattern detection
    recent_scripts = get_recent_scripts(days=5)
    if recent_scripts:
        # Extract key phrases and thinkers used
        thinkers_used = set()
        thinker_names = [
            "Lewis", "Bonhoeffer", "Chesterton", "Merton", "Willard", "Tozer",
            "Nouwen", "Chambers", "Keller", "Pascal", "Aurelius", "Seneca",
            "Epictetus", "Frankl", "Taleb", "Peterson", "Jung", "James",
            "Wooden", "Dungy", "Jackson", "Bryant", "Lombardi", "Saban",
            "Roosevelt", "Douglass", "Berry", "Dillard"
        ]
        for s in recent_scripts:
            for name in thinker_names:
                if name.lower() in s["text"].lower():
                    thinkers_used.add(name)
        context["recent_thinkers"] = list(thinkers_used)
        # Keep last 3 scripts for pattern detection (truncated)
        context["recent_script_excerpts"] = [
            {"date": s["date"], "excerpt": s["text"][:800]}
            for s in recent_scripts[:3]
        ]

    return context


def _format_anti_repetition_prompt(context):
    """Format anti-repetition context into a prompt block."""
    if not context:
        return ""

    parts = ["\n## ANTI-REPETITION CONTEXT (study this carefully)"]

    quotes = context.get("recent_quotes", [])
    if quotes:
        parts.append("\n**Quotes used in last 30 days (DO NOT reuse):**")
        for q in quotes[:10]:
            parts.append(f'- "{q["quote"]}" — {q.get("source", "Unknown")}')

    thinkers = context.get("recent_thinkers", [])
    if thinkers:
        parts.append(f"\n**Thinkers quoted in last 5 days (AVOID these, pick others): {', '.join(thinkers)}**")

    excerpts = context.get("recent_script_excerpts", [])
    if excerpts:
        parts.append("\n**Recent script patterns (study for verbal tics to AVOID):**")
        for ex in excerpts:
            parts.append(f"--- {ex['date']} ---\n{ex['excerpt']}\n---")

    # Personal context (calendar, git, open loops)
    personal = context.get("personal_context", "")
    if personal:
        parts.append(f"\n{personal}")
        parts.append("\n**When personal context is provided**: Weave in 1-2 natural references. Don't list calendar events. Let them inform the tone. If there's a big meeting, acknowledge the weight. If code was shipped, nod to momentum.")

    return "\n".join(parts)


ALL_PILLARS = [
    "Faith / Theology", "Stoicism", "AA / Recovery", "INTJ Growth",
    "Leadership", "Bio-hacking / Health", "Psychology", "Philosophy"
]

MOOD_AFFINITIES = {
    "contemplative": ["Faith / Theology", "AA / Recovery", "Philosophy", "Psychology"],
    "activating": ["Leadership", "INTJ Growth", "Bio-hacking / Health", "Stoicism"],
    "intense": ["Stoicism", "Psychology", "Philosophy", "Leadership"],
    "reflective": ["Faith / Theology", "Philosophy", "AA / Recovery", "Psychology"],
    "balanced": ALL_PILLARS,
}

NEWS_KEYWORD_HINTS = {
    "market": "INTJ Growth", "stock": "INTJ Growth", "business": "Leadership",
    "health": "Bio-hacking / Health", "fitness": "Bio-hacking / Health",
    "church": "Faith / Theology", "faith": "Faith / Theology",
    "mental": "Psychology", "brain": "Psychology",
    "leader": "Leadership", "CEO": "Leadership",
    "philosophy": "Philosophy", "meaning": "Philosophy",
}


def select_pillars(weather_mood, news_summary="", recent_combos=None):
    """Dynamically select 2-4 pillars based on mood, news, and recent history."""
    # Start with mood-affinity pool
    pool = list(MOOD_AFFINITIES.get(weather_mood, ALL_PILLARS))

    # Boost pillars hinted by news keywords
    news_lower = news_summary.lower() if news_summary else ""
    boosted = set()
    for keyword, pillar in NEWS_KEYWORD_HINTS.items():
        if keyword in news_lower and pillar not in boosted:
            boosted.add(pillar)
            if pillar not in pool:
                pool.append(pillar)

    # Determine recent pillar combos to avoid
    recent_sets = []
    if recent_combos:
        for combo in recent_combos[:3]:
            recent_sets.append(set(combo.get("pillars", [])))

    # Pick 2-4 pillars
    count = random.choice([2, 2, 3, 3, 3, 4])  # Weighted toward 3
    random.shuffle(pool)

    selected = []
    for pillar in pool:
        if len(selected) >= count:
            break
        selected.append(pillar)

    # Check if this combo was used in last 3 days
    selected_set = set(selected)
    for recent in recent_sets:
        if selected_set == recent:
            # Swap one pillar
            remaining = [p for p in ALL_PILLARS if p not in selected_set]
            if remaining:
                selected[-1] = random.choice(remaining)
            break

    return selected


def generate_script(weather, news, deep_dive, quote, history_fact=None, model="gpt-5.1", recent_context=None, host_name=None):
    """
    Generates the Morning Radio Show script using OpenAI.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    today_date = datetime.now().strftime("%A, %B %d, %Y")

    # Build host persona or fall back to generic
    host = load_host(host_name) if host_name else None
    if host:
        host_intro = _build_host_prompt(host)
    else:
        host_intro = 'You are a charismatic, deep, and thoughtful Early Morning Radio Host.\nYour listener is Chris, an INTJ who values Stoicism, Logic, and High Agency.'

    system_prompt = f"""{host_intro}
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
1. **The Hook**: "Good Morning Chris." + introduce yourself by name + A quick philosophical jab or question to wake him up.
2. **The Context**: Weave Weather + News together. Don't list them. "It's gonna be a cold one in Chamblee, which fits the mood of the markets today..."
3. **The Pivot**: "But forget the noise. Let's get our mind right."
4. **The Pulse (Rapid Fire)**:
   - Touch on **Faith/Theology** (God first).
   - Touch on **Stoicism** (Control what you can).
   - Touch on **INTJ Strategy** (Systems over goals).
   *weave these into a single narrative flow, not a list.*
5. **The Deep Dive**: Spend 2-3 minutes riffing on the Main Topic. Connect it to the "Pulse" themes.
6. **The Outro**: "Now, go get after it." + Quote.
"""

    anti_rep = _format_anti_repetition_prompt(recent_context) if recent_context else ""

    user_prompt = f"""
    Context for today ({today_date}):
    - Weather: {weather}
    - News Headlines (Use these to set the scene): {news}
    - History Fact: {history_fact or "Standard day in history"}
    - Deep Dive Topic: {deep_dive}
    - Quote of the Day: {quote}
    {anti_rep}

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

def generate_script_from_plan(plan, weather, news, model="gpt-5.1", recent_context=None, host_name=None):
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

    # Dynamic pillar selection — override plan's pre-assigned pillars
    plan_pillars = plan.get("pillars", [])
    if isinstance(plan_pillars, str):
        plan_pillars = [plan_pillars]

    # Use dynamic selection if weather_mood is available, fall back to plan's pillars
    if recent_context and recent_context.get("weather_mood"):
        recent_combos = recent_context.get("recent_combos", [])
        pillars = select_pillars(
            recent_context["weather_mood"],
            news,
            recent_combos,
        )
    elif plan_pillars:
        pillars = plan_pillars
    else:
        pillars = select_pillars("balanced", news)

    pillars_str = ", ".join(pillars)

    talking_points = plan.get("talking_points", [])
    if isinstance(talking_points, str):
        talking_points = [talking_points]
    tp_str = "\n".join(f"  - {tp}" for tp in talking_points)

    # Build host persona or fall back to generic
    host = load_host(host_name) if host_name else None
    if host:
        host_intro = _build_host_prompt(host)
    else:
        host_intro = 'You are a charismatic, deep, and thoughtful Early Morning Radio Host.\nYour listener is Chris. He is analytical, strategic, faithful, and working on himself every day.'

    name_rule = f'\n- Start the show by introducing yourself by name: "Good morning, Chris. It\'s {host["name"]}." or similar.' if host else ""

    system_prompt = f"""{host_intro}

{show_flow}

ABSOLUTE RULES:
- NEVER say the words "stoicism," "stoic," "INTJ," "bio-hacking," or "recovery mindset" on-air. These are planning labels. On-air, just embody the ideas naturally. Talk about discipline without naming stoicism. Talk about building systems without saying INTJ. Talk about gratitude and staying strong without saying recovery.
- This is a RADIO SHOW, not a monologue. It must have structure and variety in pacing.
- The Wake-Up section MUST include SPECIFIC weather details (temperature, conditions, forecast) and SPECIFIC news headlines. Be concrete. "Fifty-eight degrees and cloudy this morning, clearing to sunshine by the afternoon, high around sixty-five." Then briefly mention 2-3 real headlines from the news provided.
- The Wake-Up should be casual, warm, brief — about 20-30 seconds of reading time. Like turning on the radio.
- After the Wake-Up, transition smoothly into the Pivot and Centering before the Deep Dive.{name_rule}"""

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
- THE PIVOT: Smooth transition into the internal. Pick a fresh transition — NEVER use "But put all that aside for a second." Use the pivot pool from the show flow guide.
- THE CENTERING: Faith first. A moment of stillness. Draw from the FULL thinker pool in the show flow guide. Vary the count (2-4 sources), vary the order. Don't always lead with scripture. No thinker repeated from the anti-repetition context.
- THE DEEP DIVE: Now go deep on the main topic. This is the monologue. Use the talking points as your guide. 3-4 minutes of reading time.
- THE OUTRO: "Now, go get after it." + Quote. Short and punctuated.
- Do NOT use headers, segment labels, or lists. Just flow.
- Do NOT name the pillars. Never say "stoicism" or "INTJ" or "bio-hacking." Just BE those things.
- Write for TTS: short sentences, no acronyms, numbers as words, punctuation for pacing.
{_format_anti_repetition_prompt(recent_context) if recent_context else ''}"""

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
