import time
import logging

logger = logging.getLogger(__name__)

def retry_on_failure(func, max_retries=3, delay_seconds=5):
    """
    함수 실행을 재시도하는 데코레이터/헬퍼 함수.
    func: 실행할 함수
    max_retries: 최대 재시도 횟수
    delay_seconds: 재시도 전 대기 시간 (지수 백오프 적용)
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__ if hasattr(func, '__name__') else 'anonymous function'}: {e}")
            if attempt < max_retries - 1:
                sleep_time = delay_seconds * (2 ** attempt) + random.uniform(0, 1) # 지수 백오프 + 랜덤 지터
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"All {max_retries} attempts failed for {func.__name__ if hasattr(func, '__name__') else 'anonymous function'}.")
                raise # 모든 재시도 실패 시 예외 다시 발생
