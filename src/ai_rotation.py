import random
import logging
from src.config import Config
from typing import List, Tuple

class AIRotator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.openai_keys = Config.get_openai_keys()
        self.current_openai_index = 0
        self.gemini_key = Config.get_gemini_key()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def get_ai_key(self) -> Tuple[str, str]:
        """Returns (api_key, ai_type)"""
        if not self.openai_keys:
            self.logger.info("Using Gemini as fallback")
            return self.gemini_key, 'gemini'
            
        if random.random() < 0.7:  # 70% OpenAI, 30% Gemini
            key = self.openai_keys[self.current_openai_index]
            self.current_openai_index = (self.current_openai_index + 1) % len(self.openai_keys)
            self.logger.info(f"Using OpenAI key (index: {self.current_openai_index})")
            return key, 'openai'
        self.logger.info("Using Gemini key")
        return self.gemini_key, 'gemini'

    def get_elevenlabs_key(self) -> str:
        return Config.get_elevenlabs_key()

# 싱글톤 인스턴스 생성
ai_manager = AIRotator()
