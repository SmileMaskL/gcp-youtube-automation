# src/content_generator.py
<<<<<<< HEAD

=======
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
import logging
import random
import json
import google.generativeai as genai
from newsapi import NewsApiClient
<<<<<<< HEAD

logging.basicConfig(level=logging.INFO)

def generate_content_and_script(gemini_api_key, news_api_key, openai_api_keys):
    """
    인기 검색어 기반 유튜브 Shorts 콘텐츠 생성
    """
    newsapi = NewsApiClient(api_key=news_api_key)
    headlines = newsapi.get_top_headlines(language='en', country='us', category='technology')
    articles = headlines["articles"]

    context = ""
    if articles:
        selected = random.choice(articles)
        context = f"Trending topic: {selected['title']} - {selected.get('description','')}"
    else:
        context = "Trending topic: AI, space, future technology"

    prompt = f"""
    Generate YouTube Shorts content JSON for:
    {context}
    Format:
    {{
        "title": "...",
        "description": "...",
        "script": "...",
        "keywords": ["...", "..."]
    }}
    """

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    content = json.loads(response.text.strip())
    return content
=======
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO)

class ContentValidator(BaseModel):
    title: str
    description: str
    script: str
    keywords: list[str]

class ContentGenerator:
    """YouTube 자동화 콘츠츠 생성기 (실전 최적화 버전)"""
    
    def __init__(self, gemini_key: str, openai_keys: list):
        self.gemini = genai.configure(api_key=gemini_key)
        self.newsapi = NewsApiClient(api_key=openai_keys[0])
        self.model = genai.GenerativeModel("gemini-1.5-pro-latest")  # 최신 모델로 변경

    def _get_trending_topic(self) -> str:
        """실시간 인기 뉴스 크롤링"""
        headlines = self.newsapi.get_top_headlines(
            language='en', country='us', category='technology'
        )
        return random.choice(headlines["articles"])['title'] if headlines else "AI Technology"

    def _generate_prompt(self) -> str:
        """고수익 콘텐츠 생성 프롬프트"""
        topic = self._get_trending_topic()
        return f"""
        Generate viral YouTube Shorts content (strictly follow):
        - Title: [Emoji] {topic} [Power Word]
        - Description: 500+ characters with 5+ hashtags
        - Script: 30-60 sec video script with hooks every 5sec
        - Keywords: 10+ high-CPM keywords
        """

    def generate(self) -> ContentValidator:
        """검증된 콘텐츠 생성"""
        try:
            response = self.model.generate_content(self._generate_prompt())
            content = json.loads(response.text.strip())
            return ContentValidator(**content)
        except (json.JSONDecodeError, ValidationError) as e:
            logging.error(f"콘텐츠 검증 실패: {str(e)}")
            raise RuntimeError("잘못된 콘텐츠 형식") from e
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
