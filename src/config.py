import os
import json
import random
from google.cloud import secretmanager
from google.oauth2 import service_account

# GCP 프로젝트 ID
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "youtube-fully-automated") # GitHub Secret에서 로드됨

# Secret Manager 클라이언트 초기화 (서비스 계정 키로 인증)
def get_secret_client():
    try:
        service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        return secretmanager.SecretManagerServiceClient(credentials=credentials)
    except Exception as e:
        print(f"Error initializing Secret Manager client: {e}")
        # 로컬 개발 환경을 위해 환경 변수에서 읽도록 폴백
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return secretmanager.SecretManagerServiceClient()
        else:
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY 환경 변수가 없거나 유효하지 않습니다.")

SECRET_CLIENT = get_secret_client()

def access_secret_version(secret_id, version_id="latest"):
    name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    try:
        response = SECRET_CLIENT.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret '{secret_id}': {e}")
        # Secret Manager에서 가져오지 못할 경우 환경 변수에서 시도
        return os.getenv(secret_id.upper().replace('-', '_'))

# API 키 로드 (우선순위: GitHub Secret -> Secret Manager -> 환경 변수)
ELEVENLABS_API_KEY = access_secret_version("elevenlabs-api-key")
PEXELS_API_KEY = access_secret_version("pexels-api-key")
GEMINI_API_KEY = access_secret_version("gemini-api-key")
NEWS_API_KEY = access_secret_version("news-api-key") # 선택 사항

# OpenAI 키 로테이션을 위한 리스트
def get_openai_keys():
    openai_keys_json = os.getenv("OPENAI_KEYS_JSON") # GitHub Secret에서 직접 로드
    if openai_keys_json:
        try:
            keys = json.loads(openai_keys_json)
            if isinstance(keys, list) and all(isinstance(key, str) for key in keys):
                return keys
            else:
                print("OPENAI_KEYS_JSON 형식이 올바르지 않습니다. 리스트가 아닙니다.")
                return []
        except json.JSONDecodeError as e:
            print(f"OPENAI_KEYS_JSON 파싱 오류: {e}")
            return []
    else:
        # Secret Manager에서 가져오거나 (이전 방식), 환경 변수에서 시도 (개별 키)
        openai_keys_from_secret = access_secret_version("openai-api-keys")
        if openai_keys_from_secret:
            try:
                keys = json.loads(openai_keys_from_secret)
                if isinstance(keys, list):
                    return keys
                else:
                    print("Secret Manager의 openai-api-keys 형식이 올바르지 않습니다. 리스트가 아닙니다.")
                    return []
            except json.JSONDecodeError as e:
                print(f"Secret Manager의 openai-api-keys 파싱 오류: {e}")
                return []
        print("OPENAI_KEYS_JSON 또는 openai-api-keys secret을 찾을 수 없습니다.")
        return []

OPENAI_API_KEYS = get_openai_keys()
OPENAI_API_KEY_INDEX = 0

def get_next_openai_key():
    global OPENAI_API_KEY_INDEX
    if not OPENAI_API_KEYS:
        raise ValueError("No OpenAI API keys available.")
    key = OPENAI_API_KEYS[OPENAI_API_KEY_INDEX]
    OPENAI_API_KEY_INDEX = (OPENAI_API_KEY_INDEX + 1) % len(OPENAI_API_KEYS)
    return key

# ElevenLabs 음성 ID
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD") # 안나 킴

# Google Cloud Storage 버킷 이름
GCS_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "yt-auto-bucket-001")

# YouTube OAuth Credentials (GitHub Secret에서 직접 로드)
YOUTUBE_OAUTH_CREDENTIALS = os.getenv("YOUTUBE_OAUTH_CREDENTIALS")

# 폰트 경로 (Codespaces 환경에 맞춰 변경)
FONT_PATH = "fonts/Catfont.ttf"
if not os.path.exists(FONT_PATH):
    print(f"Warning: Font file not found at {FONT_PATH}. Please ensure it is uploaded.")
    # Fallback for local testing or if font is elsewhere
    FONT_PATH = "Catfont.ttf" # Adjust if your font is at the root or another accessible path

# AI 모델 설정 (로테이션 관리)
AI_MODELS = ["gemini", "gpt-4o"]
AI_MODEL_INDEX = 0

def get_next_ai_model():
    global AI_MODEL_INDEX
    model = AI_MODELS[AI_MODEL_INDEX]
    AI_MODEL_INDEX = (AI_MODEL_INDEX + 1) % len(AI_MODELS)
    return model

# 기타 설정
OUTPUT_DIR = "output"
LOG_DIR = "logs"
BACKGROUND_IMAGE_DIR = os.path.join(OUTPUT_DIR, "backgrounds")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
THUMBNAIL_DIR = os.path.join(OUTPUT_DIR, "thumbnails")

# API 쿼터 관리 (예시 - 실제 쿼터에 따라 조정 필요)
# 각 API의 무료 티어 한도를 명확히 파악하여 여기에 반영해야 합니다.
# 이 값은 하루에 최대로 호출할 수 있는 횟수를 의미합니다.
MAX_OPENAI_CALLS_PER_DAY = 1000 # 예시: 실제 사용량 및 키 수에 따라 조정
MAX_GEMINI_CALLS_PER_DAY = 1500 # 예시: 실제 사용량 및 무료 티어에 따라 조정
MAX_ELEVENLABS_CHARS_PER_DAY = 100000 # 예시: 실제 사용량 (무료 계정은 1만자)
MAX_PEXELS_CALLS_PER_DAY = 5000 # 예시: 실제 사용량 및 무료 티어에 따라 조정

# API 호출 횟수를 기록하고 초기화하는 메커니즘은 usage_tracker.py에서 구현됩니다.
