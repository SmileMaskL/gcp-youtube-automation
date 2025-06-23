# src/cleanup_manager.py
import os
import logging
from google.cloud import storage
from datetime import datetime, timedelta # F401 datetime.timedelta 사용되지 않으므로 제거

logger = logging.getLogger(__name__)


class CleanupManager:
    def __init__(self, project_id, bucket_name):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=self.project_id)
        self.bucket = self.storage_client.bucket(self.bucket_name)
        logger.info(f"Cleanup Manager initialized for bucket: {bucket_name}")

    def cleanup_old_gcs_files(self, days_old=7, prefix=""):
        """
        Deletes files older than 'days_old' from a specified GCS bucket prefix.
        """
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"Starting GCS cleanup for files older than {days_old} days "
                    f"in prefix '{prefix}'...")

        now = datetime.utcnow()
        deleted_count = 0

        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            if blob.time_created and (now - blob.time_created).days > days_old:
                try:
                    blob.delete()
                    deleted_count += 1
                    logger.info(f"Deleted old GCS file: {blob.name}")
                except Exception as e:
                    logger.error(f"Failed to delete GCS file {blob.name}: {e}",
                                exc_info=True)

        logger.info(f"GCS cleanup completed. Total {deleted_count} files deleted.")
        return deleted_count

    def cleanup_local_temp_files(self, temp_dir="/tmp"):
        """
        Cleans up temporary files in a local directory.
        """
        logger.info(f"Starting local temp file cleanup in: {temp_dir}")
        deleted_count = 0
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted local temp file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete local temp file {file_path}: {e}",
                                exc_info=True)
        logger.info(f"Local temp file cleanup completed. Total {deleted_count} files deleted.")
        return deleted_count
    
