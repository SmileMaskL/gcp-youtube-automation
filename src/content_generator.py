# src/content_generator.py
import os
import json
import logging
import random
import google.generativeai as genai
from newsapi import NewsApiClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_content_and_script(gemini_api_key: str, news_api_key: str):
    """
    최신 뉴스 기반으로 유튜브 쇼츠 콘텐츠 아이디어, 대본, 제목, 설명을 생성합니다.
    (GPT-4o 또는 Gemini를 활용)
    """
    logging.info("Generating content and script using Gemini...")
    
    # Gemini API 설정
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro') # 또는 'gemini-1.5-pro-latest' 등 최신 모델
    except Exception as e:
        logging.error(f"Failed to configure Gemini API: {e}")
        # fallback to a general content if Gemini fails
        return _get_default_content("Gemini API configuration failed.")

    # News API 설정 및 최신 뉴스 가져오기
    news_summary = ""
    try:
        newsapi = NewsApiClient(api_key=news_api_key)
        # 'kr' 대신 'us' 또는 다른 지역을 지정하여 영어 뉴스를 가져올 수 있습니다.
        # 쇼츠는 전 세계 시청자를 대상으로 하는 경우가 많으므로 영어 뉴스가 더 적합할 수 있습니다.
        top_headlines = newsapi.get_top_headlines(language='en', country='us', category='technology') 
        articles = top_headlines['articles']
        
        if articles:
            # 무작위로 2~3개의 뉴스 기사를 선택하여 요약에 포함
            selected_articles = random.sample(articles, min(len(articles), 3))
            news_summary = "Recent headlines for content ideas:\n"
            for i, article in enumerate(selected_articles):
                news_summary += f"Article {i+1}: Title: {article.get('title', 'N/A')}\n"
                news_summary += f"Description: {article.get('description', 'N/A')}\n"
                news_summary += f"URL: {article.get('url', 'N/A')}\n\n"
            logging.info(f"Fetched {len(selected_articles)} articles from NewsAPI.")
        else:
            logging.warning("No recent news available from NewsAPI. Generating content on a general trending topic.")
            news_summary = "No recent news available. Generate content on a current general trending topic like AI, space, or future technology."

    except Exception as e:
        logging.warning(f"Could not fetch news from NewsAPI: {e}. Generating content on a general trending topic instead.")
        news_summary = "Generate content on a current general trending topic like AI, space, or future technology."

    prompt = f"""
    You are an expert YouTube Shorts content creator. Your goal is to generate highly engaging, concise, and shareable video content ideas and scripts based on the provided context (recent news or trending topics).

    Constraints for YouTube Shorts:
    - Video duration: 30-60 seconds (script length should reflect this).
    - Aspect Ratio: Vertical (9:16) implies visual focus.
    - Captivating hook within the first 3 seconds.
    - Clear and concise message.
    - Call to action (like, subscribe, comment) at the end.

    Based on the following context, please generate:
    1.  **A highly catchy YouTube Shorts title** (under 60 characters, optimized for clicks).
    2.  **A concise and engaging video description** (2-3 sentences, includes relevant hashtags).
    3.  **A detailed video script** (for 30-60 seconds, suitable for text-to-speech).
        - Start with a strong hook.
        - Present information clearly and quickly.
        - Conclude with a clear call to action.
        - Ensure smooth transitions.
        - Each paragraph should represent a distinct spoken segment.
    4.  **5-7 highly relevant keywords/tags** for YouTube SEO.

    Context:
    {news_summary}

    Ensure the output is in strict JSON format with the following keys:
    {{
        "title": "Your Catchy Title Here",
        "description": "Your concise description here #Shorts #Trending",
        "script": "Your detailed video script here. It should be relatively short.",
        "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
    """

    try:
        response = model.generate_content(prompt)
        # Gemini 응답에서 텍스트만 추출
        content_text = response.text.strip()
        
        # 때때로 응답이 JSON 파싱이 어려울 수 있으므로, 재시도 또는 정규식 처리 로직 추가 가능
        content_json = json.loads(content_text)
        
        # 스크립트 길이 검증 (추가적인 로직 필요 시)
        # if len(content_json.get('script', '').split()) > MAX_WORDS_FOR_SHORTS:
        #     logging.warning("Generated script is too long for a short. Consider regenerating or truncating.")
        
        logging.info("Content and script generated successfully by Gemini.")
        return content_json
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from Gemini response: {e}. Response was: {content_text}", exc_info=True)
        # JSON 파싱 실패 시 기본 콘텐츠 반환
        return _get_default_content(f"JSON decoding failed: {e}")
    except Exception as e:
        logging.error(f"Error generating content with Gemini: {e}", exc_info=True)
        return _get_default_content(f"Content generation failed: {e}")

def _get_default_content(reason: str):
    """
    콘텐츠 생성 실패 시 반환할 기본 콘텐츠.
    """
    logging.warning(f"Returning default content because: {reason}")
    return {
        "title": "Daily AI News Shorts Update!",
        "description": "Stay informed with our quick AI-powered daily news shorts! #AINews #Shorts #DailyUpdate",
        "script": (
            "Hey everyone, welcome to your lightning-fast AI news update! "
            "Today, we're diving into [Brief Hook: e.g., the latest breakthrough in renewable energy]. "
            "Scientists just announced [Key detail 1]. This could mean [Impact 1]. "
            "Also, big news in [Topic 2: e.g., space exploration], with [Key detail 2]. "
            "The future is happening now! What's your take? "
            "Don't forget to like, subscribe, and hit that notification bell for more daily insights!"
        ),
        "keywords": ["AI news", "Shorts", "Daily Update", "Trending", "Technology"]
    }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 로컬 테스트용: 환경 변수에서 API 키 로드
    test_gemini_key = os.environ.get("GEMINI_API_KEY")
    test_news_key = os.environ.get("NEWS_API_KEY")

    if not test_gemini_key or not test_news_key:
        logging.error("GEMINI_API_KEY or NEWS_API_KEY environment variable not set for local testing.")
        logging.info("Please set these variables (e.g., export GEMINI_API_KEY='your_key')")
    else:
        generated_content = generate_content_and_script(test_gemini_key, test_news_key)
        print(json.dumps(generated_content, indent=2, ensure_ascii=False))
