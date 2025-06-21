# src/content_rotator.py
import random
import logging
from typing import List, Dict, Union

logger = logging.getLogger(__name__)

class ApiKeyRotator:
    def __init__(self, api_keys: List[str]):
        if not api_keys:
            raise ValueError("API keys list cannot be empty.")
        self.api_keys = api_keys
        self.current_key_index = 0
        random.shuffle(self.api_keys) # 키를 무작위로 섞어서 사용

    def get_next_key(self) -> str:
        """다음 사용 가능한 API 키를 반환하고 인덱스를 업데이트합니다."""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Using API key with index: {self.current_key_index}")
        return key

class AIModelSelector:
    def __init__(self, use_gemini: bool = True, use_openai: bool = True):
        self.available_models = []
        if use_gemini:
            self.available_models.append("gemini")
        if use_openai:
            self.available_models.append("openai")
        
        if not self.available_models:
            raise ValueError("At least one AI model (Gemini or OpenAI) must be enabled.")
        
        self.current_model_index = 0
        random.shuffle(self.available_models) # 모델 선택 순서 무작위로 섞기

    def get_next_model(self) -> str:
        """다음 사용 가능한 AI 모델 (gemini 또는 openai)을 반환하고 인덱스를 업데이트합니다."""
        model = self.available_models[self.current_model_index]
        self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
        logger.info(f"Next AI model to use: {model}")
        return model

# 이 모듈은 주로 다른 파일에서 인스턴스화하여 사용합니다.
# 예시:
# from src.content_rotator import ApiKeyRotator, AIModelSelector
# from src.config import config
# 
# openai_rotator = ApiKeyRotator(config.openai_api_keys)
# model_selector = AIModelSelector(use_gemini=True, use_openai=True)
# 
# current_openai_key = openai_rotator.get_next_key()
# selected_ai_model = model_selector.get_next_model()
