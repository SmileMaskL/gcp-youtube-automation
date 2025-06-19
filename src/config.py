# src/config.py
import os
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

def setup_logging():
    """
    로깅 설정을 초기화합니다.
    """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.StreamHandler()
                        ])
    # 더 자세한 로그를 원하면 로깅 레벨을 DEBUG로 변경하세요.
    # logging.getLogger('google').setLevel(logging.WARNING)
    # logging.getLogger('urllib3').setLevel(logging.WARNING)

def get_secret(secret_id: str, project_id: str = None) -> str:
    """
    Google Secret Manager에서 시크릿 값을 가져옵니다.
    
    Args:
        secret_id (str): Secret Manager에 저장된 시크릿의 ID.
        project_id (str): GCP 프로젝트 ID. 환경 변수에 없으면 이 값을 사용합니다.
                          Cloud Run Job 환경에서는 GCP_PROJECT_ID가 자동으로 설정됩니다.
    
    Returns:
        str: 시크릿 값.
    
    Raises:
        ValueError: 시크릿을 찾을 수 없거나 접근 권한이 없는 경우.
    """
    if project_id is None:
        project_id = os.environ.get("GCP_PROJECT_ID")
    
    if not project_id:
        logger.error("GCP_PROJECT_ID environment variable is not set. Cannot retrieve secrets.")
        raise ValueError("GCP_PROJECT_ID is not set.")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        logger.info(f"Successfully retrieved secret: {secret_id}")
        return secret_value
    except Exception as e:
        logger.error(f"Failed to retrieve secret '{secret_id}' from Secret Manager: {e}", exc_info=True)
        raise ValueError(f"Could not retrieve secret '{secret_id}'. Check if it exists and service account has access.")

# 전역적으로 로깅 설정 적용
setup_logging()

if __name__ == "__main__":
    # 로컬 테스트를 위한 환경 변수 로드 (실제 배포에서는 필요 없음)
    from dotenv import load_dotenv
    load_dotenv()

    # GCP_PROJECT_ID는 Secrets Manager에 접근하기 위해 필요합니다.
    # 실제 환경에서는 Cloud Run Job에 의해 자동으로 설정됩니다.
    # 로컬 테스트 시에는 .env 파일에 GCP_PROJECT_ID를 명시해야 합니다.
    test_project_id = os.environ.get("GCP_PROJECT_ID")

    if not test_project_id:
        print("Error: GCP_PROJECT_ID environment variable is not set for local testing.")
        print("Please set it in your .env file or command line.")
    else:
        print(f"Testing secret retrieval for project: {test_project_id}")
        try:
            # 예시: ElevenLabs API 키 가져오기
            eleven_key = get_secret("ELEVENLABS_API_KEY", project_id=test_project_id)
            print(f"ElevenLabs API Key (first 5 chars): {eleven_key[:5]}*****")
            
            # 예시: OpenAI Keys JSON 가져오기
            openai_json = get_secret("OPENAI_KEYS_JSON", project_id=test_project_id)
            print(f"OpenAI Keys JSON: {openai_json}")

            # 예시: YouTube OAuth Credentials 가져오기
            youtube_creds = get_secret("YOUTUBE_OAUTH_CREDENTIALS", project_id=test_project_id)
            print(f"YouTube OAuth Credentials: {youtube_creds}")

        except ValueError as e:
            print(f"Failed to retrieve secret during test: {e}")
