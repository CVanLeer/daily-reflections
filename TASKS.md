# Daily Reflection - Theme Engine Build Tasks

## Overview
Building a theme selection engine that takes in day, weather, news, and calendar events to produce a coherent daily show with theme, quote, deep dive topic, and pulse angles.

---

## Phase 1: Data Layer

### 1.1 Convert quotes.md to quotes.json
- [ ] Parse existing quotes from `data/quotes.md`
- [ ] Create JSON structure with metadata fields:
  - `id`: unique identifier (q001, q002, etc.)
  - `text`: the quote
  - `author`: attribution
  - `themes`: array of theme tags (from our 10 themes)
  - `energy`: contemplative | grounding | activating
  - `weather_affinity`: array of weather conditions
  - `news_affinity`: array of news categories
  - `day_affinity`: array of days (optional)
- [ ] Tag all existing quotes with appropriate metadata
- [ ] Add the 10 new quotes discussed
- [ ] Validate JSON structure

### 1.2 Create deep_dives.json
- [ ] Define 30-50 deep dive topics
- [ ] Structure:
  - `id`: unique identifier (dd001, dd002, etc.)
  - `title`: the topic title
  - `themes`: array of theme tags this topic supports
  - `description`: 1-2 sentence description for context
- [ ] Ensure coverage across all 10 themes (min 3 topics per theme)

### 1.3 Create pulse_angles.json
- [ ] Define Faith/Stoic/INTJ angles for each of the 10 themes
- [ ] Structure:
  ```json
  {
    "theme_name": {
      "faith": "angle text",
      "stoic": "angle text",
      "intj": "angle text"
    }
  }
  ```
- [ ] Write compelling angle text for all 10 themes (30 total angles)

### 1.4 Create holidays.csv
- [ ] List major US holidays with dates and weights
- [ ] Structure: `date,name,weight,theme_affinity`
- [ ] Weight scale: 1-10
  - 10: Christmas, Thanksgiving, July 4th
  - 8: Easter, New Year's Day, Memorial Day
  - 6: Labor Day, MLK Day, Veterans Day
  - 4: Presidents Day, Columbus Day
  - 2: Flag Day, minor observances
- [ ] Add theme affinities (e.g., Memorial Day → resilience, gratitude)
- [ ] Include recurring dates (month/day format for annual holidays)

### 1.5 Create history.json
- [ ] Initialize empty tracking structure
- [ ] Structure:
  ```json
  {
    "quotes_used": [],
    "themes_used": [],
    "deep_dives_used": []
  }
  ```

### 1.6 Create ratings.csv
- [ ] Initialize with headers
- [ ] Structure: `date,day_of_week,theme,quote_id,deep_dive_id,rating,notes`
- [ ] Rating scale: 1-5 (filled in manually after listening)

---

## Phase 2: Theme Engine Module

### 2.1 Create modules/theme_engine.py
- [ ] Define theme constants and weights
- [ ] Implement core functions:

```python
# Core functions to implement:

def analyze_weather(weather_data: dict) -> dict:
    """Convert weather API data to mood indicators"""
    # Returns: {"condition": "rain", "temp_feel": "cold", "mood": "contemplative"}

def classify_news(headlines: list, model: str = "gpt-4.1-nano") -> list:
    """Classify news headlines by category and severity"""
    # Returns: [{"headline": "...", "category": "tragedy", "severity": "high"}, ...]

def check_calendar(date: datetime) -> dict:
    """Check for holidays/events on given date"""
    # Returns: {"holiday": "Memorial Day", "weight": 8, "theme_affinity": ["resilience", "gratitude"]}

def calculate_theme_scores(day: str, weather: dict, news: list, calendar: dict) -> dict:
    """Calculate weighted scores for each theme"""
    # Returns: {"resilience": 8.5, "agency": 3.2, "faith": 6.1, ...}

def select_theme(scores: dict, history: dict) -> str:
    """Select theme based on scores, avoiding recent repeats"""
    # Returns: "resilience"

def select_quote(theme: str, history: dict) -> dict:
    """Select quote matching theme, avoiding recent use"""
    # Returns: {"id": "q001", "text": "...", "author": "..."}

def select_deep_dive(theme: str, history: dict) -> dict:
    """Select deep dive topic matching theme"""
    # Returns: {"id": "dd001", "title": "...", "description": "..."}

def get_pulse_angles(theme: str) -> dict:
    """Get Faith/Stoic/INTJ angles for theme"""
    # Returns: {"faith": "...", "stoic": "...", "intj": "..."}

def generate_theme_package(day: str, weather: dict, news: list) -> ThemePackage:
    """Main orchestrator - returns complete theme package"""
    # Returns: ThemePackage with all selections
```

### 2.2 Define weight constants
- [ ] News severity weights
- [ ] Weather condition weights
- [ ] Day of week weights
- [ ] Holiday weights
- [ ] Theme-to-trigger mappings

### 2.3 Implement history tracking
- [ ] Load/save history.json
- [ ] Check for recent quote usage (exclude last 30 days)
- [ ] Check for recent theme usage (exclude last 3 days)
- [ ] Check for recent deep dive usage (exclude last 14 days)

### 2.4 Implement LLM tiebreaker
- [ ] When multiple themes score within threshold, use LLM to pick
- [ ] Prompt: "Given today's context: [summary], which theme resonates more: [options]?"
- [ ] Use gpt-4.1-nano for cost efficiency

---

## Phase 3: Integration

### 3.1 Update modules/content.py
- [ ] Import theme_engine
- [ ] Modify `generate_script()` to accept ThemePackage
- [ ] Update system prompt to use:
  - Selected theme
  - Selected quote
  - Deep dive topic
  - Pulse angles
- [ ] Pass all context to LLM for coherent script generation

### 3.2 Update main.py (or create run_daily.py)
- [ ] Orchestrate full flow:
  1. Fetch weather
  2. Fetch news
  3. Generate theme package
  4. Generate script
  5. Log to history.json
  6. Append to ratings.csv (empty rating)
  7. Generate audio

### 3.3 Add rating workflow
- [ ] After listening, user can run: `python rate_today.py 4 "Great theme choice"`
- [ ] Updates ratings.csv with rating and notes

---

## Phase 4: Testing & Refinement

### 4.1 Unit tests
- [ ] Test theme scoring logic
- [ ] Test quote selection with history exclusion
- [ ] Test calendar parsing
- [ ] Test news classification

### 4.2 Integration tests
- [ ] Test full flow with mock data
- [ ] Test edge cases (no news, holiday + bad weather, etc.)

### 4.3 Manual testing
- [ ] Generate 7 days of themes, review for variety
- [ ] Check that weaving works (multiple factors in narrative)
- [ ] Verify no repeat quotes within window

---

## Theme Reference

| Theme | Description | Triggers |
|-------|-------------|----------|
| resilience | Enduring hardship, growing through pain | Bad news, tragedy, cold/rain, Monday |
| agency | Taking action, controlling what you can | Clear weather, start of week |
| truth | Self-knowledge, honesty, seeking reality | Neutral days, introspection triggers |
| faith | Trust in process, divine timing | Uncertainty, heavy news, waiting periods |
| perspective | Zooming out, bigger picture | End of week, mixed signals, Friday |
| solitude | Value of alone time, inner work | Quiet news, overcast, reflective days |
| humility | Ego death, forgiveness, blame no one | Conflict news, personal failure context |
| purpose | Finding meaning, why over how | Career news, existential triggers |
| patience | Timing, waiting, not forcing | Delays, slow news, Wednesday |
| gratitude | Appreciation, enough-ness | Holidays, positive news, abundance |

---

## Weight Priority Reference

```
Priority (highest to lowest):
1. Major holiday (weight 8-10)
2. Severe news (tragedy, crisis)
3. Significant news (economic, political)
4. Severe weather
5. Minor holiday (weight 4-6)
6. Normal weather conditions
7. Day of week baseline
8. Minor holiday (weight 1-3) - flavor only
```

---

## File Structure (Target)

```
daily-reflections/
├── data/
│   ├── quotes.json          # Tagged quotes
│   ├── deep_dives.json      # Topic bank
│   ├── pulse_angles.json    # Theme -> angles mapping
│   ├── holidays.csv         # Calendar events
│   ├── history.json         # Usage tracking
│   └── ratings.csv          # Feedback log
├── modules/
│   ├── content.py           # Script generation (updated)
│   ├── theme_engine.py      # NEW: Theme selection logic
│   ├── weather.py           # Weather fetching
│   └── news.py              # News fetching
├── scripts/
│   ├── rate_today.py        # NEW: Rating CLI
│   └── tts_preprocessor.py  # TTS preprocessing
├── main.py                  # Orchestrator (updated)
└── TASKS.md                 # This file
```

---

## Notes

- All JSON files should be human-readable (indented)
- History window: 30 days for quotes, 3 days for themes, 14 days for deep dives
- Rating scale: 1 (miss) to 5 (perfect)
- News classification uses gpt-4.1-nano for cost efficiency
- LLM tiebreaker only triggers when top themes are within 1.5 points

---

*Last updated: 2025-01-18*
