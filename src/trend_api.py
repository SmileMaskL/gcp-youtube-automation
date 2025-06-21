# src/trend_api.py
import logging
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)

class NewsAPI:
    def __init__(self, api_key: str):
        if not api_key:
            logger.error("News API Key is not provided.")
            raise ValueError("News API Key is missing.")
        self.newsapi = NewsApiClient(api_key=api_key)

    def get_trending_topics(self, language: str = "ko", country: str = "kr", count: int = 5) -> list:
        """
        최신 트렌드 뉴스를 가져와서 주제 목록을 반환합니다.
        
        Args:
            language (str): 뉴스 언어 (기본값: 'ko').
            country (str): 뉴스 국가 (기본값: 'kr').
            count (int): 가져올 주제의 최대 개수.

        Returns:
            list: 트렌드 주제 (문자열) 목록.
        """
        try:
            # NewsAPI의 top_headlines는 특정 카테고리의 인기 기사를 가져올 수 있습니다.
            # 모든 카테고리에서 가장 인기 있는 기사를 가져오는 방법은 제한적일 수 있습니다.
            # 여기서는 'general' 카테고리에서 최신 기사를 가져오고 제목을 주제로 사용합니다.
            # 실제 트렌드 분석을 위해서는 Google Trends API 또는 더 복잡한 로직이 필요할 수 있습니다.
            top_headlines = self.newsapi.get_top_headlines(
                language=language,
                country=country,
                category='general' # 또는 business, entertainment, health, science, sports, technology
            )
            
            topics = []
            if top_headlines and top_headlines['articles']:
                for article in top_headlines['articles']:
                    title = article.get('title')
                    if title and title not in topics: # 중복 제거
                        topics.append(title)
                    if len(topics) >= count:
                        break
            
            logger.info(f"Successfully fetched {len(topics)} trending topics from NewsAPI.")
            return topics[:count]

        except Exception as e:
            logger.error(f"Failed to fetch trending topics from NewsAPI: {e}", exc_info=True)
            return []
