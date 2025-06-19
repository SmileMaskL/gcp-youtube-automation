from google.cloud import storage
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def cleanup_old_files(bucket_name: str, hours_to_keep: int = 24):
    """
    Google Cloud Storage 버킷에서 특정 시간보다 오래된 파일을 삭제합니다.
    Args:
        bucket_name (str): 정리할 Cloud Storage 버킷 이름.
        hours_to_keep (int): 이 시간(시)보다 오래된 파일은 삭제됩니다.
                             무료 할당량 관리를 위해 짧게 설정하는 것이 좋습니다 (예: 1시간, 6시간, 24시간).
    """
    if not bucket_name:
        logger.error("GCP_BUCKET_NAME is not provided. Cannot perform cleanup.")
        return

    logger.info(f"Starting cleanup of old files in GCS bucket '{bucket_name}' older than {hours_to_keep} hours.")
    
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # 현재 시간으로부터 hours_to_keep 시간 이전의 기준 시간 계산
        threshold_time = datetime.utcnow() - timedelta(hours=hours_to_keep)
        
        deleted_count = 0
        for blob in bucket.list_blobs():
            # blob.time_created는 UTC 시간대 aware datetime 객체
            if blob.time_created < threshold_time:
                logger.info(f"Deleting old file: {blob.name} (Created: {blob.time_created})")
                blob.delete()
                deleted_count += 1
        
        logger.info(f"Cleanup completed. Total {deleted_count} old files deleted from GCS bucket '{bucket_name}'.")

    except Exception as e:
        logger.error(f"Error during GCS cleanup: {e}", exc_info=True)
