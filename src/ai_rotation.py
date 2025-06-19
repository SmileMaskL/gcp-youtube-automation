import google.generativeai as genai
from openai import OpenAI
import logging
from datetime import datetime
from typing import Optional
from src.config import Config

logger = logging.getLogger(__name__)

class AIRotationManager:
    def __init__(self):
        self.gemini_keys = Config.get_gemini_keys()
        self.openai_keys = Config.get_openai_keys()
        self.current_gemini = 0
        self.current_openai = 0
        self.usage = {'gemini': 0, 'openai': 0}
        self.last_reset = datetime.now().date()

    def _reset_usage(self):
        if datetime.now().date() != self.last_reset:
            self.usage = {'gemini': 0, 'openai': 0}
            self.last_reset = datetime.now().date()

    def get_gemini(self):
        self._reset_usage()
        if not self.gemini_keys:
            raise ValueError("Gemini API 키 없음")
        genai.configure(api_key=self.gemini_keys[0])
        self.usage['gemini'] += 1
        return "gemini-pro"

    def get_openai(self):
        self._reset_usage()
        if not self.openai_keys:
            raise ValueError("OpenAI API 키 없음")
        key = self.openai_keys[self.current_openai]
        self.current_openai = (self.current_openai + 1) % len(self.openai_keys)
        self.usage['openai'] += 1
        return OpenAI(api_key=key)

    def select_model(self) -> str:
        self._reset_usage()
        if self.usage['gemini'] < 3 and self.gemini_keys:
            return 'gemini'
        elif self.usage['openai'] < 7 and self.openai_keys:
            return 'openai'
        else:
            raise ValueError("일일 API 할당량 초과")

ai_manager = AIRotationManager()
