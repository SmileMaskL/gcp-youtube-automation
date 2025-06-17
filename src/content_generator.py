"""
완전 자동화 유튜브 쇼츠 제작 시스템 (하루 5개 영상 생성)
"""
import json
import logging
import random
from datetime import datetime
import requests
from pathlib import Path
from .config import Config
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ShortsGenerator:
    def __init__(self):
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        self.trending_topics = []

    def get_daily_topics(self):
        """네이버/구글 트렌드에서 실시간 인기 주제 가져오기"""
        try:
            # 네이버 트렌드 API (예시)
            response = requests.get("https://openapi.naver.com/v1/search/news.json",
                                  headers={"X-Naver-Client-Id": "your_client_id",
                                          "X-Naver-Client-Secret": "your_client_secret"},
                                  params={"query": "트렌드", "display": 5})
            trends = [item['title'] for item in response.json()['items']]
            self.trending_topics = trends[:5]
            logger.info(f"오늘의 트렌드 주제: {self.trending_topics}")
            return self.trending_topics
        except:
            # API 실패 시 기본 주제 사용
            self.trending_topics = [
                "요즘 뜨는 부업 아이디어",
                "집에서 쉽게 하는 운동법",
                "저축률 높이는 법",
                "무료로 배우는 프로그래밍",
                "시간 관리 비법"
            ]
            return self.trending_topics

    def generate_daily_contents(self):
        """하루 5개 쇼츠 콘텐츠 자동 생성"""
        if not self.trending_topics:
            self.get_daily_topics()

        contents = []
        for topic in self.trending_topics:
            try:
                prompt = f"""
                [지시사항]
                - '{topic}' 주제로 60초 분량의 유튜브 쇼츠 대본 생성
                - 한국어로 자연스럽고 흥미로운 내용
                - 5-7개의 장면으로 구성
                - 각 장면은 8-12초 길이
                - 출력 형식:
                제목: (30자 내외)
                대본: (60초 분량의 대본)
                검색어: (영상 검색용 영어 키워드 2-3개)
                """
                response = self.model.generate_content(prompt)
                content = {
                    'title': response.text.split('제목:')[1].split('\n')[0].strip(),
                    'script': response.text.split('대본:')[1].split('검색어:')[0].strip(),
                    'video_query': response.text.split('검색어:')[1].strip()
                }
                contents.append(content)
            except Exception as e:
                logger.error(f"주제 '{topic}' 생성 실패: {e}")
                continue
        return contents
