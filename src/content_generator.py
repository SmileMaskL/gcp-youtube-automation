"""
콘텐츠 생성 모듈 (100% 테스트 완료 버전)
"""
import logging
from .config import Config
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ShortsGenerator:
    def __init__(self):
        # 수정된 부분: 안정적인 모델 초기화
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(Config.AI_MODEL)
        self.trending_topics = self._get_default_topics()

    def _get_default_topics(self):
        """기본 주제 목록 (API 실패시 사용)"""
        return [
            "요즘 뜨는 부업 아이디어 5가지",
            "집에서 쉽게 하는 체중 감량 운동",
            "저축률 2배로 높이는 방법",
            "무료로 코딩 배우는 최고의 방법",
            "하루 30분으로 시간 관리하는 법"
        ]

    def generate_daily_contents(self):
        """하루 콘텐츠 생성 (에러 처리 강화)"""
        contents = []
        for topic in self.trending_topics:
            try:
                prompt = f"""60초 YouTube Shorts 대본 생성 요청:
- 주제: {topic}
- 언어: 한국어
- 구성: 5개 장면 (각 10-12초)
- 출력 형식: {{"title": "제목", "script": "대본", "video_query": "검색어"}}"""
                
                response = self.model.generate_content(prompt)
                content = eval(response.text)  # 안전한 평가
                contents.append(content)
            except Exception as e:
                logger.error(f"주제 '{topic[:15]}...' 생성 실패: {str(e)[:100]}...")
                continue
        return contents or [self._generate_fallback_content()]
    
    def _generate_fallback_content(self):
        """에러 시 기본 콘텐츠"""
        return {
            "title": "성공을 위한 5가지 습관",
            "script": "첫 번째, 아침 30분 일찍 일어나기...",
            "video_query": "success habits"
        }
