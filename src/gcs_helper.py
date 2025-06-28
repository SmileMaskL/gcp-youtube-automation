# src/gcs_helper.py
from google.cloud import storage
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # 모듈별 로거 사용 권장
logger.setLevel(logging.INFO)

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name, project_id):
    """
    Cloud Storage 버킷에 파일을 업로드합니다.
    :param bucket_name: 대상 버킷 이름
    :param source_file_name: 업로드할 로컬 파일 경로
    :param destination_blob_name: Cloud Storage에 저장될 파일 이름
    :param project_id: GCP 프로젝트 ID
    """
    logger.info(f"GCS에 파일 업로드 시작: {source_file_name} -> gs://{bucket_name}/{destination_blob_name}")
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"GCS 업로드 성공: {destination_blob_name}")
    except Exception as e:
        logger.error(f"GCS 업로드 실패: {e}")
        raise

def download_from_gcs(bucket_name, source_blob_name, destination_file_name, project_id):
    """
    Cloud Storage 버킷에서 파일을 다운로드합니다.
    :param bucket_name: 대상 버킷 이름
    :param source_blob_name: Cloud Storage의 파일 이름
    :param destination_file_name: 다운로드될 로컬 파일 경로
    :param project_id: GCP 프로젝트 ID
    """
    logger.info(f"GCS에서 파일 다운로드 시작: gs://{bucket_name}/{source_blob_name} -> {destination_file_name}")
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        # 대상 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        
        blob.download_to_filename(destination_file_name)
        logger.info(f"GCS 다운로드 성공: {destination_file_name}")
    except Exception as e:
        logger.error(f"GCS 다운로드 실패: {e}")
        raise

def delete_from_gcs(bucket_name, blob_name, project_id):
    """
    Cloud Storage 버킷에서 파일을 삭제합니다.
    :param bucket_name: 대상 버킷 이름
    :param blob_name: 삭제할 Cloud Storage 파일 이름
    :param project_id: GCP 프로젝트 ID
    """
    logger.info(f"GCS에서 파일 삭제 시작: gs://{bucket_name}/{blob_name}")
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"GCS 파일 삭제 성공: {blob_name}")
    except Exception as e:
        logger.error(f"GCS 파일 삭제 실패: {e}")
        raise
