import os
import json
import random
import logging
from openai import OpenAI, APIError
import google.generativeai as genai
from src.usage_tracker import get_current_usage, get_max_limit, update_usage, check_quota

logger = logging.getLogger(__name__)

# AI 모델 정의
# GPT-4o는 더 유료 모델이므로, 무료 할당량이 많은 Gemini를 우선 사용하도록 로직 구성
OPENAI_MODEL = "gpt-4o" # 또는 "gpt-3.5-turbo" (무료 티어 고려 시)
GEMINI_MODEL = "gemini-pro"

def get_available_openai_key(openai_keys_json: str):
    """
    사용 가능한 OpenAI API 키를 로테이션 방식으로 반환합니다.
    만료되거나 한도가 초과된 키는 건너뜁니다.
    """
    if not openai_keys_json:
        return None

    try:
        api_keys = json.loads(openai_keys_json)
    except json.JSONDecodeError:
        logger.error("Invalid OPENAI_KEYS_JSON format. Must be a JSON array string.")
        return None

    if not api_keys:
        return None

    # 키 목록을 섞어서 공정하게 사용
    random.shuffle(api_keys)

    for key in api_keys:
        # TODO: 각 키의 개별 사용량을 추적하고 한도 초과 키를 건너뛰는 로직 추가 필요
        # 현재는 전역 'openai' 사용량으로만 체크하지만, 실제로는 키별 관리가 더 정확함.
        # 이 부분은 외부 DB (예: Firestore)를 사용하여 키별 사용량을 저장해야 합니다.
        # 여기서는 단순히 키 로테이션만 구현하고, 쿼터 체크는 전체 'openai' 사용량으로 가정합니다.
        
        # 임시적으로 각 키에 대한 사용량 추적을 위한 가상의 로직 (실제 DB 연동 필요)
        # if get_openai_key_current_usage(key) < get_openai_key_max_limit(key):
        #    return key
        
        # 현재는 모든 키가 동일한 전체 'openai' 쿼터를 공유한다고 가정하고, 사용 가능한 키를 반환
        return key # 일단 첫 번째 사용 가능한 키 반환 (실제로는 사용량 체크 후 반환)
    
    logger.warning("No available OpenAI API keys found within quota.")
    return None


def generate_content_with_ai(
    ai_choice: str,
    topic: str,
    gemini_api_key: str,
    openai_keys_json: str
) -> dict:
    """
    선택된 AI (Gemini 또는 OpenAI)를 사용하여 콘텐츠를 생성합니다.
    """
    prompt = f"""
    당신은 YouTube Shorts 영상을 위한 콘텐츠를 생성하는 전문가입니다.
    주어진 '{topic}' 주제를 바탕으로 다음 항목들을 생성해주세요.

    1.  **스크립트 (Script):** 60초 이내의 영상에 적합한 간결하고 흥미로운 한국어 스크립트.
        (대략 100~150단어 정도)
    2.  **영상 제목 (Title):** YouTube SEO에 최적화된 매력적인 한국어 제목. (50자 이내)
    3.  **영상 설명 (Description):** 영상 내용을 요약하고 관련 해시태그를 포함하는 한국어 설명. (200자 이내)
    4.  **태그 (Tags):** 영상 관련 키워드 태그. (쉼표로 구분된 문자열)
    5.  **자동 댓글 (Comment):** 영상 업로드 후 자동으로 달릴 댓글. (50자 이내)

    모든 항목은 JSON 형식으로 반환해야 합니다. 예시:
    {{
        "script": "...",
        "title": "...",
        "description": "...",
        "tags": "tag1,tag2,tag3",
        "comment": "..."
    }}
    """
    
    content = {
        "script": "주어진 주제에 대한 스크립트 생성에 실패했습니다.",
        "title": f"자동 생성 영상 - {topic}",
        "description": f"이 영상은 {topic}에 대한 내용입니다.",
        "tags": "자동생성,쇼츠,AI",
        "comment": "영상이 유익했기를 바랍니다!"
    }

    try:
        if ai_choice == "gemini":
            if not gemini_api_key:
                logger.error("Gemini API Key is not provided.")
                return content
            
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info(f"Using Google Gemini model: {GEMINI_MODEL}")
            
            # 쿼터 체크
            if get_current_usage("gemini") >= get_max_limit("gemini"):
                logger.warning("Gemini API quota exceeded. Trying OpenAI if available.")
                return generate_content_with_ai("openai", topic, gemini_api_key, openai_keys_json) # OpenAI로 전환

            response = model.generate_content(prompt)
            # Gemini는 response.text 또는 response.parts[0].text 등으로 접근
            response_text = response.text
            update_usage("gemini", 1)
            check_quota("gemini")

        elif ai_choice == "openai":
            api_key = get_available_openai_key(openai_keys_json)
            if not api_key:
                logger.error("No available OpenAI API key. Cannot generate content.")
                return content
                
            client = OpenAI(api_key=api_key)
            logger.info(f"Using OpenAI model: {OPENAI_MODEL} with key ending in {api_key[-4:]}")

            # 쿼터 체크
            if get_current_usage("openai") >= get_max_limit("openai"):
                logger.warning("OpenAI API quota exceeded for current key. Trying next key or returning default.")
                return content # 다음 키 로직은 get_available_openai_key에서 처리됨.

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={ "type": "json_object" }, # JSON 응답 강제
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = response.choices[0].message.content
            update_usage("openai", 1) # 토큰 사용량에 따라 업데이트 필요 (여기서는 간단히 1로 처리)
            check_quota("openai")

        else:
            logger.error(f"Unknown AI choice: {ai_choice}")
            return content

        # JSON 파싱
        parsed_content = json.loads(response_text)
        content.update(parsed_content) # 기본값에 파싱된 값 업데이트
        logger.info(f"Content successfully generated using {ai_choice}.")
        return content

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode AI response JSON. Raw response: {response_text}. Error: {e}")
        # 유효하지 않은 JSON 응답 시, 다음 AI로 전환 시도
        if ai_choice == "gemini":
            return generate_content_with_ai("openai", topic, gemini_api_key, openai_keys_json)
        else:
            return content # 더 이상 전환할 AI가 없으면 기본값 반환
    except APIError as e: # OpenAI API 에러
        logger.error(f"OpenAI API Error: {e}")
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            logger.warning("OpenAI API quota issue. Trying next key or switching to Gemini.")
            return generate_content_with_ai("gemini", topic, gemini_api_key, openai_keys_json) # Gemini로 전환
        return content
    except Exception as e:
        logger.error(f"An unexpected error occurred during AI content generation with {ai_choice}: {e}", exc_info=True)
        # 다른 AI로 전환 시도 (재귀 호출 방지 위해 조건 추가)
        if ai_choice == "gemini":
            return generate_content_with_ai("openai", topic, gemini_api_key, openai_keys_json)
        else:
            return content
