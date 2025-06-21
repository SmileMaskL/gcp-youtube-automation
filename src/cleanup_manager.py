# src/cleanup_manager.py
import logging
from datetime import datetime, timedelta
from google.cloud import storage

logger = logging.getLogger(__name__)

def cleanup_old_files(bucket: storage.Bucket, days_old: int = 7):
    """
    Cloud Storage 버킷에서 지정된 일수보다 오래된 파일을 삭제합니다.
    """
    try:
        threshold_date = datetime.now() - timedelta(days=days_old)
        logger.info(f"Starting cleanup of Cloud Storage files older than {threshold_date.strftime('%Y-%m-%d')}")

        deleted_count = 0
        for blob in bucket.list_blobs():
            if blob.time_created.replace(tzinfo=None) < threshold_date: # 시간대 정보 제거 비교
                logger.info(f"Deleting old file: {blob.name} (created: {blob.time_created})")
                blob.delete()
                deleted_count += 1
        
        logger.info(f"Cleanup complete. Deleted {deleted_count} old files from Cloud Storage.")
        return True
    except Exception as e:
        logger.error(f"Error during Cloud Storage cleanup: {e}", exc_info=True)
        return False
