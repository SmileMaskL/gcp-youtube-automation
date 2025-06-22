    # src/openai_utils.py

    import logging
    import threading
    import os # 파일 존재 여부 확인용

    logger = logging.getLogger(__name__)

    # OpenAI 키 로테이션을 위한 전역 변수 (Cloud Functions 인스턴스 내에서 유지)
    # 실제 프로덕션 환경에서는 영속적인 저장소(예: Redis, Firestore)를 사용해야 하지만,
    # Cloud Functions의 짧은 수명 주기를 고려하여 인메모리 로테이션으로 구현합니다.
    # 인스턴스가 재시작되면 카운터는 0으로 초기화됩니다.
    _openai_key_index = 0
    _openai_keys = []
    _keys_lock = threading.Lock() # 동시성 문제를 방지하기 위한 락

    def _load_openai_keys_once(config_instance):
        """
        config에서 OpenAI 키 리스트를 한 번만 로드합니다.
        (Cloud Function 콜드 스타트 시점에 호출될 것으로 예상)
        """
        global _openai_keys
        with _keys_lock:
            if not _openai_keys: # 아직 로드되지 않았다면
                try:
                    _openai_keys = config_instance.get_openai_api_keys()
                    if not _openai_keys:
                        logger.warning("Secret Manager에서 로드된 OpenAI API 키가 없습니다.")
                except Exception as e:
                    logger.error(f"OpenAI API 키 로드 중 오류 발생: {e}", exc_info=True)
                    _openai_keys = [] # 오류 발생 시 키 목록 초기화

    def get_next_openai_key(config_instance):
        """
        다음 OpenAI API 키를 로테이션 방식으로 가져옵니다.
        """
        global _openai_key_index, _openai_keys
        
        # 키가 아직 로드되지 않았다면 로드 시도
        if not _openai_keys:
            _load_openai_keys_once(config_instance)

        if not _openai_keys:
            raise ValueError("OpenAI API 키가 설정되지 않았거나 로드할 수 없습니다.")

        with _keys_lock:
            # 현재 인덱스에 해당하는 키를 가져옵니다.
            current_key = _openai_keys[_openai_key_index]
            
            # 인덱스를 다음 키로 이동시킵니다. (원형 로테이션)
            _openai_key_index = (_openai_key_index + 1) % len(_openai_keys)
            logger.info(f"OpenAI API 키 로테이션: 다음 키 인덱스 = {_openai_key_index}")
            return current_key

    # 이 파일은 주로 get_next_openai_key 함수를 제공하며,
    # 실제 OpenAI API 호출은 ai_manager.py에서 이루어집니다.
    
