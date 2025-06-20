# src/main.py (또는 Secret Manager를 초기화하는 파일)

import os
import json
import logging
from google.cloud import secretmanager # google-cloud-secret-manager 라이브러리 사용
from src.video_creator import create_video # Assumes this handles video creation, shorts conversion, thumbnail generation

# 로깅 설정 (기존 코드에 이미 있을 수 있습니다)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Google Secret Manager 클라이언트 초기화 수정 ---
def initialize_secret_manager_client():
    try:
        # GCP_SERVICE_ACCOUNT_KEY 환경 변수에서 서비스 계정 키 JSON 문자열을 읽어옴
        # 이 환경 변수는 GitHub Actions Secrets에서 주입됩니다.
        gcp_service_account_info = os.getenv("GCP_SERVICE_ACCOUNT_KEY")

        if not gcp_service_account_info:
            logging.error("Environment variable 'GCP_SERVICE_ACCOUNT_KEY' not found.")
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY environment variable is not set.")

        # JSON 문자열을 파싱하여 클라이언트 초기화에 사용
        # credential 정보를 직접 전달하는 방식
        credentials_info = json.loads(gcp_service_account_info)

        # secretmanager.SecretManagerServiceClient는 credentials 매개변수를 받지 않습니다.
        # 대신, GOOGLE_APPLICATION_CREDENTIALS 환경 변수를 사용하거나
        # default credentials가 자동으로 로드되도록 해야 합니다.

        # 가장 좋은 방법은 환경 변수를 통해 credential을 설정하는 것입니다.
        # GitHub Actions 워크플로우에서 이 작업을 수행합니다.
        # secrets.GCP_SERVICE_ACCOUNT_KEY 내용을 임시 파일로 만들고
        # GOOGLE_APPLICATION_CREDENTIALS 환경 변수를 해당 파일 경로로 설정합니다.

        # 여기서는 Secret Manager 클라이언트 자체는 인증 정보를 명시적으로 받지 않고,
        # GOOGLE_APPLICATION_CREDENTIALS 환경 변수 (GitHub Actions에서 설정)를 통해 인증됩니다.
        client = secretmanager.SecretManagerServiceClient()
        logging.info("Google Secret Manager client initialized successfully.")
        return client
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode GCP_SERVICE_ACCOUNT_KEY JSON: {e}")
        raise ValueError(f"Invalid JSON in GCP_SERVICE_ACCOUNT_KEY environment variable: {e}")
    except Exception as e:
        logging.error(f"Failed to initialize Google Secret Manager client: {e}")
        raise

# --- 사용 예시 ---
if __name__ == "__main__":
    try:
        # GitHub Actions workflow에서 gcp_key.json 파일을 생성하고
        # GOOGLE_APPLICATION_CREDENTIALS 환경 변수를 설정한다고 가정합니다.
        # 따라서 여기서 Secret Manager 클라이언트 초기화는 별도의 credentials 파싱 없이 진행됩니다.
        sm_client = initialize_secret_manager_client()

        # 예시: Secret Manager에서 'my-secret'이라는 비밀을 가져오는 방법
        # project_id = os.getenv("GCP_PROJECT_ID") # GitHub Actions에서 project_id도 환경변수로 주입한다고 가정
        # if project_id:
        #     secret_name = f"projects/{project_id}/secrets/my-secret/versions/latest"
        #     response = sm_client.access_secret_version(request={"name": secret_name})
        #     secret_payload = response.payload.data.decode("UTF-8")
        #     logging.info(f"Successfully retrieved secret: {secret_payload[:20]}...") # 일부만 출력
        # else:
        #     logging.warning("GCP_PROJECT_ID environment variable not set. Cannot access secrets.")

        # 비디오 생성 로직 호출
        create_video()

    except Exception as e:
        logging.error(f"Application terminated with an error: {e}")
        # 오류 발생 시 GitHub Actions가 실패하도록 exit code 1 반환
        exit(1)
