import os
import random
from datetime import datetime
from .openai_utils import OpenAIClient
from .trend_api import get_trending_topics
from .config import Config

class ContentGenerator:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.config = Config()
        self.fallback_topics = [
            "최신 기술 트렌드",
            "인공지능 활용법",
            "파이썬 프로그래밍 팁",
            "클라우드 컴퓨팅 장점",
            "자동화로 시간 절약하는 방법"
        ]
        
    def generate_script(self, topic=None):
        try:
            if not topic:
                topic = self._get_daily_topic()
            
            prompt = self._build_prompt(topic)
            content = self._generate_with_ai(prompt)
            
            return {
                "topic": topic,
                "script": content or "콘텐츠 생성에 실패했습니다. 다시 시도해주세요.",
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"콘텐츠 생성 오류: {e}")
            return {
                "topic": "기술 트렌드",
                "script": "오늘의 기술 트렌드를 분석해보겠습니다. 최근 인공지능 기술이 빠르게 발전하면서...",
                "created_at": datetime.now().isoformat()
            }

    def _get_daily_topic(self):
        try:
            trends = get_trending_topics()
            if trends and len(trends) > 0:
                return random.choice(trends[:5])
        except Exception as e:
            print(f"트렌드 주제 가져오기 실패: {e}")
        
        return random.choice(self.fallback_topics)

    def _build_prompt(self, topic):
        return f"""60초 YouTube Shorts용 대본을 작성해주세요. 다음 주제에 대해 흥미롭고 간결하게 설명해주세요:
        
주제: {topic}

요구사항:
- 전체 길이: 60초에 딱 맞게 (약 150-200단어)
- 언어: 한국어 (반말 사용)
- 구조: 
  1. 흥미로운 시작 (예: "이거 알고 계셨나요?")
  2. 본문 (3개 핵심 포인트)
  3. 강력한 마무리 (예: "이런 점이 놀랍지 않나요?")
- 톤: 친근하고 유쾌한 느낌
- 해시태그 5개 포함 (예: #기술트렌드 #AI #인공지능)

출력 형식:
[제목]
[대본 내용]
[해시태그]"""

    def _generate_with_ai(self, prompt):
        # GPT-4o 시도
        content = self.openai_client.generate_content(prompt, model="gpt-4o")
        if content:
            return content
        
        # Gemini 시도
        try:
            from .gemini_utils import GeminiClient
            gemini_client = GeminiClient()
            return gemini_client.generate_content(prompt)
        except:
            return None
