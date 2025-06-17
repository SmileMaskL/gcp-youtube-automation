import google.generativeai as genai
import os
from config import Config
import json
from retrying import retry
import logging

logger = logging.getLogger(__name__)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_trending_topics():
    """최신 트렌드 주제 5개 가져오기"""
    try:
        api_key = Config.get_api_key("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""오늘의 핫한 주제 5개를 JSON 형식으로 생성해주세요. 오늘 날짜는 {datetime.now().strftime('%Y-%m-%d')}입니다.
        출력 형식: [{{"title": "제목", "script": "대본", "pexel_query": "검색어"}}]"""
        response = model.generate_content(prompt)
        # 응답 파싱
        try:
            topics = json.loads(response.text.strip())
            if not isinstance(topics, list) or len(topics) == 0:
                raise ValueError("생성된 주제가 리스트가 아니거나 비어 있습니다.")
            return topics
        except json.JSONDecodeError:
            # 응답이 JSON이 아닐 경우, 수정 시도
            # ... (수정 로직 생략)
            raise
    except Exception as e:
        logger.error(f"트렌드 주제 생성 실패: {e}")
        raise
