from google.cloud import storage
from google.oauth2 import service_account
import json
import os
from datetime import datetime, timedelta
from src.config import GCP_PROJECT_ID, GCS_BUCKET_NAME
from src.monitoring import log_system_health

# GCP 서비스 계정 키를 환경 변수에서 로드
try:
    service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
except Exception as e:
    log_system_health(f"Error loading GCP service account key for cleanup: {e}", level="error")
    credentials = None # Fallback if key is not found or invalid

def cleanup_gcs_bucket(days_old=7):
    """
    Cloud Storage 버킷에서 지정된 기간(days_old)보다 오래된 파일을 삭제합니다.
    무료 티어 용량 관리를 위해 주기적으로 실행해야 합니다.
    """
    if not GCS_BUCKET_NAME:
        log_system_health("GCS_BUCKET_NAME이 설정되지 않았습니다. 버킷 정리를 건너뜀.", level="warning")
        return

    try:
        if credentials:
            storage_client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
        else:
            storage_client = storage.Client() # Default credentials (e.g., Cloud Run environment)

        bucket = storage_client.bucket(GCS_BUCKET_NAME)

        # 삭제 기준 날짜 계산
        threshold_date = datetime.utcnow() - timedelta(days=days_old)
        log_system_health(f"GCS 버킷 '{GCS_BUCKET_NAME}'에서 {threshold_date} 이전 파일 정리 시작.", level="info")

        deleted_count = 0
        for blob in bucket.list_blobs():
            if blob.time_created.replace(tzinfo=None) < threshold_date:
                try:
                    blob.delete()
                    log_system_health(f"파일 삭제됨: {blob.name} (생성일: {blob.time_created})", level="info")
                    deleted_count += 1
                except Exception as e:
                    log_system_health(f"파일 '{blob.name}' 삭제 중 오류 발생: {e}", level="error")

        log_system_health(f"GCS 버킷 '{GCS_BUCKET_NAME}'에서 총 {deleted_count}개의 오래된 파일이 삭제되었습니다.", level="info")

    except Exception as e:
        log_system_health(f"GCS 버킷 정리 중 오류 발생: {e}", level="error")
        raise ValueError(f"GCS 버킷 정리 실패: {e}")

# For local testing (optional)
if __name__ == "__main__":
    # GCP_PROJECT_ID 및 GCS_BUCKET_NAME 환경 변수를 설정하고 실행
    # export GCP_PROJECT_ID="your-project-id"
    # export GCP_BUCKET_NAME="your-bucket-name"
    # export GCP_SERVICE_ACCOUNT_KEY='{"type": "service_account", ...}'
    try:
        print("Running GCS cleanup test...")
        cleanup_gcs_bucket(days_old=0) # 모든 파일 삭제 (주의!)
        print("GCS cleanup test completed. Please check your bucket.")
    except Exception as e:
        print(f"Error during GCS cleanup test: {e}")
