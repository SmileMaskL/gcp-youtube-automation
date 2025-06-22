# src/content_generator.py
import json
import logging
import os
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_api_key=None, gemini_api_key=None, ai_model="openai"):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

        self.ai_model = ai_model
        
        # 모델별 사용 가능성 확인
        if self.ai_model == "openai" and not self.openai_client:
            logger.warning("OpenAI client not initialized. "
                           "Falling back to Gemini if available.")
            self.ai_model = "gemini" if self.gemini_model else None
        elif self.ai_model == "gemini" and not self.gemini_model:
            logger.warning("Gemini model not initialized. "
                           "Falling back to OpenAI if available.")
            self.ai_model = "openai" if self.openai_client else None
        
        if not self.ai_model:
            logger.error("No AI models available for content generation.")
            raise ValueError("No AI models available for content generation.")

    def generate_script(self, topic: str):
        """주어진 주제로 YouTube Shorts 스크립트 생성"""
        if self.ai_model == "openai":
            return self._generate_with_openai(topic)
        elif self.ai_model == "gemini":
            return self._generate_with_gemini(topic)
        else:
            logger.error("No valid AI model selected for script generation.")
            return None

    def _generate_with_openai(self, topic: str):
        """OpenAI를 사용하여 스크립트 생성"""
        if not self.openai_client:
            logger.error("OpenAI client not initialized.")
            return None
            
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for creating "
                                    "engaging YouTube Shorts scripts. Provide "
                                    "a concise, impactful script around 60 seconds."
                    },
                    {
                        "role": "user",
                        "content": f"Generate a YouTube Shorts script about: '{topic}'"
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            script = response.choices[0].message.content.strip()
            logger.info(f"OpenAI generated script for topic: {topic}")
            return script
        except Exception as e:
            logger.error(f"Error generating script with OpenAI: {e}")
            return None

    def _generate_with_gemini(self, topic: str):
        """Gemini를 사용하여 스크립트 생성"""
        if not self.gemini_model:
            logger.error("Gemini model not initialized.")
            return None
            
        try:
            prompt = (
                f"Generate a YouTube Shorts script about: '{topic}'. "
                "Keep it concise and engaging for a 60-second video."
            )
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.7
                )
            )
            script = response.text.strip()
            logger.info(f"Gemini generated script for topic: {topic}")
            return script
        except Exception as e:
            logger.error(f"Error generating script with Gemini: {e}")
            return None
