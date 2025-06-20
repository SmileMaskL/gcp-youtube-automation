import requests
import json
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_trending_news(api_key: str, country='kr', language='ko') -> str:
    """
    News API에서 현재 대한민국 (또는 지정된 국가/언어)의 트렌딩 뉴스 헤드라인을 가져옵니다.
    """
    if not api_key:
        logger.error("News API Key is not provided.")
        return "오늘의 인기 주제"

    url = f"https://newsapi.org/v2/top-headlines?country={country}&language={language}&apiKey={api_key}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = data.get('articles', [])
        if not articles:
            logger.warning("No trending articles found from News API.")
            return "최신 인기 뉴스, 오늘 이슈"

        selected_article = random.choice(articles)
        title = selected_article.get('title', "오늘의 흥미로운 소식")
        
        if ' - ' in title:
            title = title.split(' - ')[0]
        
        logger.info(f"Successfully fetched trending news: {title}")
        return title

    except Exception as e:
        logger.error(f"An error occurred while fetching news: {e}")
        return "오늘의 인기 토픽, 최신 정보"

def get_trending_topics(api_key: str = None) -> list:
    """
    트렌딩 토픽을 가져오는 함수 (기본값 제공)
    """
    try:
        if api_key:
            news = get_trending_news(api_key)
            return [news]
        else:
            return ["최신 트렌드", "인기 주제", "오늘의 화제"]
    except Exception as e:
        logger.error(f"Error in get_trending_topics: {e}")
        return ["인기 있는 주제", "최신 동향"]
