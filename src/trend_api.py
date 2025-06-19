import os
import requests
import random
from datetime import datetime, timedelta
from google.cloud import secretmanager

def get_trending_topics(country='kr', count=10):
    """네이버/구글 트렌드에서 인기 주제 가져오기"""
    try:
        # 방법 1: NewsAPI 사용 (GitHub Secrets에 NEWS_API_KEY 필요)
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            # GCP Secret Manager에서 키 가져오기
            try:
                client = secretmanager.SecretManagerServiceClient()
                secret_name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/news-api-key/versions/latest"
                response = client.access_secret_version(name=secret_name)
                news_api_key = response.payload.data.decode("UTF-8")
            except Exception as e:
                print(f"Failed to get news api key: {e}")
                news_api_key = None

        if news_api_key:
            # 최신 뉴스 헤드라인에서 키워드 추출
            url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={news_api_key}"
            response = requests.get(url)
            articles = response.json().get('articles', [])
            
            topics = []
            for article in articles[:count]:
                title = article.get('title', '')
                # 제목에서 주요 키워드 추출
                if title:
                    topics.append(title.split('-')[0].strip())
            return topics if topics else get_default_topics()
        
        # 방법 2: 구글 트렌드 대체 (API 키 없을 경우)
        return get_google_trends(country)
        
    except Exception as e:
        print(f"Error fetching trends: {e}")
        return get_default_topics()

def get_google_trends(country='kr'):
    """구글 트렌드 대체 함수 (실제 API 대신 고정 목록)"""
    # 국가별 기본 트렌드 주제
    trends_by_country = {
        'kr': [
            "최신 IT 기술", "AI 활용 사례", "파이썬 프로그래밍", 
            "클라우드 컴퓨팅", "자동화 도구", "빅데이터 분석",
            "머신러닝 입문", "챗GPT 활용법", "개발자 취업 정보",
            "신규 스타트업 소식", "개발자 회고록", "기술 블로그"
        ],
        'us': [
            "Latest tech news", "Python tutorials", "Cloud computing",
            "AI innovations", "Programming tips", "Startup news",
            "Developer tools", "Machine learning", "Data science",
            "Coding interviews", "Tech careers", "Open source"
        ]
    }
    return trends_by_country.get(country, trends_by_country['kr'])

def get_default_topics():
    """API 실패 시 사용할 기본 주제"""
    return [
        "최신 기술 동향",
        "인공지능 활용 방법",
        "파이썬 코딩 팁",
        "클라우드 서비스 비교",
        "개발자 생산성 향상 방법",
        "빅데이터 분석 기법",
        "머신러닝 모델 최적화",
        "챗GPT 활용 사례",
        "IT 취업 시장 현황",
        "개발 도구 추천"
    ]

if __name__ == "__main__":
    print("현재 인기 주제:", get_trending_topics())
