
"""
DOC:START
Fetches top US news headlines from NewsAPI.

Purpose:
- Gets top 3 US headlines using NewsAPI
- Filters out "[Removed]" placeholder titles
- Falls back gracefully if API key missing or request fails

Inputs/Outputs:
- Input: Optional api_key (defaults to NEWS_API_KEY from environment)
- Output: List of headline strings

Side effects:
- Network call to newsapi.org (requires NEWS_API_KEY)

Run: python modules/news.py
See: modules/modules.md
DOC:END
"""

import requests
import os

def get_top_headlines(api_key=None):
    """
    Fetches top 3 US headlines using NewsAPI.
    """
    if not api_key:
        api_key = os.getenv("NEWS_API_KEY")
        
    if not api_key:
        return ["News API Key missing - checking RSS instead."]

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": "us",
            "apiKey": api_key,
            "pageSize": 5  # Get 5, return top 3 valid ones
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        articles = data.get('articles', [])
        headlines = []
        for art in articles:
            # Filter out [Removed] or empty titles
            if art['title'] and "[Removed]" not in art['title']:
                # Adding description provides more context for the Host to riff on
                desc = art.get('description', '') or ""
                headlines.append(f"Headline: {art['title']}\n   Context: {desc}")
                
        return headlines[:3]
    except Exception as e:
        print(f"Error fetching news: {e}")
        return ["Error fetching top headlines."]

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(get_top_headlines())
