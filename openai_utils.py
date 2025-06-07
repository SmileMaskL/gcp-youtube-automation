import os
import openai
from datetime import datetime, timedelta
import logging

class OpenAIClient:
    def __init__(self):
        self.api_keys = [k.strip() for k in os.getenv('OPENAI_API_KEYS', '').split(',') if k.strip()]
        self.current_key_index = 0
        self.failed_keys = {}  # {key: failure_time}
        self.key_usage = {}    # {key: [timestamps]}
        self.rate_limit = 3    # 분당 최대 요청 수
        self.logger = logging.getLogger(__name__)
        
        if not self.api_keys:
            raise ValueError("No OpenAI API keys configured")

    def _is_key_available(self, key):
        """키 사용 가능 여부 확인"""
        # 실패한 키인지 확인 (30분 동안 차단)
        if key in self.failed_keys:
            if datetime.now() - self.failed_keys[key] < timedelta(minutes=30):
                return False
            del self.failed_keys[key]  # 차단 시간 지난 경우 복구
        
        # 사용량 제한 확인
        if key not in self.key_usage:
            return True
            
        # 최근 1분간의 요청 수 확인
        now = datetime.now()
        recent_calls = [t for t in self.key_usage[key] if now - t < timedelta(minutes=1)]
        return len(recent_calls) < self.rate_limit

    def get_next_key(self):
        """사용 가능한 다음 API 키 반환"""
        valid_keys = [k for k in self.api_keys if self._is_key_available(k)]
        
        if not valid_keys:
            raise RuntimeError("All API keys are temporarily unavailable")
        
        # 라운드 로빈 방식으로 키 선택
        key = valid_keys[self.current_key_index % len(valid_keys)]
        self.current_key_index += 1
        
        # 사용 기록 업데이트
        if key not in self.key_usage:
            self.key_usage[key] = []
        self.key_usage[key].append(datetime.now())
        
        self.logger.info(f"Using API key: {key[:5]}...{key[-5:]}")
        return key

    def mark_key_failed(self, key, error):
        """실패한 키로 표시"""
        self.failed_keys[key] = datetime.now()
        self.logger.error(f"API key failed: {key[:5]}...{key[-5:]}. Error: {str(error)}")

    def generate_content(self, prompt, model="gpt-4", max_retries=5):
        """콘텐츠 생성 요청"""
        for attempt in range(max_retries):
            key = self.get_next_key()
            openai.api_key = key
            
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content.strip()
                
            except openai.error.RateLimitError as e:
                self.mark_key_failed(key, e)
                if attempt == max_retries - 1:
                    raise
            except openai.error.OpenAIError as e:
                self.mark_key_failed(key, e)
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 지수 백오프
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise

        raise RuntimeError(f"Failed after {max_retries} attempts")
