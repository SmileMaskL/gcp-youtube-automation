# src/app.py
from flask import Flask, jsonify
import logging
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    """
    API health check endpoint.
    Returns a simple JSON response to indicate the service is running.
    """
    logger.info("Health check endpoint hit.")
    return jsonify({"status": "healthy", "message": "Service is up and running!"}), 200


@app.route("/generate-and-upload", methods=["POST"])
def generate_and_upload_video():
    """
    Endpoint to trigger video generation and upload.
    This would typically be called by a scheduler or external service.
    """
    logger.info("Generate and upload video endpoint hit.")
    try:
        logger.info("Video generation and upload process simulated successfully.")
        return jsonify({
            "status": "success",
            "message": "Video generation and upload triggered successfully."
        }), 200
    except Exception as e:
        logger.error(f"Error during video generation and upload: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to generate and upload video: {str(e)}"
        }), 500


if __name__ == '__main__':
    logger.info("Starting Flask application locally...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    
