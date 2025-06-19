# src/content_generator.py
import logging
from src.ai_manager import AIManager # AIManager 임포트

logger = logging.getLogger(__name__)

# AIManager 인스턴스를 직접 여기서 생성하지 않고,
# batch_processor.py에서 생성하여 전달하거나, 전역적으로 접근하도록 합니다.
# 여기서는 generate_content_with_ai 함수가 ai_manager 인스턴스를 파라미터로 받도록 수정합니다.

def generate_content_with_ai(topic: str, ai_model_name: str):
    """
    AI 모델을 사용하여 특정 주제에 대한 YouTube Shorts 콘텐츠 (스크립트, 제목, 태그, 설명)를 생성합니다.

    Args:
        topic (str): 콘텐츠를 생성할 주제.
        ai_model_name (str): 사용할 AI 모델 이름 ('openai' 또는 'gemini').

    Returns:
        dict: 생성된 콘텐츠 (스크립트, 제목, 태그, 설명) 딕셔너리.
              실패 시 빈 딕셔너리.
    """
    logger.info(f"Generating content for topic: '{topic}' using AI model: {ai_model_name}")

    # AIManager 인스턴스를 함수 내에서 생성하지 않고, 외부에서 주입받아 사용
    # 이렇게 해야 AIManager의 상태 (API 키 로테이션, 사용량)가 유지됩니다.
    ai_manager = AIManager() # 새로운 인스턴스를 생성 (싱글턴 패턴을 사용하지 않는 경우)

    # 콘텐츠 생성 프롬프트
    prompt = f"""
    Please create a script for a 60-second YouTube Shorts video about "{topic}".
    The script should be engaging, concise, and informative.
    Also, suggest a catchy video title (under 100 characters), a brief description (under 500 characters), and relevant tags (comma-separated, up to 10 tags).
    
    Format your response as a JSON object with the following keys:
    "script": "Your video script here...",
    "title": "Your video title here",
    "description": "Your video description here...",
    "tags": "tag1,tag2,tag3..."
    
    Ensure the script is suitable for text-to-speech conversion and visual representation with background videos.
    The tone should be enthusiastic and easy to understand.
    """
    
    try:
        # AIManager를 통해 텍스트 생성 요청
        raw_response = ai_manager.generate_text(prompt, ai_model_name, max_tokens=1500)
        
        if not raw_response:
            logger.error(f"AI ({ai_model_name}) did not return any content for topic: {topic}")
            return {}

        # JSON 파싱 시도
        try:
            content_data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from AI ({ai_model_name}): {e}", exc_info=True)
            logger.error(f"Raw AI response: {raw_response}")
            # JSON 파싱 실패 시, 응답에서 스크립트만이라도 추출 시도
            script_match = re.search(r'"script":\s*"(.*?)(?<!\\)"', raw_response, re.DOTALL)
            title_match = re.search(r'"title":\s*"(.*?)(?<!\\)"', raw_response)
            tags_match = re.search(r'"tags":\s*"(.*?)(?<!\\)"', raw_response)
            description_match = re.search(r'"description":\s*"(.*?)(?<!\\)"', raw_response, re.DOTALL)

            fallback_script = script_match.group(1).replace("\\n", "\n").replace('\\"', '"') if script_match else raw_response
            fallback_title = title_match.group(1) if title_match else f"Generated Shorts on {topic}"
            fallback_tags = tags_match.group(1) if tags_match else f"shorts,{topic.lower().replace(' ', ',')}"
            fallback_description = description_match.group(1).replace("\\n", "\n").replace('\\"', '"') if description_match else f"Explore {topic} in this quick short!"

            content_data = {
                "script": fallback_script,
                "title": fallback_title,
                "description": fallback_description,
                "tags": fallback_tags
            }
            logger.warning("Falling back to regex parsing for content extraction due to JSON error.")

        # 필수 키 확인
        if not all(k in content_data for k in ["script", "title", "description", "tags"]):
            logger.error(f"AI response missing required keys for topic: {topic}. Response: {content_data}")
            return {}

        logger.info(f"Successfully generated content for topic: '{topic}'")
        return content_data

    except Exception as e:
        logger.error(f"An unexpected error occurred during content generation for topic '{topic}': {e}", exc_info=True)
        return {}

# 필요한 경우, 다른 함수들도 여기에 통합
import re
import json # Ensure json is imported

# 테스트용 코드
if __name__ == "__main__":
    from dotenv import load_dotenv
    from src.config import setup_logging
    load_dotenv()
    setup_logging()

    test_topic = "Quantum Computing Breakthroughs"
    
    print(f"\n--- Generating content for '{test_topic}' using AI models ---")
    
    # AI Manager 초기화
    test_ai_manager = AIManager()

    # OpenAI (GPT-4o) 테스트
    print("\n--- Testing with OpenAI (GPT-4o) ---")
    openai_content = generate_content_with_ai(test_topic, "openai")
    if openai_content:
        print(f"Title: {openai_content.get('title')}")
        print(f"Tags: {openai_content.get('tags')}")
        print(f"Script (first 100 chars): {openai_content.get('script')[:100]}...")
    else:
        print("Failed to generate content with OpenAI.")

    # Gemini 테스트
    print("\n--- Testing with Gemini ---")
    gemini_content = generate_content_with_ai(test_topic, "gemini")
    if gemini_content:
        print(f"Title: {gemini_content.get('title')}")
        print(f"Tags: {gemini_content.get('tags')}")
        print(f"Script (first 100 chars): {gemini_content.get('script')[:100]}...")
    else:
        print("Failed to generate content with Gemini.")
    
    print(f"\nFinal OpenAI Usage: {test_ai_manager.get_api_usage('openai')}")
    print(f"Final Gemini Usage: {test_ai_manager.get_api_usage('gemini')}")
