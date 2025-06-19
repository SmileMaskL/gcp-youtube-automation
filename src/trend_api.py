import requests
import json
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_trending_news(api_key: str, country='kr', language='ko') -> str:
    """
    News API에서 현재 대한민국 (또는 지정된 국가/언어)의 트렌딩 뉴스 헤드라인을 가져옵니다.
    뉴스 API의 무료 티어 제한을 고려하여 사용합니다.
    """
    if not api_key:
        logger.error("News API Key is not provided.")
        return ""

    # News API의 무료 플랜은 개발용으로, 검색 결과가 제한될 수 있습니다.
    # 상업적 사용 또는 더 많은 데이터가 필요하면 유료 플랜을 고려해야 합니다.
    # 여기서는 'top-headlines' 엔드포인트를 사용하여 최신 트렌드를 파악합니다.
    url = f"https://newsapi.org/v2/top-headlines?country={country}&language={language}&apiKey={api_key}"

    try:
        response = requests.get(url, timeout=10) # 10초 타임아웃
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()

        articles = data.get('articles', [])
        if not articles:
            logger.warning("No trending articles found from News API.")
            return "최신 인기 뉴스, 오늘 이슈" # 기본 주제 반환

        # 무작위로 하나의 기사 선택하여 제목 반환
        # 더 복잡한 로직이 필요하면 여러 기사를 분석하여 핵심 키워드 추출 가능
        selected_article = random.choice(articles)
        title = selected_article.get('title', "오늘의 흥미로운 소식")
        
        # 제목에서 불필요한 부분 제거 (예: "- 뉴스 출처")
        if ' - ' in title:
            title = title.split(' - ')[0]
        
        logger.info(f"Successfully fetched trending news: {title}")
        return title

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching news: {http_err} - {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred while fetching news: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred while fetching news: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred while fetching news: {req_err}")
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding error: {json_err} - Response text: {response.text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_trending_news: {e}")
        
    return "오늘의 인기 토픽, 최신 정보" # 오류 발생 시 기본 주제 반환
