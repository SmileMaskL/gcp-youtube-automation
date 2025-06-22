import os
import logging
import google.generativeai as genai
from openai import OpenAI
from src.config import get_next_openai_key
from src.usage_tracker import api_usage_tracker

logger = logging.getLogger(__name__)

class AIRotationManager:
    def __init__(self, config_instance):
        self.config = config_instance
        self.gemini_client = None
        self.openai_client = None
        self._init_clients()

    def _init_clients(self):
        """API 클라이언트 초기화"""
        # Gemini 클라이언트
        try:
            gemini_key = self.config.get_gemini_api_key()
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_client = genai
                logger.info("Gemini 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"Gemini 초기화 실패: {e}")

        # OpenAI 클라이언트
        try:
            openai_key = get_next_openai_key(self.config)
            self.openai_client = OpenAI(api_key=openai_key)
            logger.info("OpenAI 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"OpenAI 초기화 실패: {e}")

    def generate_content(self, prompt, max_tokens=1000):
        """AI 모델 로테이션으로 콘텐츠 생성"""
        try:
            # OpenAI 시도
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                )
                api_usage_tracker.record_usage("openai")
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI 오류: {e}")

        # Gemini 폴백
        if self.gemini_client:
            try:
                model = self.gemini_client.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                api_usage_tracker.record_usage("gemini")
                return response.text
            except Exception as e:
                logger.error(f"Gemini 오류: {e}")

        raise Exception("모든 AI 모델 실패")
