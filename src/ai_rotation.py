# src/ai_rotation.py

import os
import random
import logging
from typing import Optional
import openai
import google.generativeai as genai
from .config import Config  # 상대 경로 임포트

class AIClient:
    def __init__(self):
        self.openai_keys = [key.strip() for key in Config.get_api_key("OPENAI_API_KEYS").split(",") if key.strip()]
        self.gemini_key = Config.get_api_key("GEMINI_API_KEY")
        self.ai_model = Config.AI_MODEL
        
    def generate_content(self, prompt: str) -> Optional[str]:
        """70% 확률로 Gemini, 30% 확률로 OpenAI를 사용하여 콘텐츠를 생성합니다."""
        use_gemini = random.random() < 0.7
        
        if use_gemini and self.gemini_key:
            logging.info("🤖 Gemini AI로 콘텐츠 생성을 시도합니다.")
            content = self._use_gemini(prompt)
            if content:
                return content
            logging.warning("Gemini 생성 실패. OpenAI로 재시도합니다.")
        
        if self.openai_keys:
            logging.info("🤖 OpenAI로 콘텐츠 생성을 시도합니다.")
            return self._use_openai(prompt)
            
        logging.error("사용 가능한 AI API 키가 없습니다.")
        return None
    
    def _use_gemini(self, prompt: str) -> Optional[str]:
        try:
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel(self.ai_model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini API 오류 발생: {e}")
            return None
            
    def _use_openai(self, prompt: str) -> Optional[str]:
        if not self.openai_keys:
            return None
        try:
            key = random.choice(self.openai_keys)
            client = openai.OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o",  # 최신 모델 사용
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"OpenAI API 오류 발생: {e}")
            return None
