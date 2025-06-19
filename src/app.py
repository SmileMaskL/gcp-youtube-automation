from flask import Flask, request, jsonify
import os
import subprocess
import threading
from src.monitoring import log_system_health

app = Flask(__name__)

@app.route('/')
def hello():
    return 'YouTube Automation Service is running. Access /run to start the automation process.'

@app.route('/run', methods=['POST'])
def run_automation():
    log_system_health("Automation process triggered via HTTP request.", level="info")
    
    # 백그라운드에서 src/batch_processor.py 실행
    # Cloud Run은 요청에 즉시 응답해야 하므로, 오랜 시간 걸리는 작업은 비동기로 처리
    # 실제 프로덕션 환경에서는 Cloud Tasks 또는 Cloud Functions를 트리거하는 방식이 더 견고합니다.
    def run_script():
        try:
            # batch_processor.py를 직접 실행 (환경 변수는 이미 주입됨)
            result = subprocess.run(["python", "-m", "src.batch_processor"], capture_output=True, text=True, check=True)
            log_system_health(f"Automation script completed successfully. Output: {result.stdout}", level="info")
        except subprocess.CalledProcessError as e:
            log_system_health(f"Automation script failed. Error: {e.stderr}", level="error")
        except Exception as e:
            log_system_health(f"Unexpected error during script execution: {e}", level="error")

    # 스크립트를 새 스레드에서 실행하여 HTTP 요청이 즉시 응답하도록 함
    thread = threading.Thread(target=run_script)
    thread.start()

    return jsonify({"status": "Automation process started in background."}), 202

if __name__ == '__main__':
    # Cloud Run은 PORT 환경 변수를 통해 포트를 제공합니다.
    port = int(os.environ.get("PORT", 8080))
    # Gunicorn을 사용하여 프로덕션 환경에서 Flask 앱 실행
    # CMD에서 Gunicorn을 직접 실행할 예정이므로, 이 부분은 로컬 테스트용
    # app.run(host='0.0.0.0', port=port)
    log_system_health(f"Flask app will be served by Gunicorn on port {port}", level="info")
