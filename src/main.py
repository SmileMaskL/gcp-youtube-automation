import logging
from google.cloud import secretmanager
from src.video_creator import create_video

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def access_secret_version(secret_id: str, version_id: str = "latest") -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()  # ADC 인증 사용 (OIDC 기반)
        project_id = os.environ.get("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID 환경변수가 설정되지 않았습니다.")

        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Failed to initialize Google Secret Manager client: {e}")
        raise

if __name__ == "__main__":
    try:
        logging.info("✅ GCP Secret Manager 클라이언트 초기화 테스트 중...")

        # 예시: 시크릿 불러오기 (테스트용)
        # my_api_key = access_secret_version("MY_SECRET_ID")
        # logging.info(f"✅ 시크릿 값 일부: {my_api_key[:10]}...")

        # 비디오 생성 실행
        create_video()

    except Exception as e:
        logging.error(f"❌ 애플리케이션 실패: {e}")
        exit(1)
