# src/content_generator.py
import os
import json
import logging
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_api_key=None, gemini_api_key=None, ai_model="openai"):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro') # 사용할 Gemini 모델 선택 (예: gemini-pro)
        else:
            self.gemini_model = None

        self.ai_model = ai_model # 현재 선택된 AI 모델
        
        # 모델별 사용 가능성 확인
        if self.ai_model == "openai" and not self.openai_client:
            logger.warning("OpenAI client not initialized. Falling back to Gemini if available.")
            self.ai_model = "gemini" if self.gemini_model else None
        elif self.ai_model == "gemini" and not self.gemini_model:
            logger.warning("Gemini model not initialized. Falling back to OpenAI if available.")
            self.ai_model = "openai" if self.openai_client else None
        
        if not self.ai_model:
            logger.error("No AI models are available for content generation.")
            raise ValueError("No AI models available for content generation.")

    def generate_script(self, topic: str):
        """주어진 주제로 YouTube Shorts 스크립트를 생성합니다."""
        if self.ai_model == "openai":
            if not self.openai_client:
                logger.error("OpenAI client not initialized. Cannot generate script with OpenAI.")
                return None
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o", # 또는 "gpt-3.5-turbo"
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for creating engaging YouTube Shorts scripts. Provide a concise, impactful script that is around 60 seconds long. Focus on a single trending topic. The script should be suitable for text-to-speech conversion and on-screen text."},
                        {"role": "user", "content": f"Generate a YouTube Shorts script about the trending topic: '{topic}'"}
                    ],
                    max_tokens=200, # 60초 영상에 적합한 길이로 조절
                    temperature=0.7
                )
                script = response.choices[0].message.content.strip()
                logger.info(f"OpenAI generated script for topic: {topic}")
                return script
            except Exception as e:
                logger.error(f"Error generating script with OpenAI: {e}")
                return None
        
        elif self.ai_model == "gemini":
            if not self.gemini_model:
                logger.error("Gemini model not initialized. Cannot generate script with Gemini.")
                return None
            try:
                # Gemini API 호출 (예시, 모델에 따라 사용법이 다를 수 있습니다)
                response = self.gemini_model.generate_content(
                    f"Generate a YouTube Shorts script about the trending topic: '{topic}'. Keep it concise and engaging, suitable for a 60-second video with on-screen text.",
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=200, # 최대 토큰 수
                        temperature=0.7
                    )
                )
                script = response.text.strip()
                logger.info(f"Gemini generated script for topic: {topic}")
                return script
            except Exception as e:
                logger.error(f"Error generating script with Gemini: {e}")
                return None
        else:
            logger.error("No valid AI model selected for script generation.")
            return None

# Pexels API 키는 VideoCreator에서 사용하므로 여기서는 제거합니다.
