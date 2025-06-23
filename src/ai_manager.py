# src/ai_manager.py
import logging
from openai import OpenAI
import google.generativeai as genai
import json
from openai_utils import get_next_openai_key

logger = logging.getLogger(__name__)

def generate_content_with_openai(config_instance, prompt_text, model="gpt-4o"):
    try:
        openai_api_key = get_next_openai_key(config_instance)
        client = OpenAI(api_key=openai_api_key)

        logger.info(f"OpenAI (GPT-4o) 모델로 콘텐츠 생성 요청. 모델: {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that generates concise "
                        "and engaging content for YouTube Shorts. Provide a "
                        "title and content in JSON format."
                    )
                },
                {"role": "user", "content": prompt_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=200
        )
        
        content_json = json.loads(response.choices[0].message.content)
        logger.info(f"OpenAI 응답 성공: {content_json.get('title', '제목 없음')}")
        return content_json
    
    except Exception as e:
        logger.error(f"OpenAI (GPT-4o) 콘텐츠 생성 실패: {e}", exc_info=True)
        return {
            "title": "AI 콘텐츠 생성 오류",
            "content": "콘텐츠를 생성하는 데 문제가 발생했습니다. 다시 시도해주세요."
        }

# ... 나머지 코드 동일 ...
