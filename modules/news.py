"""
Fetches news headlines from NewsAPI and Google News RSS.

Sources:
- NewsAPI: Top US headlines (requires NEWS_API_KEY)
- Google News RSS: Local Atlanta news, AI/tech news (free, no key)

Output: get_all_news() returns structured dict with world, local, ai categories
"""

import requests
import os
import feedparser
from urllib.parse import quote


def get_top_headlines(api_key=None):
    """Fetches top 3 US headlines using NewsAPI."""
    if not api_key:
        api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return _get_google_news_world()

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": "us",
            "apiKey": api_key,
            "pageSize": 5,
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        articles = data.get("articles", [])
        headlines = []
        for art in articles:
            if art["title"] and "[Removed]" not in art["title"]:
                desc = art.get("description", "") or ""
                headlines.append(f"Headline: {art['title']}\n   Context: {desc}")

        return headlines[:3]
    except Exception as e:
        print(f"Error fetching NewsAPI: {e}")
        return _get_google_news_world()


def _get_google_news_world():
    """Fallback: top world headlines from Google News RSS."""
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
        headlines = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            if title:
                headlines.append(f"Headline: {title}")
        return headlines[:3] if headlines else ["World news unavailable."]
    except Exception as e:
        print(f"Error fetching Google News world: {e}")
        return ["World news unavailable."]


def get_local_news(location="Atlanta"):
    """Fetches local news headlines from Google News RSS."""
    try:
        query = quote(f"{location} Georgia")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)

        headlines = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            if title and location.lower() in title.lower():
                headlines.append(f"Local: {title}")
            elif title:
                headlines.append(f"Local: {title}")
        return headlines[:2] if headlines else [f"No local {location} news available."]
    except Exception as e:
        print(f"Error fetching local news: {e}")
        return [f"Local {location} news unavailable."]


def get_ai_news():
    """Fetches AI/tech news from Google News RSS."""
    try:
        url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)

        headlines = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            if title:
                headlines.append(f"AI/Tech: {title}")
        return headlines[:1] if headlines else ["No AI news available."]
    except Exception as e:
        print(f"Error fetching AI news: {e}")
        return ["AI news unavailable."]


def get_all_news():
    """
    Fetches all news categories and returns structured dict.

    Returns:
        dict with keys: world, local, ai, combined_summary
    """
    world = get_top_headlines()
    local = get_local_news()
    ai = get_ai_news()

    # Build combined summary for the LLM prompt
    all_headlines = world + local + ai
    combined = "; ".join(all_headlines)

    return {
        "world": world,
        "local": local,
        "ai": ai,
        "combined_summary": combined,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    result = get_all_news()
    print("=== World ===")
    for h in result["world"]:
        print(f"  {h}")
    print("\n=== Local (Atlanta) ===")
    for h in result["local"]:
        print(f"  {h}")
    print("\n=== AI/Tech ===")
    for h in result["ai"]:
        print(f"  {h}")
