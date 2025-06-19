import logging
import os

logger = logging.getLogger(__name__)

def log_system_health(message: str, level: str = "info"):
    """
    시스템 상태 및 중요한 이벤트를 로깅합니다.
    Args:
        message (str): 로그 메시지.
        level (str): 로그 레벨 ('info', 'warning', 'error', 'critical').
    """
    if level == "info":
        logger.info(f"[HEALTH] {message}")
    elif level == "warning":
        logger.warning(f"[HEALTH] {message}")
    elif level == "error":
        logger.error(f"[HEALTH] {message}")
    elif level == "critical":
        logger.critical(f"[HEALTH] {message}")
    else:
        logger.debug(f"[HEALTH] {message}")

    # 실제 환경에서는 Cloud Logging과 연동하여 중앙 집중식 로그 관리가 필요
    # 예를 들어, print() 대신 Python의 logging 모듈을 사용하면 자동으로 Cloud Logging에 수집될 수 있습니다.
    # 이 프로젝트는 이미 logging 모듈을 사용하고 있으므로 별도 추가 필요 없음.

def get_process_info():
    """
    현재 프로세스의 간단한 정보를 반환합니다.
    (예: 메모리 사용량, CPU 사용량 - 실제 구현은 OS에 따라 복잡)
    """
    # 이 함수는 실제 시스템 모니터링 툴(Datadog, Prometheus 등)에서 데이터를 가져오거나
    # OS별 라이브러리(psutil 등)를 사용하여 구현되어야 합니다.
    # 간단한 예시로 더미 데이터 반환.
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=None) # 논블로킹
        return {
            "pid": os.getpid(),
            "cpu_percent": cpu_percent,
            "memory_usage_mb": mem_info.rss / (1024 * 1024)
        }
    except ImportError:
        logger.warning("psutil not installed. Cannot get detailed process info.")
        return {"pid": os.getpid(), "cpu_percent": "N/A", "memory_usage_mb": "N/A"}
    except Exception as e:
        logger.error(f"Error getting process info: {e}")
        return {"pid": os.getpid(), "cpu_percent": "N/A", "memory_usage_mb": "N/A"}

# 실제 사용은 batch_processor.py 등에서 import 하여 사용.
