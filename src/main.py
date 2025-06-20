import logging
import os
from google.cloud import secretmanager
from src.video_creator import create_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def access_secret_version(secret_id: str, version_id: str = "latest") -> str:
    """
    Google Secret Manager에서 secret을 가져옵니다.
    :param secret_id: secret 이름
    :param version_id: 버전 (기본값 "latest")
    :return: secret 내용 문자열
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID 환경변수가 설정되어 있지 않습니다.")
        
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        secret_payload = response.payload.data.decode("UTF-8")
        logging.info(f"✅ Secret '{secret_id}' 버전 '{version_id}' 성공적으로 읽음")
        return secret_payload
    except Exception as e:
        logging.error(f"Failed to access secret '{secret_id}': {e}")
        raise

def main():
    logging.info("프로그램 시작")
    
    # 필요하다면 Secret Manager에서 시크릿을 미리 읽어 환경변수로 설정 가능
    # 예시: OPENAI_KEYS_JSON secret 읽기 (필요하면 uncomment)
    # openai_keys_json = access_secret_version("OPENAI_KEYS_JSON")
    # os.environ["OPENAI_KEYS_JSON"] = openai_keys_json
    
    # ElevenLabs API Key, Voice ID 등은 GitHub Actions 환경변수 또는 Secret Manager에서 직접 주입한다고 가정
    try:
        create_video()
        logging.info("프로그램 정상 종료")
    except Exception as e:
        logging.error(f"프로그램 비정상 종료: {e}")
        exit(1)

if __name__ == "__main__":
    main()
