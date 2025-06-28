# src/video_script_generator.py
import requests
import json
import logging
import random
from openai import OpenAI # 실제 사용
from google.generativeai import GenerativeModel, configure as configure_gemini # 실제 사용
from newsapi import NewsApiClient # 실제 사용

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_latest_news(api_key, query="재미있는 뉴스"):
    """NewsAPI에서 최신 뉴스를 가져옵니다."""
    logger.info(f"NewsAPI에서 뉴스 검색 중... 쿼리: {query}")
    url = f"https://newsapi.org/v2/everything?q={query}&language=ko&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        articles = response.json().get('articles', [])
        logger.info(f"NewsAPI에서 {len(articles)}개의 기사 발견.")
        if not articles:
            logger.warning("NewsAPI에서 뉴스를 찾을 수 없습니다. 기본 쿼리로 재시도합니다.")
            url = f"https://newsapi.org/v2/top-headlines?country=kr&pageSize=5&apiKey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            logger.info(f"기본 쿼리로 {len(articles)}개의 기사 발견.")

        return articles
    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI 요청 실패: {e}")
        return []

def summarize_with_openai(text, api_keys):
    """OpenAI GPT 모델을 사용하여 텍스트를 요약합니다."""
    logger.info("OpenAI GPT로 요약 및 스크립트 생성 시도 중...")
    api_key_list = [key.strip() for key in api_keys.split(',')]
    if not api_key_list:
        raise ValueError("OPENAI_API_KEYS가 설정되지 않았거나 유효하지 않습니다.")

    for api_key in api_key_list:
        try:
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-4o", # 또는 gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": "너는 재미있고 유익한 1분짜리 YouTube 쇼츠 비디오 스크립트를 작성하는 전문 크리에이터야. 복잡한 뉴스를 쉽고 간결하며 흥미롭게 요약하여 시청자의 호기심을 자극하고 끝까지 시청하게 만들어야 해. 스크립트에는 대본 내용과 함께 비디오 클립을 검색할 키워드, 그리고 쇼츠 영상 제목을 포함해야 해."},
                    {"role": "user", "content": f"""다음 뉴스 기사를 바탕으로 YouTube 쇼츠 비디오 스크립트를 작성해줘. 스크립트는 40초에서 55초 분량으로 하고, 다음과 같은 JSON 형식으로 출력해야 해:

{{
  "title": "[흥미로운 쇼츠 제목]",
  "script": "여기에 재미있고 간결한 대본 내용을 작성하세요. 각 문장은 짧고 간결하게.",
  "search_keywords": "[비디오 클립을 찾기 위한 핵심 키워드 3~5개, 쉼표로 구분]"
}}

뉴스 기사:
{text}
"""
                    }
                ],
                response_format={"type": "json_object"}
            )
            response_content = completion.choices[0].message.content
            logger.info("OpenAI GPT 응답 수신 완료.")
            return json.loads(response_content)
        except Exception as e:
            logger.warning(f"OpenAI GPT 사용 중 오류 발생 (API Key: {api_key[:5]}...): {e}. 다음 키로 시도합니다.")
            continue # 다음 API 키로 재시도
    raise Exception("모든 OpenAI API 키 시도가 실패했습니다. 키를 확인하거나 할당량을 늘리세요.")

def summarize_with_gemini(text, api_key):
    """Google Gemini 모델을 사용하여 텍스트를 요약합니다."""
    logger.info("Google Gemini로 요약 및 스크립트 생성 시도 중...")
    try:
        configure_gemini(api_key=api_key)
        model = GenerativeModel("gemini-1.5-flash-latest") # 또는 gemini-1.5-pro-latest
        response = model.generate_content(
            f"""다음 뉴스 기사를 바탕으로 YouTube 쇼츠 비디오 스크립트를 작성해줘. 스크립트는 40초에서 55초 분량으로 하고, 다음과 같은 JSON 형식으로 출력해야 해:

{{
  "title": "[흥미로운 쇼츠 제목]",
  "script": "여기에 재미있고 간결한 대본 내용을 작성하세요. 각 문장은 짧고 간결하게.",
  "search_keywords": "[비디오 클립을 찾기 위한 핵심 키워드 3~5개, 쉼표로 구분]"
}}

뉴스 기사:
{text}
""",
            generation_config={"response_mime_type": "application/json"}
        )
        logger.info("Google Gemini 응답 수신 완료.")
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Google Gemini 사용 중 오류 발생: {e}")
        raise

def generate_script_from_news(newsapi_key, openai_api_keys, gemini_api_key, news_query="최신 기술 뉴스"):
    """
    뉴스 기사를 기반으로 비디오 스크립트, 제목, 검색 키워드를 생성합니다.
    GPT-4o를 우선 사용하고, 오류 시 Gemini 1.5-Flash로 폴백합니다.
    """
    articles = get_latest_news(newsapi_key, news_query)
    
    if not articles:
        raise Exception("뉴스 기사를 가져올 수 없습니다. NewsAPI 키 또는 쿼리를 확인하세요.")

    # 가장 긴 기사 3개 선택 (내용이 충분한 기사를 선호)
    selected_articles = sorted(articles, key=lambda x: len(x.get('content', '') or ''), reverse=True)[:3]
    
    # 선택된 기사의 제목과 내용 합치기
    combined_news_text = ""
    for article in selected_articles:
        combined_news_text += f"제목: {article.get('title', 'N/A')}\n"
        combined_news_text += f"내용: {article.get('content', '') or article.get('description', 'N/A')}\n\n"

    # OpenAI GPT-4o로 스크립트 생성 시도
    try:
        script_data = summarize_with_openai(combined_news_text, openai_api_keys)
        logger.info("OpenAI GPT-4o로 스크립트 생성 성공.")
        return script_data
    except Exception as e:
        logger.warning(f"OpenAI GPT-4o 스크립트 생성 실패: {e}. Google Gemini로 폴백합니다.")
        # Gemini로 폴백
        try:
            script_data = summarize_with_gemini(combined_news_text, gemini_api_key)
            logger.info("Google Gemini로 스크립트 생성 성공.")
            return script_data
        except Exception as e_gemini:
            logger.error(f"Google Gemini 스크립트 생성도 실패: {e_gemini}. 스크립트 생성 실패!")
            raise Exception(f"AI 스크립트 생성에 실패했습니다: {e_gemini}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    news_api_key = os.getenv("NEWSAPI_API_KEY")
    openai_api_keys = os.getenv("OPENAI_API_KEYS")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not news_api_key or not openai_api_keys or not gemini_api_key:
        print("필수 환경 변수(NEWSAPI_API_KEY, OPENAI_API_KEYS, GEMINI_API_KEY)를 .env 파일에 설정해주세요.")
    else:
        try:
            generated_data = generate_script_from_news(news_api_key, openai_api_keys, gemini_api_key)
            print("\n--- 생성된 쇼츠 스크립트 ---")
            print(f"제목: {generated_data['title']}")
            print(f"스크립트:\n{generated_data['script']}")
            print(f"검색 키워드: {generated_data['search_keywords']}")
        except Exception as e:
            print(f"스크립트 생성 중 오류 발생: {e}")
