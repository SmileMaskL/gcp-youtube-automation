import random
from src.config import Config
from typing import List, Optional

class AIRotator:
    def __init__(self):
        self.openai_keys: List[str] = Config.get_openai_keys()
        self.current_openai_index = 0
        self.gemini_key: str = Config.get_gemini_key()
        self.ai_choice = random.choice(['openai', 'gemini'])

    def get_ai_key(self) -> tuple[str, str]:
        """Returns (api_key, ai_type)"""
        if self.ai_choice == 'openai':
            key = self.openai_keys[self.current_openai_index]
            self.current_openai_index = (self.current_openai_index + 1) % len(self.openai_keys)
            return key, 'openai'
        return self.gemini_key, 'gemini'

    def get_elevenlabs_key(self) -> str:
        return Config.get_elevenlabs_key()
