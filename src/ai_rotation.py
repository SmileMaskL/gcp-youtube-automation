import random
from src.config import Config
from typing import List

class AIRotator:
    def __init__(self):
        self.openai_keys: List[str] = Config.get_openai_keys()
        self.current_index = 0

    def get_openai_key(self) -> str:
        key = self.openai_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.openai_keys)
        return key

    def get_gemini_key(self) -> str:
        return Config.get_gemini_key()

    def get_elevenlabs_key(self) -> str:
        return Config.get_elevenlabs_key()
