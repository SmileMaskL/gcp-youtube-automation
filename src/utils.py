# src/utils.py
import logging
from google.cloud import storage
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def upload_to_gcs(bucket_name, source_file_name, destination_blob_name, project_id=None):
    """Uploads a file to the Google Cloud Storage bucket."""
    try:
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"Uploading {source_file_name} to GCS bucket '{bucket_name}' "
                    f"as '{destination_blob_name}'...")
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to {destination_blob_name} in GCS.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {source_file_name} to GCS: {e}", exc_info=True)
        return False


def download_from_gcs(bucket_name, source_blob_name, destination_file_name, project_id=None):
    """Downloads a blob from the Google Cloud Storage bucket."""
    try:
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"Downloading {source_blob_name} from GCS bucket '{bucket_name}' "
                    f"to '{destination_file_name}'...")
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        logger.info(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
        return True
    except Exception as e:
        logger.error(f"Failed to download {source_blob_name} from GCS: {e}", exc_info=True)
        return False


def generate_unique_filename(prefix="", suffix="", extension=".mp4"):
    """Generates a unique filename based on current timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}{timestamp}{suffix}{extension}"


def get_file_extension(filename):
    """Extracts file extension from a filename."""
    return os.path.splitext(filename)[1]


def ensure_dir(directory):
    """Ensures that a directory exists, creates it if not."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


def cleanup_local_file(file_path):
    """Deletes a local file if it exists."""
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up local file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete local file {file_path}: {e}", exc_info=True)
            return False
    return False
    
