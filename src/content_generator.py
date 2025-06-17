"""
콘텐츠 생성 모듈 (최종확인 버전)
"""
import json
import logging
import google.generativeai as genai
from .config import Config

logger = logging.getLogger(__name__)

def generate_content(base_topic: str) -> dict:
    """Gemini AI를 사용하여 유튜브 쇼츠 콘텐츠 생성"""
    try:
        # API 설정
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        model = genai.GenerativeModel(Config.AI_MODEL)
        
        # 프롬프트 작성
        prompt = f"""
        [지시사항]
        - '{base_topic}' 주제로 15-20초 분량의 유튜브 쇼츠 콘텐츠 생성
        - 반드시 아래 JSON 형식으로 응답
        
        [출력 형식]
        {{
            "title": "흥미로운 제목 (25자 내외)",
            "description": "영상 설명 (200자 내외) #shorts #지식 #꿀팁 포함",
            "script": "15-20초 분량의 자연스러운 대본",
            "script_with_timing": [
                {{"text": "문장1", "start": 0.0, "end": 3.5}},
                {{"text": "문장2", "start": 3.6, "end": 7.0}}
            ],
            "tags": ["키워드1", "키워드2", "shorts"],
            "video_query": "영어 배경 검색어 2-3개"
        }}
        """
        
        # 콘텐츠 생성
        response = model.generate_content(prompt)
        content = json.loads(response.text)
        
        # 시간 정보 자동 계산 (스크립트 길이 기반)
        total_duration = sum([item['end']-item['start'] for item in content['script_with_timing']])
        if total_duration < 15 or total_duration > 60:
            raise ValueError("영상 길이가 적절하지 않습니다")
            
        return content
        
    except Exception as e:
        logger.error(f"콘텐츠 생성 실패: {e}")
        raise
