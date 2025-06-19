import os
import shutil
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def clean_local_temp_files(retention_days: int = 1):
    """
    temp/ 폴더의 오래된 파일들을 삭제합니다.
    Args:
        retention_days: 파일을 보관할 일수. 이보다 오래된 파일은 삭제됩니다.
    """
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        logger.info(f"임시 폴더 '{temp_dir}'가 존재하지 않습니다. 스킵합니다.")
        return

    now = datetime.now()
    deleted_count = 0
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        if os.path.isfile(filepath):
            try:
                modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if (now - modified_time).days >= retention_days:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"오래된 임시 파일 삭제: {filepath}")
            except Exception as e:
                logger.warning(f"임시 파일 '{filepath}' 삭제 중 오류 발생: {e}")
    
    if deleted_count > 0:
        logger.info(f"총 {deleted_count}개의 오래된 임시 파일 삭제 완료.")
    else:
        logger.info("삭제할 오래된 임시 파일이 없습니다.")

def clean_gcp_bucket_files(bucket_name: str, retention_days: int = 7):
    """
    GCP Cloud Storage 버킷의 오래된 파일들을 삭제합니다.
    GCP_SERVICE_ACCOUNT 환경 변수가 설정되어 있어야 합니다.
    """
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        now = datetime.now(tz=bucket.client._http.transport._credentials.token_info['expires_at_dt'].tz) # 타임존 일치
        deleted_count = 0

        for blob in bucket.list_blobs():
            # blob.time_created는 ISO 8601 문자열 또는 datetime 객체
            # Python 3.7+에서는 datetime.fromisoformat() 사용 가능
            # Python 3.6에서는 dateutil.parser 사용 (pip install python-dateutil)
            # 여기서는 UTC로 가정하고 간단히 처리 (더 정확한 시간 비교를 위해 타임존 고려 필요)
            blob_created_time = blob.time_created
            
            if (now - blob_created_time).days >= retention_days:
                blob.delete()
                deleted_count += 1
                logger.info(f"GCP 버킷에서 오래된 파일 삭제: gs://{bucket_name}/{blob.name}")
        
        if deleted_count > 0:
            logger.info(f"GCP 버킷에서 총 {deleted_count}개의 오래된 파일 삭제 완료.")
        else:
            logger.info("GCP 버킷에서 삭제할 오래된 파일이 없습니다.")

    except ImportError:
        logger.error("google-cloud-storage 라이브러리가 설치되지 않았습니다. pip install google-cloud-storage를 실행하세요.")
    except Exception as e:
        logger.error(f"GCP 버킷 파일 삭제 중 오류 발생: {e}")
