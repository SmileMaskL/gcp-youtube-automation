import os
import logging
import random
import google.generativeai as genai
from openai import OpenAI
from .utils import get_secret

logger = logging.getLogger(__name__)

class YouTubeAutomation:
    def __init__(self):
        # API 키 로테이션 초기화
        self.openai_keys = json.loads(get_secret("OPENAI_API_KEYS"))['keys']
        self.gemini_keys = json.loads(get_secret("GEMINI_API_KEYS"))['keys']

    # src/content_generator.py 수익형 콘텐츠 생성 로직
    def generate_content(topic):
    # 수익형 키워드 강조
        profit_keywords = ["확대해석", "충격적 진실", "공개합니다", "무료 수익"]
        title = f"{random.choice(profit_keywords)} {topic} {random.choice(['쇼킹!', '꿀팁!'])}"
    
    def _select_api_key(self):
        """무작위 API 키 선택"""
        return {
            'openai': random.choice(self.openai_keys),
            'gemini': random.choice(self.gemini_keys)
        }

    def generate_content(self, topic):
        """실전용 콘텐츠 생성 (로테이션 + 장애 대응)"""
        keys = self._select_api_key()
        logger.info(f"🔑 사용 키: OpenAI({keys['openai'][:5]}..), Gemini({keys['gemini'][:5]}..)")
        
        try:
            # 1. Gemini로 제목 생성
            genai.configure(api_key=keys['gemini'])
            gemini_model = genai.GenerativeModel('gemini-pro')
            
            title_prompt = (
                f"15초 YouTube Shorts용 제목 생성:\n"
                f"- 주제: {topic}\n"
                f"- 조건: 이모지 2개 포함, 12자 이내\n"
                f"- 예시: '🚀AI가 바꾸는 미래!🔥'"
            )
            title_response = gemini_model.generate_content(title_prompt)
            title = title_response.text.strip().replace('"', '')
            logger.info(f"📌 생성 제목: {title}")

            # 2. GPT-4o로 스크립트 생성
            openai_client = OpenAI(api_key=keys['openai'])
            
            script_prompt = (
                f"60초 YouTube Shorts 스크립트 작성:\n"
                f"- 제목: {title}\n"
                f"- 구조: 1) 충격적 사실(3초) 2) 핵심 정보(10초) 3) 호기심 유발 질문(2초)\n"
                f"- 문체: 반말, 이모지 활용\n"
                f"- 예시: '놀랍게도 AI가...'"
            )
            
            gpt_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": script_prompt}],
                max_tokens=300
            )
            script = gpt_response.choices[0].message.content
            logger.info(f"📜 생성 스크립트: {script[:50]}...")

            return {
                'title': title,
                'title_text': title.replace(' ', '').replace('!', ''),
                'script': script,
                'description': (
                    f"{title}\n\n"
                    f"{script[:100]}...\n\n"
                    "#Shorts #AI자동생성\n"
                    "구독과 좋아요 부탁드려요! 😍"
                )
            }
            
        except Exception as e:
            logger.error(f"🔴 AI 생성 실패: {str(e)}")
            # 장애 시 기본 콘텐츠
            return {
                'title': f"{topic} 초고속 분석",
                'title_text': topic[:5],
                'script': f"{topic}에 대한 놀라운 사실! 계속 지켜봐 주세요.",
                'description': f"{topic} 최신 정보! #Shorts"
            }
