import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import json
import logging
from datetime import datetime
from .config import Config

logger = logging.getLogger(__name__)

def get_trending_topics():
    try:
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-pro")

        today = datetime.now().strftime("%Y년 %m월 %d일")
        prompt = f"""오늘({today}) 한국에서 가장 인기 있는 주제 5개를 JSON 형식으로 생성해주세요.
[
  {{
    "title": "제목 (15자 이내)",
    "script": "간결한 대본 (3문장 이내)",
    "pexel_query": "영어 검색어"
  }}
]
"""

        config = GenerationConfig(
            temperature=0.7,
            max_output_tokens=512
        )

        response = model.generate_content(
            prompt=prompt,
            generation_config=config
        )

        json_str = response.text.replace('```json', '').replace('```', '').strip()
        topics = json.loads(json_str)
        return topics[:5]
        
    except Exception as e:
        logger.error(f"주제 생성 실패: {e}")
        # 기본값 반환 (시스템이 계속 작동하도록)
        return [
            {
                "title": "AI 기술 동향",
                "script": "인공지능이 다양한 산업을 변화시키고 있습니다. 특히 헬스케어 분야에서 혁신적인 진전이 있었습니다. 앞으로 더 많은 분야에 적용될 것으로 기대됩니다.",
                "pexel_query": "AI technology"
            },
            {
                "title": "지속 가능 에너지",
                "script": "태양광과 풍력 에너지가 점점 더 중요해지고 있습니다. 정부의 지원 정책으로 재생에너지 시장이 확대되고 있습니다. 친환경 에너지로의 전환이 가속화되고 있습니다.",
                "pexel_query": "sustainable energy"
            }
        ]
