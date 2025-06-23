# src/ai_rotation.py
import threading
import time
import logging

logger = logging.getLogger(__name__)


class AIRotationManager:
    def __init__(self, api_keys):
        if not api_keys:
            raise ValueError("API keys list cannot be empty.")
        self.api_keys = api_keys
        self.current_key_index = 0
        self.lock = threading.Lock()
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
    
