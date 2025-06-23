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
                    "content": "You are a helpful assistant that generates "
                    "concise and engaging content for YouTube Shorts. "
                    "Provide a title and content in JSON format."
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


def generate_content_with_gemini(
    gemini_api_key, prompt_text, model="gemini-1.5-flash"
):
    try:
        genai.configure(api_key=gemini_api_key)
        model_instance = genai.GenerativeModel(model_name=model)

        logger.info(f"Google Gemini 모델로 콘텐츠 생성 요청. 모델: {model}")
        full_prompt = (
            f"{prompt_text}\n\n"
            "Your response MUST be a JSON object with two keys: "
            "'title' (string) and 'content' (string). "
            "Example: {{\"title\": \"추천 제목\", \"content\": \"생성된 내용\"}}"
        )
        
        response = model_instance.generate_content(full_prompt)
        content_text = response.text
        
        if content_text.startswith("```json"):
            content_text = content_text.replace("```json\n", "").replace(
                "\n```", "")
        
        content_json = json.loads(content_text)
        logger.info(f"Gemini 응답 성공: {content_json.get('title', '제목 없음')}")
        return content_json

    except Exception as e:
        logger.error(f"Google Gemini 콘텐츠 생성 실패: {e}", exc_info=True)
        return {
            "title": "AI 콘텐츠 생성 오류",
            "content": "콘텐츠를 생성하는 데 문제가 발생했습니다. 다시 시도해주세요."
        }


def generate_niche_content(config_instance, niche_keyword, 
                           model_preference="openai"):
    prompt = (
        f"유튜브 쇼츠 영상을 위해 '{niche_keyword}'에 대한 흥미로운 사실, "
        "유용한 팁, 또는 짧은 스토리를 1개 작성해주세요. "
        "제목과 내용을 포함하는 JSON 형식으로 응답해주세요. "
        "내용은 50단어 이내로 간결하게 작성해주세요. "
        f"예시: {{\"title\": \"{niche_keyword}의 놀라운 비밀\", "
        f"\"content\": \"{niche_keyword}에 대한 놀라운 사실입니다...\"}}"
    )
    
    if model_preference == "openai":
        return generate_content_with_openai(config_instance, prompt)
    else:
        try:
            gemini_api_key = config_instance.get_gemini_api_key()
            return generate_content_with_gemini(gemini_api_key, prompt)
        except Exception as e:
            logger.error(
                f"틈새 콘텐츠 생성 중 Gemini 키 로드 실패: {e}", exc_info=True)
            return {"title": "AI 오류", "content": "Gemini 키 로드 실패."}
