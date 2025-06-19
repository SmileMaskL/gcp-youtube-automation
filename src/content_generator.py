import logging
import random
import google.generativeai as genai
from openai import OpenAI
from src.ai_rotation import ai_manager # 수정: ai_manager 사용
from src.trend_api import get_trending_topics # 새로 추가

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        # AI 모델은 ai_manager에서 동적으로 가져옵니다.
        pass

    def _generate_content_with_gemini(self, topic: str) -> dict:
        model_name = ai_manager.get_next_gemini_model() # 수정: AI 모델 가져오기
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        당신은 유튜브 쇼츠 콘텐츠 생성 전문가입니다. 다음 주제에 대해 60초 이내의 쇼츠 영상에 적합한 스크립트, 제목, 설명, 그리고 영상 배경에 사용할 키워드를 생성해 주세요.
        
        주제: {topic}
        
        요구 사항:
        1. 스크립트는 150단어 이내로 간결하고 흥미롭게 작성해 주세요. (한국어)
        2. 제목은 시청자의 클릭을 유도할 수 있는 매력적인 제목으로, 해시태그 3개 이상 포함해 주세요. (예: #핫이슈 #트렌드 #주목)
        3. 설명은 영상 내용을 요약하고 관련성 높은 해시태그를 5개 이상 포함해 주세요.
        4. 영상 배경 키워드는 Pexels API에서 검색할 때 사용할 수 있는 영어 단어 2~3개로 구성해 주세요. (예: 'nature background', 'city night', 'futuristic abstract')
        5. 출력 형식은 JSON으로 부탁드립니다.

        예시 JSON 형식:
        ```json
        {{
            "script": "...",
            "title": "...",
            "description": "...",
            "video_query": "..."
        }}
        ```
        """
        
        try:
            response = model.generate_content(prompt)
            # 안전 모드 필터링된 응답 처리
            if not response.candidates:
                logger.warning(f"Gemini content generation failed for topic '{topic}': No candidates returned. Prompt was: {prompt}")
                return None
            
            # 텍스트가 비어있는 경우 체크
            if not response.text:
                logger.warning(f"Gemini content generation failed for topic '{topic}': Empty text response. Prompt was: {prompt}")
                return None

            content = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Gemini를 사용한 콘텐츠 생성 실패: {e}")
            return None

    def _generate_content_with_openai(self, topic: str) -> dict:
        client = ai_manager.get_next_openai_client() # 수정: AI 모델 가져오기
        
        prompt = f"""
        You are a YouTube Shorts content creation expert. Generate a script, title, description, and video background keywords suitable for a 60-second Shorts video on the following topic:
        
        Topic: {topic}
        
        Requirements:
        1. The script should be concise and engaging, under 150 words. (Korean)
        2. The title should be attractive to encourage clicks, including at least 3 hashtags. (e.g., #HotIssue #Trends #MustWatch)
        3. The description should summarize the video content and include at least 5 relevant hashtags.
        4. The video background keywords should be 2-3 English words suitable for searching on Pexels API. (e.g., 'nature background', 'city night', 'futuristic abstract')
        5. Output format must be JSON.

        Example JSON format:
        ```json
        {{
            "script": "...",
            "title": "...",
            "description": "...",
            "video_query": "..."
        }}
        ```
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o", # 또는 "gpt-3.5-turbo" 등 사용 가능한 모델
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500 # 적절한 토큰 수
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI를 사용한 콘텐츠 생성 실패: {e}")
            return None

    def create_content(self) -> dict:
        trending_topics = get_trending_topics() # 핫이슈 트렌드 가져오기
        if trending_topics:
            topic = random.choice(trending_topics) # 무작위로 핫이슈 하나 선택
            logger.info(f"선택된 핫이슈 주제: {topic}")
        else:
            # 핫이슈를 가져오지 못했을 경우 대체 주제 목록
            predefined_topics = [
                "최신 인공지능 기술 트렌드",
                "지속 가능한 친환경 생활 습관",
                "건강한 식단 관리 비법",
                "재테크 초보를 위한 투자 전략",
                "흥미로운 우주 탐사 이야기",
                "생산성을 높이는 시간 관리 팁",
                "세계 각국의 이색 축제",
                "미래 도시의 모습 상상하기",
                "스트레스 해소에 좋은 취미",
                "새로운 직업의 세계"
            ]
            topic = random.choice(predefined_topics)
            logger.warning(f"핫이슈 트렌드를 가져오지 못하여 대체 주제 '{topic}' 사용.")

        for _ in range(3): # 최대 3번 시도
            selected_model = ai_manager.get_llm_model() # AI 모델 로테이션
            logger.info(f"콘텐츠 생성을 위해 선택된 AI 모델: {selected_model}")

            if selected_model == "gemini":
                content = self._generate_content_with_gemini(topic)
            elif selected_model == "openai":
                content = self._generate_content_with_openai(topic)
            else:
                content = None
            
            if content and content.get('script') and content.get('title'):
                logger.info("콘텐츠 생성 성공.")
                return content
            else:
                logger.warning(f"선택된 AI 모델({selected_model})로 콘텐츠 생성 실패. 재시도합니다.")
        
        raise ValueError(f"콘텐츠 생성에 실패했습니다. 주제: {topic}")
