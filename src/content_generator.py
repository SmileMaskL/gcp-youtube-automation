"""
실시간 트렌딩 콘텐츠 생성기 (무료 API 버전)
"""

import requests
import logging
import random
from datetime import datetime
from bs4 import BeautifulSoup
from utils import Config

logger = logging.getLogger(__name__)

# 무료 트렌드 API 목록
TREND_APIS = [
    {
        "name": "Google Trends",
        "url": "https://trends.google.com/trends/api/dailytrends?geo=KR",
        "parse": lambda data: [trend["title"] for trend in data["default"]["trendingSearchesDays"][0]["trendingSearches"]]
    },
    {
        "name": "Daum 실검",
        "url": "https://www.daum.net",
        "parse": lambda soup: [a.text for a in soup.select('.list_mini .rank_cont > .link_issue')[:10]]
    }
]

def get_hot_topics():
    """실시간 인기 주제 수집 (에러 방지 버전)"""
    for api in TREND_APIS:
        try:
            if api["name"] == "Daum 실검":
                response = requests.get(api["url"], headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, 'html.parser')
                topics = api["parse"](soup)
            else:
                response = requests.get(api["url"], timeout=5)
                data = json.loads(response.text[5:])  # Google Trends는 특이한 형식
                topics = api["parse"](data)
                
            if topics:
                logger.info(f"{api['name']}에서 {len(topics)}개 주제 수집")
                return topics[:5]  # 상위 5개만
                
        except Exception as e:
            logger.warning(f"{api['name']} 오류: {e}")
            continue
            
    # 모두 실패 시 기본 주제
    money_topics = [
        "주식 투자 전략",
        "부업으로 월 100만원 버는 법",
        "암호화폐 최신 동향",
        "재테크 성공 비결",
        "온라인 수익 창출"
    ]
    logger.warning("API 실패로 기본 주제 사용")
    return money_topics

def generate_content(topic: str) -> str:
    """AI로 콘텐츠 생성 (무료 버전)"""
    try:
        from utils import generate_viral_content
        content = generate_viral_content(topic)
        return content["script"]
    except Exception as e:
        logger.error(f"콘텐츠 생성 실패: {e}")
        return f"{topic}에 대한 최신 정보입니다. 놀라운 내용을 확인해보세요!"
