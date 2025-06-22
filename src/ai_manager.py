# src/ai_manager.py

import logging
import json
import time
from openai import OpenAI
import google.generativeai as genai

from openai_utils import get_next_openai_key  # OpenAI 키 로테이션 함수 임포트

logger = logging.getLogger(__name__)

... (생략) ...

def generate_niche_content(config_instance, niche_keyword, model_preference="openai"):
    """
    특정 틈새시장(Niche) 키워드를 기반으로 콘텐츠를 생성합니다.
    """
    prompt = (
        f"유튜브 쇼츠 영상을 위해 '{niche_keyword}'에 대한 흥미로운 사실, 유용한 팁, "
        "또는 짧은 스토리를 1개 작성해주세요. 제목과 내용을 포함하는 JSON 형식으로 응답해주세요. "
        "내용은 50단어 이내로 간결하게 작성해주세요. "
        f"예시: {{\"title\": \"{niche_keyword}의 놀라운 비밀\", "
        f"\"content\": \"{niche_keyword}에 대한 놀라운 사실입니다...\"}}"
    )
    
    if model_preference == "openai":
        return generate_content_with_openai(config_instance, prompt)
    else:  # default to gemini
        try:
            gemini_api_key = config_instance.get_gemini_api_key()
            return generate_content_with_gemini(gemini_api_key, prompt)
        except Exception as e:
            logger.error(
                f"틈새 콘텐츠 생성 중 Gemini 키 로드 실패: {e}", exc_info=True
            )
            return {"title": "AI 오류", "content": "Gemini 키 로드 실패."}
