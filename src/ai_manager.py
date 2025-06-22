    # src/ai_manager.py

    import logging
    from openai import OpenAI
    import google.generativeai as genai
    import json
    import time # 지연 시간 추가

    from openai_utils import get_next_openai_key # OpenAI 키 로테이션 함수 임포트
    from config import Config # config 인스턴스 전달을 위해 임포트

    logger = logging.getLogger(__name__)

    # --- OpenAI (GPT-4o) 콘텐츠 생성 함수 ---
    def generate_content_with_openai(config_instance, prompt_text, model="gpt-4o"):
        """
        OpenAI API (GPT-4o)를 사용하여 콘텐츠를 생성합니다.
        키 로테이션을 적용합니다.
        """
        try:
            openai_api_key = get_next_openai_key(config_instance) # 로테이션 키 가져오기
            client = OpenAI(api_key=openai_api_key)

            logger.info(f"OpenAI (GPT-4o) 모델로 콘텐츠 생성 요청. 모델: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates concise and engaging content for YouTube Shorts. Provide a title and content in JSON format."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format={"type": "json_object"}, # JSON 응답 형식 요청
                temperature=0.7, # 창의성 조절
                max_tokens=200 # 최대 토큰 수
            )
            
            # JSON 응답을 파싱
            content_json = json.loads(response.choices[0].message.content)
            logger.info(f"OpenAI 응답 성공: {content_json.get('title', '제목 없음')}")
            return content_json
        
        except Exception as e:
            logger.error(f"OpenAI (GPT-4o) 콘텐츠 생성 실패: {e}", exc_info=True)
            # 실패 시에도 기본 응답을 반환하여 파이프라인이 멈추지 않도록 합니다.
            return {"title": "AI 콘텐츠 생성 오류", "content": "콘텐츠를 생성하는 데 문제가 발생했습니다. 다시 시도해주세요."}

    # --- Google Gemini 콘텐츠 생성 함수 ---
    def generate_content_with_gemini(gemini_api_key, prompt_text, model="gemini-1.5-flash"):
        """
        Google Gemini API를 사용하여 콘텐츠를 생성합니다.
        """
        try:
            genai.configure(api_key=gemini_api_key)
            model_instance = genai.GenerativeModel(model_name=model)

            logger.info(f"Google Gemini 모델로 콘텐츠 생성 요청. 모델: {model}")
            # JSON 응답을 요청하는 프롬프트 추가
            full_prompt = (
                f"{prompt_text}\n\n"
                f"Your response MUST be a JSON object with two keys: 'title' (string) and 'content' (string). "
                f"Example: {{\"title\": \"추천 제목\", \"content\": \"생성된 내용\"}}"
            )
            
            response = model_instance.generate_content(full_prompt)
            
            # Gemini 응답에서 텍스트 추출 후 JSON 파싱
            content_text = response.text
            # 때때로 응답이 '```json\n{...}\n```' 형태로 올 수 있으므로 파싱 전 처리
            if content_text.startswith("```json"):
                content_text = content_text.replace("```json\n", "").replace("\n```", "")
            
            content_json = json.loads(content_text)
            logger.info(f"Gemini 응답 성공: {content_json.get('title', '제목 없음')}")
            return content_json

        except Exception as e:
            logger.error(f"Google Gemini 콘텐츠 생성 실패: {e}", exc_info=True)
            # 실패 시에도 기본 응답을 반환하여 파이프라인이 멈추지 않도록 합니다.
            return {"title": "AI 콘텐츠 생성 오류", "content": "콘텐츠를 생성하는 데 문제가 발생했습니다. 다시 시도해주세요."}

    # --- 실전 수익화를 위한 아이디어 (추가) ---
    def generate_niche_content(config_instance, niche_keyword, model_preference="openai"):
        """
        특정 틈새시장(Niche) 키워드를 기반으로 콘텐츠를 생성합니다.
        수익화에 유리한 '정보성', '팁', '흥미로운 사실' 등에 초점을 맞춥니다.
        """
        prompt = (
            f"유튜브 쇼츠 영상을 위해 '{niche_keyword}'에 대한 흥미로운 사실, 유용한 팁, 또는 짧은 스토리를 1개 작성해주세요. "
            f"제목과 내용을 포함하는 JSON 형식으로 응답해주세요. 내용은 50단어 이내로 간결하게 작성해주세요. "
            f"예시: {{\"title\": \"{niche_keyword}의 놀라운 비밀\", \"content\": \"{niche_keyword}에 대한 놀라운 사실입니다...\"}}"
        )
        
        if model_preference == "openai":
            return generate_content_with_openai(config_instance, prompt)
        else: # default to gemini
            # Gemini API 키를 직접 전달해야 하므로 config에서 가져와야 함.
            # ai_manager 외부에서 config.get_gemini_api_key()를 호출하여 전달하는 것이 일반적입니다.
            # 여기서는 편의상 config_instance에서 직접 접근 가능하다고 가정합니다.
            try:
                gemini_api_key = config_instance.get_gemini_api_key()
                return generate_content_with_gemini(gemini_api_key, prompt)
            except Exception as e:
                logger.error(f"틈새 콘텐츠 생성 중 Gemini 키 로드 실패: {e}", exc_info=True)
                return {"title": "AI 오류", "content": "Gemini 키 로드 실패."}
    
