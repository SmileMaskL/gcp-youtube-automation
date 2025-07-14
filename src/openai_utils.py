# src/openai_utils.py
<<<<<<< HEAD

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
=======

import logging
import time
import threading
import openai
from typing import Optional, List
from .ai_rotation import AIRotationManager

logger = logging.getLogger(__name__)

# 초기화 블록 ============================================
_openai_key_index = 0
_keys_lock = threading.Lock()
ai_rotation_manager = None  # 지연 초기화용

def initialize_keys(openai_api_keys: List[str], max_retries: int = 3):
    """
    API 키 관리 시스템 초기화 (기존 코드와의 호환성을 위해 유지)
    """
    global ai_rotation_manager
    if not openai_api_keys:
        raise ValueError("API keys list cannot be empty.")
    
    ai_rotation_manager = AIRotationManager(openai_api_keys, max_retries)
    logger.info(f"OpenAI key manager initialized with {len(openai_api_keys)} keys")

# 하위 호환성을 위한 기존 함수 =============================
def get_next_openai_key(openai_api_keys: List[str]) -> str:
    """
    [기존 기능 유지] 단순 키 순환 (AIRotationManager와 연동)
    """
    global _openai_key_index, ai_rotation_manager
    
    # AIRotationManager가 초기화되지 않은 경우 예전 방식 유지
    if ai_rotation_manager is None:
        with _keys_lock:
            key = openai_api_keys[_openai_key_index]
            _openai_key_index = (_openai_key_index + 1) % len(openai_api_keys)
            return key
    
    # 새로운 관리 시스템 사용
    return ai_rotation_manager.get_next_key()

# 향상된 API 기능 ========================================
def generate_text(
    prompt: str,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_retries: int = 3,
    api_keys: Optional[List[str]] = None
) -> Optional[str]:
    """
    향상된 OpenAI 텍스트 생성 함수 (기존 시스템과 신규 시스템 호환)
    
    Args:
        prompt: 입력 프롬프트
        model: 사용할 모델 (기본값: gpt-4o)
        temperature: 창의성 (0.0~2.0)
        max_retries: 최대 재시도 횟수
        api_keys: Optional. 제공시 즉시 초기화
        
    Returns:
        생성된 텍스트 또는 None (실패 시)
    """
    global ai_rotation_manager
    
    # 초기화 확인
    if api_keys:
        initialize_keys(api_keys, max_retries)
    elif ai_rotation_manager is None:
        raise RuntimeError("API keys not initialized. Call initialize_keys() first.")
    
    # 요청 실행
    for attempt in range(max_retries):
        try:
            key = ai_rotation_manager.get_next_key()
            openai.api_key = key
            
            response = openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if any(err in str(e) for err in ["Incorrect API key", "quota", "rate limit"]):
                ai_rotation_manager.mark_failure(key)
            time.sleep(1.5 ** attempt)  # 지수 백오프
    
    logger.error("All retry attempts exhausted")
    return None

# 비동기 버전 ===========================================
async def generate_text_async(prompt: str, **kwargs):
    """generate_text의 비동기 버전"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: generate_text(prompt, **kwargs))

# 기존 코드 호환성을 위한 래퍼 ===========================
def generate_text_legacy(prompt: str, api_keys: List[str], **kwargs):
    """기존 코드와의 호환성을 유지하는 래퍼"""
    initialize_keys(api_keys)
    return generate_text(prompt, **kwargs)
>>>>>>> 39084fc7b559941b38b6aa3e14ae067a1e397f39
