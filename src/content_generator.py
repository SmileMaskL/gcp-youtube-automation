"""
핫이슈 기반 60초 YouTube Shorts 콘텐츠 생성 모듈
"""
import logging
import json
from datetime import datetime
from .config import Config
import google.generativeai as genai
from .trend_api import get_today_trends  # 실시간 트렌드 API (직접 구현 필요)

logger = logging.getLogger(__name__)

class ShortsGenerator:
    def __init__(self):
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-pro")
        
    def _get_today_hot_topics(self):
        """오늘의 핫이슈 5개 조회"""
        try:
            trends = get_today_trends()  # 커스텀 트렌드 API (예: 네이버/구글 트렌드)
            return trends[:5]
        except Exception as e:
            logger.error(f"트렌드 조회 실패: {e}")
            return [
                "오늘 가장 화제된 뉴스",
                "인기 급상승 검색어 1위",
                "SNS에서 핫한 주제",
                "최신 유행어",
                "이번 주 가장 많이 본 영상"
            ]

    def _generate_script(self, topic):
        """60초 대본 생성 (정확한 포맷 강제)"""
        prompt = f"""오늘의 핫이슈: {topic}
        
        - 60초 YouTube Shorts용 대본 생성
        - 구조: 인트로(10초) + 본문(40초) + 마무리(10초)
        - 출력 형식 (JSON):
        {{
            "title": "제목 (이모지 포함)",
            "script": "대본 (시간 표시 필수)\n예) [0:00-0:10] 인트로...",
            "hashtags": ["#해시태그1", "#해시태그2"]
        }}"""
        
        response = self.model.generate_content(prompt)
        return json.loads(response.text)

    def generate_contents(self):
        """오늘의 핫이슈 기반 콘텐츠 5개 생성"""
        contents = []
        for topic in self._get_today_hot_topics():
            try:
                content = self._generate_script(topic)
                contents.append(content)
            except Exception as e:
                logger.error(f"주제 '{topic}' 생성 실패: {e}")
        return contents
