from google.cloud import storage
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def cleanup_old_files(bucket: storage.Bucket, retention_days: int = 7):
    if not bucket:
        logger.error("Cloud Storage bucket object is not provided for cleanup.")
        return

    now = datetime.utcnow()
    prefixes_to_clean = ["videos/", "thumbnails/", "api_usage_log.json"]
    logger.info(f"Starting cleanup of files older than {retention_days} days in bucket '{bucket.name}'.")
    deleted_count = 0
    
    for prefix in prefixes_to_clean:
        if prefix == "api_usage_log.json":
            continue 

        blobs = bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            if blob.time_created and (now - blob.time_created) > timedelta(days=retention_days):
                try:
                    blob.delete()
                    logger.info(f"Deleted old file: gs://{bucket.name}/{blob.name} (Created: {blob.time_created.strftime('%Y-%m-%d %H:%M:%S')})")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete blob {blob.name}: {e}")
    
    logger.info(f"Finished cleanup. Total {deleted_count} old files deleted.")
