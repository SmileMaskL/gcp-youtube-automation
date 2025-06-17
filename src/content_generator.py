"""
콘텐츠 생성 모듈 (최종 수정본)
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
        
        # 모델 초기화 (최신 버전)
        model = genai.GenerativeModel(Config.AI_MODEL)
        
        # 프롬프트 작성
        prompt = f"""
        [지시사항]
        - '{base_topic}' 주제로 15-20초 분량의 유튜브 쇼츠 콘텐츠 생성
        - 반드시 아래 JSON 형식으로 응답
        - 모든 내용은 한국어로 작성
        - 다른 설명 없이 순수 JSON 데이터만 출력
        
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
        
        # 콘텐츠 생성 (새로운 응답 처리 방식)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
        # 응답 처리 (새로운 방식)
        if not response.candidates:
            raise ValueError("AI 응답이 비어있습니다")
            
        # 첫 번째 후보의 텍스트 내용 추출
        response_text = response.candidates[0].content.parts[0].text
        
        # JSON 파싱 전 문자열 정리
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # JSON 파싱
        content = json.loads(response_text)
        
        # 필수 필드 검증
        required_fields = ['title', 'description', 'script', 'script_with_timing', 'tags', 'video_query']
        for field in required_fields:
            if field not in content:
                raise ValueError(f"필수 필드 '{field}'가 없습니다")
        
        # 시간 정보 자동 계산 (스크립트 길이 기반)
        total_duration = sum([item['end']-item['start'] for item in content['script_with_timing']])
        if total_duration < 15 or total_duration > 60:
            raise ValueError("영상 길이가 적절하지 않습니다")
            
        return content
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류. 응답 내용: {response_text if 'response_text' in locals() else '없음'}")
        raise
    except Exception as e:
        logger.error(f"콘텐츠 생성 실패: {e}")
        raise
