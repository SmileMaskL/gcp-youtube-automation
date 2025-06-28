# src/content_generator.py
import os
import json
import logging
import random
import google.generativeai as genai
from newsapi import NewsApiClient
from openai import OpenAI # OpenAI 라이브러리 임포트

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_content_and_script(gemini_api_key: str, news_api_key: str, openai_api_keys: list):
    """
    최신 뉴스 기반으로 유튜브 쇼츠 콘텐츠 아이디어, 대본, 제목, 설명을 생성합니다.
    Gemini 또는 GPT-4o 중 선택하여 사용합니다.
    """
    logging.info("Starting content and script generation...")

    # 어떤 AI 모델을 사용할지 결정
    use_openai_for_content = False # True로 변경하면 OpenAI (GPT-4o) 사용
    
    # News API 설정 및 최신 뉴스 가져오기
    news_summary = ""
    try:
        newsapi = NewsApiClient(api_key=news_api_key)
        top_headlines = newsapi.get_top_headlines(language='en', country='us', category='technology') 
        articles = top_headlines['articles']
        
        if articles:
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

    prompt_template = f"""
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

    if use_openai_for_content and openai_api_keys:
        logging.info("Using OpenAI (GPT-4o) for content generation.")
        try:
            # 여러 OpenAI API 키 중 하나를 랜덤하게 선택하여 사용
            selected_openai_api_key = random.choice(openai_api_keys)
            client = OpenAI(api_key=selected_openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o", # 또는 "gpt-4-turbo", "gpt-3.5-turbo"
                response_format={ "type": "json_object" }, # JSON 형식 응답 요청
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt_template}
                ]
            )
            content_text = response.choices[0].message.content
            content_json = json.loads(content_text)
            logging.info("Content and script generated successfully by OpenAI.")
            return content_json
        except Exception as e:
            logging.error(f"Error generating content with OpenAI: {e}", exc_info=True)
            logging.info("Falling back to Gemini for content generation.")
            # OpenAI 실패 시 Gemini로 폴백
            return _generate_with_gemini(gemini_api_key, prompt_template)
    else:
        logging.info("Using Google Gemini for content generation.")
        return _generate_with_gemini(gemini_api_key, prompt_template)

def _generate_with_gemini(gemini_api_key: str, prompt: str):
    """
    Gemini API를 사용하여 콘텐츠를 생성합니다.
    """
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro') # 또는 'gemini-1.5-pro-latest' 등 최신 모델
        response = model.generate_content(prompt)
        content_text = response.text.strip()
        
        # JSON 파싱 시도
        content_json = json.loads(content_text)
        logging.info("Content and script generated successfully by Gemini.")
        return content_json
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from Gemini response: {e}. Response was: {content_text}", exc_info=True)
        return _get_default_content(f"JSON decoding failed from Gemini: {e}")
    except Exception as e:
        logging.error(f"Error generating content with Gemini: {e}", exc_info=True)
        return _get_default_content(f"Content generation failed with Gemini: {e}")

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
            "Today, we're diving into the latest breakthrough in renewable energy. "
            "Scientists just announced a new solar panel technology that boasts 30% higher efficiency. "
            "This could mean cleaner, cheaper energy for millions! "
            "Also, big news in space exploration, with new images from the James Webb Telescope revealing stunning cosmic nurseries. "
            "The universe continues to amaze us! What's your take on these incredible discoveries? "
            "Don't forget to like, subscribe, and hit that notification bell for more daily insights!"
        ),
        "keywords": ["AI news", "Shorts", "Daily Update", "Trending", "Technology", "Space", "Renewable Energy"]
    }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 로컬 테스트용: 환경 변수에서 API 키 로드
    test_gemini_key = os.environ.get("GEMINI_API_KEY")
    test_news_key = os.environ.get("NEWS_API_KEY")
    test_openai_keys_str = os.environ.get("OPENAI_API_KEYS")
    test_openai_keys = [key.strip() for key in test_openai_keys_str.split(',') if key.strip()] if test_openai_keys_str else []


    if not test_gemini_key or not test_news_key:
        logging.error("GEMINI_API_KEY or NEWS_API_KEY environment variable not set for local testing.")
        logging.info("Please set these variables (e.g., export GEMINI_API_KEY='your_key')")
    else:
        generated_content = generate_content_and_script(test_gemini_key, test_news_key, test_openai_keys)
        print(json.dumps(generated_content, indent=2, ensure_ascii=False))
