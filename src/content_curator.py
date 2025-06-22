import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ContentCurator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        if not self.api_key:
            logger.warning("News API Key is not provided. Trend analysis may be limited.")
    
    def get_hot_topics(self, query: str = "technology OR science OR finance", 
                      language: str = "en", num_topics: int = 3, days_ago: int = 1):
        if not self.api_key:
            logger.error("News API Key is missing. Cannot fetch hot topics.")
            return []

        from_date = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec='seconds') + 'Z'
        params = {
            'q': query,
            'language': language,
            'from': from_date,
            'sortBy': 'relevancy',
            'apiKey': self.api_key,
            'pageSize': 20
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            topics = set()
            for article in data.get('articles', []):
                title = article.get('title')
                if title:
                    topic_candidate = title.split(' - ')[0].strip()
                    if len(topic_candidate) > 10:
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
