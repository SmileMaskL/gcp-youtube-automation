import google.generativeai as genai
from datetime import datetime
import random
import json
from .config import Config
import logging

logger = logging.getLogger(__name__)

def get_trending_topics():
    """오늘의 트렌딩 주제 5개 생성"""
    try:
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        prompt = f"""2025년 6월 현재 한국에서 가장 인기 있는 주제 5개를 생성해주세요. 반드시 다음 JSON 형식으로 출력해야 합니다:
        [
            {{
                "title": "제목 (15자 이내)",
                "script": "간결한 대본 (3문장 이내)",
                "pexel_query": "영어 검색어"
            }}
        ]
        예시:
        {{
            "title": "AI 기술 동향",
            "script": "인공지능이 헬스케어 분야를 혁신하고 있습니다. ...",
            "pexel_query": "artificial intelligence healthcare"
        }}"""
        
        response = model.generate_content(prompt)
        topics = json.loads(response.text)
        logger.info("트렌딩 주제 생성 성공")
        return topics[:5]  # 최대 5개 반환
        
    except Exception as e:
        logger.error(f"주제 생성 실패: {e}")
        # 기본값 반환
        return [
            {
                "title": "AI 기술 동향",
                "script": "인공지능이 헬스케어 분야를 혁신 중입니다.",
                "pexel_query": "artificial intelligence"
            }
        ]
