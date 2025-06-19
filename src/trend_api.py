import requests
import feedparser # pip install feedparser
import logging

logger = logging.getLogger(__name__)

def get_trending_topics() -> list[str]:
    # 예시: Google News RSS 피드에서 인기 주제 가져오기
    # 실제 운영에서는 더 다양한 뉴스 소스나 트렌드 분석 API를 연동하는 것이 좋습니다.
    # Google News의 경우, IP에 따라 차단될 수 있으므로 주의가 필요합니다.
    # 대안: NewsAPI.org, RapidAPI 등의 트렌드 API
    
    # NewsAPI.org 사용 예시 (NewsAPI_API_KEY가 필요)
    # NEWS_API_KEY = os.getenv("NEWS_API_KEY") # GitHub Secrets에 NEWS_API_KEY 설정 필요
    # if NEWS_API_KEY:
    #     try:
    #         response = requests.get(f"https://newsapi.org/v2/top-headlines?language=ko&apiKey={NEWS_API_KEY}", timeout=5)
    #         response.raise_for_status()
    #         articles = response.json().get('articles', [])
    #         topics = [article['title'] for article in articles if article.get('title')]
    #         logger.info(f"NewsAPI에서 {len(topics)}개 트렌딩 주제 가져옴.")
    #         return topics[:10] # 상위 10개 주제 반환
    #     except Exception as e:
    #         logger.warning(f"NewsAPI에서 트렌딩 주제 가져오기 실패: {e}")

    # RSS 피드 사용 예시 (더 안정적일 수 있음)
    rss_feed_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR" # 한국 구글 트렌드
    try:
        feed = feedparser.parse(rss_feed_url)
        topics = [entry.title for entry in feed.entries if entry.title]
        logger.info(f"Google Trends RSS에서 {len(topics)}개 트렌딩 주제 가져옴.")
        return topics[:10] # 상위 10개 주제 반환
    except Exception as e:
        logger.error(f"RSS 피드에서 트렌딩 주제 가져오기 실패: {e}")
        return []
