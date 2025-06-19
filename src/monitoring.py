import logging
import psutil
from datetime import datetime

def log_system_health():
    """시스템 상태 로깅 (CPU, 메모리 사용량)"""
    logger = logging.getLogger(__name__)
    try:
        # CPU 사용량
        cpu_percent = psutil.cpu_percent(interval=1)
        # 메모리 사용량
        memory = psutil.virtual_memory()
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available': memory.available / (1024 ** 2)  # MB 단위
        }
        
        logger.info(
            f"📊 시스템 상태: "
            f"CPU={health_status['cpu_usage']}%, "
            f"메모리={health_status['memory_usage']}% "
            f"(사용 가능: {health_status['memory_available']:.2f}MB)"
        )
        return health_status
    except Exception as e:
        logger.error(f"❌ 시스템 상태 모니터링 실패: {e}")
        return None
