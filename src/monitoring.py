import logging
import psutil

def log_system_health():
    logger = logging.getLogger(__name__)
    try:
        # CPU 사용량
        cpu_percent = psutil.cpu_percent()
        # 메모리 사용량
        memory = psutil.virtual_memory()
        
        logger.info(f"✅ 시스템 상태: CPU 사용량={cpu_percent}%, 메모리 사용량={memory.percent}%")
        return True
    except Exception as e:
        logger.error(f"❌ 시스템 상태 모니터링 실패: {e}")
        return False
