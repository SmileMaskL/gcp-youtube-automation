# src/trend_api.py
import requests
import logging

logger = logging.getLogger(__name__)

class NewsAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        if not self.api_key:
            logger.error("News API Key is not provided.")
            raise ValueError("News API Key is required.")

    def get_trending_topics(self, count: int = 5):
        """NewsAPI에서 최신 트렌드 토픽을 가져옵니다."""
        # 'everything' 엔드포인트를 사용하여 최신 기사 검색
        # 'q' 파라미터를 사용하지 않고, 'top-headlines'에서 인기 있는 기사를 가져올 수도 있습니다.
        # 여기서는 'top-headlines'의 일반적인 트렌드를 활용합니다.
        
        # 특정 국가의 트렌드를 원하면 'country' 파라미터 사용 (예: 'kr' for South Korea)
        # category, q, language 등 다양한 필터를 조합하여 원하는 뉴스 필터링
        params = {
            "country": "us", # 미국 뉴스에서 트렌드를 가져옴 (글로벌 트렌드에 가까움)
            "apiKey": self.api_key,
            "pageSize": count * 2 # 요청하는 개수보다 더 많이 가져와서 중복 제거 및 필터링
        }
        
        # 'top-headlines' 엔드포인트를 사용하여 트렌드 분석
        # NewsAPI는 직접적인 '트렌딩 토픽' API를 제공하지 않으므로, 
        # 최근 인기 있는 기사들을 분석하여 트렌드를 유추해야 합니다.
        # 여기서는 간단하게 상위 기사들의 제목에서 키워드를 추출하는 방식을 사용합니다.
        
        url = f"{self.base_url}/top-headlines"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status() # HTTP 에러 발생 시 예외
            data = response.json()
            
            articles = data.get('articles', [])
            if not articles:
                logger.warning("No articles found from NewsAPI.")
                return []

            topics = []
            seen_topics = set()
            for article in articles:
                title = article.get('title')
                if title:
                    # 간단한 키워드 추출 (여기서는 단순히 제목을 토픽으로 사용)
                    # 실제로는 NLTK 등을 사용하여 키워드를 추출하고 필터링하는 로직이 필요
                    topic = title.split(' - ')[0].strip() # '기사 제목 - 언론사' 형식에서 제목만 추출
                    
                    # 이미 처리된 토픽이 아니고, 너무 짧거나 일반적이지 않은 토픽만 추가
                    if len(topic) > 10 and topic.lower() not in seen_topics and "재생" not in topic.lower() and "광고" not in topic.lower():
                        topics.append(topic)
                        seen_topics.add(topic.lower())
                        if len(topics) >= count:
                            break
            
            logger.info(f"Successfully retrieved {len(topics)} trending topics.")
            return topics

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending topics from NewsAPI: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred in NewsAPI: {e}")
            return []
