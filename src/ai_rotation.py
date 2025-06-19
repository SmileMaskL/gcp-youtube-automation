import os
import google.generativeai as genai
from openai import OpenAI
from src.config import (
    get_next_openai_key, GEMINI_API_KEY, get_next_ai_model,
    MAX_OPENAI_CALLS_PER_DAY, MAX_GEMINI_CALLS_PER_DAY
)
from src.usage_tracker import api_usage_tracker
from src.monitoring import log_system_health

class AIRotationManager:
    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self._init_clients()

    def _init_clients(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_client = genai
            log_system_health("Gemini client initialized.", level="info")
        else:
            log_system_health("Gemini API Key not found. Gemini client will not be available.", level="warning")

        try:
            # OpenAI 클라이언트는 키 로테이션을 위해 매번 새로 생성하거나,
            # 내부적으로 키를 업데이트하는 방식 고려. 여기서는 get_next_openai_key()로 키를 가져와 사용
            # 초기화 시에는 첫 번째 키를 사용하거나, 실제 호출 시점에 키를 가져오도록 합니다.
            self.openai_client = OpenAI(api_key=get_next_openai_key())
            log_system_health("OpenAI client initialized with first key.", level="info")
        except Exception as e:
            log_system_health(f"Error initializing OpenAI client: {e}. OpenAI client will not be available.", level="error")
            self.openai_client = None


    def generate_content(self, prompt, model_preference=None, max_tokens=1000, temperature=0.7):
        """
        주어진 프롬프트에 따라 AI 콘텐츠를 생성합니다.
        model_preference를 통해 특정 모델을 우선할 수 있습니다.
        """
        selected_model = model_preference if model_preference else get_next_ai_model()
        log_system_health(f"콘텐츠 생성을 위해 '{selected_model}' 모델을 시도합니다.", level="info")

        for _ in range(2): # 최대 2번 시도 (다른 모델로 폴백)
            if selected_model == "gpt-4o":
                if api_usage_tracker.check_limit("openai", api_usage_tracker.get_usage("openai"), MAX_OPENAI_CALLS_PER_DAY):
                    try:
                        # OpenAI 클라이언트에 항상 최신 키를 사용하도록
                        self.openai_client = OpenAI(api_key=get_next_openai_key())
                        chat_completion = self.openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,
                            temperature=temperature
                        )
                        api_usage_tracker.record_usage("openai")
                        log_system_health("GPT-4o로 콘텐츠를 성공적으로 생성했습니다.", level="info")
                        return chat_completion.choices[0].message.content
                    except Exception as e:
                        log_system_health(f"GPT-4o 콘텐츠 생성 오류: {e}. 다른 모델로 전환합니다.", level="error")
                        selected_model = "gemini" # 오류 발생 시 다음 모델로 전환
                else:
                    log_system_health("GPT-4o 일일 사용 한도 초과. Gemini로 전환합니다.", level="warning")
                    selected_model = "gemini"
            elif selected_model == "gemini":
                if api_usage_tracker.check_limit("gemini", api_usage_tracker.get_usage("gemini"), MAX_GEMINI_CALLS_PER_DAY):
                    if self.gemini_client:
                        try:
                            model = self.gemini_client.GenerativeModel('gemini-pro')
                            response = model.generate_content(prompt,
                                generation_config=genai.types.GenerationConfig(
                                    max_output_tokens=max_tokens,
                                    temperature=temperature
                                )
                            )
                            api_usage_tracker.record_usage("gemini")
                            log_system_health("Gemini로 콘텐츠를 성공적으로 생성했습니다.", level="info")
                            return response.text
                        except Exception as e:
                            log_system_health(f"Gemini 콘텐츠 생성 오류: {e}. 다른 모델로 전환합니다.", level="error")
                            selected_model = "gpt-4o" # 오류 발생 시 다음 모델로 전환
                    else:
                        log_system_health("Gemini 클라이언트가 초기화되지 않았습니다. GPT-4o로 전환합니다.", level="warning")
                        selected_model = "gpt-4o"
                else:
                    log_system_health("Gemini 일일 사용 한도 초과. GPT-4o로 전환합니다.", level="warning")
                    selected_model = "gpt-4o"

            # 첫 시도에서 실패하여 모델이 전환되었다면, 두 번째 시도
            if model_preference: # 초기 선호 모델이 있었던 경우, 폴백 후 다시 시도하지 않음
                break
            else: # 로테이션으로 선택된 경우, 다음 모델로 다시 시도
                log_system_health(f"다음 모델인 '{selected_model}'로 다시 시도합니다.", level="info")


        log_system_health("모든 AI 모델이 콘텐츠 생성에 실패했습니다.", level="error")
        raise Exception("Failed to generate content with any AI model.")

ai_rotation_manager = AIRotationManager()
