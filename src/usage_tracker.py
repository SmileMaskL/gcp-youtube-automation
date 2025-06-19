import json
import os
from datetime import datetime, timedelta
from google.cloud import storage
from google.oauth2 import service_account
from src.monitoring import log_system_health
from src.config import GCP_PROJECT_ID, GCS_BUCKET_NAME # config에서 GCP 설정 가져오기

# GCP 서비스 계정 키를 환경 변수에서 로드
try:
    service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
except Exception as e:
    log_system_health(f"Error loading GCP service account key for usage tracker: {e}", level="error")
    credentials = None # Fallback if key is not found or invalid

def get_storage_client():
    if credentials:
        return storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
    else:
        return storage.Client() # Default credentials (e.g., Cloud Run environment)

def load_usage_data(bucket_name, blob_name="api_usage_data.json"):
    """GCS에서 API 사용량 데이터를 로드합니다."""
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        data = blob.download_as_text()
        return json.loads(data)
    except Exception as e:
        log_system_health(f"사용량 데이터 로드 실패 또는 파일 없음 ({e}). 새 데이터 생성.", level="warning")
        return {}

def save_usage_data(usage_data, bucket_name, blob_name="api_usage_data.json"):
    """API 사용량 데이터를 GCS에 저장합니다."""
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        blob.upload_from_string(json.dumps(usage_data))
        log_system_health("API 사용량 데이터가 GCS에 성공적으로 저장되었습니다.", level="info")
    except Exception as e:
        log_system_health(f"API 사용량 데이터 저장 실패: {e}", level="error")

class APIUsageTracker:
    def __init__(self, bucket_name=GCS_BUCKET_NAME, blob_name="api_usage_data.json"):
        self.bucket_name = bucket_name
        self.blob_name = blob_name
        self.usage_data = self.load_data()
        self._initialize_daily_data()

    def load_data(self):
        return load_usage_data(self.bucket_name, self.blob_name)

    def save_data(self):
        save_usage_data(self.usage_data, self.bucket_name, self.blob_name)

    def _initialize_daily_data(self):
        """매일 자정에 사용량 데이터를 초기화합니다."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if "last_reset_date" not in self.usage_data or self.usage_data["last_reset_date"] != today_str:
            self.usage_data["daily_counts"] = {
                "openai": 0,
                "gemini": 0,
                "elevenlabs_chars": 0,
                "pexels": 0
            }
            self.usage_data["last_reset_date"] = today_str
            log_system_health(f"API 일일 사용량 데이터가 {today_str}로 초기화되었습니다.", level="info")
            self.save_data() # 초기화 후 즉시 저장

    def record_usage(self, api_name, count=1):
        """API 사용량을 기록합니다."""
        self._initialize_daily_data() # 매 호출 시점에도 날짜 확인 및 초기화
        if api_name in self.usage_data["daily_counts"]:
            self.usage_data["daily_counts"][api_name] += count
            log_system_health(f"API 사용량 기록: {api_name} +{count}. 총: {self.usage_data['daily_counts'][api_name]}", level="info")
        else:
            self.usage_data["daily_counts"][api_name] = count
            log_system_health(f"새로운 API '{api_name}' 사용량 기록: {count}", level="info")
        self.save_data()

    def get_usage(self, api_name):
        """특정 API의 현재 사용량을 반환합니다."""
        self._initialize_daily_data()
        return self.usage_data["daily_counts"].get(api_name, 0)

    def check_limit(self, api_name, current_usage, max_limit):
        """API 사용 한도를 확인하고 초과 여부를 반환합니다."""
        if current_usage >= max_limit:
            log_system_health(f"경고: {api_name} API 일일 사용 한도({max_limit})를 초과했습니다. 현재: {current_usage}", level="warning")
            return False
        return True

    def reset_daily_usage(self):
        """수동으로 일일 사용량을 초기화합니다."""
        self.usage_data["daily_counts"] = {
            "openai": 0,
            "gemini": 0,
            "elevenlabs_chars": 0,
            "pexels": 0
        }
        self.usage_data["last_reset_date"] = datetime.now().strftime("%Y-%m-%d")
        self.save_data()
        log_system_health("API 일일 사용량이 수동으로 초기화되었습니다.", level="info")

# APIUsageTracker 인스턴스 생성
api_usage_tracker = APIUsageTracker()
