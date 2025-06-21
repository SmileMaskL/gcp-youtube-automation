# src/cleanup_manager.py
from google.cloud import storage
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def cleanup_old_files(bucket: storage.Bucket, retention_days: int = 7):
    """
    Cloud Storage 버킷에서 지정된 보관 기간(기본 7일)보다 오래된 파일을 삭제합니다.
    """
    if not bucket:
        logger.error("Cloud Storage bucket object is not provided for cleanup.")
        return

    # 현재 시간을 UTC 기준으로 가져옴 (Cloud Storage 시간과 일치시키는 것이 좋음)
    now = datetime.utcnow()
    
    # 프리 티어 용량 관리를 위해 특정 경로만 정리하도록 제한할 수 있습니다.
    # 예: 'videos/' 폴더와 'thumbnails/' 폴더만 정리
    # 여기서는 모든 파일을 대상으로 하되, 필요시 prefix 필터링 추가
    prefixes_to_clean = ["videos/", "thumbnails/", "api_usage_log.json"] # 정리할 폴더 및 파일

    logger.info(f"Starting cleanup of files older than {retention_days} days in bucket '{bucket.name}'.")
    deleted_count = 0
    
    for prefix in prefixes_to_clean:
        # 'api_usage_log.json' 파일은 사용량 추적에 중요하므로, 전체 파일을 삭제하는 대신
        # 내부의 오래된 데이터만 지우는 로직은 `openai_utils.py`에 구현되어 있습니다.
        # 여기서는 파일 자체를 삭제하는 용도로만 사용합니다.
        if prefix == "api_usage_log.json":
            # api_usage_log.json은 파일 자체가 삭제되면 안되므로 건너뜁니다.
            # 이 파일의 내부 데이터 정리는 openai_utils.py에서 처리됩니다.
            continue 

        blobs = bucket.list_blobs(prefix=prefix) # 특정 접두사(폴더) 내의 파일만 나열
        for blob in blobs:
            # 파일을 업로드할 때 생성 시간 또는 수정 시간이 기록됩니다.
            # 여기서는 blob.time_created (생성 시간)을 기준으로 합니다.
            if blob.time_created and (now - blob.time_created) > timedelta(days=retention_days):
                try:
                    blob.delete()
                    logger.info(f"Deleted old file: gs://{bucket.name}/{blob.name} (Created: {blob.time_created.strftime('%Y-%m-%d %H:%M:%S')})")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete blob {blob.name}: {e}")
    
    logger.info(f"Finished cleanup. Total {deleted_count} old files deleted.")
