import os
import random
from typing import Optional
import openai
import google.generativeai as genai

class AIClient:
    def __init__(self):
        self.openai_keys = os.getenv("OPENAI_API_KEYS", "").split(",")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
    def generate_content(self, prompt: str) -> Optional[str]:
        # 70% 확률로 Gemini, 30% 확률로 OpenAI 사용
        if random.random() < 0.7 and self.gemini_key:
            return self._use_gemini(prompt)
        elif self.openai_keys:
            return self._use_openai(prompt)
        return None
    
    def _use_gemini(self, prompt: str) -> Optional[str]:
        try:
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel(self.AI_MODEL)
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            return None
            
    def _use_openai(self, prompt: str) -> Optional[str]:
        try:
            client = openai.OpenAI(api_key=random.choice(self.openai_keys))
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception:
            return None
