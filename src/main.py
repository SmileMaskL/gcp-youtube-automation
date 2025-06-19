import os
import sys

# src 디렉토리를 Python 경로에 추가 (Github Actions 환경에서 모듈 import 문제 방지)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batch_processor import main as batch_main
from monitoring import log_system_health

if __name__ == "__main__":
    log_system_health("main.py 시작.", level="info")
    try:
        batch_main()
    except Exception as e:
        log_system_health(f"main.py 실행 중 예기치 않은 오류 발생: {e}", level="critical")
    log_system_health("main.py 종료.", level="info")
