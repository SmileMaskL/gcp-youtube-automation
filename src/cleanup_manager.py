import os
from datetime import datetime, timedelta
from pathlib import Path
from .config import Config

class CleanupManager:
    @staticmethod
    def auto_clean():
        """주간 정리 작업 수행"""
        # 7일 이상된 파일 삭제
        for file in Config.OUTPUT_DIR.glob("*"):
            if file.is_file() and (datetime.now() - datetime.fromtimestamp(file.stat().st_mtime)) > timedelta(days=7):
                file.unlink()
        
        # 로그 파일 정리 (30일 보관)
        for log_file in Config.LOG_DIR.glob("*.log"):
            if (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)) > timedelta(days=30):
                log_file.unlink()
