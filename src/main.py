import logging
import os
import time
from datetime import datetime

# Import modules from src
from src.config import load_config
from src.content_generator import generate_content # Assumes this handles topic selection (hot issues)
from src.video_creator import create_video # Assumes this handles video creation, shorts conversion, thumbnail generation
from src.youtube_uploader import upload_video # Assumes this handles YouTube upload and comment posting
from src.cleanup_manager import cleanup_old_data # For data retention and free tier limits

# Configure logging for better visibility in GitHub Actions logs
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    handlers=[logging.StreamHandler()])

def run_automation_cycle(config):
    """
    Executes a single cycle of content generation, video creation, and YouTube upload.
    This function will be called multiple times a day based on the GitHub Actions schedule.
    """
    try:
        logging.info(f"--- Starting new automation cycle at {datetime.now()} ---")

        # Step 1: Generate Content (incorporating hot issues, API key rotation)
        logging.info("Step 1: Content generation started.")
        # Pass config to content_generator to manage API keys and news API access
        content = generate_content(config)
        if not content:
            logging.error("Content generation failed. Skipping video creation and upload.")
            return

        logging.info("Step 1: Content generation completed.")

        # Step 2: Create Video (incorporating ElevenLabs for voice, custom font, thumbnail, shorts conversion)
        logging.info("Step 2: Video creation started.")
        # Pass config to video_creator to access ElevenLabs key, voice ID, font path
        video_path = create_video(content, config)
        if not video_path or not os.path.exists(video_path):
            logging.error("Video creation failed or video file not found. Skipping YouTube upload.")
            return
        logging.info(f"Step 2: Video creation completed. Video path: {video_path}")

        # Step 3: Upload Video to YouTube (incorporating YouTube OAuth, comment posting)
        logging.info("Step 3: YouTube upload started.")
        # Pass config to youtube_uploader to access YouTube OAuth credentials
        upload_successful = upload_video(video_path, content, config) # content might contain title/description etc.
        if not upload_successful:
            logging.error("YouTube upload failed.")
            return
        logging.info("Step 3: YouTube upload completed.")

        # Step 4: Cleanup generated video file to save storage space
        try:
            os.remove(video_path)
            logging.info(f"Cleaned up video file: {video_path}")
        except OSError as e:
            logging.warning(f"Error cleaning up video file {video_path}: {e}")

        logging.info(f"--- Automation cycle completed successfully at {datetime.now()} ---")

    except Exception as e:
        logging.exception(f"An unhandled error occurred during automation cycle: {e}")
        # Send error notification (e.g., to Sentry, Slack, or log to a specific file in storage)
        # For this setup, logging to stream and GitHub Actions will capture it.

def main():
    """
    Main entry point for the YouTube automation script.
    Loads configuration and runs the automation cycle.
    """
    config = load_config()

    if not config.get("GCP_PROJECT_ID"):
        logging.critical("GCP_PROJECT_ID is not set in environment variables. Exiting.")
        return
    if not config.get("OPENAI_KEYS") and not config.get("GEMINI_API_KEY"):
        logging.critical("No OpenAI or Gemini API keys loaded. Cannot proceed with content generation. Exiting.")
        return
    if not config.get("ELEVENLABS_API_KEY"):
        logging.critical("ElevenLabs API key not loaded. Cannot proceed with voice generation. Exiting.")
        return
    if not config.get("YOUTUBE_OAUTH_CREDENTIALS"):
        logging.critical("YouTube OAuth credentials not loaded. Cannot upload video. Exiting.")
        return
    if not config.get("FONT_PATH") or not os.path.exists(config.get("FONT_PATH")):
         logging.critical(f"Font file not found at {config.get('FONT_PATH')}. Exiting.")
         return

    # Run the automation cycle
    run_automation_cycle(config)

    # Clean up old data from persistent storage (e.g., GCP Cloud Storage if used for logs/intermediate files)
    # This ensures that free tier limits for storage are not exceeded.
    # The cleanup_old_data function would need to interact with GCP Cloud Storage.
    logging.info("Running daily data cleanup for older generated files...")
    try:
        cleanup_old_data(config, days_to_retain=7) # Retain data for 7 days
        logging.info("Data cleanup completed.")
    except Exception as e:
        logging.error(f"Error during data cleanup: {e}")


if __name__ == "__main__":
    main()
