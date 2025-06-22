from flask import Flask, jsonify
import subprocess
import threading
import os
from src.monitoring import log_system_health

app = Flask(__name__)

@app.route('/')
def hello():
    return 'YouTube 자동화 서비스 실행 중'

@app.route('/run', methods=['POST'])
def run_automation():
    def run_script():
        try:
            subprocess.run(["python", "src/batch_processor.py"], check=True)
            log_system_health("배치 처리 완료", level="info")
        except Exception as e:
            log_system_health(f"배치 처리 실패: {e}", level="error")

    thread = threading.Thread(target=run_script)
    thread.start()
    return jsonify({"status": "백그라운드에서 처리 시작"}), 202

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
