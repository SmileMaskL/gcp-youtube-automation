# src/cleanup_manager.py
import os
import logging
from datetime import datetime, timedelta, timezone
from google.cloud import storage

logger = logging.getLogger(__name__)

def cleanup_old_files(bucket_name: str, hours_to_keep: int = 24):
    """
    Google Cloud Storage 버킷에서 특정 시간보다 오래된 파일을 삭제합니다.
    
    Args:
        bucket_name (str): 정리할 GCS 버킷의 이름.
        hours_to_keep (int): 이 시간(이전)보다 오래된 파일은 삭제됩니다.
    """
    logger.info(f"Starting GCS cleanup for bucket '{bucket_name}'. Keeping files newer than {hours_to_keep} hours.")
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # 현재 시간에서 지정된 시간(hours_to_keep)을 뺀 시간 계산
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_to_keep)
        
        deleted_count = 0
        for blob in bucket.list_blobs():
            # blob.time_created는 UTC 시간입니다.
            if blob.time_created < threshold_time:
                logger.info(f"Deleting old file: {blob.name} (Created: {blob.time_created})")
                blob.delete()
                deleted_count += 1
        
        logger.info(f"GCS cleanup completed for bucket '{bucket_name}'. Deleted {deleted_count} files older than {hours_to_keep} hours.")
        return True
    except Exception as e:
        logger.error(f"Error during GCS cleanup for bucket '{bucket_name}': {e}", exc_info=True)
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    from src.config import setup_logging
    load_dotenv()
    setup_logging()

    test_bucket_name = os.environ.get("GCP_BUCKET_NAME")
    if not test_bucket_name:
        print("Please set GCP_BUCKET_NAME environment variable for local testing.")
    else:
        print(f"Running cleanup test on bucket: {test_bucket_name}")
        # 테스트를 위해 임시 파일을 업로드하고 삭제해 볼 수 있습니다.
        # 예시:
        # from src.utils import upload_to_gcs
        # import time
        # temp_file_path = "temp_old_file.txt"
        # with open(temp_file_path, "w") as f:
        #     f.write("This is an old file.")
        # upload_to_gcs(test_bucket_name, temp_file_path, "old_files/temp_old_file.txt")
        # print("Uploaded a temporary file. Waiting 5 seconds to simulate older file...")
        # time.sleep(5)
        # if cleanup_old_files(test_bucket_name, hours_to_keep=0.001): # 아주 짧은 시간으로 테스트
        #     print("Cleanup test completed.")
        # else:
        #     print("Cleanup test failed.")
        # os.remove(temp_file_path)

        # 실제 사용 시:
        # cleanup_old_files(test_bucket_name, hours_to_keep=24) # 24시간 이전 파일 삭제
        print("\nNote: For a real test, ensure you have old files in your GCS bucket.")
        print(f"Initiating cleanup for {test_bucket_name} with 24 hours retention...")
        cleanup_old_files(test_bucket_name, hours_to_keep=24)
