# src/video_script_generator.py

import logging
from datetime import datetime
from newsapi import NewsApiClient
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_script_from_news(newsapi_key, openai_keys=None, gemini_key=None, topic="latest technology"):
    """
    NewsAPI → GPT-4o(OpenAI) or Gemini → Script dict 반환
    """

    # 1. NewsAPI에서 뉴스 가져오기
    newsapi = NewsApiClient(api_key=newsapi_key)
    articles = newsapi.get_everything(q=topic, language='en', sort_by='publishedAt', page_size=1)
    logger.info(f"✅ NewsAPI에서 '{topic}' 기사 {len(articles['articles'])}개 획득")

    if not articles["articles"]:
        raise Exception("NewsAPI에서 기사를 찾을 수 없습니다.")

    first_article = articles["articles"][0]
    news_content = first_article["description"] or first_article["title"]
    logger.info(f"DEBUG: News summary: {news_content}")

    # 2. 프롬프트 생성
    prompt = f"""
You are a concise YouTube Shorts script generator.
Generate an engaging script (max 100 words) summarizing this news:
"{news_content}"
Output only the script.
"""

    # 3. OpenAI GPT-4o 시도
    if openai_keys:
        try:
            openai_client = OpenAI(api_key=openai_keys[0])
            completion = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            script = completion.choices[0].message.content.strip()
            logger.info("✅ GPT-4o 스크립트 생성 성공")
            return {
                "script": script,
                "title": f"{first_article['title']} | Shorts",
                "search_keywords": topic
            }
        except Exception as e:
            logger.warning(f"⚠️ GPT-4o 실패: {e}")

    # 4. Gemini 시도
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            script = response.text.strip()
            logger.info("✅ Gemini 스크립트 생성 성공")
            return {
                "script": script,
                "title": f"{first_article['title']} | Shorts",
                "search_keywords": topic
            }
        except Exception as e:
            logger.error(f"❌ Gemini 실패: {e}")
            raise Exception("Gemini에서도 스크립트 생성 실패.")

    raise Exception("모든 AI 모델에서 스크립트 생성 실패.")
