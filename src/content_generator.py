import json
import logging
import random
from typing import Dict, List
import google.generativeai as genai
from datetime import datetime
from .config import Config
from .trend_api import fetch_daily_trends # 트렌드 API 모듈 (가정)

logger = logging.getLogger(name)

class ShortsGenerator:
def init(self):
# API 초기화
genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
self.model = genai.GenerativeModel(
Config.AI_MODEL,
generation_config={
"temperature": 0.8, # 창의성 증가
"top_p": 0.95,
"top_k": 50,
"max_output_tokens": 4096 # 더 긴 응답 처리
}
)
self.trending_topics = []

text
def get_daily_topics(self) -> List[str]:
    """오늘의 핫이슈 5개 주제 가져오기"""
    try:
        trends = fetch_daily_trends(count=5)
        self.trending_topics = [trend['title'] for trend in trends]
        logger.info(f"오늘의 트렌드 주제: {self.trending_topics}")
        return self.trending_topics
    except Exception as e:
        logger.error(f"트렌드 주제 조회 실패: {e}")
        raise RuntimeError("트렌드 주제를 가져오는데 실패했습니다")

def generate_daily_contents(self) -> List[Dict]:
    """하루 5개 쇼츠 콘텐츠 자동 생성"""
    if not self.trending_topics:
        self.get_daily_topics()

    daily_contents = []
    for idx, topic in enumerate(self.trending_topics, 1):
        try:
            content = self._generate_content(topic, video_length=60)
            content['video_id'] = f"{datetime.now().strftime('%Y%m%d')}_{idx}"
            daily_contents.append(content)
            logger.info(f"주제 '{topic}'에 대한 콘텐츠 생성 완료 (ID: {content['video_id']})")
        except Exception as e:
            logger.error(f"주제 '{topic}' 처리 중 오류: {e}")
            continue

    return daily_contents

def _generate_content(self, topic: str, video_length: int = 60) -> Dict:
    """단일 쇼츠 콘텐츠 생성 (60초 버전)"""
    prompt = f"""
    [지시사항]
    - '{topic}' 주제로 {video_length}초 분량의 유튜브 쇼츠 콘텐츠 생성
    - 반드시 아래 JSON 형식으로 응답
    - 한국어로 자연스럽고 흥미로운 내용으로 작성
    - 다른 설명 없이 순수 JSON 데이터만 출력
    - 영상은 5-7개의 장면으로 구성
    - 각 장면은 8-12초 길이

    [출력 형식]
    {{
        "title": "흥미로운 제목 (30자 내외)",
        "description": "영상 설명 (200자 내외) #shorts #트렌드 #꿀팁 포함",
        "script": "{video_length}초 분량의 대본",
        "script_with_timing": [
            {{"text": "문장1", "start": 0.0, "end": 10.5}},
            {{"text": "문장2", "start": 10.6, "end": 22.0}}
        ],
        "tags": ["키워드1", "키워드2", "shorts", "트렌드"],
        "video_query": "영어 배경 검색어 2-3개",
        "estimated_duration": {video_length}.0
    }}
    """

    response = self.model.generate_content(prompt)
    
    if not response.candidates:
        raise ValueError("AI 응답이 비어있습니다")

    response_text = response.candidates[0].content.parts[0].text
    response_text = self._clean_response_text(response_text)
    
    content = json.loads(response_text)
    self._validate_content(content, video_length)
    
    return content

def _clean_response_text(self, text: str) -> str:
    """응답 텍스트 정제"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _validate_content(self, content: Dict, expected_duration: int):
    """생성된 콘텐츠 검증"""
    required_fields = [
        'title', 'description', 'script', 
        'script_with_timing', 'tags', 'video_query',
        'estimated_duration'
    ]
    
    for field in required_fields:
        if field not in content:
            raise ValueError(f"필수 필드 '{field}' 누락")

    # 영상 길이 검증 (55-65초 허용)
    if not (expected_duration-5 <= content['estimated_duration'] <= expected_duration+5):
        raise ValueError(f"영상 길이 오류: {content['estimated_duration']}초")

    # 스크립트 타이밍 검증
    last_timing = content['script_with_timing'][-1]['end']
    if abs(last_timing - expected_duration) > 5:
        raise ValueError(f"최종 영상 길이 불일치: {last_timing}초")
