"""
핫이슈 기반 60초 YouTube Shorts 콘텐츠 생성 모듈
"""
import logging
import json
from datetime import datetime
from time import sleep
from .config import Config
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ShortsGenerator:
    def __init__(self):
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-pro")
        
    def _get_today_hot_topics(self):
        """오늘의 핫이슈 5개 조회 (기본값 + 실제 트렌드 API 연동 가능)"""
        return [
            "오늘 가장 화제된 뉴스",
            "인기 급상승 검색어 1위",
            "SNS에서 핫한 주제",
            "최신 유행어",
            "이번 주 가장 많이 본 영상"
        ]

    def _generate_valid_content(self, topic, max_retries=3):
        """재시도 로직이 포함된 콘텐츠 생성"""
        for attempt in range(max_retries):
            try:
                prompt = f"""60초 YouTube Shorts용 대본 생성 요청:
- 주제: {topic}
- 정확한 길이: 60초 (인트로 10초 + 본문 40초 + 마무리 10초)
- 출력 형식 (반드시 JSON):
{{
    "title": "제목 (이모지 2개 포함)",
    "script": "[0:00-0:10] 인트로...\\n[0:10-0:50] 본문...\\n[0:50-1:00] 마무리",
    "hashtags": ["#해시태그1", "#해시태그2"],
    "video_query": "검색용 키워드"
}}"""
                
                response = self.model.generate_content(prompt)
                content = json.loads(response.text)
                
                # 필수 필드 검증
                if not all(k in content for k in ["title", "script", "hashtags"]):
                    raise ValueError("필수 필드 누락")
                return content
                
            except Exception as e:
                logger.warning(f"시도 {attempt+1} 실패 - {topic[:15]}...: {str(e)[:100]}")
                sleep(2)
        return None

    def generate_daily_contents(self):
        """에러 처리 강화된 일일 콘텐츠 생성"""
        contents = []
        for topic in self._get_today_hot_topics():
            content = self._generate_valid_content(topic)
            if content:
                contents.append(content)
            else:
                logger.error(f"주제 '{topic}' 생성 실패. 기본 콘텐츠 사용")
                contents.append({
                    "title": f"{topic} 🚨",
                    "script": f"[0:00-0:10] 인트로\\n[0:10-0:50] {topic}에 대해 알아보겠습니다\\n[0:50-1:00] 마무리",
                    "hashtags": ["#Shorts", "#트렌드"],
                    "video_query": topic.split()[0]
                })
        return contents
