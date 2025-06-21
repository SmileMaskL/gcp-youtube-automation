import os
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Config:
    def __init__(self):
        logger.info("📦 Config 초기화 시작...")

        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

        if not self.gcp_project_id:
            logger.critical("❗ 환경 변수 GCP_PROJECT_ID가 누락되었습니다.")
            raise ValueError("환경 변수 GCP_PROJECT_ID가 필요합니다.")
        if not self.gcp_bucket_name:
            logger.critical("❗ 환경 변수 GCP_BUCKET_NAME이 누락되었습니다.")
            raise ValueError("환경 변수 GCP_BUCKET_NAME가 필요합니다.")
        if not self.elevenlabs_voice_id:
            logger.critical("❗ 환경 변수 ELEVENLABS_VOICE_ID가 누락되었습니다.")
            raise ValueError("환경 변수 ELEVENLABS_VOICE_ID가 필요합니다.")

        logger.info(f"✅ GCP_PROJECT_ID: {self.gcp_project_id}")
        logger.info(f"✅ GCP_BUCKET_NAME: {self.gcp_bucket_name}")
        logger.info(f"✅ ELEVENLABS_VOICE_ID: {self.elevenlabs_voice_id}")

        try:
            logger.info("🔐 Secret Manager 클라이언트 초기화 중...")
            self.secret_manager_client = secretmanager.SecretManagerServiceClient()

            # Secret 경로 설정 (여기는 secret_id까지만 설정해도 됩니다. 버전은 access_secret_version에서 추가)
            self.youtube_client_id_secret_name = self.secret_manager_client.secret_path(
                self.gcp_project_id, "youtube-client-id"
            )
            self.youtube_client_secret_secret_name = self.secret_manager_client.secret_path(
                self.gcp_project_id, "youtube-client-secret"
            )
            self.youtube_refresh_token_secret_name = self.secret_manager_client.secret_path(
                self.gcp_project_id, "youtube-refresh-token"
            )
            self.elevenlabs_api_key_secret_name = self.secret_manager_client.secret_path(
                self.gcp_project_id, "elevenlabs-api-key"
            )

            logger.debug("🧪 Secret 테스트 로드 중...")
            yt_test = self.get_youtube_client_id()
            logger.debug(f"✅ YOUTUBE_CLIENT_ID 확인 성공 (앞 5자): {yt_test[:5]}...")
            el_test = self.get_elevenlabs_api_key()
            logger.debug(f"✅ ELEVENLABS_API_KEY 확인 성공 (앞 5자): {el_test[:5]}...")

        except Exception as e:
            logger.critical("🔥 Secret Manager 초기화 중 오류 발생", exc_info=True)
            raise RuntimeError(f"Secret Manager 접근 실패: {e}")

        logger.info("✅ Config 초기화 완료.")

    # ⬇️ Secret Manager에서 시크릿 가져오는 내부 메서드
    def _access_secret_version(self, secret_name_base): # 변경: secret_name_base로 이름 변경
        try:
            # 이 부분이 중요합니다: secret_name_base에 '/versions/latest'를 추가
            secret_version_name = f"{secret_name_base}/versions/latest"
            logger.debug(f"시크릿 버전 접근 시도: {secret_version_name}")
            response = self.secret_manager_client.access_secret_version(
                request={"name": secret_version_name}
            )
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"❌ 시크릿 접근 실패 - {secret_name_base}", exc_info=True)
            logger.error("⚠️ Secret Manager에 올바른 IAM 권한이 있는지, 시크릿 이름이 정확한지, 버전이 'latest'로 유효한지 확인하세요.")
            raise

    # ⬇️ 공개 Getter 메서드들 (이 부분은 수정할 필요 없습니다. _access_secret_version이 변경되었으므로)
    def get_youtube_client_id(self):
        return self._access_secret_version(self.youtube_client_id_secret_name)

    def get_youtube_client_secret(self):
        return self._access_secret_version(self.youtube_client_secret_secret_name)

    def get_youtube_refresh_token(self):
        return self._access_secret_version(self.youtube_refresh_token_secret_name)

    def get_elevenlabs_api_key(self):
        return self._access_secret_version(self.elevenlabs_api_key_secret_name)
