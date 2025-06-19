# src/ai_manager.py
import os
import json
import logging
from src.config import get_secret
import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AIManager:
    """
    OpenAI (GPT-4o)와 Google Gemini API 키를 관리하고 로테이션하며,
    모델 선택 및 사용량 모니터링을 담당합니다.
    """
    def __init__(self):
        self.openai_keys = self._load_openai_keys()
        self.gemini_key = self._load_gemini_key()
        self.current_openai_key_index = 0
        self.api_usage = {"openai": 0, "gemini": 0}
        self.model_preference = ["openai", "gemini"] # 선호 모델 순서
        self.current_model_index = 0

        # Gemini 설정
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            logger.info("Google Gemini API configured.")
        else:
            logger.warning("Gemini API Key not found. Gemini models will not be available.")

        # OpenAI 설정 (첫 번째 키로 초기화)
        if self.openai_keys:
            openai.api_key = self.openai_keys[self.current_openai_key_index]
            logger.info(f"OpenAI API initialized with key index {self.current_openai_key_index}.")
        else:
            logger.warning("OpenAI API Keys not found. OpenAI models will not be available.")

    def _load_openai_keys(self):
        """Secret Manager에서 OpenAI API 키 리스트를 로드합니다."""
        try:
            openai_keys_json = get_secret("OPENAI_KEYS_JSON")
            keys = json.loads(openai_keys_json)
            if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
                logger.error("OPENAI_KEYS_JSON secret is not a valid JSON list of strings.")
                return []
            logger.info(f"Loaded {len(keys)} OpenAI API keys.")
            return keys
        except Exception as e:
            logger.error(f"Error loading OpenAI API keys from Secret Manager: {e}")
            return []

    def _load_gemini_key(self):
        """Secret Manager에서 Gemini API 키를 로드합니다."""
        try:
            key = get_secret("GEMINI_API_KEY")
            logger.info("Loaded Gemini API key.")
            return key
        except Exception as e:
            logger.error(f"Error loading Gemini API key from Secret Manager: {e}")
            return None

    def rotate_openai_key(self):
        """OpenAI API 키를 다음 키로 로테이션합니다."""
        if self.openai_keys:
            self.current_openai_key_index = (self.current_openai_key_index + 1) % len(self.openai_keys)
            openai.api_key = self.openai_keys[self.current_openai_key_index]
            logger.info(f"Rotated OpenAI API key to index: {self.current_openai_key_index}")
        else:
            logger.warning("No OpenAI API keys available for rotation.")

    def get_current_model(self):
        """현재 사용할 AI 모델을 반환하고 다음 모델로 로테이션합니다."""
        selected_model = self.model_preference[self.current_model_index]
        self.current_model_index = (self.current_model_index + 1) % len(self.model_preference)
        
        # 선택된 모델에 따라 OpenAI 키 로테이션
        if selected_model == "openai":
            self.rotate_openai_key()
            if not openai.api_key:
                logger.error("OpenAI API key not set. Cannot use OpenAI model.")
                return None
        elif selected_model == "gemini":
            if not self.gemini_key:
                logger.error("Gemini API key not set. Cannot use Gemini model.")
                return None
        
        return selected_model

    def generate_text(self, prompt: str, model_name: str, max_tokens: int = 1000):
        """
        주어진 모델로 텍스트를 생성합니다.

        Args:
            prompt (str): AI에 전달할 프롬프트.
            model_name (str): 사용할 AI 모델 이름 ('openai', 'gemini').
            max_tokens (int): 생성할 최대 토큰 수.

        Returns:
            str: 생성된 텍스트.
        """
        generated_text = ""
        try:
            if model_name == "openai":
                response = openai.chat.completions.create(
                    model="gpt-4o", # GPT-4o 모델 사용
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                )
                generated_text = response.choices[0].message.content.strip()
                self.api_usage["openai"] += 1
                logger.info(f"Text generated using OpenAI (gpt-4o). Usage count: {self.api_usage['openai']}")
            elif model_name == "gemini":
                # Gemini Pro 1.5 모델 사용
                gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest') 
                response = gemini_model.generate_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens))
                generated_text = response.text.strip()
                self.api_usage["gemini"] += 1
                logger.info(f"Text generated using Gemini (gemini-1.5-pro-latest). Usage count: {self.api_usage['gemini']}")
            else:
                logger.error(f"Unsupported AI model: {model_name}")
                return ""
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            # API 키 문제일 경우 다음 키로 로테이션 시도
            if "Incorrect API key" in str(e) or "invalid_api_key" in str(e):
                self.rotate_openai_key()
                logger.warning("OpenAI API key might be invalid, rotated to next key.")
            return ""
        except genai.APIError as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return ""
        except Exception as e:
            logger.error(f"An unexpected error occurred during AI text generation with {model_name}: {e}", exc_info=True)
            return ""
        return generated_text

    def get_api_usage(self, api_type: str):
        """특정 API의 사용량을 반환합니다."""
        return self.api_usage.get(api_type, 0)

# 테스트용 코드
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # .env 파일 로드 (로컬 테스트용)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    ai_manager = AIManager()
    
    test_prompt = "Short script about a cat learning to code."

    for _ in range(5): # 5번 반복하여 모델 로테이션 확인
        current_model = ai_manager.get_current_model()
        if current_model:
            print(f"\n--- Using {current_model} ---")
            generated_text = ai_manager.generate_text(test_prompt, current_model, max_tokens=200)
            print(f"Generated Text:\n{generated_text[:200]}...")
            print(f"OpenAI Usage: {ai_manager.get_api_usage('openai')}")
            print(f"Gemini Usage: {ai_manager.get_api_usage('gemini')}")
        else:
            print("No AI model available.")
