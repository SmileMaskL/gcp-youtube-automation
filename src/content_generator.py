# src/content_generator.py (수정 버전)

import os
import google.generativeai as genai
import logging
import requests

logger = logging.getLogger(__name__)

def get_hot_topics() -> list:
    """대한민국 핫이슈 6개를 가져옵니다."""
    try:
        # 예시: 뉴스 API 사용 (실제 사용 시 API 키 필요)
        api_key = os.getenv("NEWS_API_KEY")
        if api_key:
            url = f"https://newsapi.org/v2/top-headlines?country=kr&apiKey={api_key}"
            response = requests.get(url)
            data = response.json()
            topics = [article['title'] for article in data['articles'][:6]]
            return topics
        else:
            # API 키가 없으면 테스트용 주제 반환
            return [
                "클로드 3.5 소네트, GPT-4o보다 정말 똑똑할까?",
                "Suno V3, 단 1분만에 노래 만드는 AI",
                "무료 AI 영상 제작 툴 'Luma Dream Machine' 사용법",
                "월 500만원 버는 AI 자동화 부업",
                "평생 무료로 쓰는 구글 클라우드",
                "2025년 최신 AI 트렌드"
            ]
    except Exception as e:
        logger.error(f"핫이슈 가져오기 실패: {e}")
        return ["AI 기술 발전", "자동화 부업", "구글 클라우드", "AI 음악 제작", "AI 영상 제작", "AI 대화 기술"]

def generate_content(topic: str) -> str:
    """
    Google Gemini AI를 사용하여 주어진 주제에 대한 유튜브 대본을 생성합니다.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        return f"'{topic}'에 대한 기본 스크립트입니다. AI 대본 생성에 실패했습니다."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') # 빠르고 효율적인 모델

        prompt = f"""
        당신은 시청자의 눈길을 사로잡는 유튜브 쇼츠 비디오 스크립트 작가입니다.
        주어진 주제에 대해 60초 내로 읽을 수 있는 간결하고 흥미로운 스크립트를 작성해주세요.
        반드시 다음 규칙을 지켜주세요:
        1. 첫 문장에서 시청자의 호기심을 자극하세요.
        2. 어려운 단어 대신 쉽고 친근한 단어를 사용하세요.
        3. 문장은 짧고 명확하게 끊어서 말해주세요.
        4. 마지막은 다음 영상에 대한 기대감을 주는 문장으로 마무리하세요.
        
        주제: "{topic}"
        """

        response = model.generate_content(prompt)
        script = response.text.strip()
        
        logger.info(f"✅ Gemini AI가 '{topic}'에 대한 대본을 성공적으로 생성했습니다.")
        return script

    except Exception as e:
        logger.error(f"❌ Gemini AI 대본 생성 중 오류 발생: {str(e)}")
        return f"'{topic}'에 대한 기본 스크립트입니다. AI 대본 생성 중 오류가 발생했습니다."
