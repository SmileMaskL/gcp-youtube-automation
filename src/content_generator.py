# src/content_generator.py

import logging
import random
import json
import google.generativeai as genai
from newsapi import NewsApiClient

logging.basicConfig(level=logging.INFO)

def generate_content_and_script(gemini_api_key, news_api_key, openai_api_keys):
    """
    인기 검색어 기반 유튜브 Shorts 콘텐츠 생성
    """
    newsapi = NewsApiClient(api_key=news_api_key)
    headlines = newsapi.get_top_headlines(language='en', country='us', category='technology')
    articles = headlines["articles"]

    context = ""
    if articles:
        selected = random.choice(articles)
        context = f"Trending topic: {selected['title']} - {selected.get('description','')}"
    else:
        context = "Trending topic: AI, space, future technology"

    prompt = f"""
    Generate YouTube Shorts content JSON for:
    {context}
    Format:
    {{
        "title": "...",
        "description": "...",
        "script": "...",
        "keywords": ["...", "..."]
    }}
    """

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    content = json.loads(response.text.strip())
    return content
