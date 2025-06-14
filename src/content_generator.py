"""
실시간 트렌딩 콘텐츠 생성기 (무료 API 버전)
"""

import os
import requests
import logging
import random
import json
import re

os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'  # ImageMagick 경로 지정
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)

def get_hot_topics():
    """실시간 인기 주제 수집"""
    try:
        # 1. 뉴스 API 시도
        news_api_key = os.getenv("NEWS_API_KEY")
        if news_api_key:
            url = f"https://newsapi.org/v2/top-headlines?country=kr&apiKey={news_api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            topics = [article['title'] for article in data.get('articles', [])[:5]]
            if topics:
                return topics
    except Exception as e:
        logger.warning(f"뉴스 API 오류: {e}")

    # 2. 기본 주제 리턴
    return [
        "주식 투자 전략",
        "부업으로 월 100만원 버는 법",
        "암호화폐 최신 동향",
        "재테크 성공 비결",
        "온라인 수익 창출"
    ]

def generate_content(topic: str) -> str:
    """AI로 콘텐츠 생성"""
    try:
        # Gemini API 키 확인
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY가 설정되지 않았습니다.")
            return default_content(topic)
            
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"'{topic}'에 대한 30초 YouTube Shorts 대본을 한국어로 작성해주세요. "
            "첫 문장은 강렬한 훅 문장으로 시작하고, 2-3가지 핵심 내용을 간결하게 설명한 후 "
            "시청자 참여를 유도하는 문구로 마무리해주세요."
        )
        
        return response.text
    except Exception as e:
        logger.error(f"콘텐츠 생성 실패: {e}")
        return default_content(topic)

def default_content(topic: str) -> str:
    """기본 콘텐츠 생성"""
    return (
        f"여러분은 {topic}에 대해 얼마나 알고 있나요? "
        "오늘은 대부분이 모르는 3가지 비밀을 알려드리겠습니다. "
        "첫째,... 둘째,... 마지막으로 가장 중요한 셋째는... "
        "유용했다면 구독과 좋아요 부탁드립니다!"
    )
