# src/openai_utils.py

import threading
import random

_openai_key_index = 0
_keys_lock = threading.Lock()

def get_next_openai_key(openai_api_keys):
    """
    OpenAI API 키를 로테이션 방식으로 반환
    """
    global _openai_key_index
    with _keys_lock:
        key = openai_api_keys[_openai_key_index]
        _openai_key_index = (_openai_key_index + 1) % len(openai_api_keys)
        return key
