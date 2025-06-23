# src/openai_utils.py

import logging
import threading
# F401 'os' imported but unused 제거 (실제 사용되지 않음)

logger = logging.getLogger(__name__)

_openai_key_index = 0
_openai_keys = []
_keys_lock = threading.Lock()


def _load_openai_keys_once(config_instance):
    """
    config에서 OpenAI 키 리스트를 한 번만 로드합니다.
    """
    global _openai_keys
    with _keys_lock:
        if not _openai_keys:
            try:
                _openai_keys = config_instance.get_openai_api_keys()
                if not _openai_keys:
                    logger.warning("Secret Manager에서 로드된 OpenAI API 키가 없습니다.")
            except Exception as e:
                logger.error(f"OpenAI API 키 로드 중 오류 발생: {e}", exc_info=True)
                _openai_keys = []


def get_next_openai_key(config_instance):
    """
    다음 OpenAI API 키를 로테이션 방식으로 가져옵니다.
    """
    global _openai_key_index, _openai_keys

    if not _openai_keys:
        _load_openai_keys_once(config_instance)

    if not _openai_keys:
        raise ValueError("OpenAI API 키가 설정되지 않았거나 로드할 수 없습니다.")

    with _keys_lock:
        current_key = _openai_keys[_openai_key_index]
        _openai_key_index = (_openai_key_index + 1) % len(_openai_keys)
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"OpenAI API 키 로테이션: 다음 키 인덱스 = {_openai_key_index}")
        return current_key
    
