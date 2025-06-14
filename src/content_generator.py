import os
import google.generativeai as genai
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def get_hot_topics():
    """네이버/다음 실시간 검색어 수집"""
    try:
        # 네이버 실시간 검색어
        naver_url = "https://api.signal.bz/news/realtime"
        response = requests.get(naver_url)
        naver_topics = [item['keyword']
                        for item in response.json()['top15'][:3]]

        # 다음 실시간 검색어
        daum_url = "https://m.daum.net/api/hotissue/list"
        response = requests.get(daum_url)
        daum_topics = [item['title']
                       for item in response.json()['list'] if item['type'] == 'now'][:3]

        return list(set(naver_topics + daum_topics))
    except Exception as e:
        logger.error(f"⚠️ 실시간 이슈 수집 실패: {e}")
        return [
            "AI 기술 발전 현황",
            "주식 시장 동향",
            "국제 정세 변화",
            "신기술 트렌드",
            "환경 문제 대응",
            "건강 관리 팁"
        ]


def generate_content(topic: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY 환경변수 없음")
        return f"{topic}에 대한 최신 정보입니다. 자세한 내용은 전문가의 조언을 참고하세요."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        [대한민국 실시간 이슈 기반 유튜브 쇼츠 스크립트 생성]
        주제: "{topic}"
        요구사항:
        1. 50자 내외로 간결하게 작성
        2. 첫 문장은 충격적인 사실로 시작
        3. 중간에는 핵심 정보 2-3개 제시
        4. 마지막은 행동 유도 문장으로 마무리
        5. 초보자도 이해할 수 있는 쉬운 용어 사용
        6. 해시태그는 제외
        """

        response = model.generate_content(prompt)
        script = response.text.strip()

        # 불필요한 문구 제거
        for phrase in ["**", "```", "해시태그", "유튜브"]:
            script = script.replace(phrase, "")

        return script[:150]  # 150자 제한

    except Exception as e:
        logger.error(f"❌ 대본 생성 오류: {str(e)}")
        return f"{topic} 관련 최신 소식입니다. 자세한 내용은 전문가 분석을 참고하세요."
