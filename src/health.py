# src/health.py
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Cloud Function의 헬스 체크 엔드포인트.
    컨테이너가 정상적으로 시작되고 요청을 처리할 수 있는지 확인합니다.
    """
    logger.info("Health check endpoint called.")
    return "OK", 200
