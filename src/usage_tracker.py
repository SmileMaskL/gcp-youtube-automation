import logging
import os
import json

logger = logging.getLogger(__name__)

# 각 API의 최대 허용 사용량 (무료 티어 기준 또는 설정한 한도)
# 이 값은 프로젝트의 실제 무료 티어 정책에 따라 정확하게 설정해야 합니다.
# YouTube API는 10,000 할당량/일, ElevenLabs는 10,000자/월 등
# 여기서는 대략적인 값이며, 실제 API 문서를 참고하세요.
API_LIMITS = {
    "gemini": 1000, # 예시: 하루 1000회 요청 (실제 무료 할당량 확인 필요)
    "openai": 1000, # 예시: 하루 1000회 요청 (실제 무료 할당량 확인 필요)
    "elevenlabs": 10000, # 예시: 월 10,000자 (이 코드는 글자 수로 계산)
    "pexels": 1000, # 예시: 하루 1000회 요청
    "youtube": 9000, # 예시: 하루 9000 할당량 (10,000 중 1000 남겨둠)
    "news_api": 500, # 예시: 하루 500회 요청
}

# 현재 API 사용량을 저장하는 임시 변수 (Cloud Run Job이 종료되면 초기화됨)
# 장기적인 사용량 관리가 필요하면 Cloud Firestore 등 영구 저장소 사용 필요
current_api_usage = {
    "gemini": 0,
    "openai": 0,
    "elevenlabs": 0,
    "pexels": 0,
    "youtube": 0,
    "news_api": 0
}

def update_usage(api_name, amount=1):
    """API 사용량을 업데이트합니다."""
    if api_name in current_api_usage:
        current_api_usage[api_name] += amount
        logger.info(f"API Usage for {api_name}: {current_api_usage[api_name]}")
    else:
        logger.warning(f"Unknown API name for usage tracking: {api_name}")

def get_current_usage(api_name):
    """현재 API 사용량을 반환합니다."""
    return current_api_usage.get(api_name, 0)

def get_max_limit(api_name):
    """API의 최대 허용 한도를 반환합니다."""
    return API_LIMITS.get(api_name, float('inf')) # 설정되지 않은 API는 무한대로 간주

def check_quota(api_name, current_usage=None):
    """
    API 쿼터를 확인하고, 한도에 근접하면 경고를 출력합니다.
    current_usage: 현재 API 사용량 (없으면 전역 current_api_usage 참조)
    """
    if current_usage is None:
        current_usage = get_current_usage(api_name)

    max_limit = get_max_limit(api_name)
    if max_limit == float('inf'):
        return # 한도가 설정되지 않은 API는 체크하지 않음

    # 80% 이상 사용 시 경고
    if current_usage / max_limit > 0.8:
        logger.warning(f"🚨 ALERT: {api_name} quota is at {current_usage / max_limit:.2%} ({current_usage}/{max_limit}). Consider reducing usage or preparing for new keys.")
    
    # 95% 이상 사용 시 심각 경고
    if current_usage / max_limit > 0.95:
        logger.error(f"🔥 CRITICAL ALERT: {api_name} quota is nearly exhausted at {current_usage / max_limit:.2%} ({current_usage}/{max_limit}). Operations may fail soon.")
        
    # 한도를 초과했을 경우
    if current_usage >= max_limit:
        logger.critical(f"🚫 QUOTA EXCEEDED: {api_name} quota has been fully consumed ({current_usage}/{max_limit}). All subsequent requests will likely fail.")
        # 이 시점에서 해당 API를 사용하는 작업을 중단하거나 다른 키로 전환하는 로직이 필요
        # (로테이션 로직은 content_generator.py에서 처리)
