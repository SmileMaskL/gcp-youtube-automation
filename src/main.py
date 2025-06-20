# src/main.py

import os
import logging
from google.cloud import secretmanager
from src.video_creator import create_video

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Secret Manager에서 시크릿을 불러오는 함수 (Workload Identity 사용) ---
def access_secret_version(secret_id: str, project_id: str, version_id: str = "latest") -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()  # OIDC 기반 ADC 사용
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        secret_data = response.payload.data.decode("UTF-8")
        logging.info(f"✅ Secret '{secret_id}' 불러오기 성공")
        return secret_data
    except Exception as e:
        logging.error(f"❌ Secret Manager 초기화 실패: {e}")
        raise

# --- 메인 로직 ---
if __name__ == "__main__":
    try:
        # GitHub Actions에서 환경변수로 GCP_PROJECT_ID를 주입했는지 확인
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            logging.error("환경변수 'GCP_PROJECT_ID'가 설정되지 않았습니다.")
            raise ValueError("GCP_PROJECT_ID environment variable is required.")

        # Secret 예시 호출 (원한다면 주석 해제)
        # my_secret_value = access_secret_version("your-secret-id", project_id)

        # 영상 생성 로직 실행
        create_video()

    except Exception as e:
        logging.error(f"❌ 애플리케이션 실행 중 에러 발생: {e}")
        exit(1)
