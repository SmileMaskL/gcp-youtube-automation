# src/openai_utils.py
import os
import json
import time
import threading
from collections import deque
from datetime import datetime, timedelta
from google.cloud import storage
import logging

from src.config import config # config에서 API 키와 버킷 정보 가져옴

logger = logging.getLogger(__name__)

class APIKeyManager:
    def __init__(self, openai_keys, gemini_key, bucket_name, usage_file_name):
        self.openai_keys = deque(openai_keys) # 큐로 사용하여 로테이션
        self.gemini_key = gemini_key
        self.current_openai_key = None
        self.current_ai_model = None # 현재 사용 중인 AI 모델 (openai 또는 gemini)

        self.storage_client = storage.Client(project=config.project_id)
        self.bucket = self.storage_client.bucket(bucket_name)
        self.usage_file_name = usage_file_name
        self.usage_data = self._load_usage_data()
        self.lock = threading.Lock() # 스레드 안전성을 위한 락

        # AI 모델 로테이션 순서 (OpenAI 10회, Gemini 1회)
        self.model_rotation_schedule = (['openai'] * 10) + ['gemini']
        self.rotation_index = 0

    def _load_usage_data(self):
        """Cloud Storage에서 API 사용량 데이터를 로드합니다."""
        try:
            blob = self.bucket.blob(self.usage_file_name)
            if blob.exists():
                data = blob.download_as_text()
                loaded_data = json.loads(data)
                logger.info(f"API usage data loaded from GCS: {self.usage_file_name}")
                
                # 사용량 데이터 정비: 이전 날짜 데이터 제거 (예: 30일 이전 데이터)
                current_date = datetime.now().strftime("%Y-%m-%d")
                cleaned_data = {}
                for key, dates in loaded_data.items():
                    cleaned_data[key] = {
                        date: count for date, count in dates.items() 
                        if (datetime.strptime(date, "%Y-%m-%d") >= datetime.now() - timedelta(days=30))
                    }
                return cleaned_data
            else:
                logger.info(f"API usage file not found in GCS: {self.usage_file_name}. Initializing new data.")
                return {}
        except Exception as e:
            logger.error(f"Failed to load API usage data from GCS: {e}")
            return {}

    def _save_usage_data(self):
        """API 사용량 데이터를 Cloud Storage에 저장합니다."""
        try:
            with self.lock:
                blob = self.bucket.blob(self.usage_file_name)
                blob.upload_from_string(json.dumps(self.usage_data, indent=2), content_type="application/json")
                logger.info(f"API usage data saved to GCS: {self.usage_file_name}")
        except Exception as e:
            logger.error(f"Failed to save API usage data to GCS: {e}")

    def _track_usage(self, api_key_or_model_name):
        """API 키/모델 사용량을 추적합니다."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.lock:
            if api_key_or_model_name not in self.usage_data:
                self.usage_data[api_key_or_model_name] = {}
            self.usage_data[api_key_or_model_name][today] = self.usage_data[api_key_or_model_name].get(today, 0) + 1
            self._save_usage_data()

    def get_available_openai_key(self):
        """사용 가능한 OpenAI API 키를 가져오고 로테이션합니다."""
        if not self.openai_keys:
            logger.error("No OpenAI API keys available.")
            return None

        # 쿼터 관리: 각 키마다 하루 호출 횟수 제한 (예: 500회 또는 OpenAI 제한에 맞게 조정)
        # 이 부분은 OpenAI의 실제 API 제한에 따라 조정해야 합니다.
        # 정확한 API 사용량은 OpenAI 대시보드에서 확인해야 합니다.
        MAX_DAILY_CALLS_PER_KEY = 500 # 예시 값

        for _ in range(len(self.openai_keys)): # 모든 키를 확인
            key = self.openai_keys[0] # 현재 키
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 사용량 데이터가 없으면 초기화
            if key not in self.usage_data:
                self.usage_data[key] = {}
            
            # 오늘 사용량 확인
            current_calls = self.usage_data[key].get(today, 0)

            if current_calls < MAX_DAILY_CALLS_PER_KEY:
                self.current_openai_key = key
                self._track_usage(key)
                self.openai_keys.rotate(-1) # 사용한 키는 큐의 뒤로 보냄
                logger.info(f"Using OpenAI API key: {key[:5]}... (Daily calls: {current_calls + 1})")
                return key
            else:
                logger.warning(f"OpenAI API key {key[:5]}... reached daily limit ({MAX_DAILY_CALLS_PER_KEY} calls). Rotating to next key.")
                self.openai_keys.rotate(-1) # 사용 제한에 도달한 키는 뒤로 보냄

        logger.error("All OpenAI API keys have reached their daily limit or are exhausted.")
        return None

    def get_ai_model_for_task(self):
        """현재 작업에 사용할 AI 모델(OpenAI 또는 Gemini)을 결정하고 반환합니다."""
        with self.lock:
            model = self.model_rotation_schedule[self.rotation_index]
            self.rotation_index = (self.rotation_index + 1) % len(self.model_rotation_schedule)
            self.current_ai_model = model
            self._track_usage(model) # 모델별 사용량 추적

            if model == 'openai':
                key = self.get_available_openai_key()
                if key:
                    logger.info(f"Selected AI model: OpenAI (Key: {key[:5]}...)")
                    return 'openai', key
                else:
                    logger.warning("No available OpenAI key. Falling back to Gemini if available.")
                    if self.gemini_key:
                        self.current_ai_model = 'gemini'
                        logger.info("Selected AI model: Gemini (fallback)")
                        self._track_usage('gemini')
                        return 'gemini', self.gemini_key
                    else:
                        logger.error("Neither OpenAI nor Gemini keys are available.")
                        return None, None
            elif model == 'gemini':
                if self.gemini_key:
                    logger.info("Selected AI model: Gemini")
                    return 'gemini', self.gemini_key
                else:
                    logger.warning("Gemini API key not available. Falling back to OpenAI if available.")
                    key = self.get_available_openai_key()
                    if key:
                        self.current_ai_model = 'openai'
                        logger.info(f"Selected AI model: OpenAI (fallback) (Key: {key[:5]}...)")
                        return 'openai', key
                    else:
                        logger.error("Neither OpenAI nor Gemini keys are available.")
                        return None, None
            else:
                logger.error(f"Unknown AI model in rotation schedule: {model}")
                return None, None


# API Key Manager 인스턴스 초기화
# config가 이미 Secret Manager에서 키를 로드했으므로, 그 값을 사용합니다.
api_key_manager = APIKeyManager(
    openai_keys=config.openai_api_keys,
    gemini_key=config.gemini_api_key,
    bucket_name=config.api_usage_tracking_bucket,
    usage_file_name=config.api_usage_tracking_file
)
