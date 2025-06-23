# src/utils.py
import os
import uuid
import logging
from google.cloud import storage

logger = logging.getLogger(__name__)

def generate_unique_id():
    """고유한 ID를 생성합니다."""
    return str(uuid.uuid4())[:8]

def upload_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str):
    """
    로컬 파일을 Google Cloud Storage에 업로드합니다.

    Args:
        bucket_name (str): 대상 버킷의 이름.
        source_file_name (str): 업로드할 로컬 파일의 경로.
        destination_blob_name (str): GCS에 저장될 파일의 경로 및 이름.
    """
    if not os.path.exists(source_file_name):
        logger.error(f"Source file not found for GCS upload: {source_file_name}")
        return False
        
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")
        return True
    except Exception as e:
        logger.error(f"Error uploading {source极速赛车开奖直播官网飞飞
