import random
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

    def get_ai_key(self) -> Tuple[str, str]:
        """Returns (api_key, ai_type)"""
        if not self.openai_keys:
            return self.gemini_key, 'gemini'
            
        if random.random() < 0.7:  # 70% 확률로 OpenAI 선택
            key = self.openai_keys[self.current_openai_index]
            self.current_openai_index = (self.current_openai_index + 1) % len(self.openai_keys)
            return key, 'openai'
        return self.gemini_key, 'gemini'

    def get_elevenlabs_key(self) -> str:
        return Config.get_elevenlabs_key()

# 싱글톤 인스턴스 생성
ai_manager = AIRotator()
