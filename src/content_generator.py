import google.generativeai as genai
from datetime import datetime
import random
from config import Config  # Config 클래스 import 추가
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_trending_topics():
    """오늘의 핫한 주제 5개 생성"""
    try:
        genai.configure(api_key=Config.get_api_key("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""2025년 6월 현재 대한민국에서 가장 인기 있는 주제 5개를 JSON 형식으로 생성해주세요.
        반드시 다음 형식을 따라야 합니다:
        [{{"title": "제목 (15자 이내)", "script": "간결한 대본 (3문장 이내)", "pexel_query": "영어 검색어"}}]
        예시:
        {{
          "title": "AI 기술 동향",
          "script": "인공지능은 모든 산업을 변화시키고 있습니다. 특히 헬스케어 분야에서 큰 진전이 있었습니다. 앞으로 더 많은 혁신이 예상됩니다.",
          "pexel_query": "artificial intelligence"
        }}"""
        
        response = model.generate_content(prompt)
        content = eval(response.text)
        logger.info("트렌딩 주제 생성 성공")
        return content[:5]  # 상위 5개만 반환
        
    except Exception as e:
        logger.error(f"트렌딩 주제 생성 실패: {e}")
        # 기본값 반환
        return [
            {
                "title": "AI 기술 동향",
                "script": "인공지능은 모든 산업을 변화시키고 있습니다.",
                "pexel_query": "artificial intelligence"
            },
            {
                "title": "지속 가능 에너지",
                "script": "태양광과 풍력 에너지가 점점 더 중요해지고 있습니다.",
                "pexel_query": "sustainable energy"
            }
        ]
