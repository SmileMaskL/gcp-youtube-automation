import os
import subprocess
import threading
import logging
from flask import Flask, request, jsonify
from src.monitoring import log_system_health

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route('/')
def hello():
    return 'YouTube Automation Service is running. Access /run to start.'


@app.route('/run', methods=['POST'])
def run_automation():
    log_system_health(
        "Automation process triggered via HTTP request.", level="info")
    
    def run_script():
        try:
            result = subprocess.run(
                ["python", "-m", "src.batch_processor"],
                capture_output=True,
                text=True,
                check=True
            )
            log_system_health(
                f"Automation script completed successfully. "
                f"Output: {result.stdout}",
                level="info")
        except subprocess.CalledProcessError as e:
            log_system_health(
                f"Automation script failed. Error: {e.stderr}", level="error")
        except Exception as e:
            log_system_health(
                f"Unexpected error during script execution: {e}", level="error")

    thread = threading.Thread(target=run_script)
    thread.start()
    return jsonify({"status": "Automation process started in background."}), 202


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Flask app will be served by Gunicorn on port {port}")
