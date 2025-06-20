import logging
import json
from src.config import SecretManager
import openai
import google.generativeai as genai

secret_manager = SecretManager()
openai_api_key = secret_manager.get_secret("OPENAI_API_KEYS")

logger = logging.getLogger(__name__)

class AIManager:
    def __init__(self):
        self.openai_keys = self._load_openai_keys()
        self.gemini_key = get_secret("GEMINI_API_KEY")
        self.current_key_index = 0
        self.model_rotation = ["openai", "gemini"]  # 모델 로테이션 순서
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)

    def _load_openai_keys(self):
        try:
            keys_json = get_secret("OPENAI_KEYS_JSON")
            return json.loads(keys_json)
        except Exception as e:
            logger.error(f"OpenAI keys load failed: {str(e)}")
            return []

    def get_current_model(self):
        """현재 사용할 모델 선택 및 키 로테이션"""
        model = self.model_rotation[self.current_key_index % len(self.model_rotation)]
        self.current_key_index += 1
        
        if model == "openai" and self.openai_keys:
            openai.api_key = self.openai_keys[self.current_key_index % len(self.openai_keys)]
        return model

    def generate_content(self, prompt, model_type=None):
        """AI로 콘텐츠 생성"""
        model = model_type or self.get_current_model()
        
        try:
            if model == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return response.choices[0].message.content
            elif model == "gemini":
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            logger.error(f"{model} API error: {str(e)}")
            return None
