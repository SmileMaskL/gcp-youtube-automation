<<<<<<< HEAD
# src/ai_rotation.py
import threading
import time
import logging

logger = logging.getLogger(__name__)


class AIRotationManager:
    def __init__(self, api_keys):
=======
import threading
import time
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class AIRotationManager:
    def __init__(self, api_keys: List[str], max_retries: int = 3):
        """
        Args:
            api_keys: OpenAI API 키 리스트
            max_retries: 키 실패 시 최대 재시도 횟수
        """
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
        if not api_keys:
            raise ValueError("API keys list cannot be empty.")
        self.api_keys = api_keys
        self.current_key_index = 0
        self.lock = threading.Lock()
<<<<<<< HEAD
        logger.info(f"AI Rotation Manager initialized with {len(api_keys)} keys.")

    def get_next_key(self):
        """Returns the next API key in a round-robin fashion."""
        with self.lock:
            key = self.api_keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info(f"Returning key at index {self.current_key_index - 1}. "
                        f"Next key index: {self.current_key_index}")
            return key

    def rotate_key_on_failure(self, failed_key):
        """Moves a failed key to the end or removes it if persistently failing."""
        with self.lock:
            if failed_key in self.api_keys:
                self.api_keys.remove(failed_key)
                self.api_keys.append(failed_key)
                # E501 해결: 줄 길이를 79자 이하로 맞춤
                logger.warning(f"Key {failed_key[:5]}... moved to end of rotation "
                               f"due to failure.")
            if not self.api_keys:
                raise RuntimeError("All API keys have failed.")
        self.current_key_index = self.current_key_index % len(self.api_keys)

# Example usage (if this file were directly executable or for testing)
if __name__ == '__main__':
    test_keys = ["key1_abc", "key2_def", "key3_ghi"]
    rotation_manager = AIRotationManager(test_keys)

    print("--- Testing key rotation ---")
    for _ in range(5):
        print(f"Current key: {rotation_manager.get_next_key()}")
        time.sleep(0.1)

    print("\n--- Testing key failure rotation ---")
    try:
        print(f"Using key: {rotation_manager.get_next_key()}")
        rotation_manager.rotate_key_on_failure("key1_abc")
        print("Key1 failed, rotated.")

        print(f"Using key: {rotation_manager.get_next_key()}")
        print(f"Using key: {rotation_manager.get_next_key()}")

    except RuntimeError as e:
        print(f"Error: {e}")
    
=======
        self.fail_counts = {key: 0 for key in api_keys}
        self.max_retries = max_retries
        logger.info(f"Initialized with {len(api_keys)} keys (max retries: {max_retries})")

    def get_next_key(self) -> str:
        """사용 가능한 다음 API 키를 반환 (라운드 로빈)"""
        with self.lock:
            for _ in range(len(self.api_keys)):
                key = self.api_keys[self.current_key_index]
                if self.fail_counts[key] < self.max_retries:
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    logger.debug(f"Using key: {key[:5]}... (Index: {self.current_key_index})")
                    return key
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            raise RuntimeError("All keys exceeded maximum retry attempts")

    def mark_failure(self, failed_key: str):
        """실패한 키 기록 및 회전 처리"""
        with self.lock:
            if failed_key in self.fail_counts:
                self.fail_counts[failed_key] += 1
                logger.warning(
                    f"Key {failed_key[:5]}... failed "
                    f"(attempt {self.fail_counts[failed_key]}/{self.max_retries})"
                )
                
                if self.fail_counts[failed_key] >= self.max_retries:
                    logger.error(f"Key {failed_key[:5]}... permanently disabled")

# 테스트 코드
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_keys = ["key1_abc", "key2_def", "key3_ghi"]
    manager = AIRotationManager(test_keys, max_retries=2)

    # 정상 동작 테스트
    print("--- Normal rotation ---")
    for _ in range(5):
        print(manager.get_next_key())

    # 실패 시뮬레이션
    print("\n--- Failure simulation ---")
    manager.mark_failure("key1_abc")
    manager.mark_failure("key1_abc")  # 2회 실패 -> 비활성화
    for _ in range(5):
        try:
            print(manager.get_next_key())
        except RuntimeError as e:
            print(f"Error: {e}")
            break
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
