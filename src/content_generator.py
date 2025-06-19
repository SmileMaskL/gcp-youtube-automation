import os
import json
import logging
from datetime import datetime
from src.ai_rotation import ai_manager
from src.trend_api import get_daily_trends

class ContentGenerator:
    def __init__(self, api_key: str, ai_type: str):
        self.api_key = api_key
        self.ai_type = ai_type
        self.logger = logging.getLogger(__name__)

    def get_daily_topic(self) -> str:
        try:
            trends = get_daily_trends()
            return trends[0] if trends else "최신 기술 트렌드"
        except Exception as e:
            self.logger.error(f"트렌드 가져오기 실패: {e}")
            return "최신 기술 트렌드"

    def generate_script(self, topic: str) -> str:
        if self.ai_type == 'openai':
            return self._generate_with_openai(topic)
        else:
            return self._generate_with_gemini(topic)

    def _generate_with_openai(self, topic: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates engaging YouTube Shorts scripts."},
                {"role": "user", "content": f"Create a 60-second YouTube Short script about {topic} in Korean. Include engaging hooks and hashtags."}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

    def _generate_with_gemini(self, topic: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Create a 60-second YouTube Short script about {topic} in Korean. Include engaging hooks and hashtags."
        )
        return response.text
