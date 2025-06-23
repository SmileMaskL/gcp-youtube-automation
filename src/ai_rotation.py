# src/ai_rotation.py
import google.generativeai as genai
from open极 import OpenAI
import logging
from src.config import (
    get_next_openai_key, GEMINI_API_KEY, get_next_ai_model,
    MAX_OPENAI_CALLS_PER_DAY, MAX_GEMINI_CALLS_PER_DAY
)
from src.usage_tracker import api_usage_tracker
from src.monitoring import log_system_health

logger = logging.getLogger(__name__)

class AIRotationManager:
    # ... (생략) ...

    def generate_content(self, prompt, model_preference=None, 
                         max_tokens=1000, temperature=0.7):
        selected_model = model_preference if model_preference \
            else get_next_ai_model()
        log_system_health(
            f"콘텐츠 생성을 위해 '{selected_model}' 모델을 시도합니다.",
            level="info"
        )

        for _ in range(2):
            if selected_model == "gpt-4o":
                if api_usage_tracker.check_limit(
                    "openai", 
                    api_usage_tracker.get_usage("openai"),
                    MAX_OPENAI_CALLS_PER_DAY
                ):
                    try:
                        self.openai_client = OpenAI(
                            api_key=get_next_openai_key()
                        )
                        chat_completion = self.openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,
                            temperature=temperature
                        )
                        api_usage_tracker.record_usage("openai")
                        log_system_health(
                            "GPT-4o로 콘텐츠를 성공적으로 생성했습니다.",
                            level="info"
                        )
                        return chat_completion.choices[0].message.content
                    except Exception as e:
                        log_system_health(
                            f"GPT-4o 콘텐츠 생성 오류: {e}. 다른 모델로 전환합니다.",
                            level="error"
                        )
                        selected_model = "gemini"
                else:
                    log_system_health(
                        "GPT-4o 일일 사용 한도 초과. Gemini로 전환합니다.",
                        level="warning"
                    )
                    selected_model = "gemini"
            
            # ... (gemini 처리 로직도 동일하게 수정) ...

# ... (나머지 코드) ...
