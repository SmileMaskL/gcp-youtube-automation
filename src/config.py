# src/config.py

import os
import logging
from google.cloud import secretmanager

# 로깅 기본 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Config:
    def __init__(self):
        logger.info("📦 Config 초기화 시작...")

        # ⬇️ 필수 환경 변수 로드
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

        # ⛔ 누락된 환경변수 확인
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

        # ⬇️ Secret Manager 클라이언트 초기화
        try:
            logger.info("🔐 Secret Manager 클라이언트 초기화 중...")
            self.secret_manager_client = secretmanager.SecretManagerServiceClient()

            # Secret 경로 설정 (명명 규칙: 소문자 + 하이픈 권장)
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

            # ⬇️ 테스트 로드로 시크릿 접근 확인
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
    def _access_secret_version(self, secret_name):
        try:
            response = self.secret_manager_client.access_secret_version(
                request={"name": secret_name}
            )
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"❌ 시크릿 접근 실패 - {secret_name}", exc_info=True)
            logger.error("⚠️ Secret Manager에 올바른 IAM 권한이 있는지 확인하세요.")
            raise

    # ⬇️ 공개 Getter 메서드들
    def get_youtube_client_id(self):
        return self._access_secret_version(self.youtube_client_id_secret_name)

    def get_youtube_client_secret(self):
        return self._access_secret_version(self.youtube_client_secret_secret_name)

    def get_youtube_refresh_token(self):
        return self._access_secret_version(self.youtube_refresh_token_secret_name)

    def get_elevenlabs_api_key(self):
        return self._access_secret_version(self.elevenlabs_api_key_secret_name)
