# src/app.py
import os
import logging
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    logger.info("Health check endpoint hit.")
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Cloud Run용 포트 리스닝
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)
