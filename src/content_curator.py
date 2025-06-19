# src/content_curator.py
import requests
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ContentCurator:
    """
    News API를 사용하여 최신 트렌드 및 핫이슈를 기반으로 콘텐츠 주제를 큐레이션합니다.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        if not self.api_key:
            logger.warning("News API Key is not provided. Trend analysis may be limited.")

    def get_hot_topics(self, query: str = "technology OR science OR finance", language: str = "en", num_topics: int = 3, days_ago: int = 1):
        """
        주어진 쿼리에 따라 최신 뉴스를 검색하고, 제목에서 핫 토픽을 추출합니다.
        
        Args:
            query (str): 검색할 키워드 (OR로 여러 키워드 가능).
            language (str): 뉴스 언어 (예: 'en' for English, 'ko' for Korean).
            num_topics (int): 추출할 주제의 최대 개수.
            days_ago (int): 몇 일 전까지의 뉴스를 검색할지.
            
        Returns:
            list[str]: 핫 토픽 문자열 리스트.
        """
        if not self.api_key:
            logger.error("News API Key is missing. Cannot fetch hot topics.")
            return []

        from_date = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec='seconds') + 'Z'
        params = {
            'q': query,
            'language': language,
            'from': from_date,
            'sortBy': 'relevancy', # 관련성 높은 순
            'apiKey': self.api_key,
            'pageSize': 20 # 최대 20개 기사 가져오기
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
            data = response.json()
            
            topics = set()
            for article in data.get('articles', []):
                title = article.get('title')
                if title:
                    # 간단하게 제목에서 키워드를 추출하거나, 더 정교한 NLP를 사용할 수 있습니다.
                    # 여기서는 제목을 그대로 주제로 사용하거나 첫 몇 단어를 사용합니다.
                    topic_candidate = title.split(' - ')[0].strip() # ' - Source' 부분을 제거
                    if len(topic_candidate) > 10: # 너무 짧은 제목은 제외
                        topics.add(topic_candidate)
                    if len(topics) >= num_topics:
                        break
            
            logger.info(f"Found {len(topics)} hot topics for query '{query}': {list(topics)[:num_topics]}")
            return list(topics)[:num_topics]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news from News API: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred in ContentCurator: {e}", exc_info=True)
            return []

# 테스트용 코드
if __name__ == "__main__":
    from dotenv import load_dotenv
    from src.config import setup_logging
    load_dotenv()
    setup_logging()

    news_api_key = os.environ.get("NEWS_API_KEY")
    if not news_api_key:
        print("Please set NEWS_API_KEY environment variable for local testing.")
    else:
        curator = ContentCurator(news_api_key)
        print("--- Getting hot topics (English) ---")
        topics = curator.get_hot_topics(query="AI OR cryptocurrency OR climate change", num_topics=3)
        for i, topic in enumerate(topics):
            print(f"{i+1}. {topic}")

        print("\n--- Getting hot topics (Korean - requires Korean news sources or general topics) ---")
        # NewsAPI는 한국어 뉴스 소스가 제한적일 수 있습니다.
        # 한국어 핫이슈를 원한다면 별도의 한국어 뉴스 API나 스크래핑이 필요할 수 있습니다.
        # 여기서는 일반적인 기술 키워드로 검색합니다.
        korean_topics = curator.get_hot_topics(query="기술 OR 인공지능 OR 경제", language="ko", num_topics=2)
        for i, topic in enumerate(korean_topics):
            print(f"{i+1}. {topic}")
