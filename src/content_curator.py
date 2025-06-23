# src/content_curator.py
import logging
import requests
from bs4 import BeautifulSoup
import random

logger = logging.getLogger(__name__)


class ContentCurator:
    def __init__(self, news_api_key):
        self.news_api_key = news_api_key
        self.news_api_base_url = "[https://newsapi.org/v2/top-headlines](https://newsapi.org/v2/top-headlines)"
        logger.info("ContentCurator initialized.")

    def get_trending_news(self, country='us', category=None, query=None, page_size=10):
        """
        Fetches trending news headlines using NewsAPI.
        """
        params = {
            'apiKey': self.news_api_key,
            'country': country,
            'pageSize': page_size
        }
        if category:
            params['category'] = category
        if query:
            params['q'] = query

        try:
            logger.info(f"Fetching trending news with params: {params}")
            response = requests.get(self.news_api_base_url, params=params)
            response.raise_for_status()
            data = response.json()
            articles = data.get('articles', [])
            logger.info(f"Found {len(articles)} trending news articles.")
            return articles
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending news: {e}", exc_info=True)
            return []
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred in get_trending_news: {e}",
                        exc_info=True)
            return []

    def extract_content_from_url(self, url):
        """
        Extracts main content from a given URL using BeautifulSoup.
        """
        try:
            logger.info(f"Extracting content from URL: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            text_content = ' '.join([p.get_text() for p in paragraphs])
            logger.info(f"Content extracted. Length: {len(text_content)} characters.")
            return text_content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL content: {e}", exc_info=True)
            return ""
        except Exception as e:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.error(f"An unexpected error occurred in extract_content_from_url: {e}",
                        exc_info=True)
            return ""

    def get_random_news_topic(self, country='us', category=None):
        """
        Fetches trending news and returns a random article's title and description.
        """
        articles = self.get_trending_news(country=country, category=category, page_size=5)
        if articles:
            selected_article = random.choice(articles)
            title = selected_article.get('title', "No Title")
            description = selected_article.get('description', "No Description")
            logger.info(f"Selected news topic: '{title}'")
            return {"title": title, "content": description}
        return {"title": "No News Available", "content": "Could not fetch trending news."}
    
