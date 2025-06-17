# src/content_generator.py

import os
import json
import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from datetime import datetime
from .config import config

# 로거 설정
logger = logging.getLogger(__name__)

# config.py에서 설정한 API 키를 가져옵니다.
# main.py에서 이미 sys.path를 설정했으므로 직접 임포트 가능합니다.
from src.config import config

def generate_content(base_topic: str) -> dict | None:
    """
    주어진 주제를 바탕으로 Gemini AI를 사용하여 유튜브 쇼츠 콘텐츠를 생성합니다.
    (스크립트, 제목, 설명, 태그, 비디오 검색어 포함)
    """
    logger.info(f"'{base_topic}' 주제로 콘텐츠 생성을 시작합니다.")
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # 사용할 AI 모델 선택 (gemini-1.5-flash는 빠르고 비용 효율적)
        model = genai.GenerativeModel(config.AI_MODEL)

        # AI에게 전달할 프롬프트 (요구사항을 매우 구체적으로 작성)
        prompt = f"""
        당신은 '지식'을 주제로 유튜브 쇼츠를 만드는 전문 작가입니다.
        주제: "{base_topic}"

        아래 JSON 형식에 맞춰 쇼츠 비디오 콘텐츠를 생성해주세요.

        {{
            "title": "사람들의 시선을 사로잡는 강력한 제목 (25자 내외)",
            "description": "영상에 대한 흥미로운 설명과 함께 #shorts, #지식, #꿀팁 등의 필수 해시태그를 포함한 글 (200자 내외)",
            "script": "15~20초 분량의 짧고 흥미로운 내레이션 스크립트. 각 문장은 다음 문장과 자연스럽게 이어져야 함.",
            "script_with_timing": [
                {{"text": "첫 번째 문장.", "start": 0.0, "end": 3.5}},
                {{"text": "두 번째 문장.", "start": 3.6, "end": 7.0}},
                {{"text": "세 번째 문장.", "start": 7.1, "end": 11.0}},
                {{"text": "네 번째 문장.", "start": 11.1, "end": 15.0}}
            ],
            "tags": ["핵심키워드1", "키워드2", "주제와 관련된 단어", "shorts"],
            "video_query": "영상 분위기와 가장 잘 맞는 배경 비디오 검색어 (Pexels 검색용, 영어 단어 2~3개)"
        }}

        - script_with_timing의 시간은 전체 영상 길이를 고려하여 현실적으로 배분해주세요.
        - 모든 텍스트는 한국어로 작성해주세요.
        - 반드시 JSON 형식으로만 응답해야 합니다. 다른 설명은 절대 추가하지 마세요.
        """

        # GenerationConfig 설정
        generation_config = GenerationConfig(
            temperature=0.8,          # 창의성을 조금 높임
            top_p=0.9,
            top_k=40,
            max_output_tokens=2048, # 충분한 토큰 수
            response_mime_type="application/json", # 응답을 JSON으로 강제
        )

        # -------------------------------------------------------------
        # ★★★★★ 핵심 수정 포인트 ★★★★★
        # 이전: model.generate_content(prompt=prompt, ...) -> 에러 발생
        # 변경: model.generate_content(prompt, ...) -> 올바른 최신 방식
        # -------------------------------------------------------------
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        logger.debug(f"Gemini API 응답 수신: {response.text}")
        
        # 응답 받은 텍스트를 JSON 객체로 파싱
        content_json = json.loads(response.text)
        
        logger.info("콘텐츠 JSON 파싱 성공!")
        return content_json

    except Exception as e:
        logger.error(f"콘텐츠 생성 중 심각한 오류 발생: {e}", exc_info=True)
        # 오류 발생 시 None을 반환하여 main.py에서 처리하도록 함
        return None
