import os
import openai
import google.generativeai as genai
from typing import Optional

def generate_content(topic: str) -> Optional[str]:
    """주제에 맞는 콘텐츠 생성"""
    try:
        # 1. 먼저 무료 Gemini 시도
        if os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(
                f"유튜브 영상 대본을 작성해주세요. 주제: {topic}. "
                "재미있고 실용적인 내용으로 500자 정도 작성해주세요."
            )
            return response.text
        
        # 2. OpenAI 사용
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 유튜버입니다. 조회수가 높은 영상 대본을 작성해주세요."},
                {"role": "user", "content": f"주제: {topic}. 대본을 작성해주세요."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ 콘텐츠 생성 오류: {e}")
        return None
