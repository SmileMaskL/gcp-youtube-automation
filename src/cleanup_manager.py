# src/cleanup_manager.py
import logging
from datetime import datetime, timedelta
from google.cloud import storage

logger = logging.getLogger(__name__)

def cleanup_old_files(bucket: storage.Bucket, retention_days: int = 7):
    """
    Cloud Storage 버킷에서 지정된 보존 기간(일)보다 오래된 파일을 삭제합니다.
    주로 'videos/' 및 'thumbnails/' 프리픽스 내의 파일을 대상으로 합니다.

    Args:
        bucket (google.cloud.storage.Bucket): 정리할 Cloud Storage 버킷 객체.
        retention_days (int): 파일을 보존할 일수. 이 일수보다 오래된 파일은 삭제됩니다.
    """
    logger.info(f"Starting cleanup of old files in bucket '{bucket.name}'. Retention days: {retention_days}")
    
    cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
    deleted_count = 0

    # 'videos/' 폴더 내 파일 정리
    for blob in bucket.list_blobs(prefix="videos/"):
        if blob.time_created < cutoff_time:
            try:
                blob.delete()
                logger.info(f"Deleted old video file: {blob.name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete video file {blob.name}: {e}")
    
    # 'thumbnails/' 폴더 내 파일 정리
    for blob in bucket.list_blobs(prefix="thumbnails/"):
        if blob.time_created < cutoff_time:
            try:
                blob.delete()
                logger.info(f"Deleted old thumbnail file: {blob.name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete thumbnail file {blob.name}: {e}")

    logger.info(f"Finished cleanup. Total {deleted_count} old files deleted from bucket '{bucket.name}'.")

if __name__ == "__main__":
    # 이 부분은 로컬 테스트용이며, 실제 환경에서는 Cloud Function이 bucket 객체를 전달합니다.
    # 로컬에서 테스트하려면 GCP Credential과 버킷 이름이 필요합니다.
    from src.config import config
    try:
        if config.project_id and config.bucket_name:
            local_storage_client = storage.Client(project=config.project_id)
            local_bucket = local_storage_client.bucket(config.bucket_name)
            print("--- Running local test of cleanup_old_files ---")
            cleanup_old_files(local_bucket, retention_days=1) # 1일 이상된 파일 테스트 삭제
            print("--- Local test finished ---")
        else:
            print("GCP_PROJECT_ID and GCP_BUCKET_NAME are not set in config. Skipping local cleanup test.")
    except Exception as e:
        print(f"Error during local cleanup test setup: {e}")
