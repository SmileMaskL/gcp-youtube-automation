import os
import json
import logging
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_api_key=None, gemini_api_key=None, ai_model="openai"):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

        self.ai_model = ai_model
        
        # 모델 가용성 체크
        if self.ai_model == "openai" and not self.openai_client:
            logger.warning("OpenAI 클라이언트 초기화 실패. Gemini로 전환")
            self.ai_model = "gemini" if self.gemini_model else None
        elif self.ai_model == "gemini" and not self.gemini_model:
            logger.warning("Gemini 모델 초기화 실패. OpenAI로 전환")
            self.ai_model = "openai" if self.openai_client else None
        
        if not self.ai_model:
            logger.error("사용 가능한 AI 모델 없음")
            raise ValueError("AI 모델 초기화 실패")

    def generate_script(self, topic: str):
        """주제 기반 YouTube Shorts 스크립트 생성"""
        if self.ai_model == "openai":
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a YouTube Shorts assistant"},
                        {"role": "user", "content": f"'{topic}' 주제로 60초 스크립트 생성"}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                script = response.choices[0].message.content.strip()
                logger.info(f"OpenAI 스크립트 생성: {topic}")
                return script
            except Exception as e:
                logger.error(f"OpenAI 오류: {e}")
                return None
        
        elif self.ai_model == "gemini":
            try:
                response = self.gemini_model.generate_content(
                    f"'{topic}' 주제로 60초 YouTube Shorts 스크립트 생성",
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=200,
                        temperature=0.7
                    )
                )
                script = response.text.strip()
                logger.info(f"Gemini 스크립트 생성: {topic}")
                return script
            except Exception as e:
                logger.error(f"Gemini 오류: {e}")
                return None
