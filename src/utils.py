import os
import uuid
import logging
from google.cloud import storage

logger = logging.getLogger(__name__)

def generate_unique_id():
    return str(uuid.uuid4())[:8]

def upload_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str):
    if not os.path.exists(source_file_name):
        logger.error(f"Source file not found for GCS upload: {source_file_name}")
        return False
        
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        # 수정: 82자 → 분할 (원본 23번 라인)
        logger.info(
            f"File {source_file_name} uploaded to "
            f"gs://{bucket_name}/{destination_blob_name}."
        )
        return True
    except Exception as e:
        logger.error(f"Error uploading {source_file_name} to GCS: {e}")
        return False
