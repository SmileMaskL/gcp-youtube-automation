# src/content_generator.py
import logging
from typing import List
from src.config import config
from src.content_rotator import ApiKeyRotator, AIModelSelector
import google.generativeai as genai
from openai import OpenAI

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        self.openai_rotator = ApiKeyRotator(config.openai_api_keys)
        self.ai_model_selector = AIModelSelector(use_gemini=True, use_openai=True)
        
        # Gemini API 키 설정 (config에서 로드)
        genai.configure(api_key=config.gemini_api_key)
        self.gemini_client = genai.GenerativeModel('gemini-pro') # 또는 'gemini-1.5-flash' 등 최신 모델

    def generate_script(self, topic: str, video_length_seconds: int = 60) -> str:
        """
        주제를 바탕으로 비디오 스크립트를 생성합니다.
        AI 모델 (Gemini 또는 OpenAI)을 로테이션하여 사용합니다.
        """
        selected_model = self.ai_model_selector.get_next_model()
        script = ""

        if selected_model == "openai":
            api_key = self.openai_rotator.get_next_key()
            openai_client = OpenAI(api_key=api_key)
            logger.info(f"Generating script using OpenAI model with key: {api_key[:5]}...")
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o", # 또는 "gpt-3.5-turbo" 등
                    messages=[
                        {"role": "system", "content": f"You are a helpful assistant specialized in creating engaging 60-second YouTube Shorts scripts based on trending topics. Ensure the script is concise, captivating, and suitable for a broad audience. Focus on a factual, informative, and entertaining tone. Avoid copyrighted material. Generate a script that is approximately {video_length_seconds} seconds long when read naturally."},
                        {"role": "user", "content": f"Generate a short video script about the following topic: {topic}"}
                    ],
                    max_tokens=500 # 스크립트 길이에 따라 조정
                )
                script = response.choices[0].message.content.strip()
                logger.info(f"OpenAI script generated successfully for topic: {topic}")
            except Exception as e:
                logger.error(f"OpenAI script generation failed: {e}")
                # OpenAI 실패 시 Gemini로 폴백하거나 오류 처리
                script = self._generate_script_with_gemini(topic, video_length_seconds) # 실패 시 Gemini 시도
        
        elif selected_model == "gemini":
            logger.info(f"Generating script using Google Gemini model.")
            script = self._generate_script_with_gemini(topic, video_length_seconds)
            
        if not script:
            logger.error(f"Failed to generate script for topic: {topic} using any available AI model.")
            raise Exception("Script generation failed.")
        
        return script

    def _generate_script_with_gemini(self, topic: str, video_length_seconds: int) -> str:
        """Gemini 모델을 사용하여 스크립트를 생성하는 내부 함수"""
        try:
            response = self.gemini_client.generate_content(
                f"You are a helpful assistant specialized in creating engaging 60-second YouTube Shorts scripts based on trending topics. Ensure the script is concise, captivating, and suitable for a broad audience. Focus on a factual, informative, and entertaining tone. Avoid copyrighted material. Generate a script that is approximately {video_length_seconds} seconds long when read naturally. Generate a short video script about the following topic: {topic}",
                generation_config=genai.types.GenerationConfig(max_output_tokens=500) # 스크립트 길이에 따라 조정
            )
            script = response.text.strip()
            logger.info(f"Gemini script generated successfully for topic: {topic}")
            return script
        except Exception as e:
            logger.error(f"Google Gemini script generation failed: {e}")
            return "" # 실패 시 빈 문자열 반환
