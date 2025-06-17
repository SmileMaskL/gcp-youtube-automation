import os
import random
import google.generativeai as genai
from openai import OpenAI
from typing import Optional

class AIClient:
    def __init__(self):
        self.gemini_keys = os.getenv("GEMINI_API_KEYS", "").split(",")
        self.openai_keys = os.getenv("OPENAI_API_KEYS", "").split(",")
        
    def generate_content(self, prompt: str) -> Optional[str]:
        # 70% 확률로 Gemini, 30% 확률로 GPT 사용
        if random.random() < 0.7 and self.gemini_keys:
            return self._use_gemini(prompt)
        elif self.openai_keys:
            return self._use_openai(prompt)
        return None
    
    def _use_gemini(self, prompt: str) -> Optional[str]:
        try:
            genai.configure(api_key=random.choice(self.gemini_keys))
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            return None
            
    def _use_openai(self, prompt: str) -> Optional[str]:
        try:
            client = OpenAI(api_key=random.choice(self.openai_keys))
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception:
            return None
