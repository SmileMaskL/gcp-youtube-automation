import logging
import sentry_sdk
import os
from google.cloud import logging as cloud_logging
from google.cloud import storage
from google.oauth2 import service_account
import json
import datetime

# GCP 서비스 계정 키를 환경 변수에서 로드
try:
    service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
except Exception as e:
    print(f"Error loading GCP service account key for logging: {e}")
    credentials = None # Fallback if key is not found or invalid

# Cloud Logging 클라이언트 초기화
if credentials:
    client = cloud_logging.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=credentials)
    handler = cloud_logging.handlers.CloudLoggingHandler(client)
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
else:
    # GCP 서비스 계정 키가 없을 경우 로컬 콘솔에만 로깅
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sentry 초기화 (오류 추적)
sentry_dsn = os.getenv("SENTRY_DSN") # GitHub Secret에 SENTRY_DSN을 추가하여 사용 가능
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

def log_system_health(message, level="info"):
    """시스템 상태 및 중요한 이벤트를 로깅합니다."""
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
        if sentry_dsn:
            sentry_sdk.capture_exception()
    elif level == "critical":
        logging.critical(message)
        if sentry_dsn:
            sentry_sdk.capture_exception()

def upload_log_to_gcs(log_file_path, bucket_name, destination_blob_name):
    """로컬 로그 파일을 GCS 버킷에 업로드합니다."""
    try:
        if credentials:
            storage_client = storage.Client(project=os.getenv("GCP_PROJECT_ID"), credentials=credentials)
        else:
            storage_client = storage.Client() # 기본 인증 시도 (Cloud Run 등)

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(log_file_path)
        log_system_health(f"로그 파일 '{log_file_path}'이 GCS 버킷 '{bucket_name}/{destination_blob_name}'에 성공적으로 업로드되었습니다.", level="info")
    except Exception as e:
        log_system_health(f"로그 파일 업로드 중 오류 발생: {e}", level="error")

def monitor_api_usage(api_name, usage_count, max_limit):
    """API 사용량을 모니터링하고 임계치에 도달하면 경고를 로깅합니다."""
    if usage_count >= max_limit:
        log_system_health(f"경고: {api_name} API 일일 사용 한도({max_limit})에 도달했습니다.", level="warning")
    elif usage_count >= max_limit * 0.8: # 80% 사용 시 경고
        log_system_health(f"알림: {api_name} API 일일 사용 한도의 80%({max_limit*0.8})에 도달했습니다. 현재 사용량: {usage_count}", level="warning")
    else:
        log_system_health(f"정보: {api_name} API 현재 사용량: {usage_count}/{max_limit}", level="info")

# 예시: Cloud Logging에서 로그 확인
# GCP 콘솔 > Logging > Logs Explorer 에서 'youtube-automation-project' 프로젝트의 로그를 확인할 수 있습니다.
