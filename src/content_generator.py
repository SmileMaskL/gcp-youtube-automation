import os
from datetime import datetime
from .openai_utils import OpenAIClient
from .trend_api import get_trending_topics
from .config import Config

class ContentGenerator:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.config = Config()
        
    def generate_script(self, topic=None):
        if not topic:
            topic = self._get_daily_topic()
        
        prompt = self._build_prompt(topic)
        content = self._generate_with_ai(prompt)
        
        return {
            "topic": topic,
            "script": content,
            "created_at": datetime.now().isoformat()
        }

    def _get_daily_topic(self):
        # 트렌드 API에서 오늘의 인기 주제 가져오기
        try:
            trends = get_trending_topics()
            return random.choice(trends[:5])  # 상위 5개 주제 중 랜덤 선택
        except:
            # 트렌드 API 실패 시 기본 주제 사용
            default_topics = [
                "최신 기술 트렌드",
                "인공지능 활용법",
                "파이썬 프로그래밍 팁",
                "클라우드 컴퓨팅 장점",
                "자동화로 시간 절약하는 방법"
            ]
            return random.choice(default_topics)

    def _build_prompt(self, topic):
        return f"""60초 YouTube Shorts용 대본을 작성해주세요. 다음 주제에 대해 흥미롭고 간결하게 설명해주세요:
        
        주제: {topic}
        
        요구사항:
        - 전체 길이: 60초에 딱 맞게
        - 언어: 한국어 (반말 사용)
        - 구조: 흥미로운 시작 → 본문 (3개 포인트) → 강력한 마무리
        - 톤: 친근하고 유쾌한 느낌
        - 해시태그 5개 포함
        
        출력 형식:
        [제목]
        [대본 내용]
        [해시태그]"""

    def _generate_with_ai(self, prompt):
        # GPT-4o 시도
        content = self.openai_client.generate_content(prompt, model="gpt-4o")
        if content:
            return content
        
        # 실패 시 Gemini 시도
        from .gemini_utils import GeminiClient
        gemini_client = GeminiClient()
        return gemini_client.generate_content(prompt)
