# 콘텐츠 회전자
import os
import random
import google.generativeai as genai
import openai
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        # 10개의 Gemini 키 로드 (콤마로 구분)
        self.gemini_keys = os.getenv("GEMINI_API_KEYS").split(",")
        # 10개의 OpenAI 키 로드
        self.openai_keys = os.getenv("OPENAI_API_KEYS").split(",")
        self.current_gemini_key = 0
        self.current_openai_key = 0
        
    def rotate_gemini_key(self):
        self.current_gemini_key = (self.current_gemini_key + 1) % len(self.gemini_keys)
        return self.gemini_keys[self.current_gemini_key]
    
    def rotate_openai_key(self):
        self.current_openai_key = (self.current_openai_key + 1) % len(self.openai_keys)
        return self.openai_keys[self.current_openai_key]
    
    def get_daily_trends(self):
        """실시간 트렌드 크롤링"""
        try:
            # 여기에 실제 트렌드 API 호출 코드
            return ["AI 기술", "주식 시장", "과학 뉴스"]
        except:
            return ["AI 동향", "테크 리뷰", "경제 분석"]
    
    def generate_with_gemini(self, prompt):
        genai.configure(api_key=random.choice(self.gemini_keys))
        model = genai.GenerativeModel('gemini-1.0-pro')
        response = model.generate_content(prompt)
        return response.text
    
    def generate_with_gpt(self, prompt):
        openai.api_key = random.choice(self.openai_keys)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def create_content(self):
        trends = self.get_daily_trends()
        prompt = f"{datetime.now().strftime('%Y-%m-%d')} {random.choice(trends)} 주제로 1분 분량 유튜브 스크립트 생성"
        
        try:
            if random.random() > 0.5:
                content = self.generate_with_gemini(prompt)
            else:
                content = self.generate_with_gpt(prompt)
                
            return {
                "title": f"{datetime.now().strftime('%m월 %d일')} {content[:20]}...",
                "script": content,
                "keywords": trends,
                "video_query": random.choice(trends)
            }
        except Exception as e:
            logger.error(f"콘텐츠 생성 실패: {e}")
            return self.default_content()

    def default_content(self):
        return {
            "title": "오늘의 핫한 주제",
            "script": "이 영상에서는 최신 트렌드를 분석합니다...",
            "keywords": ["트렌드", "뉴스"],
            "video_query": "abstract background"
        }
