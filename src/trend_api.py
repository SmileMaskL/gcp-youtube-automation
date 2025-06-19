import requests
from datetime import datetime, timedelta

def get_daily_trends() -> list:
    """네이버/구글 트렌드에서 일간 인기 검색어 수집"""
    try:
        # 최근 24시간 내 인기 검색어 (가상의 API 호출)
        date = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')
        params = {
            'date': date,
            'country': 'kr',
            'count': 10
        }
        
        # 실제로는 NEWS_API_KEY 등을 사용해 구현
        response = requests.get('https://api.example.com/trends', params=params)
        return response.json().get('items', [])
    except:
        return ["AI 기술", "최신 스마트폰", "주식 시장", "건강 관리", "여행지 추천"]
