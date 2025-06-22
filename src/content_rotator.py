import random
import logging

logger = logging.getLogger(__name__)

class ApiKeyRotator:
    def __init__(self, api_keys: list):
        if not api_keys:
            raise ValueError("API keys list cannot be empty.")
        self.api_keys = api_keys
        self.current_key_index = 0
        random.shuffle(self.api_keys)
    
    def get_next_key(self) -> str:
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
            raise ValueError("At least one AI model must be enabled.")
        
        self.current_model_index = 0
        random.shuffle(self.available_models)

    def get_next_model(self) -> str:
        model = self.available_models[self.current_model_index]
        self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
        logger.info(f"Next AI model to use: {model}")
        return model
