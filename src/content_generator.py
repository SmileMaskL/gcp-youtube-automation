import os
import openai
from typing import Optional

# Gemini 모듈 사용 가능 여부 초기화
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    # 모듈 기능 테스트 (유효하지 않은 키로 시도)
    genai.configure(api_key="dummy_key")
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Google GenerativeAI 모듈 초기화 실패: {str(e)[:100]}. OpenAI로 대체합니다.")
    GEMINI_AVAILABLE = False

def generate_content(topic: str) -> Optional[str]:
    """주제에 맞는 콘텐츠 생성 (Gemini 없어도 작동)"""
    try:
        # 1. Gemini 사용 시도 (가능한 경우만)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(
                f"유튜브 영상 대본을 작성해주세요. 주제: {topic}. "
                "재미있고 실용적인 내용으로 500자 정도 작성해주세요."
            )
            return response.text
        
        # 2. 무조건 작동하는 OpenAI 버전
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.chat.completions.create(
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
