import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def ensure_directory_exists(path: str):
    """주어진 경로에 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Directory created: {path}")

def get_timestamp_string():
    """현재 시간을 기반으로 타임스탬프 문자열을 반환합니다."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_file_size_mb(file_path: str):
    """파일 크기를 MB 단위로 반환합니다."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0
